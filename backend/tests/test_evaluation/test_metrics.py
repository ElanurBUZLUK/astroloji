"""
Tests for evaluation metrics
"""
import pytest
from datetime import datetime
from app.evaluation.metrics import (
    RAGMetrics, InterpretationMetrics, PerformanceMetrics, 
    EvaluationSuite, MetricResult, MetricType
)

def test_rag_metrics_recall_at_k():
    """Test Recall@K calculation"""
    metrics = RAGMetrics()
    
    retrieved_docs = ["doc1", "doc2", "doc3", "doc4", "doc5"]
    relevant_docs = ["doc1", "doc3", "doc6", "doc7"]
    
    recall = metrics.calculate_recall_at_k(retrieved_docs, relevant_docs, k=5)
    
    # Should find 2 out of 4 relevant docs
    expected_recall = 2 / 4  # 0.5
    assert abs(recall - expected_recall) < 0.01

def test_rag_metrics_precision_at_k():
    """Test Precision@K calculation"""
    metrics = RAGMetrics()
    
    retrieved_docs = ["doc1", "doc2", "doc3", "doc4", "doc5"]
    relevant_docs = ["doc1", "doc3", "doc6", "doc7"]
    
    precision = metrics.calculate_precision_at_k(retrieved_docs, relevant_docs, k=5)
    
    # Should find 2 relevant out of 5 retrieved
    expected_precision = 2 / 5  # 0.4
    assert abs(precision - expected_precision) < 0.01

def test_rag_metrics_ndcg():
    """Test NDCG calculation"""
    metrics = RAGMetrics()
    
    retrieved_docs = ["doc1", "doc2", "doc3"]
    relevance_scores = {"doc1": 3, "doc2": 1, "doc3": 2}
    
    ndcg = metrics.calculate_ndcg(retrieved_docs, relevance_scores, k=3)
    
    # NDCG should be between 0 and 1
    assert 0 <= ndcg <= 1

def test_rag_metrics_faithfulness():
    """Test faithfulness calculation"""
    metrics = RAGMetrics()
    
    generated_text = "The almuten figuris shows the strongest planet in dignity"
    source_documents = [
        "Almuten figuris represents the planet with strongest essential dignity",
        "The almuten calculation considers all significators"
    ]
    
    faithfulness = metrics.calculate_faithfulness(generated_text, source_documents)
    
    # Should have some overlap
    assert faithfulness > 0
    assert faithfulness <= 1

def test_rag_metrics_groundedness():
    """Test groundedness calculation"""
    metrics = RAGMetrics()
    
    generated_text = "The almuten shows strength. The chart indicates timing."
    citations = [
        {"credibility": 0.9, "title": "Traditional Astrology"},
        {"credibility": 0.8, "title": "Hellenistic Methods"}
    ]
    
    groundedness = metrics.calculate_groundedness(generated_text, citations)
    
    # Should be reasonable given 2 citations for 2 sentences
    assert 0 <= groundedness <= 1

def test_interpretation_metrics_coherence():
    """Test interpretation coherence"""
    metrics = InterpretationMetrics()
    
    # Coherent text
    coherent_text = "Your chart shows strong Mercury influence. This indicates good communication skills and analytical thinking."
    coherence = metrics.calculate_coherence(coherent_text)
    assert coherence > 0.8
    
    # Contradictory text
    contradictory_text = "You have strong communication. You have weak communication. You are very good at talking. You are very bad at talking."
    coherence = metrics.calculate_coherence(contradictory_text)
    assert coherence < 0.9  # Should be penalized

def test_interpretation_metrics_confidence_accuracy():
    """Test confidence calibration"""
    metrics = InterpretationMetrics()
    
    # Perfect calibration
    predictions = [
        (0.9, True), (0.8, True), (0.7, True),
        (0.3, False), (0.2, False), (0.1, False)
    ]
    
    accuracy = metrics.calculate_confidence_accuracy(predictions)
    assert accuracy > 0.5  # Should be reasonably calibrated

def test_interpretation_metrics_astrological_accuracy():
    """Test astrological accuracy"""
    metrics = InterpretationMetrics()
    
    interpretation = "Your almuten is Mercury, indicating strong communication. This is a day birth with emphasis on solar themes."
    
    chart_data = {
        "almuten": {"winner": "Mercury"},
        "is_day_birth": True,
        "zodiacal_releasing": {
            "current_periods": {
                "l1": {"ruler": "Sun"}
            }
        }
    }
    
    accuracy = metrics.calculate_astrological_accuracy(interpretation, chart_data)
    
    # Should score well since Mercury and day birth are mentioned
    assert accuracy > 0.5

