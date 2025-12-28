"""Quality assurance monitoring"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy.orm import Session

from src.database.database import get_db
from src.database.models import Call, QAScore, Notification, BusinessConfig
from src.qa.sentiment_analyzer import SentimentAnalyzer
from src.qa.compliance_checker import ComplianceChecker
from src.utils.logging import get_logger
import uuid

logger = get_logger(__name__)


class QAMonitor:
    """Real-time quality assurance monitoring"""

    def __init__(self):
        """Initialize QA monitor"""
        self.sentiment_analyzer = SentimentAnalyzer()
        self.compliance_checker = ComplianceChecker()

    async def analyze_interaction(
        self,
        call_id: str,
        interaction_text: str,
        speaker: str,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a single interaction for quality
        
        Args:
            call_id: Call identifier
            interaction_text: Interaction text
            speaker: "ai" or "customer"
            db: Database session
            
        Returns:
            Analysis results dictionary
        """
        try:
            analysis = {
                "timestamp": datetime.utcnow(),
                "speaker": speaker,
                "text": interaction_text,
            }

            # Sentiment analysis
            sentiment_result = self.sentiment_analyzer.analyze(interaction_text)
            analysis["sentiment"] = sentiment_result

            # Compliance check (only for AI responses)
            if speaker == "ai":
                compliance_result = self.compliance_checker.check(interaction_text)
                analysis["compliance"] = compliance_result

            logger.debug("interaction_analyzed", call_id=call_id, speaker=speaker)

            return analysis

        except Exception as e:
            logger.error("interaction_analysis_error", error=str(e), call_id=call_id)
            return {}

    async def score_call(
        self,
        call_id: str,
        db: Optional[Session] = None,
    ) -> QAScore:
        """
        Generate QA score for a completed call
        
        Args:
            call_id: Call identifier
            db: Database session
            
        Returns:
            QAScore model instance
        """
        if db is None:
            db = next(get_db())

        try:
            # Get call and interactions
            call = db.query(Call).filter(Call.id == call_id).first()
            if not call:
                raise ValueError(f"Call not found: {call_id}")

            interactions = call.interactions
            if not interactions:
                raise ValueError(f"No interactions found for call: {call_id}")

            # Analyze all interactions
            analyses = []
            for interaction in interactions:
                analysis = await self.analyze_interaction(
                    call_id=call_id,
                    interaction_text=interaction.text,
                    speaker=interaction.speaker,
                    db=db,
                )
                analyses.append(analysis)

            # Calculate scores
            scores = self._calculate_scores(analyses)

            # Create QA score record
            qa_score = QAScore(
                call_id=call_id,
                overall_score=scores["overall"],
                sentiment_score=scores["sentiment"],
                compliance_score=scores["compliance"],
                accuracy_score=scores["accuracy"],
                professionalism_score=scores["professionalism"],
                sentiment_label=scores["sentiment_label"],
                compliance_issues=scores["compliance_issues"],
                flagged_issues=scores["flagged_issues"],
                reviewed_by="auto",
            )

            db.add(qa_score)
            db.commit()
            db.refresh(qa_score)

            # Check if QA score is below threshold and create notification
            min_score_threshold = 0.6  # Default threshold, could come from business config
            if qa_score.overall_score < min_score_threshold:
                # Get business config owner to notify
                if call.business_id:
                    business_config = db.query(BusinessConfig).filter(
                        BusinessConfig.id == call.business_id
                    ).first()
                    if business_config and business_config.created_by_user_id:
                        notification = Notification(
                            id=str(uuid.uuid4()),
                            user_id=business_config.created_by_user_id,
                            type="qa_alert",
                            title=f"Low QA Score Alert - Call {call_id[:8]}...",
                            message=f"Call scored {qa_score.overall_score:.2f} (below threshold of {min_score_threshold}). Issues: {', '.join(qa_score.flagged_issues or [])}",
                            read=False,
                            metadata={
                                "call_id": call_id,
                                "qa_score_id": qa_score.id,
                                "overall_score": qa_score.overall_score,
                                "flagged_issues": qa_score.flagged_issues or [],
                            },
                            action_url=f"/calls/{call_id}",
                        )
                        db.add(notification)
                        db.commit()
                        db.refresh(notification)
                        
                        # Emit notification event
                        try:
                            from src.api.routes.websocket import emit_notification_created
                            import asyncio
                            
                            notification_data = {
                                "id": notification.id,
                                "type": notification.type,
                                "title": notification.title,
                                "message": notification.message,
                                "read": notification.read,
                                "created_at": notification.created_at.isoformat(),
                                "metadata": notification.metadata,
                                "action_url": notification.action_url,
                            }
                            
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    asyncio.create_task(emit_notification_created(business_config.created_by_user_id, notification_data))
                                else:
                                    loop.run_until_complete(emit_notification_created(business_config.created_by_user_id, notification_data))
                            except RuntimeError:
                                asyncio.run(emit_notification_created(business_config.created_by_user_id, notification_data))
                        except Exception as e:
                            logger.warning("notification_emit_failed", error=str(e), call_id=call_id)

            # Emit WebSocket events
            try:
                from src.api.routes.websocket import emit_qa_score_updated, emit_sentiment_changed
                import asyncio
                
                qa_score_data = {
                    "id": qa_score.id,
                    "call_id": qa_score.call_id,
                    "overall_score": qa_score.overall_score,
                    "sentiment_score": qa_score.sentiment_score,
                    "compliance_score": qa_score.compliance_score,
                    "accuracy_score": qa_score.accuracy_score,
                    "professionalism_score": qa_score.professionalism_score,
                    "sentiment_label": qa_score.sentiment_label,
                    "compliance_issues": qa_score.compliance_issues or [],
                    "flagged_issues": qa_score.flagged_issues or [],
                }
                
                sentiment_data = {
                    "score": qa_score.sentiment_score or 0.0,
                    "label": qa_score.sentiment_label or "neutral",
                }
                
                # Emit events (run in event loop if available)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(emit_qa_score_updated(call_id, qa_score_data))
                        asyncio.create_task(emit_sentiment_changed(call_id, sentiment_data))
                    else:
                        loop.run_until_complete(emit_qa_score_updated(call_id, qa_score_data))
                        loop.run_until_complete(emit_sentiment_changed(call_id, sentiment_data))
                except RuntimeError:
                    # No event loop, create new one
                    asyncio.run(emit_qa_score_updated(call_id, qa_score_data))
                    asyncio.run(emit_sentiment_changed(call_id, sentiment_data))
            except Exception as e:
                logger.warning("websocket_emit_failed", error=str(e), call_id=call_id)

            logger.info("call_scored", call_id=call_id, overall_score=scores["overall"])

            return qa_score

        except Exception as e:
            db.rollback()
            logger.error("call_scoring_error", error=str(e), call_id=call_id)
            raise

    def _calculate_scores(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate QA scores from analyses
        
        Args:
            analyses: List of interaction analyses
            
        Returns:
            Dictionary of scores
        """
        if not analyses:
            return {
                "overall": 0.0,
                "sentiment": 0.0,
                "compliance": 1.0,
                "accuracy": 0.0,
                "professionalism": 0.0,
                "sentiment_label": "neutral",
                "compliance_issues": [],
                "flagged_issues": [],
            }

        # Aggregate sentiment scores
        sentiment_scores = [
            a.get("sentiment", {}).get("score", 0.0)
            for a in analyses
            if "sentiment" in a
        ]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0

        # Determine sentiment label
        if avg_sentiment > 0.1:
            sentiment_label = "positive"
        elif avg_sentiment < -0.1:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"

        # Aggregate compliance issues
        compliance_issues = []
        for analysis in analyses:
            if "compliance" in analysis:
                issues = analysis["compliance"].get("issues", [])
                compliance_issues.extend(issues)

        # Calculate compliance score (1.0 if no issues, decreasing with issues)
        compliance_score = max(0.0, 1.0 - (len(compliance_issues) * 0.1))

        # Calculate professionalism (based on sentiment and compliance)
        professionalism_score = (avg_sentiment + 1.0) / 2.0  # Normalize to 0-1
        if compliance_issues:
            professionalism_score *= 0.8  # Penalize for compliance issues

        # Accuracy score (placeholder - would need ground truth)
        accuracy_score = 0.8  # Default assumption

        # Overall score (weighted average)
        overall_score = (
            (avg_sentiment + 1.0) / 2.0 * 0.3 +  # Sentiment (30%)
            compliance_score * 0.3 +  # Compliance (30%)
            accuracy_score * 0.2 +  # Accuracy (20%)
            professionalism_score * 0.2  # Professionalism (20%)
        )

        # Flag issues
        flagged_issues = []
        if avg_sentiment < -0.3:
            flagged_issues.append("negative_sentiment")
        if compliance_issues:
            flagged_issues.append("compliance_issues")
        if overall_score < 0.5:
            flagged_issues.append("low_overall_score")

        return {
            "overall": round(overall_score, 3),
            "sentiment": round(avg_sentiment, 3),
            "compliance": round(compliance_score, 3),
            "accuracy": round(accuracy_score, 3),
            "professionalism": round(professionalism_score, 3),
            "sentiment_label": sentiment_label,
            "compliance_issues": list(set(compliance_issues)),
            "flagged_issues": flagged_issues,
        }

