# backend/src/models.py
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

# Type aliases for Redis operations
RedisStreamInfo = Dict[str, Any]
RedisMessage = Tuple[str, Dict[str, str]]
RedisStreamEntry = Tuple[str, List[RedisMessage]]
RedisXReadResult = List[RedisStreamEntry]

# Pydantic Models for Type Safety
class LiveStatus(BaseModel):
    status: str = Field(..., description="green, yellow, or red")
    last_updated: datetime
    message: Optional[str] = None

class ActiveCallsMetric(BaseModel):
    count: int = Field(..., ge=0)
    timestamp: datetime

class ErrorSummary(BaseModel):
    error_type: str
    count: int
    last_occurrence: datetime
    severity: str

class DashboardMetrics(BaseModel):
    live_status: LiveStatus
    active_calls: ActiveCallsMetric
    error_summary: List[ErrorSummary]
    last_updated: datetime

class DemoErrorRequest(BaseModel):
    error_type: str = Field("DEFAULT_ERROR", description="Type of the error, e.g., 'API_TIMEOUT'.")
    message: str = Field("This is a simulated error.", description="Detailed error message.")
    severity: str = Field("medium", description="Severity of the error (low, medium, high, critical).")
    count: int = Field(1, description="Number of errors to inject.")
    conversation_id: str = Field("demo-conv-12345", description="Simulated conversation ID.")

class SimulateActiveCallsRequest(BaseModel):
    count: int = Field(..., description="Target number of active calls to simulate (absolute value).") 