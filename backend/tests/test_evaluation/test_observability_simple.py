"""
Simple tests for observability system
"""
import pytest
from datetime import datetime, timedelta
from app.evaluation.observability import AstroObservability, AlertLevel

def test_observability_initialization():
    """Test observability system initialization"""
    obs = AstroObservability()
    
    # Should have default alert rules
    assert len(obs.alerts.alert_rules) > 0
    
    # Should have empty alerts initially
    assert len(obs.alerts.alerts) == 0

def test_track_api_request():
    """Test API request tracking"""
    obs = AstroObservability()
    
    # Track a request
    obs.track_api_request(
        endpoint="/charts",
        method="POST",
        status_code=200,
        response_time=1.5,
        user_id="user123"
    )
    
    # Should have recorded metrics
    assert obs.metrics.counters["api_requests_total"] >= 1
    
    # Should have response time recorded
    response_times = obs.metrics.get_metric_values("api_response_time", 60)
    assert len(response_times) >= 1

def test_track_interpretation_quality():
    """Test interpretation quality tracking"""
    obs = AstroObservability()
    
    obs.track_interpretation_quality(
        coherence=0.85,
        accuracy=0.78,
        confidence=0.82,
        user_satisfaction=4.2
    )
    
    # Should have recorded quality metrics
    coherence_values = obs.metrics.get_metric_values("interpretation_coherence", 60)
    assert len(coherence_values) >= 1
    assert 0.85 in coherence_values

def test_track_rag_performance():
    """Test RAG performance tracking"""
    obs = AstroObservability()
    
    obs.track_rag_performance(
        recall=0.75,
        precision=0.82,
        faithfulness=0.88,
        response_time=2.1
    )
    
    # Should have recorded RAG metrics
    faithfulness_values = obs.metrics.get_metric_values("rag_faithfulness", 60)
    assert len(faithfulness_values) >= 1
    assert 0.88 in faithfulness_values

def test_cache_performance_tracking():
    """Test cache performance tracking"""
    obs = AstroObservability()
    
    # Track cache hits and misses
    obs.track_cache_performance(hit=True)
    obs.track_cache_performance(hit=True)
    obs.track_cache_performance(hit=False)
    
    # Should have recorded cache metrics
    assert obs.metrics.counters["cache_hits_total"] >= 2
    assert obs.metrics.counters["cache_misses_total"] >= 1

def test_system_health_update():
    """Test system health calculation"""
    obs = AstroObservability()
    
    # Add some good metrics
    obs.track_api_request("/test", "GET", 200, 1.0)
    obs.track_interpretation_quality(0.85, 0.8, 0.75)
    obs.track_rag_performance(0.8, 0.75, 0.9, 1.5)
    
    health_data = obs.update_system_health()
    
    # Should have health score
    assert "health_score" in health_data
    assert 0 <= health_data["health_score"] <= 1
    assert "metrics" in health_data

def test_dashboard_data():
    """Test dashboard data generation"""
    obs = AstroObservability()
    
    # Add some sample data
    obs.track_api_request("/charts", "POST", 200, 1.5)
    obs.track_interpretation_quality(0.82, 0.75, 0.8, 4.0)
    obs.track_rag_performance(0.8, 0.75, 0.85, 1.8)
    
    dashboard_data = obs.get_dashboard_data()
    
    # Should have all required sections
    assert "system_health" in dashboard_data
    assert "performance" in dashboard_data
    assert "quality" in dashboard_data
    assert "activity" in dashboard_data
    assert "alerts" in dashboard_data

def test_alert_generation():
    """Test alert generation"""
    obs = AstroObservability()
    
    # Add alert rule for testing
    obs.alerts.add_alert_rule(
        "test_metric", 5.0, "greater", AlertLevel.WARNING,
        "Test Alert", "Test metric exceeded threshold"
    )
    
    # Trigger the alert
    metrics = {"test_metric": 10.0}
    new_alerts = obs.alerts.check_alerts(metrics)
    
    # Should have generated an alert
    assert len(new_alerts) >= 1
    assert new_alerts[0].metric_name == "test_metric"
    assert new_alerts[0].current_value == 10.0

def test_alert_resolution():
    """Test alert resolution"""
    obs = AstroObservability()
    
    # Add alert rule
    obs.alerts.add_alert_rule("test_metric", 5.0, "greater", AlertLevel.WARNING)
    
    # Trigger alert
    metrics = {"test_metric": 10.0}
    new_alerts = obs.alerts.check_alerts(metrics)
    
    # Should have alert
    assert len(new_alerts) >= 1
    alert_id = new_alerts[0].id
    
    # Resolve alert
    obs.alerts.resolve_alert(alert_id)
    
    # Alert should be resolved
    resolved_alert = next(a for a in obs.alerts.alerts if a.id == alert_id)
    assert resolved_alert.resolved == True
    assert resolved_alert.resolved_at is not None

def test_metric_summary():
    """Test metric summary generation"""
    obs = AstroObservability()
    
    # Add multiple values
    for i in range(10):
        obs.metrics.record_histogram("test_metric", float(i))
    
    summary = obs.metrics.get_metric_summary("test_metric", 60)
    
    # Should have summary statistics
    assert summary["count"] == 10
    assert "mean" in summary
    assert "median" in summary
    assert "min" in summary
    assert "max" in summary