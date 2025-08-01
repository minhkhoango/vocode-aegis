# backend/src/api_endpoints.py
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, List

from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status

from .models import DashboardMetrics, ActiveCallsMetric, DemoErrorRequest, SimulateActiveCallsRequest
from .websocket_manager import ConnectionManager
from .metrics_aggregator import MetricsAggregator
from .redis_consumer import VocodeRedisConsumer

logger = logging.getLogger(__name__)

# Global variables for API endpoints
manager: ConnectionManager | None = None
redis_consumer: VocodeRedisConsumer | None = None
aggregator: MetricsAggregator | None = None

def set_global_dependencies(
    connection_manager: ConnectionManager,
    redis_consumer_instance: VocodeRedisConsumer | None,
    metrics_aggregator: MetricsAggregator
) -> None:
    """Set global dependencies for API endpoints."""
    global manager, redis_consumer, aggregator
    manager = connection_manager
    redis_consumer = redis_consumer_instance
    aggregator = metrics_aggregator

async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time metrics broadcasting."""
    if manager is None:
        await websocket.close(code=1008)  # Policy violation
        return
    
    await manager.connect(websocket)
    try:
        while True:
            if manager.active_connections and redis_consumer and aggregator: # Only send if there are active connections
                metrics = DashboardMetrics(
                    live_status=aggregator.calculate_live_status(redis_consumer),
                    active_calls=ActiveCallsMetric(
                        count=redis_consumer.active_calls,
                        timestamp=datetime.now()
                    ),
                    error_summary=aggregator.get_24h_error_summary(redis_consumer),
                    last_updated=datetime.now()
                )
                await manager.broadcast_metrics(metrics)
            
            # Use the environment variable for refresh interval
            refresh_interval_ms = int(os.getenv("DASHBOARD_REFRESH_INTERVAL", "5000"))
            await asyncio.sleep(refresh_interval_ms / 1000.0)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
    except Exception as e:
        logger.exception(f"Error in websocket_endpoint: {e}")
    finally:
        if manager:
            manager.disconnect(websocket) # Ensure disconnection is handled

async def inject_demo_error(request: DemoErrorRequest) -> Dict[str, str]:
    """
    Allows injecting simulated error events for demonstration purposes.
    NOTE: THIS ENDPOINT IS FOR DEMO/DEVELOPMENT ONLY AND SHOULD BE REMOVED OR SECURED IN PRODUCTION.
    """
    if redis_consumer is None:
        logger.error("Attempted to inject demo error, but Redis consumer is not initialized.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error: Redis consumer service not initialized."
        )

    injected_count = 0
    for _ in range(request.count):
        timestamp_ms = str(int(datetime.now().timestamp() * 1000))
        demo_error_data: Dict[str, Any] = {
            "timestamp": timestamp_ms,
            "error_type": request.error_type,
            "message": request.message,
            "severity": request.severity,
            "conversation_id": request.conversation_id
        }
        redis_consumer.error_buffer.append(demo_error_data)
        injected_count += 1
        logger.warning(f"DEMO MODE: Injected {request.severity.upper()} error: {request.error_type} - '{request.message}' (Count: {injected_count})")

    return {"message": f"Successfully injected {injected_count} errors of type '{request.error_type}' with severity '{request.severity}'.", "status": "success"}

async def simulate_active_calls(request: SimulateActiveCallsRequest) -> Dict[str, str]:
    """
    Allows simulating a specific number of active calls for demonstration purposes.
    NOTE: THIS ENDPOINT IS FOR DEMO/DEVELOPMENT ONLY AND SHOULD BE REMOVED OR SECURED IN PRODUCTION.
    """
    if redis_consumer is None:
        logger.error("Attempted to simulate active calls, but Redis consumer is not initialized.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error: Redis consumer service not initialized."
        )

    redis_consumer.active_calls = request.count
    logger.warning(f"DEMO MODE: Simulated active calls set to: {request.count}")

    return {"message": f"Successfully simulated {request.count} active calls.", "status": "success"}

async def reset_demo_state() -> Dict[str, str]:
    """
    Resets all demo-related states to their defaults.
    - Resets active calls to 0.
    - Clears the error buffer.
    NOTE: THIS ENDPOINT IS FOR DEMO/DEVELOPMENT ONLY.
    """
    if redis_consumer is None:
        logger.error("Attempted to reset demo state, but Redis consumer is not initialized.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error: Redis consumer service not initialized."
        )

    # Reset active calls
    redis_consumer.active_calls = 0
    
    # Clear the error buffer
    redis_consumer.error_buffer.clear()
    
    logger.warning("DEMO MODE: All demo states have been reset.")
    
    return {"message": "Successfully reset all demo states.", "status": "success"}

async def health_check() -> Dict[str, Any]:
    """Enhanced health check that includes Redis connectivity status and LiveStatus calculation."""
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "redis_connected": False,
        "active_calls": 0,
        "error_count": 0,
        "websocket_connections": 0,
        "live_status": None
    }
    
    # Check WebSocket connections
    if manager:
        health_status["websocket_connections"] = len(manager.active_connections)
    
    # Calculate LiveStatus for comprehensive health assessment
    if aggregator:
        live_status = aggregator.calculate_live_status(redis_consumer)
        health_status["live_status"] = {
            "status": live_status.status,
            "message": live_status.message,
            "last_updated": live_status.last_updated.isoformat()
        }
        
        # Prioritize LiveStatus over Redis connectivity for overall system health
        if live_status.status == "red":
            health_status["status"] = "degraded"
            health_status["message"] = f"System compromised: {live_status.message}"
        elif live_status.status == "yellow":
            health_status["status"] = "degraded"
            health_status["message"] = f"System warning: {live_status.message}"
        else:
            health_status["status"] = "healthy"
            health_status["message"] = live_status.message
    else:
        health_status["status"] = "degraded"
        health_status["message"] = "Metrics aggregator not initialized"
        return health_status
    
    # Check Redis connectivity (secondary to LiveStatus)
    if redis_consumer is None:
        # Only override if LiveStatus is green and Redis is unavailable
        if health_status["live_status"]["status"] == "green":
            health_status["status"] = "degraded"
            health_status["message"] = "Redis consumer not initialized"
        return health_status
    
    if redis_consumer.redis_client:
        try:
            # Ping Redis to check connectivity - await the async ping
            await redis_consumer.redis_client.ping()  # type: ignore
            health_status["redis_connected"] = True
            health_status["active_calls"] = redis_consumer.active_calls
            health_status["error_count"] = len(redis_consumer.error_buffer)
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            health_status["redis_connected"] = False
            # Only update status if LiveStatus is green and Redis is critical
            if health_status["live_status"]["status"] == "green":
                health_status["status"] = "degraded"
                health_status["message"] = f"Redis connection issue: {str(e)}"
    else:
        health_status["redis_connected"] = False
        # Only update status if LiveStatus is green and Redis is critical
        if health_status["live_status"]["status"] == "green":
            health_status["status"] = "degraded"
            health_status["message"] = "Redis client not available"
    
    return health_status

async def get_error_logs(error_type: str, limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch recent error logs for drill-down functionality."""
    if redis_consumer is None:
        return {"errors": []}
    
    # Filter error_buffer for matching error_type and sort by timestamp
    matching_errors: List[Dict[str, Any]] = sorted(
        [
            error for error in list(redis_consumer.error_buffer) # Convert deque to list for sorting
            if error.get('error_type') == error_type
        ],
        key=lambda x: int(x['timestamp']), # Sort by timestamp numerically
        reverse=True # Most recent first
    )
    return {"errors": matching_errors[:limit]} 