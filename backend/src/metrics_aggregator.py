# backend/src/metrics_aggregator.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from .models import LiveStatus, ErrorSummary
from .redis_consumer import VocodeRedisConsumer

logger = logging.getLogger(__name__)

class MetricsAggregator:
    def __init__(self) -> None:
        # error_buffer is now directly accessed from redis_consumer
        pass

    def calculate_live_status(self, redis_consumer: VocodeRedisConsumer | None) -> LiveStatus:
        """Calculate system health based on recent metrics with severity weighting."""
        now = datetime.now()
        # Convert deque to list for easier filtering, assuming 'timestamp' is a string of epoch milliseconds
        if redis_consumer is None:
            return LiveStatus(
                status="red",
                last_updated=now,
                message="Redis consumer not initialized"
            )
        
        recent_errors = [
            e for e in list(redis_consumer.error_buffer)
            if now - datetime.fromtimestamp(float(e['timestamp']) / 1000) < timedelta(minutes=5)
        ]

        # Define severity weights for weighted error scoring
        severity_weights = {
            'low': 1,
            'medium': 3,
            'high': 5,
            'critical': 10  # For critical business impact errors
        }

        # Calculate weighted error score
        total_error_score = 0
        high_severity_count = 0
        critical_severity_count = 0
        
        for error in recent_errors:
            severity = error.get('severity', 'medium').lower()
            weight = severity_weights.get(severity, 3)  # Default to medium weight
            total_error_score += weight
            
            if severity == 'high':
                high_severity_count += 1
            elif severity == 'critical':
                critical_severity_count += 1

        status: str
        message: str | None = None

        # Enhanced thresholds based on weighted error score
        if total_error_score >= 10 or critical_severity_count > 0 or high_severity_count > 0:
            status = "red"
            if critical_severity_count > 0:
                message = f"CRITICAL: {critical_severity_count} critical errors detected! Immediate attention required."
            elif high_severity_count > 0:
                message = f"RED ALERT: {high_severity_count} high severity errors + {total_error_score} weighted score. System compromised."
            else:
                message = f"RED ALERT: {total_error_score} weighted error score indicates critical system issues."
        elif total_error_score >= 5:
            status = "yellow"
            if high_severity_count > 0:
                message = f"WARNING: {high_severity_count} high severity errors detected. Monitor closely."
            else:
                message = f"WARNING: {total_error_score} weighted error score indicates potential issues."
        else:
            status = "green"
            if len(recent_errors) > 0:
                message = f"System healthy. {len(recent_errors)} low/medium severity errors in last 5 minutes."
            else:
                message = "System healthy."

        return LiveStatus(
            status=status,
            last_updated=now,
            message=message
        )

    def get_24h_error_summary(self, redis_consumer: VocodeRedisConsumer | None) -> List[ErrorSummary]:
        """Aggregate last 24 hours of errors."""
        now = datetime.now()
        cutoff = now - timedelta(hours=24)
        
        if redis_consumer is None:
            return []
        
        # Convert deque to list for easier filtering
        recent_errors: List[Dict[str, Any]] = [
            e for e in list(redis_consumer.error_buffer)
            if datetime.fromtimestamp(float(e['timestamp']) / 1000) > cutoff
        ]

        error_counts: Dict[str, Dict[str, Any]] = {}
        for error in recent_errors:
            error_type: str = error.get('error_type', 'unknown')
            timestamp_dt: datetime = datetime.fromtimestamp(float(error['timestamp']) / 1000)

            if error_type not in error_counts:
                error_counts[error_type] = {
                    'count': 0,
                    'last_occurrence': timestamp_dt,
                    'severity': error.get('severity', 'medium')
                }
            error_counts[error_type]['count'] += 1
            # Update last_occurrence if this error is more recent
            if timestamp_dt > error_counts[error_type]['last_occurrence']:
                error_counts[error_type]['last_occurrence'] = timestamp_dt

        return [
            ErrorSummary(
                error_type=error_type,
                count=data['count'],
                last_occurrence=data['last_occurrence'],
                severity=data['severity']
            )
            for error_type, data in error_counts.items()
        ] 