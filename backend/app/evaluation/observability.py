"""
Observability and monitoring system for astrological interpretation platform
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import asyncio
from collections import defaultdict, deque
import statistics

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """Types of metrics to monitor"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class Alert:
    """System alert"""
    id: str
    level: AlertLevel
    title: str
    description: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class MetricPoint:
    """Single metric data point"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)

class MetricCollector:
    """Collects and stores metrics"""
    
    def __init__(self, max_points_per_metric: int = 1000):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points_per_metric))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        self.counters[name] += value
        self._add_point(name, self.counters[name], tags or {})
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric value"""
        self.gauges[name] = value
        self._add_point(name, value, tags or {})
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram value"""
        self._add_point(name, value, tags or {})
    
    def time_function(self, name: str, tags: Dict[str, str] = None):
        """Decorator to time function execution"""
        def decorator(func):
            async def async_wrapper(*args, **kwargs):
                start_time = datetime.now()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = (datetime.now() - start_time).total_seconds()
                    self.record_histogram(f"{name}_duration", duration, tags)
            
            def sync_wrapper(*args, **kwargs):
                start_time = datetime.now()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = (datetime.now() - start_time).total_seconds()
                    self.record_histogram(f"{name}_duration", duration, tags)
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def _add_point(self, name: str, value: float, tags: Dict[str, str]):
        """Add a metric point"""
        point = MetricPoint(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags
        )
        self.metrics[name].append(point)
    
    def get_metric_values(self, name: str, time_window_minutes: int = 60) -> List[float]:
        """Get metric values within time window"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        if name not in self.metrics:
            return []
        
        return [
            point.value for point in self.metrics[name]
            if point.timestamp >= cutoff_time
        ]
    
    def get_metric_summary(self, name: str, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get metric summary statistics"""
        values = self.get_metric_values(name, time_window_minutes)
        
        if not values:
            return {"count": 0}
        
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0.0,
            "latest": values[-1] if values else None
        }

class AlertManager:
    """Manages system alerts and notifications"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_rules: List[Dict[str, Any]] = []
        self.notification_handlers: List[Callable] = []
    
    def add_alert_rule(self, metric_name: str, threshold: float, 
                      comparison: str = "greater", level: AlertLevel = AlertLevel.WARNING,
                      title: str = None, description: str = None):
        """Add an alert rule"""
        rule = {
            "metric_name": metric_name,
            "threshold": threshold,
            "comparison": comparison,  # "greater", "less", "equal"
            "level": level,
            "title": title or f"{metric_name} threshold exceeded",
            "description": description or f"{metric_name} is {comparison} than {threshold}"
        }
        self.alert_rules.append(rule)
    
    def check_alerts(self, metrics: Dict[str, float]):
        """Check metrics against alert rules"""
        new_alerts = []
        
        for rule in self.alert_rules:
            metric_name = rule["metric_name"]
            if metric_name not in metrics:
                continue
            
            current_value = metrics[metric_name]
            threshold = rule["threshold"]
            comparison = rule["comparison"]
            
            should_alert = False
            if comparison == "greater" and current_value > threshold:
                should_alert = True
            elif comparison == "less" and current_value < threshold:
                should_alert = True
            elif comparison == "equal" and abs(current_value - threshold) < 0.001:
                should_alert = True
            
            if should_alert:
                # Check if we already have an active alert for this metric
                existing_alert = next(
                    (alert for alert in self.alerts 
                     if alert.metric_name == metric_name and not alert.resolved),
                    None
                )
                
                if not existing_alert:
                    alert = Alert(
                        id=f"{metric_name}_{datetime.now().timestamp()}",
                        level=rule["level"],
                        title=rule["title"],
                        description=rule["description"],
                        metric_name=metric_name,
                        current_value=current_value,
                        threshold=threshold,
                        timestamp=datetime.now()
                    )
                    
                    self.alerts.append(alert)
                    new_alerts.append(alert)
        
        # Send notifications for new alerts
        for alert in new_alerts:
            self._send_notifications(alert)
        
        return new_alerts
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                break
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for specified time window"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alerts if alert.timestamp >= cutoff_time]
    
    def add_notification_handler(self, handler: Callable[[Alert], None]):
        """Add a notification handler"""
        self.notification_handlers.append(handler)
    
    def _send_notifications(self, alert: Alert):
        """Send notifications for an alert"""
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"Error sending notification: {e}")

