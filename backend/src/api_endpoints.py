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
    logger.info("WebSocket endpoint function called")
    
    if manager is None:
        logger.error("Manager is None, closing WebSocket connection")
        await websocket.close(code=1008)  # Policy violation
        return
    
    logger.info("Manager is available, connecting WebSocket")
    await manager.connect(websocket)
    logger.info("WebSocket connected, entering broadcast loop")
    
    try:
        while True:
            # Debug logging to see the state
            logger.info(f"WebSocket loop - Active connections: {len(manager.active_connections) if manager else 0}, "
                       f"Redis consumer: {redis_consumer is not None}, "
                       f"Aggregator: {aggregator is not None}")
            
            if manager.active_connections and redis_consumer and aggregator: # Only send if there are active connections
                metrics = DashboardMetrics(
                    live_status=aggregator.calculate_live_status(redis_consumer),
                    active_calls=ActiveCallsMetric(
                        count=redis_consumer.active_calls,
                        timestamp=datetime.now()
                    ),
                    error_summary=aggregator.get_24h_error_summary(redis_consumer),
                    financial_impact=aggregator.calculate_financial_metrics(redis_consumer),
                    last_updated=datetime.now()
                )
                
                # Debug logging for financial metrics
                logger.info(f"WebSocket Broadcast Debug - Active Calls: {metrics.active_calls.count}, "
                           f"Financial Impact: {metrics.financial_impact}")
                
                await manager.broadcast_metrics(metrics)
            else:
                logger.info("Skipping broadcast - missing required components")
            
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

async def inject_demo_error(request: DemoErrorRequest, broadcast: bool = True) -> Dict[str, str]:
    """
    Allows injecting simulated error events for demonstration purposes.
    If broadcast is True, it will immediately broadcast updated metrics.
    """
    if redis_consumer is None or aggregator is None or manager is None:
        logger.error("Attempted to inject demo error, but a required service is not initialized.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error: A required service is not initialized."
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
        logger.warning(f"DEMO MODE: Injected error. Type: '{request.error_type}', Severity: '{request.severity.upper()}', Message: '{request.message}', Count: {injected_count}")

    if broadcast:
        # After injecting, immediately recalculate and broadcast metrics
        metrics = DashboardMetrics(
            live_status=aggregator.calculate_live_status(redis_consumer),
            active_calls=ActiveCallsMetric(
                count=redis_consumer.active_calls,
                timestamp=datetime.now()
            ),
            error_summary=aggregator.get_24h_error_summary(redis_consumer),
            financial_impact=aggregator.calculate_financial_metrics(redis_consumer),
            last_updated=datetime.now()
        )
        await manager.broadcast_metrics(metrics)

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

    # Add/subtract from current active calls
    redis_consumer.active_calls = max(0, redis_consumer.active_calls + request.delta)
    logger.warning(f"DEMO MODE: Active calls changed by {request.delta}. New total: {redis_consumer.active_calls}")

    action_word = "added" if request.delta >= 0 else "subtracted"
    return {"message": f"Successfully {action_word} {abs(request.delta)} active calls. New total: {redis_consumer.active_calls}.", "status": "success"}

async def reset_demo_state() -> Dict[str, str]:
    """
    Resets all demo-related states to their defaults.
    - Resets active calls to 0.
    - Clears the error buffer.
    - Resets app start time for Min Run calculation.
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
    
    # Reset app start time for Min Run calculation
    import src.main as main_app_globals
    if main_app_globals.app_start_time:
        main_app_globals.app_start_time = datetime.now()
        logger.warning("DEMO MODE: Resetting app_start_time for Min Run calculation.")
    
    logger.warning("DEMO MODE: All demo states have been reset.")
    
    return {"message": "All demo states reset.", "status": "success"}

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
        logger.error("get_error_logs called but redis_consumer is None.")
        return {"errors": []}
    
    logger.info(f"Fetching logs for error_type: '{error_type}'. Buffer size: {len(redis_consumer.error_buffer)}")

    # Filter error_buffer for matching error_type and sort by timestamp
    matching_errors: List[Dict[str, Any]] = sorted(
        [
            error for error in list(redis_consumer.error_buffer) # Convert deque to list for sorting
            if error.get('error_type') == error_type
        ],
        key=lambda x: int(x['timestamp']), # Sort by timestamp numerically
        reverse=True # Most recent first
    )
    
    logger.info(f"Found {len(matching_errors)} matching logs for error_type: '{error_type}'.")
    
    return {"errors": matching_errors[:limit]} 