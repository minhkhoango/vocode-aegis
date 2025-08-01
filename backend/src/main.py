# backend/src/main.py
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .api_endpoints import (
    websocket_endpoint, serve_frontend, health_check, 
    get_error_logs, log_viewer_page, set_global_dependencies,
    inject_demo_error
)
from .metrics_aggregator import MetricsAggregator
from .redis_consumer import VocodeRedisConsumer
from .websocket_manager import ConnectionManager
from .models import DemoErrorRequest

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables for lifespan management
manager: ConnectionManager | None = None
redis_consumer: VocodeRedisConsumer | None = None
aggregator: MetricsAggregator | None = None
consumer_task: asyncio.Task[None] | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global manager, redis_consumer, aggregator, consumer_task
    manager = ConnectionManager()
    
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
)

# Mount static files - React build creates nested static directory
# Only mount if the directory exists (for testing purposes)
static_dir = Path("static/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static/static"), name="static")
else:
    # Fallback: mount the static directory directly if nested structure doesn't exist
    fallback_static_dir = Path("static")
    if fallback_static_dir.exists():
        app.mount("/static", StaticFiles(directory="static"), name="static")

# --- API Endpoints ---

@app.websocket("/ws")
async def websocket_endpoint_handler(websocket: WebSocket):
    """WebSocket endpoint handler."""
    await websocket_endpoint(websocket)

@app.get("/", response_class=HTMLResponse)
async def root():
    return await serve_frontend()

@app.get("/health")
async def health():
    return await health_check()

@app.get("/logs/{error_type}")
async def logs_endpoint(error_type: str, limit: int = 50):
    return await get_error_logs(error_type, limit)

@app.get("/logs/{error_type}/viewer", response_class=HTMLResponse)
async def logs_viewer_endpoint(error_type: str):
    return await log_viewer_page(error_type)

@app.post("/demo/error", status_code=status.HTTP_200_OK)
async def demo_error_endpoint(request: DemoErrorRequest):
    """Demo error injection endpoint for testing purposes."""
    return await inject_demo_error(request) 