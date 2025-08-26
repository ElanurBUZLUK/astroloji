"""
Tests for observability system
"""
import pytest
from datetime import datetime, timedelta
from app.evaluation.observability import AstroObservability, AlertLevel, Alert

def test_observability_system_initialization():
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
    assert 1.5 in response_times

def test_track_rag_query():
    """Test RAG query tracking"""
    obs = ObservabilitySystem()
    
    obs.track_rag_query(
        query="What is almuten?",
        retrieved_docs=3,
        response_time=2.1,
        faithfulness_score=0.85
    )
    
    # Should have recorded metrics
    assert obs.counters["rag_queries_total"] == 1
    assert len(obs.histograms["rag_response_time"]) == 1
    assert len(obs.histograms["rag_retrieved_docs"]) == 1
    assert len(obs.gauges["rag_faithfulness"]) == 1

def test_track_interpretation():
    """Test interpretation tracking"""
    obs = ObservabilitySystem()
    
    obs.track_interpretation(
        chart_type="natal",
        coherence_score=0.82,
        confidence_score=0.75,
        processing_time=3.2
    )
    
    # Should have recorded metrics
    assert obs.counters["interpretations_total"] == 1
    assert obs.counters["interpretations_by_type"]["natal"] == 1
    assert len(obs.gauges["interpretation_coherence"]) == 1
    assert len(obs.gauges["interpretation_confidence"]) == 1

def test_track_user_feedback():
    """Test user feedback tracking"""
    obs = ObservabilitySystem()
    
    obs.track_user_feedback(
        rating=4,
        feedback_type="interpretation",
        user_id="user123"
    )
    
    # Should have recorded metrics
    assert obs.counters["user_feedback_total"] == 1
    assert len(obs.gauges["user_satisfaction"]) == 1
    assert obs.gauges["user_satisfaction"][-1] == 4

def test_alert_rule_evaluation():
    """Test alert rule evaluation"""
    obs = ObservabilitySystem()
    
    # Add some high response times to trigger alert
    for _ in range(10):
        obs.track_api_request("/test", "GET", 200, 3.0)  # Slow requests
    
    # Check for alerts
    obs.check_alerts()
    
    # Should have triggered high response time alert
    high_response_alerts = [a for a in obs.alerts if "response time" in a.message.lower()]
    assert len(high_response_alerts) > 0

def test_custom_alert_rule():
    """Test custom alert rule"""
    obs = ObservabilitySystem()
    
    # Add custom alert rule
    custom_rule = AlertRule(
        name="test_rule",
        condition=lambda obs: obs.counters.get("api_requests_total", 0) > 5,
        message="Too many requests",
        severity=AlertSeverity.WARNING
    )
    obs.add_alert_rule(custom_rule)
    
    # Trigger the condition
    for _ in range(10):
        obs.track_api_request("/test", "GET", 200, 1.0)
    
    # Check alerts
    obs.check_alerts()
    
    # Should have triggered custom alert
    custom_alerts = [a for a in obs.alerts if a.rule_name == "test_rule"]
    assert len(custom_alerts) > 0

def test_system_health_calculation():
    """Test system health score calculation"""
    obs = ObservabilitySystem()
    
    # Add some good metrics
    obs.track_api_request("/test", "GET", 200, 1.0)  # Fast request
    obs.track_rag_query("test", 3, 1.5, 0.9)  # Good RAG query
    obs.track_interpretation("natal", 0.85, 0.8, 2.0)  # Good interpretation
    
    health_data = obs.update_system_health()
    
    # Should have good health score
    assert health_data["health_score"] > 0.7
    assert health_data["status"] in ["excellent", "good"]

def test_system_health_with_issues():
    """Test system health with performance issues"""
    obs = ObservabilitySystem()
    
    # Add some problematic metrics
    for _ in range(5):
        obs.track_api_request("/test", "GET", 500, 4.0)  # Slow errors
    
    obs.track_rag_query("test", 1, 3.0, 0.3)  # Poor RAG performance
    obs.track_interpretation("natal", 0.4, 0.3, 5.0)  # Poor interpretation
    
    health_data = obs.update_system_health()
    
    # Should have poor health score
    assert health_data["health_score"] < 0.6
    assert health_data["status"] in ["poor", "critical"]

