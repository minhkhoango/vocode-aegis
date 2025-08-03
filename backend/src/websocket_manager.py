# backend/src/websocket_manager.py
import json
import logging
from typing import List

from fastapi import WebSocket

from .models import DashboardMetrics

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        if websocket.client:
            logger.debug(f"WebSocket client info: {websocket.client.host}:{websocket.client.port}")

    def disconnect(self, websocket: WebSocket) -> None:
        try:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        except ValueError:
            logger.warning("Attempted to remove non-existent WebSocket from active connections.")

    async def broadcast_metrics(self, metrics: DashboardMetrics) -> None:
        disconnected_connections: List[WebSocket] = []
        
        # Debug logging for financial metrics
        logger.info(f"Broadcasting metrics - Active connections: {len(self.active_connections)}, "
                   f"Financial Impact: {metrics.financial_impact}")
        
        for connection in self.active_connections:
            try:
                # Convert Pydantic model to dict and handle datetime serialization
                metrics_dict = metrics.model_dump(mode='json')
                await connection.send_text(json.dumps(metrics_dict))
                logger.debug(f"Successfully sent metrics to WebSocket")
            except RuntimeError as e: # Catch specific runtime errors for disconnected sockets
                logger.warning(f"Failed to send to WebSocket (likely disconnected): {e}")
                disconnected_connections.append(connection)
            except Exception as e:
                logger.exception(f"Error broadcasting to WebSocket: {e}")
                disconnected_connections.append(connection)

        # Clean up disconnected clients
        for conn in disconnected_connections:
            self.disconnect(conn) 