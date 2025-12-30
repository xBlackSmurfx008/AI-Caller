"""Health check and integration status endpoints"""

from fastapi import APIRouter
from src.integrations.manager import get_integration_manager

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Voice Assistant"
    }


@router.get("/health/integrations")
async def integrations_health():
    """Detailed integration health check"""
    manager = get_integration_manager()
    
    # Verify all integrations if not already initialized
    if not manager._initialized:
        manager.initialize_all()
    else:
        manager.verify_all()
    
    summary = manager.get_health_summary()
    return summary


@router.get("/health/integrations/{integration_name}")
async def integration_status(integration_name: str):
    """Get status for a specific integration"""
    manager = get_integration_manager()
    
    # Initialize if needed
    if not manager._initialized:
        manager.initialize_all()
    
    # Re-verify the specific integration
    if integration_name == "database":
        info = manager.verify_database()
    elif integration_name == "openai":
        info = manager.verify_openai()
    elif integration_name == "twilio":
        info = manager.verify_twilio()
    elif integration_name == "google_calendar":
        info = manager.verify_google_calendar()
    elif integration_name == "gmail":
        info = manager.verify_gmail()
    elif integration_name == "outlook":
        info = manager.verify_outlook()
    elif integration_name == "smtp":
        info = manager.verify_smtp()
    else:
        return {
            "error": f"Unknown integration: {integration_name}",
            "available": ["database", "openai", "twilio", "google_calendar", "gmail", "outlook", "smtp"]
        }
    
    return {
        "name": info.name,
        "status": info.status.value,
        "message": info.message,
        "error": info.error,
        "config_required": info.config_required
    }


@router.get("/health/connections")
async def connections_health():
    """Detailed connection health check including services and dependencies"""
    from src.integrations.connections import get_connection_manager
    connection_manager = get_connection_manager()
    return connection_manager.verify_all_connections()


@router.get("/health/connections/summary")
async def connections_summary():
    """Get summary of all integration connections"""
    from src.integrations.connections import get_connection_manager
    connection_manager = get_connection_manager()
    return connection_manager.get_connection_summary()

