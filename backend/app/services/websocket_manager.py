from fastapi import WebSocket
from typing import Dict, List
import json
import structlog
from ..models.schemas import WebSocketMessage

logger = structlog.get_logger()

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info("WebSocket connected", client_id=client_id)

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from session connections
        for session_id, clients in self.session_connections.items():
            if client_id in clients:
                clients.remove(client_id)
                if not clients:
                    del self.session_connections[session_id]
                break
        
        logger.info("WebSocket disconnected", client_id=client_id)

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def send_session_update(self, session_id: str, message: WebSocketMessage):
        if session_id in self.session_connections:
            message_json = message.model_dump_json()
            for client_id in self.session_connections[session_id]:
                if client_id in self.active_connections:
                    try:
                        await self.active_connections[client_id].send_text(message_json)
                    except Exception as e:
                        logger.error("Failed to send message", 
                                   client_id=client_id, error=str(e))
                        # Remove failed connection
                        self.disconnect(client_id)

    def subscribe_to_session(self, client_id: str, session_id: str):
        if session_id not in self.session_connections:
            self.session_connections[session_id] = []
        
        if client_id not in self.session_connections[session_id]:
            self.session_connections[session_id].append(client_id)
        
        logger.info("Client subscribed to session", 
                   client_id=client_id, session_id=session_id)