def test_get_dashboard_data():
    """Test dashboard data generation"""
    obs = ObservabilitySystem()
    
    # Add some sample data
    obs.track_api_request("/charts", "POST", 200, 1.5)
    obs.track_api_request("/interpretations", "GET", 200, 2.1)
    obs.track_rag_query("almuten", 3, 1.8, 0.85)
    obs.track_interpretation("natal", 0.82, 0.75, 2.5)
    obs.track_user_feedback(4, "interpretation", "user123")
    
    dashboard_data = obs.get_dashboard_data()
    
    # Should have all required sections
    assert "system_health" in dashboard_data
    assert "performance" in dashboard_data
    assert "quality" in dashboard_data
    assert "activity" in dashboard_data
    assert "alerts" in dashboard_data
    
    # Check performance metrics
    perf = dashboard_data["performance"]
    assert "avg_response_time" in perf
    assert "total_requests" in perf
    assert "error_rate" in perf
    
    # Check quality metrics
    quality = dashboard_data["quality"]
    assert "avg_faithfulness" in quality
    assert "avg_coherence" in quality
    assert "user_satisfaction" in quality

def test_alert_resolution():
    """Test alert resolution"""
    obs = ObservabilitySystem()
    
    # Trigger an alert
    for _ in range(10):
        obs.track_api_request("/test", "GET", 500, 1.0)  # High error rate
    
    obs.check_alerts()
    
    # Should have alerts
    assert len(obs.alerts) > 0
    
    # Resolve first alert
    alert_id = obs.alerts[0].id
    obs.resolve_alert(alert_id)
    
    # Alert should be resolved
    resolved_alert = next(a for a in obs.alerts if a.id == alert_id)
    assert resolved_alert.resolved_at is not None

def test_metrics_time_window():
    """Test metrics filtering by time window"""
    obs = ObservabilitySystem()
    
    # Add old metric
    old_time = datetime.now() - timedelta(hours=2)
    obs.track_api_request("/test", "GET", 200, 1.0)
    # Manually set timestamp to old time
    if obs.histograms["response_time"]:
        obs.timers["response_time"][-1] = old_time
    
    # Add recent metric
    obs.track_api_request("/test", "GET", 200, 1.5)
    
    # Get recent metrics only
    dashboard_data = obs.get_dashboard_data(time_window_hours=1)
    
    # Should only include recent metrics
    assert dashboard_data["performance"]["total_requests"] <= 2

def test_performance_percentiles():
    """Test performance percentile calculations"""
    obs = ObservabilitySystem()
    
    # Add various response times
    response_times = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
    for rt in response_times:
        obs.track_api_request("/test", "GET", 200, rt)
    
    dashboard_data = obs.get_dashboard_data()
    perf = dashboard_data["performance"]
    
    # Should have percentile calculations
    assert "p50_response_time" in perf
    assert "p95_response_time" in perf
    assert "p99_response_time" in perf
    
    # P95 should be higher than P50
    assert perf["p95_response_time"] > perf["p50_response_time"]

def test_concurrent_metric_tracking():
    """Test concurrent metric tracking"""
    obs = ObservabilitySystem()
    
    # Simulate concurrent requests
    import threading
    
    def track_requests():
        for i in range(100):
            obs.track_api_request(f"/test{i%5}", "GET", 200, 1.0)
    
    # Start multiple threads
    threads = []
    for _ in range(5):
        t = threading.Thread(target=track_requests)
        threads.append(t)
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    # Should have tracked all requests
    assert obs.counters["api_requests_total"] == 500

def test_memory_management():
    """Test memory management for metrics"""
    obs = ObservabilitySystem()
    
    # Add many metrics
    for i in range(1000):
        obs.track_api_request("/test", "GET", 200, 1.0)
    
    # Should not grow indefinitely (implementation dependent)
    # This test ensures the system doesn't crash with many metrics
    dashboard_data = obs.get_dashboard_data()
    assert dashboard_data["performance"]["total_requests"] > 0