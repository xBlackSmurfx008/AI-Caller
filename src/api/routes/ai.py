"""AI capabilities and status API routes."""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, List

from src.utils.logging import get_logger
from src.utils.config import get_settings

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("/status")
async def get_ai_status() -> Dict[str, Any]:
    """
    Get AI system status including models and skills.
    
    Returns current configuration for:
    - Chat model (for task planning)
    - Realtime model (for voice conversations)
    - Available skills/tools
    - Integration status
    """
    try:
        from src.ai.model_manager import get_model_manager
        from src.ai.skill_manager import get_skill_manager
        
        model_manager = get_model_manager()
        skill_manager = get_skill_manager()
        
        return {
            "status": "ready",
            "models": {
                "chat": model_manager.chat_model,
                "realtime": model_manager.realtime_model,
                "voice": model_manager.realtime_voice,
            },
            "skills": skill_manager.get_status(),
            "realtime_enabled": bool(settings.TWILIO_MEDIA_STREAMS_ENABLED),
        }
    except Exception as e:
        logger.error("ai_status_error", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "models": {
                "chat": settings.OPENAI_MODEL,
                "realtime": settings.OPENAI_REALTIME_MODEL,
                "voice": settings.OPENAI_REALTIME_VOICE,
            },
        }


@router.get("/models")
async def list_models() -> Dict[str, Any]:
    """
    List all available OpenAI models and their capabilities.
    """
    try:
        from src.ai.model_manager import get_model_manager, MODEL_REGISTRY
        
        model_manager = get_model_manager()
        
        return {
            "configured": {
                "chat": model_manager.chat_model,
                "realtime": model_manager.realtime_model,
            },
            "available": model_manager.list_available_models(),
        }
    except Exception as e:
        logger.error("list_models_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skills")
async def list_skills() -> Dict[str, Any]:
    """
    List all available AI skills/tools.
    
    Returns skills organized by category with their:
    - Name and description
    - Risk level
    - Integration requirements
    - Approval requirements
    """
    try:
        from src.ai.skill_manager import get_skill_manager
        
        skill_manager = get_skill_manager()
        skills = skill_manager.get_available_skills(check_integrations=False)
        
        # Organize by category
        by_category: Dict[str, List[Dict[str, Any]]] = {}
        for skill in skills:
            cat = skill.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append({
                "name": skill.name,
                "description": skill.description,
                "risk": skill.risk.value,
                "requires_integration": skill.requires_integration,
                "requires_approval": skill.requires_approval,
                "enabled": skill.enabled,
            })
        
        return {
            "total": len(skills),
            "by_category": by_category,
            "integrations": skill_manager.get_status()["integrations"],
        }
    except Exception as e:
        logger.error("list_skills_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime/config")
async def get_realtime_config() -> Dict[str, Any]:
    """
    Get configuration for OpenAI Realtime API voice calls.
    
    Returns WebSocket URL, model, and session configuration.
    Note: Excludes API key for security.
    """
    try:
        from src.ai.model_manager import get_model_manager
        
        model_manager = get_model_manager()
        config = model_manager.get_realtime_config()
        
        # Remove sensitive data
        config.pop("headers", None)
        
        return {
            "enabled": bool(settings.TWILIO_MEDIA_STREAMS_ENABLED),
            "url": config.get("url"),
            "model": config.get("model"),
            "voice": config.get("voice"),
            "session_config": config.get("session_config"),
            "twilio_ws_url": settings.TWILIO_MEDIA_STREAMS_WS_BASE_URL or None,
        }
    except Exception as e:
        logger.error("realtime_config_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/chat")
async def test_chat_model(request: Request) -> Dict[str, Any]:
    """
    Test the chat model with a simple prompt.
    
    Body:
        prompt: Test prompt (optional, defaults to "Hello")
    """
    try:
        from src.ai.model_manager import get_model_manager, ModelPurpose
        
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
        prompt = body.get("prompt", "Hello, please respond with 'AI is working!'")
        
        model_manager = get_model_manager()
        client, config = model_manager.create_client_for_purpose(ModelPurpose.CHAT)
        
        response = client.chat.completions.create(
            model=config.name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7,
        )
        
        return {
            "success": True,
            "model": config.name,
            "response": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
        }
    except Exception as e:
        logger.error("test_chat_error", error=str(e))
        return {
            "success": False,
            "error": str(e),
        }

