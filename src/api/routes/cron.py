"""Serverless-friendly cron endpoint (for Vercel Cron)."""

from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException

from src.utils.logging import get_logger
from src.utils.runtime import is_vercel
from src.security.auth import require_godfather


logger = get_logger(__name__)
router = APIRouter()


def _is_vercel_cron(request: Request) -> bool:
    """
    Vercel Cron adds an `x-vercel-cron` header.
    We treat this as the primary signal for allowing unauthenticated cron invocation.
    """
    return (request.headers.get("x-vercel-cron") or "").strip() == "1"


@router.get("/cron/tick")
async def cron_tick(request: Request):
    """
    Periodic maintenance tick.
    - Safe to run on Vercel (no infinite loops)
    - On Vercel: only accepts requests with x-vercel-cron=1
    - Off Vercel: requires Godfather token (manual admin trigger)
    """
    if is_vercel():
        if not _is_vercel_cron(request):
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        # Manual/admin usage in non-Vercel environments.
        require_godfather(request)

    results = {}

    # 1) Reminders (best-effort)
    try:
        from src.calendar.reminders import ReminderEngine

        await ReminderEngine().run_once()
        results["reminders"] = {"ok": True}
    except Exception as e:
        logger.warning("cron_reminders_failed", error=str(e))
        results["reminders"] = {"ok": False, "error": str(e)}

    # 2) Messaging conversation summarization (best-effort)
    try:
        from src.messaging.background_tasks import _messaging_background_tasks

        await _messaging_background_tasks.process_conversation_summaries()
        results["messaging_summaries"] = {"ok": True}
    except Exception as e:
        logger.warning("cron_messaging_summaries_failed", error=str(e))
        results["messaging_summaries"] = {"ok": False, "error": str(e)}

    # 3) Expire old suggestions (best-effort)
    try:
        from src.database.database import SessionLocal
        from src.orchestrator.suggestion_manager import SuggestionManager

        db = SessionLocal()
        try:
            count = SuggestionManager.expire_old_suggestions(db)
        finally:
            db.close()
        results["expire_suggestions"] = {"ok": True, "expired": count}
    except Exception as e:
        logger.warning("cron_expire_suggestions_failed", error=str(e))
        results["expire_suggestions"] = {"ok": False, "error": str(e)}

    # 4) Budget checks (best-effort)
    try:
        from src.database.database import SessionLocal
        from src.cost.budget_manager import BudgetManager

        budget_manager = BudgetManager()
        db = SessionLocal()
        try:
            alerts = budget_manager.check_budgets(db)
        finally:
            db.close()
        results["budget_check"] = {"ok": True, "alerts": len(alerts or [])}
    except Exception as e:
        logger.warning("cron_budget_check_failed", error=str(e))
        results["budget_check"] = {"ok": False, "error": str(e)}

    # 5) Email ingestion (best-effort, runs before relationship ops to ensure fresh data)
    try:
        from src.database.database import SessionLocal
        from src.api.routes.email_ingest import _ingest_gmail_messages, _ingest_outlook_messages

        db = SessionLocal()
        try:
            gmail_result = await _ingest_gmail_messages(db, max_messages=30, query="newer_than:6h")
            outlook_result = await _ingest_outlook_messages(db, max_messages=30)
            results["email_ingest"] = {
                "ok": True,
                "gmail": {"ingested": gmail_result.ingested, "skipped": gmail_result.skipped},
                "outlook": {"ingested": outlook_result.ingested, "skipped": outlook_result.skipped},
            }
        finally:
            db.close()
    except Exception as e:
        logger.warning("cron_email_ingest_failed", error=str(e))
        results["email_ingest"] = {"ok": False, "error": str(e)}

    # 6) Relationship ops scheduler (runs at 7:00, 12:00, 15:00, 20:00 ET)
    # The service has built-in dedup (won't re-run if already completed today for that run_type).
    try:
        from datetime import datetime
        import pytz
        from src.database.database import SessionLocal
        from src.orchestrator.relationship_ops import RelationshipOpsService

        tz = pytz.timezone("America/New_York")
        now = datetime.now(tz)
        current_hour = now.hour

        # Map current hour to run_type (if applicable)
        hour_to_run_type = {
            7: "morning",
            12: "midday",
            15: "afternoon",
            20: "evening",
        }

        run_type = hour_to_run_type.get(current_hour)
        if run_type:
            db = SessionLocal()
            try:
                service = RelationshipOpsService()
                # execute_run returns existing run if already completed today (dedup built-in)
                result = service.execute_run(db, run_type)
                results["relationship_ops"] = {
                    "ok": True,
                    "run_type": run_type,
                    "run_id": result.id,
                    "actions": len(result.top_actions or []),
                    "status": result.status,
                }
                logger.info(
                    "cron_relationship_ops_triggered",
                    run_type=run_type,
                    run_id=result.id,
                    status=result.status,
                )
            finally:
                db.close()
        else:
            results["relationship_ops"] = {"ok": True, "skipped": True, "reason": f"hour_{current_hour}_not_scheduled"}
    except Exception as e:
        logger.warning("cron_relationship_ops_failed", error=str(e))
        results["relationship_ops"] = {"ok": False, "error": str(e)}

    return {"ok": True, "results": results}


