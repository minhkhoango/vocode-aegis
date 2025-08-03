# backend/src/main.py
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .api_endpoints import (
    websocket_endpoint, health_check, 
    get_error_logs, set_global_dependencies,
    inject_demo_error, simulate_active_calls,
    reset_demo_state
)
from .metrics_aggregator import MetricsAggregator
from .redis_consumer import VocodeRedisConsumer
from .websocket_manager import ConnectionManager
from .models import DemoErrorRequest, SimulateActiveCallsRequest

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables for lifespan management
manager: ConnectionManager | None = None
redis_consumer: VocodeRedisConsumer | None = None
aggregator: MetricsAggregator | None = None
consumer_task: asyncio.Task[None] | None = None
app_start_time: Optional[datetime] = None  # New global variable for tracking app start time

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global manager, redis_consumer, aggregator, consumer_task, app_start_time
    manager = ConnectionManager()
    app_start_time = datetime.now()  # Set on app startup
    logger.info(f"FastAPI application started at {app_start_time}.")
    
    try:
        redis_consumer = VocodeRedisConsumer(
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379"))
        )
        logger.info("FastAPI application started. Redis consumer initialized.")
        
        # Start Redis consumer immediately after initialization
        consumer_task = asyncio.create_task(redis_consumer.consume_vocode_events())
        logger.info("Redis consumer started in background.")
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_consumer = None
    
    aggregator = MetricsAggregator()
    
    # Set global dependencies for API endpoints
    set_global_dependencies(manager, redis_consumer, aggregator)
    
    # Yield to allow FastAPI to start and become available
    yield
    
    # Shutdown
    logger.info("FastAPI application shutting down.")
    if consumer_task and not consumer_task.done():
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

app = FastAPI(title="Vocode Analytics Dashboard", lifespan=lifespan)

# Enable CORS for React frontend
# In production, specify exact origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# --- API Endpoints ---

@app.websocket("/ws")
async def websocket_endpoint_handler(websocket: WebSocket):
    """WebSocket endpoint handler."""
    logger.info("WebSocket endpoint handler called")
    try:
        await websocket_endpoint(websocket)
        logger.info("WebSocket endpoint function completed")
    except Exception as e:
        logger.exception(f"Error in WebSocket endpoint handler: {e}")
        raise

@app.get("/health")
async def health():
    return await health_check()

@app.get("/logs/{error_type}")
async def logs_endpoint(error_type: str, limit: int = 50):
    return await get_error_logs(error_type, limit)

@app.post("/demo/error", status_code=status.HTTP_200_OK)
async def demo_error_endpoint(request: DemoErrorRequest, broadcast: bool = True):
    """
    Demo error injection endpoint for testing purposes.
    `broadcast` query param forces immediate metric broadcast.
    """
    return await inject_demo_error(request, broadcast=broadcast)

@app.post("/demo/active_calls", status_code=status.HTTP_200_OK)
async def demo_active_calls_endpoint(request: SimulateActiveCallsRequest):
    """Demo active calls simulation endpoint for testing purposes."""
    return await simulate_active_calls(request)

@app.post("/demo/reset", status_code=status.HTTP_200_OK)
async def demo_reset_endpoint():
    """Endpoint to reset all demo-related states."""
    return await reset_demo_state()

# Mount static files - the React build creates a 'static' directory.
# The 'build' directory from the frontend is copied to 'static' in the Dockerfile.
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir / "static"), name="static")
    
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_react_app(full_path: str):
        """
        Serve the React application.
        This endpoint catches all other paths and serves the index.html,
        allowing React Router to handle the client-side routing.
        """
        index_path = static_dir / "index.html"
        if index_path.exists():
            with open(index_path, "r") as f:
                return HTMLResponse(content=f.read(), status_code=200)
        return HTMLResponse(content="Frontend not found.", status_code=404)
else:
    logger.warning("Static directory not found. Frontend will not be served.")