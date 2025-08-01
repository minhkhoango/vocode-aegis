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
    error_type: str = Field(..., description="Type of error to simulate (e.g., 'LLM_FAILURE', 'SPEECH_API_DOWN')")
    message: str = Field("Simulated demo error for immediate crisis aversion.", description="Custom message for the simulated error.")
    severity: str = Field("high", description="Severity of the error (low, medium, high, critical). Defaults to 'high' for impactful demos.")
    count: int = Field(1, ge=1, description="Number of times to inject this error.")
    conversation_id: str = Field("demo-conv-12345", description="Simulated conversation ID.") 