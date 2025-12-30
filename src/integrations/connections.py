"""Integration connection verification and wiring"""

from typing import Dict, Any, List, Optional
from src.utils.logging import get_logger
from src.integrations.manager import get_integration_manager, IntegrationStatus
from src.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class IntegrationConnections:
    """Manages and verifies connections between integrations and services"""
    
    def __init__(self):
        """Initialize connection manager"""
        self.integration_manager = get_integration_manager()
        self.connections: Dict[str, List[str]] = {}
    
    def verify_all_connections(self) -> Dict[str, Any]:
        """
        Verify all integration connections and service dependencies
        
        Returns:
            Dictionary with connection status for each integration
        """
        logger.info("verifying_all_integration_connections")
        
        # Ensure integrations are initialized
        if not self.integration_manager._initialized:
            self.integration_manager.initialize_all()
        
        results = {
            "integrations": {},
            "services": {},
            "dependencies": {},
            "overall_status": "healthy"
        }
        
        # Verify each integration
        integration_statuses = self.integration_manager.get_all_status()
        
        for name, info in integration_statuses.items():
            results["integrations"][name] = {
                "status": info.status.value,
                "message": info.message,
                "error": info.error,
                "connected": info.status == IntegrationStatus.CONNECTED
            }
        
        # Verify service connections
        service_results = self._verify_service_connections()
        results["services"] = service_results
        
        # Verify dependencies
        dependency_results = self._verify_dependencies()
        results["dependencies"] = dependency_results
        
        # Determine overall status
        critical_failures = [
            name for name, info in integration_statuses.items()
            if info.status == IntegrationStatus.ERROR
            and name in ["database", "openai"]
        ]
        
        if critical_failures:
            results["overall_status"] = "unhealthy"
        elif any(info.status == IntegrationStatus.ERROR for info in integration_statuses.values()):
            results["overall_status"] = "degraded"
        
        logger.info(
            "integration_connections_verified",
            overall_status=results["overall_status"],
            connected_integrations=sum(
                1 for info in integration_statuses.values()
                if info.status == IntegrationStatus.CONNECTED
            )
        )
        
        return results
    
    def _verify_service_connections(self) -> Dict[str, Any]:
        """Verify that services can access their required integrations"""
        results = {}
        
        # Verify TwilioService
        try:
            from src.telephony.twilio_client import TwilioService
            twilio_service = TwilioService()
            results["twilio_service"] = {
                "status": "connected",
                "phone_number": twilio_service.phone_number,
                "client_initialized": twilio_service.client is not None
            }
        except Exception as e:
            results["twilio_service"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Verify MemoryService
        try:
            from src.memory.memory_service import MemoryService
            memory_service = MemoryService()
            results["memory_service"] = {
                "status": "connected",
                "client_initialized": memory_service.client is not None,
                "model": memory_service.model
            }
        except Exception as e:
            results["memory_service"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Verify VoiceAssistant
        try:
            from src.agent.assistant import VoiceAssistant
            voice_assistant = VoiceAssistant()
            results["voice_assistant"] = {
                "status": "connected",
                "client_initialized": voice_assistant.client is not None,
                "model": voice_assistant.model,
                "orchestrator_connected": voice_assistant.orchestrator is not None
            }
        except Exception as e:
            results["voice_assistant"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Verify MessagingService
        try:
            from src.messaging.messaging_service import MessagingService
            messaging_service = MessagingService()
            results["messaging_service"] = {
                "status": "connected",
                "twilio_connected": messaging_service.twilio is not None,
                "memory_connected": messaging_service.memory_service is not None
            }
        except Exception as e:
            results["messaging_service"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Verify OrchestratorService
        try:
            from src.orchestrator.orchestrator_service import OrchestratorService
            orchestrator_service = OrchestratorService()
            results["orchestrator_service"] = {
                "status": "connected",
                "client_initialized": orchestrator_service.client is not None,
                "model": orchestrator_service.model
            }
        except Exception as e:
            results["orchestrator_service"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Verify Database connection
        try:
            from src.database.database import SessionLocal, engine
            from sqlalchemy import text
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
                db.commit()
                results["database"] = {
                    "status": "connected",
                    "engine_initialized": engine is not None
                }
            finally:
                db.close()
        except Exception as e:
            results["database"] = {
                "status": "error",
                "error": str(e)
            }
        
        return results
    
    def _verify_dependencies(self) -> Dict[str, Any]:
        """Verify that service dependencies are properly wired"""
        dependencies = {
            "messaging_service": {
                "requires": ["twilio", "openai", "database"],
                "status": "unknown"
            },
            "voice_assistant": {
                "requires": ["openai", "database"],
                "status": "unknown"
            },
            "memory_service": {
                "requires": ["openai", "database"],
                "status": "unknown"
            },
            "orchestrator_service": {
                "requires": ["openai", "database"],
                "status": "unknown"
            },
            "tools": {
                "requires": ["twilio", "smtp", "google_calendar", "gmail", "outlook"],
                "status": "unknown"
            }
        }
        
        integration_statuses = self.integration_manager.get_all_status()
        
        for service_name, deps in dependencies.items():
            required = deps["requires"]
            missing = []
            disconnected = []
            
            for req in required:
                if req not in integration_statuses:
                    missing.append(req)
                elif integration_statuses[req].status != IntegrationStatus.CONNECTED:
                    if integration_statuses[req].status == IntegrationStatus.DISCONNECTED:
                        disconnected.append(req)
                    else:
                        missing.append(req)
            
            if missing:
                dependencies[service_name]["status"] = "missing_dependencies"
                dependencies[service_name]["missing"] = missing
            elif disconnected:
                dependencies[service_name]["status"] = "disconnected_dependencies"
                dependencies[service_name]["disconnected"] = disconnected
            else:
                dependencies[service_name]["status"] = "ready"
        
        return dependencies
    
    def get_connection_summary(self) -> Dict[str, Any]:
        """Get a summary of all connections"""
        verification = self.verify_all_connections()
        
        summary = {
            "overall": verification["overall_status"],
            "integrations_ready": sum(
                1 for info in verification["integrations"].values()
                if info["connected"]
            ),
            "total_integrations": len(verification["integrations"]),
            "services_ready": sum(
                1 for info in verification["services"].values()
                if info.get("status") == "connected"
            ),
            "total_services": len(verification["services"]),
            "dependencies_ready": sum(
                1 for deps in verification["dependencies"].values()
                if deps.get("status") == "ready"
            ),
            "total_dependencies": len(verification["dependencies"])
        }
        
        return summary


# Singleton instance
_connection_manager: Optional[IntegrationConnections] = None


def get_connection_manager() -> IntegrationConnections:
    """Get singleton connection manager instance"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = IntegrationConnections()
    return _connection_manager