def test_performance_metrics():
    """Test performance metrics collection"""
    metrics = PerformanceMetrics()
    
    # Record some data
    metrics.record_response_time(1.5)
    metrics.record_response_time(2.0)
    metrics.record_response_time(0.8)
    
    metrics.record_cache_hit()
    metrics.record_cache_hit()
    metrics.record_cache_miss()
    
    metrics.record_error()
    
    # Test calculations
    avg_time = metrics.get_avg_response_time()
    assert abs(avg_time - 1.43) < 0.1  # (1.5 + 2.0 + 0.8) / 3
    
    cache_hit_rate = metrics.get_cache_hit_rate()
    assert abs(cache_hit_rate - 0.67) < 0.1  # 2 hits out of 3 total
    
    error_rate = metrics.get_error_rate()
    assert abs(error_rate - 0.33) < 0.1  # 1 error out of 3 requests

def test_evaluation_suite_rag_evaluation():
    """Test complete RAG evaluation"""
    suite = EvaluationSuite()
    
    query = "What is almuten figuris?"
    retrieved_docs = ["doc1", "doc2", "doc3"]
    relevant_docs = ["doc1", "doc3"]
    generated_text = "Almuten figuris shows the strongest planet"
    citations = [{"credibility": 0.8, "title": "Traditional Astrology"}]
    
    results = suite.evaluate_rag_system(
        query, retrieved_docs, relevant_docs, generated_text, citations
    )
    
    assert len(results) >= 4  # Should have recall, precision, faithfulness, groundedness
    
    # Check that all results are MetricResult objects
    for result in results:
        assert isinstance(result, MetricResult)
        assert 0 <= result.value <= 1  # Most metrics should be 0-1

def test_evaluation_suite_interpretation_evaluation():
    """Test interpretation evaluation"""
    suite = EvaluationSuite()
    
    interpretation = "Your Mercury almuten indicates strong communication skills in this day birth chart."
    chart_data = {
        "almuten": {"winner": "Mercury"},
        "is_day_birth": True
    }
    confidence = 0.75
    
    results = suite.evaluate_interpretation(interpretation, chart_data, confidence)
    
    assert len(results) >= 2  # Should have coherence and accuracy
    
    # Check metric types
    metric_names = [r.name for r in results]
    assert "interpretation_coherence" in metric_names
    assert "astrological_accuracy" in metric_names

def test_evaluation_suite_performance_evaluation():
    """Test performance evaluation"""
    suite = EvaluationSuite()
    
    response_time = 1.5
    results = suite.evaluate_system_performance(response_time)
    
    assert len(results) >= 3  # Should have response time, avg, cache hit rate
    
    # Check that response time is recorded
    response_time_metric = next(r for r in results if r.name == "response_time")
    assert response_time_metric.value == response_time

def test_evaluation_suite_summary():
    """Test evaluation summary generation"""
    suite = EvaluationSuite()
    
    # Add some mock results
    mock_results = [
        MetricResult(
            name="faithfulness",
            value=0.8,
            metric_type=MetricType.QUALITY,
            description="Test metric",
            timestamp=datetime.now()
        ),
        MetricResult(
            name="faithfulness",
            value=0.7,
            metric_type=MetricType.QUALITY,
            description="Test metric",
            timestamp=datetime.now()
        )
    ]
    
    suite.add_evaluation_results(mock_results)
    
    summary = suite.get_evaluation_summary(time_window_hours=1)
    
    assert "metrics_summary" in summary
    assert "overall_health_score" in summary
    assert "total_evaluations" in summary
    
    # Should have faithfulness metrics
    assert "faithfulness" in summary["metrics_summary"]
    assert summary["metrics_summary"]["faithfulness"]["count"] == 2

def test_metric_result_is_good():
    """Test metric quality assessment"""
    # Good faithfulness score
    good_metric = MetricResult(
        name="faithfulness",
        value=0.85,
        metric_type=MetricType.QUALITY,
        description="Good faithfulness",
        timestamp=datetime.now()
    )
    assert good_metric.is_good
    
    # Poor faithfulness score
    poor_metric = MetricResult(
        name="faithfulness",
        value=0.4,
        metric_type=MetricType.QUALITY,
        description="Poor faithfulness",
        timestamp=datetime.now()
    )
    assert not poor_metric.is_good
    
    # Response time (lower is better)
    fast_response = MetricResult(
        name="response_time",
        value=1.0,
        metric_type=MetricType.PERFORMANCE,
        description="Fast response",
        timestamp=datetime.now()
    )
    assert fast_response.is_good
    
    slow_response = MetricResult(
        name="response_time",
        value=3.0,
        metric_type=MetricType.PERFORMANCE,
        description="Slow response",
        timestamp=datetime.now()
    )
    assert not slow_response.is_good