class AstroObservability:
    """Main observability system for astrological platform"""
    
    def __init__(self):
        self.metrics = MetricCollector()
        self.alerts = AlertManager()
        self._setup_default_alerts()
        self._setup_default_metrics()
    
    def _setup_default_alerts(self):
        """Setup default alert rules"""
        # Performance alerts
        self.alerts.add_alert_rule(
            "avg_response_time", 2.0, "greater", AlertLevel.WARNING,
            "High Response Time", "Average API response time is above 2 seconds"
        )
        
        self.alerts.add_alert_rule(
            "error_rate", 0.05, "greater", AlertLevel.ERROR,
            "High Error Rate", "Error rate is above 5%"
        )
        
        self.alerts.add_alert_rule(
            "cache_hit_rate", 0.5, "less", AlertLevel.WARNING,
            "Low Cache Hit Rate", "Cache hit rate is below 50%"
        )
        
        # Quality alerts
        self.alerts.add_alert_rule(
            "interpretation_coherence", 0.6, "less", AlertLevel.WARNING,
            "Low Interpretation Coherence", "Interpretation coherence is below 60%"
        )
        
        self.alerts.add_alert_rule(
            "rag_faithfulness", 0.7, "less", AlertLevel.WARNING,
            "Low RAG Faithfulness", "RAG faithfulness score is below 70%"
        )
        
        # System health alerts
        self.alerts.add_alert_rule(
            "active_users", 1000, "greater", AlertLevel.INFO,
            "High User Activity", "More than 1000 active users"
        )
    
    def _setup_default_metrics(self):
        """Setup default metrics tracking"""
        # Initialize counters
        self.metrics.increment_counter("api_requests_total", 0)
        self.metrics.increment_counter("api_errors_total", 0)
        self.metrics.increment_counter("cache_hits_total", 0)
        self.metrics.increment_counter("cache_misses_total", 0)
        
        # Initialize gauges
        self.metrics.set_gauge("active_users", 0)
        self.metrics.set_gauge("system_health_score", 1.0)
    
    def track_api_request(self, endpoint: str, method: str, status_code: int, 
                         response_time: float, user_id: str = None):
        """Track API request metrics"""
        tags = {"endpoint": endpoint, "method": method, "status": str(status_code)}
        
        # Increment request counter
        self.metrics.increment_counter("api_requests_total", 1, tags)
        
        # Track response time
        self.metrics.record_histogram("api_response_time", response_time, tags)
        
        # Track errors
        if status_code >= 400:
            self.metrics.increment_counter("api_errors_total", 1, tags)
        
        # Track user activity
        if user_id:
            self.metrics.increment_counter("user_requests", 1, {"user_id": user_id})
    
    def track_interpretation_quality(self, coherence: float, accuracy: float, 
                                   confidence: float, user_satisfaction: Optional[float] = None):
        """Track interpretation quality metrics"""
        self.metrics.record_histogram("interpretation_coherence", coherence)
        self.metrics.record_histogram("interpretation_accuracy", accuracy)
        self.metrics.record_histogram("interpretation_confidence", confidence)
        
        if user_satisfaction is not None:
            self.metrics.record_histogram("user_satisfaction", user_satisfaction)
    
    def track_rag_performance(self, recall: float, precision: float, 
                            faithfulness: float, response_time: float):
        """Track RAG system performance"""
        self.metrics.record_histogram("rag_recall", recall)
        self.metrics.record_histogram("rag_precision", precision)
        self.metrics.record_histogram("rag_faithfulness", faithfulness)
        self.metrics.record_histogram("rag_response_time", response_time)
    
    def track_cache_performance(self, hit: bool):
        """Track cache performance"""
        if hit:
            self.metrics.increment_counter("cache_hits_total")
        else:
            self.metrics.increment_counter("cache_misses_total")
    
    def update_system_health(self):
        """Update overall system health score"""
        # Collect key metrics
        metrics_to_check = {
            "avg_response_time": self.metrics.get_metric_summary("api_response_time", 60).get("mean", 0),
            "error_rate": self._calculate_error_rate(),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "interpretation_coherence": self.metrics.get_metric_summary("interpretation_coherence", 60).get("mean", 1.0),
            "rag_faithfulness": self.metrics.get_metric_summary("rag_faithfulness", 60).get("mean", 1.0)
        }
        
        # Check for alerts
        new_alerts = self.alerts.check_alerts(metrics_to_check)
        
        # Calculate health score
        health_score = self._calculate_health_score(metrics_to_check)
        self.metrics.set_gauge("system_health_score", health_score)
        
        return {
            "health_score": health_score,
            "metrics": metrics_to_check,
            "new_alerts": len(new_alerts),
            "active_alerts": len(self.alerts.get_active_alerts())
        }
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        total_requests = self.metrics.get_metric_summary("api_requests_total", 60).get("latest", 0)
        total_errors = self.metrics.get_metric_summary("api_errors_total", 60).get("latest", 0)
        
        if total_requests == 0:
            return 0.0
        
        return total_errors / total_requests
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate current cache hit rate"""
        cache_hits = self.metrics.get_metric_summary("cache_hits_total", 60).get("latest", 0)
        cache_misses = self.metrics.get_metric_summary("cache_misses_total", 60).get("latest", 0)
        
        total_cache_requests = cache_hits + cache_misses
        if total_cache_requests == 0:
            return 0.0
        
        return cache_hits / total_cache_requests
    
    def _calculate_health_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall system health score"""
        scores = []
        
        # Response time score (lower is better)
        response_time = metrics.get("avg_response_time", 0)
        if response_time <= 1.0:
            scores.append(1.0)
        elif response_time <= 2.0:
            scores.append(0.8)
        elif response_time <= 3.0:
            scores.append(0.6)
        else:
            scores.append(0.4)
        
        # Error rate score (lower is better)
        error_rate = metrics.get("error_rate", 0)
        if error_rate <= 0.01:
            scores.append(1.0)
        elif error_rate <= 0.05:
            scores.append(0.8)
        elif error_rate <= 0.1:
            scores.append(0.6)
        else:
            scores.append(0.4)
        
        # Cache hit rate score
        cache_hit_rate = metrics.get("cache_hit_rate", 0)
        scores.append(min(cache_hit_rate * 2, 1.0))  # Scale 0.5 -> 1.0
        
        # Quality scores
        coherence = metrics.get("interpretation_coherence", 1.0)
        faithfulness = metrics.get("rag_faithfulness", 1.0)
        scores.extend([coherence, faithfulness])
        
        return statistics.mean(scores) if scores else 0.0
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system_health": {
                "score": self.metrics.get_metric_summary("system_health_score", 5).get("latest", 0),
                "status": self._get_health_status()
            },
            "performance": {
                "avg_response_time": self.metrics.get_metric_summary("api_response_time", 60).get("mean", 0),
                "p95_response_time": self._get_p95_response_time(),
                "error_rate": self._calculate_error_rate(),
                "cache_hit_rate": self._calculate_cache_hit_rate()
            },
            "quality": {
                "interpretation_coherence": self.metrics.get_metric_summary("interpretation_coherence", 60).get("mean", 0),
                "rag_faithfulness": self.metrics.get_metric_summary("rag_faithfulness", 60).get("mean", 0),
                "user_satisfaction": self.metrics.get_metric_summary("user_satisfaction", 60).get("mean", 0)
            },
            "activity": {
                "total_requests": self.metrics.get_metric_summary("api_requests_total", 60).get("latest", 0),
                "active_users": self.metrics.get_metric_summary("active_users", 60).get("latest", 0)
            },
            "alerts": {
                "active_count": len(self.alerts.get_active_alerts()),
                "recent_alerts": [
                    {
                        "level": alert.level.value,
                        "title": alert.title,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in self.alerts.get_alert_history(1)[-5:]  # Last 5 alerts
                ]
            }
        }
    
    def _get_health_status(self) -> str:
        """Get health status string"""
        score = self.metrics.get_metric_summary("system_health_score", 5).get("latest", 0)
        
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "good"
        elif score >= 0.6:
            return "fair"
        elif score >= 0.4:
            return "poor"
        else:
            return "critical"
    
    def _get_p95_response_time(self) -> float:
        """Get 95th percentile response time"""
        values = self.metrics.get_metric_values("api_response_time", 60)
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(0.95 * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]

# Global observability instance
observability = AstroObservability()

# Notification handlers
def console_notification_handler(alert: Alert):
    """Simple console notification handler"""
    print(f"[{alert.level.value.upper()}] {alert.title}: {alert.description}")
    print(f"  Metric: {alert.metric_name} = {alert.current_value} (threshold: {alert.threshold})")
    print(f"  Time: {alert.timestamp}")

def log_notification_handler(alert: Alert):
    """Log-based notification handler"""
    log_entry = {
        "timestamp": alert.timestamp.isoformat(),
        "level": alert.level.value,
        "alert_id": alert.id,
        "title": alert.title,
        "description": alert.description,
        "metric_name": alert.metric_name,
        "current_value": alert.current_value,
        "threshold": alert.threshold
    }
    
    # In a real system, this would write to a proper logging system
    print(f"ALERT_LOG: {json.dumps(log_entry)}")

# Setup default notification handlers
observability.alerts.add_notification_handler(console_notification_handler)
observability.alerts.add_notification_handler(log_notification_handler)