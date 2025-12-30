"""Service Registry - Centralized service instance management"""

from typing import Dict, Any, Optional, TypeVar, Type
from functools import lru_cache

from src.utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class ServiceRegistry:
    """Centralized registry for service instances (singleton pattern)"""
    
    def __init__(self):
        """Initialize service registry"""
        self._services: Dict[str, Any] = {}
        self._initialized = False
    
    def register(self, name: str, service: Any) -> None:
        """Register a service instance"""
        if name in self._services:
            logger.warning("service_already_registered", service_name=name)
        self._services[name] = service
        logger.debug("service_registered", service_name=name, service_type=type(service).__name__)
    
    def get(self, name: str) -> Optional[Any]:
        """Get a service instance by name"""
        return self._services.get(name)
    
    def get_or_create(self, name: str, factory: callable) -> Any:
        """Get existing service or create new one using factory"""
        if name not in self._services:
            logger.info("creating_service", service_name=name)
            service = factory()
            self.register(name, service)
        return self._services[name]
    
    def has(self, name: str) -> bool:
        """Check if service is registered"""
        return name in self._services
    
    def initialize_services(self) -> None:
        """Initialize all core services"""
        if self._initialized:
            return
        
        logger.info("initializing_service_registry")
        
        # Initialize services in dependency order
        from src.telephony.twilio_client import TwilioService
        from src.messaging.messaging_service import MessagingService
        from src.memory.memory_service import MemoryService
        from src.agent.assistant import VoiceAssistant
        from src.orchestrator.orchestrator_service import OrchestratorService
        from src.voice.realtime_bridge import RealtimeCallBridge
        
        # 1. TwilioService (no dependencies)
        twilio_service = TwilioService()
        self.register("twilio", twilio_service)
        
        # 2. MemoryService (depends on OpenAI, Database)
        memory_service = MemoryService()
        self.register("memory", memory_service)
        
        # 3. OrchestratorService (depends on OpenAI, Database)
        orchestrator_service = OrchestratorService()
        self.register("orchestrator", orchestrator_service)
        
        # 4. MessagingService (depends on TwilioService, MemoryService)
        messaging_service = MessagingService()
        self.register("messaging", messaging_service)
        
        # 5. VoiceAssistant (depends on OpenAI, OrchestratorService)
        voice_assistant = VoiceAssistant()
        self.register("voice_assistant", voice_assistant)
        
        # 6. RealtimeCallBridge (depends on VoiceAssistant)
        from src.voice.realtime_bridge import get_realtime_bridge as _get_realtime_bridge
        realtime_bridge = _get_realtime_bridge()
        self.register("realtime_bridge", realtime_bridge)
        
        self._initialized = True
        logger.info(
            "service_registry_initialized",
            services=list(self._services.keys())
        )
    
    def get_all(self) -> Dict[str, Any]:
        """Get all registered services"""
        return self._services.copy()


# Singleton instance
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get singleton service registry instance"""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry


# Convenience functions for common services
def get_twilio_service():
    """Get TwilioService instance"""
    registry = get_service_registry()
    if not registry.has("twilio"):
        registry.initialize_services()
    return registry.get("twilio")


def get_messaging_service():
    """Get MessagingService instance"""
    registry = get_service_registry()
    if not registry.has("messaging"):
        registry.initialize_services()
    return registry.get("messaging")


def get_memory_service():
    """Get MemoryService instance"""
    registry = get_service_registry()
    if not registry.has("memory"):
        registry.initialize_services()
    return registry.get("memory")


def get_voice_assistant():
    """Get VoiceAssistant instance"""
    registry = get_service_registry()
    if not registry.has("voice_assistant"):
        registry.initialize_services()
    return registry.get("voice_assistant")


def get_orchestrator_service():
    """Get OrchestratorService instance"""
    registry = get_service_registry()
    if not registry.has("orchestrator"):
        registry.initialize_services()
    return registry.get("orchestrator")


def get_realtime_bridge():
    """Get RealtimeCallBridge instance"""
    from src.voice.realtime_bridge import get_realtime_bridge as _get_realtime_bridge
    return _get_realtime_bridge()

