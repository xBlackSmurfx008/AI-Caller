"""WebSocket routes for real-time updates"""

import socketio
from typing import Optional
import jwt
from jose import JWTError
from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Create Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode='asgi'
)

# Store connected clients and their user IDs
connected_clients = set()
client_user_map = {}  # Map sid -> user_id


def get_token_from_query(query_string: str) -> Optional[str]:
    """Extract token from query string"""
    if not query_string:
        return None
    params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
    return params.get('token')


def verify_token(token: str) -> bool:
    """Verify JWT token"""
    try:
        jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return True
    except JWTError:
        return False


def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    query_string = environ.get('QUERY_STRING', '')
    token = get_token_from_query(query_string)
    
    # Enforce authentication based on environment
    if settings.APP_ENV == "production":
        # In production, require authentication
        if not token:
            logger.warning("websocket_auth_missing", sid=sid)
            return False
        if not verify_token(token):
            logger.warning("websocket_auth_failed", sid=sid)
            return False
    else:
        # In development, allow connections without token but verify if provided
        if token and not verify_token(token):
            logger.warning("websocket_auth_failed", sid=sid)
            return False
    
    # Extract user ID from token and store mapping
    if token:
        user_id = get_user_id_from_token(token)
        if user_id:
            client_user_map[sid] = user_id
            # Automatically subscribe to user's notification room
            await sio.enter_room(sid, f"user:{user_id}")
            logger.info("websocket_user_subscribed", sid=sid, user_id=user_id)
    
    connected_clients.add(sid)
    logger.info("websocket_client_connected", sid=sid)
    return True


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    connected_clients.discard(sid)
    # Clean up user mapping
    if sid in client_user_map:
        user_id = client_user_map.pop(sid)
        await sio.leave_room(sid, f"user:{user_id}")
    logger.info("websocket_client_disconnected", sid=sid)


@sio.event
async def subscribe(sid, data):
    """Handle subscription requests"""
    subscription_type = data.get('type')
    
    if subscription_type == 'all_calls':
        await sio.enter_room(sid, 'all_calls')
        logger.info("websocket_subscribed", sid=sid, room='all_calls')
    elif subscription_type == 'call' and data.get('call_id'):
        room = f"call:{data['call_id']}"
        await sio.enter_room(sid, room)
        logger.info("websocket_subscribed", sid=sid, room=room)
    elif subscription_type == 'notifications':
        # Subscribe to notifications for the authenticated user
        # User ID should be extracted from token during connection
        # For now, we'll use a general notifications room
        await sio.enter_room(sid, 'notifications')
        logger.info("websocket_subscribed", sid=sid, room='notifications')


@sio.event
async def unsubscribe(sid, data):
    """Handle unsubscription requests"""
    subscription_type = data.get('type')
    
    if subscription_type == 'all_calls':
        await sio.leave_room(sid, 'all_calls')
    elif subscription_type == 'call' and data.get('call_id'):
        room = f"call:{data['call_id']}"
        await sio.leave_room(sid, room)
    
    logger.info("websocket_unsubscribed", sid=sid)


# Event emitter functions
async def emit_call_started(call_data: dict):
    """Emit call.started event"""
    await sio.emit('call.started', {'call': call_data}, room='all_calls')
    await sio.emit('call.started', {'call': call_data}, room=f"call:{call_data.get('id')}")


async def emit_call_updated(call_data: dict):
    """Emit call.updated event"""
    await sio.emit('call.updated', {'call': call_data}, room='all_calls')
    await sio.emit('call.updated', {'call': call_data}, room=f"call:{call_data.get('id')}")


async def emit_call_ended(call_id: str):
    """Emit call.ended event"""
    await sio.emit('call.ended', {'call_id': call_id}, room='all_calls')
    await sio.emit('call.ended', {'call_id': call_id}, room=f"call:{call_id}")


async def emit_interaction_added(call_id: str, interaction_data: dict):
    """Emit interaction.added event"""
    await sio.emit('interaction.added', {
        'call_id': call_id,
        'interaction': interaction_data
    }, room='all_calls')
    await sio.emit('interaction.added', {
        'call_id': call_id,
        'interaction': interaction_data
    }, room=f"call:{call_id}")


async def emit_qa_score_updated(call_id: str, qa_score_data: dict):
    """Emit qa.score.updated event"""
    await sio.emit('qa.score.updated', {
        'call_id': call_id,
        'qa_score': qa_score_data
    }, room='all_calls')
    await sio.emit('qa.score.updated', {
        'call_id': call_id,
        'qa_score': qa_score_data
    }, room=f"call:{call_id}")


async def emit_sentiment_changed(call_id: str, sentiment_data: dict):
    """Emit sentiment.changed event"""
    await sio.emit('sentiment.changed', {
        'call_id': call_id,
        'sentiment': sentiment_data
    }, room='all_calls')
    await sio.emit('sentiment.changed', {
        'call_id': call_id,
        'sentiment': sentiment_data
    }, room=f"call:{call_id}")


async def emit_escalation_triggered(call_id: str, escalation_data: dict):
    """Emit escalation.triggered event"""
    await sio.emit('escalation.triggered', {
        'call_id': call_id,
        'escalation': escalation_data
    }, room='all_calls')
    await sio.emit('escalation.triggered', {
        'call_id': call_id,
        'escalation': escalation_data
    }, room=f"call:{call_id}")


async def emit_escalation_completed(call_id: str, escalation_data: dict):
    """Emit escalation.completed event"""
    await sio.emit('escalation.completed', {
        'call_id': call_id,
        'escalation': escalation_data
    }, room='all_calls')
    await sio.emit('escalation.completed', {
        'call_id': call_id,
        'escalation': escalation_data
    }, room=f"call:{call_id}")


async def emit_notification_created(user_id: str, notification_data: dict):
    """Emit notification.created event to specific user"""
    # Emit to user-specific room
    await sio.emit('notification.created', {
        'notification': notification_data
    }, room=f"user:{user_id}")
    # Also emit to general notifications room for any listeners
    await sio.emit('notification.created', {
        'notification': notification_data
    }, room='notifications')

