"""
Evaluation metrics for astrological interpretation system
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math
import statistics
from datetime import datetime, timedelta

class MetricType(Enum):
    """Types of evaluation metrics"""
    INTRINSIC = "intrinsic"  # System-internal metrics
    EXTRINSIC = "extrinsic"  # User-facing metrics
    PERFORMANCE = "performance"  # System performance
    QUALITY = "quality"  # Content quality

@dataclass
class MetricResult:
    """Single metric evaluation result"""
    name: str
    value: float
    metric_type: MetricType
    description: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    @property
    def is_good(self) -> bool:
        """Determine if metric value is considered good"""
        # Define thresholds for different metrics
        thresholds = {
            'recall_at_k': 0.7,
            'precision_at_k': 0.6,
            'ndcg': 0.7,
            'faithfulness': 0.8,
            'groundedness': 0.75,
            'confidence_accuracy': 0.7,
            'response_time': 2.0,  # seconds (lower is better)
            'cache_hit_rate': 0.6,
            'interpretation_coherence': 0.7,
            'citation_quality': 0.8,
        }
        
        threshold = thresholds.get(self.name, 0.5)
        
        # For response time, lower is better
        if self.name == 'response_time':
            return self.value <= threshold
        
        return self.value >= threshold

class RAGMetrics:
    """RAG system evaluation metrics"""
    
    def __init__(self):
        self.query_history = []
        self.retrieval_history = []
    
    def calculate_recall_at_k(self, retrieved_docs: List[str], 
                             relevant_docs: List[str], k: int = 10) -> float:
        """Calculate Recall@K for retrieval system"""
        if not relevant_docs:
            return 0.0
        
        retrieved_set = set(retrieved_docs[:k])
        relevant_set = set(relevant_docs)
        
        intersection = retrieved_set & relevant_set
        recall = len(intersection) / len(relevant_set)
        
        return recall
    
    def calculate_precision_at_k(self, retrieved_docs: List[str], 
                                relevant_docs: List[str], k: int = 10) -> float:
        """Calculate Precision@K for retrieval system"""
        if not retrieved_docs:
            return 0.0
        
        retrieved_k = retrieved_docs[:k]
        relevant_set = set(relevant_docs)
        
        relevant_retrieved = sum(1 for doc in retrieved_k if doc in relevant_set)
        precision = relevant_retrieved / len(retrieved_k)
        
        return precision
    
    def calculate_ndcg(self, retrieved_docs: List[str], 
                      relevance_scores: Dict[str, float], k: int = 10) -> float:
        """Calculate Normalized Discounted Cumulative Gain"""
        if not retrieved_docs or not relevance_scores:
            return 0.0
        
        # DCG calculation
        dcg = 0.0
        for i, doc in enumerate(retrieved_docs[:k]):
            if doc in relevance_scores:
                relevance = relevance_scores[doc]
                dcg += (2**relevance - 1) / math.log2(i + 2)
        
        # IDCG calculation (ideal ranking)
        sorted_relevance = sorted(relevance_scores.values(), reverse=True)
        idcg = 0.0
        for i, relevance in enumerate(sorted_relevance[:k]):
            idcg += (2**relevance - 1) / math.log2(i + 2)
        
        if idcg == 0:
            return 0.0
        
        ndcg = dcg / idcg
        return ndcg
    
    def calculate_faithfulness(self, generated_text: str, 
                              source_documents: List[str]) -> float:
        """Calculate faithfulness score (how well generation follows sources)"""
        if not source_documents or not generated_text:
            return 0.0
        
        # Simple faithfulness calculation based on content overlap
        generated_words = set(generated_text.lower().split())
        
        total_overlap = 0
        total_source_words = 0
        
        for doc in source_documents:
            doc_words = set(doc.lower().split())
            overlap = len(generated_words & doc_words)
            total_overlap += overlap
            total_source_words += len(doc_words)
        
        if total_source_words == 0:
            return 0.0
        
        # Normalize by source content length
        faithfulness = min(total_overlap / len(generated_words), 1.0)
        return faithfulness
    
    def calculate_groundedness(self, generated_text: str, 
                              citations: List[Dict[str, Any]]) -> float:
        """Calculate groundedness score (how well claims are supported)"""
        if not citations or not generated_text:
            return 0.0
        
        # Count sentences in generated text
        sentences = [s.strip() for s in generated_text.split('.') if s.strip()]
        if not sentences:
            return 0.0
        
        # Simple heuristic: assume each citation supports some claims
        supported_ratio = min(len(citations) / len(sentences), 1.0)
        
        # Weight by citation credibility
        avg_credibility = sum(c.get('credibility', 0.5) for c in citations) / len(citations)
        
        groundedness = supported_ratio * avg_credibility
        return groundedness

class InterpretationMetrics:
    """Interpretation quality evaluation metrics"""
    
    def calculate_coherence(self, interpretation_text: str) -> float:
        """Calculate interpretation coherence score"""
        if not interpretation_text:
            return 0.0
        
        sentences = [s.strip() for s in interpretation_text.split('.') if s.strip()]
        if len(sentences) < 2:
            return 1.0  # Single sentence is coherent by definition
        
        # Start with perfect coherence
        coherence_score = 1.0
        
        # Check for direct contradictions
        text_lower = interpretation_text.lower()
        
        # Define contradictory pairs
        contradictions = [
            ('strong', 'weak'),
            ('good', 'bad'),
            ('very good', 'very bad'),
            ('excellent', 'poor'),
            ('beneficial', 'harmful'),
            ('positive', 'negative'),
            ('favorable', 'unfavorable')
        ]
        
        contradiction_penalty = 0.0
        for pos_word, neg_word in contradictions:
            if pos_word in text_lower and neg_word in text_lower:
                # Check if they're about the same topic
                pos_sentences = [s for s in sentences if pos_word in s.lower()]
                neg_sentences = [s for s in sentences if neg_word in s.lower()]
                
                # If contradictory words appear in different sentences about similar topics
                if pos_sentences and neg_sentences:
                    contradiction_penalty += 0.2
        
        # Apply contradiction penalty
        coherence_score -= min(contradiction_penalty, 0.5)
        
        # Check for excessive repetition
        word_counts = {}
        words = [word for word in text_lower.split() if len(word) > 3]
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Penalize if any word appears too frequently
        total_words = len(words)
        if total_words > 0:
            max_frequency = max(word_counts.values()) if word_counts else 0
            repetition_ratio = max_frequency / total_words
            if repetition_ratio > 0.15:  # More than 15% repetition
                coherence_score *= 0.9
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, coherence_score))
    
    def calculate_confidence_accuracy(self, predictions: List[Tuple[float, bool]]) -> float:
        """Calculate confidence calibration accuracy"""
        if not predictions:
            return 0.0
        
        # Group predictions by confidence bins
        bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        bin_accuracies = []
        
        for i in range(len(bins) - 1):
            bin_predictions = [
                (conf, correct) for conf, correct in predictions
                if bins[i] <= conf < bins[i + 1]
            ]
            
            if bin_predictions:
                accuracy = sum(correct for _, correct in bin_predictions) / len(bin_predictions)
                expected_accuracy = (bins[i] + bins[i + 1]) / 2
                bin_accuracies.append(abs(accuracy - expected_accuracy))
        
        if not bin_accuracies:
            return 0.0
        
        # Lower deviation from expected accuracy is better
        avg_deviation = sum(bin_accuracies) / len(bin_accuracies)
        calibration_score = max(0.0, 1.0 - avg_deviation)
        
        return calibration_score
    
    def calculate_astrological_accuracy(self, interpretation: str, 
                                      chart_data: Dict[str, Any]) -> float:
        """Calculate astrological accuracy based on chart data"""
        if not interpretation or not chart_data:
            return 0.0
        
        accuracy_score = 0.0
        total_checks = 0
        
        # Check if almuten is mentioned correctly
        almuten = chart_data.get('almuten', {}).get('winner')
        if almuten:
            total_checks += 1
            if almuten.lower() in interpretation.lower():
                accuracy_score += 1.0
        
        # Check if sect is mentioned correctly
        is_day = chart_data.get('is_day_birth')
        if is_day is not None:
            total_checks += 1
            sect_word = 'day' if is_day else 'night'
            if sect_word in interpretation.lower():
                accuracy_score += 1.0
        
        # Check if current time-lord periods are mentioned
        zr_data = chart_data.get('zodiacal_releasing', {})
        current_periods = zr_data.get('current_periods', {})
        
        if current_periods.get('l1'):
            total_checks += 1
            l1_ruler = current_periods['l1'].get('ruler', '')
            if l1_ruler.lower() in interpretation.lower():
                accuracy_score += 1.0
        
        # Check profection year lord
        profection = chart_data.get('profection', {})
        year_lord = profection.get('year_lord')
        if year_lord:
            total_checks += 1
            if year_lord.lower() in interpretation.lower():
                accuracy_score += 1.0
        
        if total_checks == 0:
            return 0.5  # Neutral score if no checks possible
        
        return accuracy_score / total_checks

class PerformanceMetrics:
    """System performance evaluation metrics"""
    
    def __init__(self):
        self.response_times = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.error_count = 0
        self.total_requests = 0
    
    def record_response_time(self, response_time: float):
        """Record API response time"""
        self.response_times.append(response_time)
        self.total_requests += 1
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.cache_misses += 1
    
    def record_error(self):
        """Record system error"""
        self.error_count += 1
    
    def get_avg_response_time(self) -> float:
        """Get average response time"""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)
    
    def get_p95_response_time(self) -> float:
        """Get 95th percentile response time"""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate"""
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return self.cache_hits / total_cache_requests
    
    def get_error_rate(self) -> float:
        """Get error rate"""
        if self.total_requests == 0:
            return 0.0
        return self.error_count / self.total_requests
    
    def get_throughput(self, time_window_hours: float = 1.0) -> float:
        """Get requests per hour throughput"""
        if not self.response_times:
            return 0.0
        
        # Simple approximation - in real system would use timestamps
        return len(self.response_times) / time_window_hours

class EvaluationSuite:
    """Complete evaluation suite for the astrological system"""
    
    def __init__(self):
        self.rag_metrics = RAGMetrics()
        self.interpretation_metrics = InterpretationMetrics()
        self.performance_metrics = PerformanceMetrics()
        self.evaluation_history = []
    
    def evaluate_rag_system(self, query: str, retrieved_docs: List[str],
                           relevant_docs: List[str], generated_text: str,
                           citations: List[Dict[str, Any]]) -> List[MetricResult]:
        """Evaluate RAG system performance"""
        results = []
        timestamp = datetime.now()
        
        # Recall@K
        recall_5 = self.rag_metrics.calculate_recall_at_k(retrieved_docs, relevant_docs, k=5)
        results.append(MetricResult(
            name="recall_at_5",
            value=recall_5,
            metric_type=MetricType.INTRINSIC,
            description="Recall@5 for document retrieval",
            timestamp=timestamp
        ))
        
        # Precision@K
        precision_5 = self.rag_metrics.calculate_precision_at_k(retrieved_docs, relevant_docs, k=5)
        results.append(MetricResult(
            name="precision_at_5",
            value=precision_5,
            metric_type=MetricType.INTRINSIC,
            description="Precision@5 for document retrieval",
            timestamp=timestamp
        ))
        
        # Faithfulness
        faithfulness = self.rag_metrics.calculate_faithfulness(generated_text, retrieved_docs)
        results.append(MetricResult(
            name="faithfulness",
            value=faithfulness,
            metric_type=MetricType.QUALITY,
            description="Faithfulness of generated text to sources",
            timestamp=timestamp
        ))
        
        # Groundedness
        groundedness = self.rag_metrics.calculate_groundedness(generated_text, citations)
        results.append(MetricResult(
            name="groundedness",
            value=groundedness,
            metric_type=MetricType.QUALITY,
            description="How well claims are supported by citations",
            timestamp=timestamp
        ))
        
        return results
    
    def evaluate_interpretation(self, interpretation: str, chart_data: Dict[str, Any],
                              confidence: float, user_feedback: Optional[bool] = None) -> List[MetricResult]:
        """Evaluate interpretation quality"""
        results = []
        timestamp = datetime.now()
        
        # Coherence
        coherence = self.interpretation_metrics.calculate_coherence(interpretation)
        results.append(MetricResult(
            name="interpretation_coherence",
            value=coherence,
            metric_type=MetricType.QUALITY,
            description="Coherence of interpretation text",
            timestamp=timestamp
        ))
        
        # Astrological accuracy
        accuracy = self.interpretation_metrics.calculate_astrological_accuracy(interpretation, chart_data)
        results.append(MetricResult(
            name="astrological_accuracy",
            value=accuracy,
            metric_type=MetricType.QUALITY,
            description="Accuracy of astrological claims",
            timestamp=timestamp
        ))
        
        # User satisfaction (if feedback available)
        if user_feedback is not None:
            results.append(MetricResult(
                name="user_satisfaction",
                value=1.0 if user_feedback else 0.0,
                metric_type=MetricType.EXTRINSIC,
                description="User satisfaction with interpretation",
                timestamp=timestamp
            ))
        
        return results
    
    def evaluate_system_performance(self, response_time: float) -> List[MetricResult]:
        """Evaluate system performance"""
        results = []
        timestamp = datetime.now()
        
        # Record metrics
        self.performance_metrics.record_response_time(response_time)
        
        # Response time
        results.append(MetricResult(
            name="response_time",
            value=response_time,
            metric_type=MetricType.PERFORMANCE,
            description="API response time in seconds",
            timestamp=timestamp
        ))
        
        # Average response time
        avg_response_time = self.performance_metrics.get_avg_response_time()
        results.append(MetricResult(
            name="avg_response_time",
            value=avg_response_time,
            metric_type=MetricType.PERFORMANCE,
            description="Average response time",
            timestamp=timestamp
        ))
        
        # Cache hit rate
        cache_hit_rate = self.performance_metrics.get_cache_hit_rate()
        results.append(MetricResult(
            name="cache_hit_rate",
            value=cache_hit_rate,
            metric_type=MetricType.PERFORMANCE,
            description="Cache hit rate",
            timestamp=timestamp
        ))
        
        return results
    
    def get_evaluation_summary(self, time_window_hours: float = 24.0) -> Dict[str, Any]:
        """Get evaluation summary for specified time window"""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        recent_results = [
            result for result in self.evaluation_history
            if result.timestamp >= cutoff_time
        ]
        
        if not recent_results:
            return {"message": "No recent evaluation data"}
        
        # Group by metric name
        metrics_by_name = {}
        for result in recent_results:
            if result.name not in metrics_by_name:
                metrics_by_name[result.name] = []
            metrics_by_name[result.name].append(result.value)
        
        # Calculate summary statistics
        summary = {}
        for metric_name, values in metrics_by_name.items():
            summary[metric_name] = {
                "count": len(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0.0
            }
        
        # Overall health score
        health_metrics = ['recall_at_5', 'faithfulness', 'interpretation_coherence', 'astrological_accuracy']
        health_scores = []
        
        for metric in health_metrics:
            if metric in summary:
                health_scores.append(summary[metric]["mean"])
        
        overall_health = statistics.mean(health_scores) if health_scores else 0.0
        
        return {
            "time_window_hours": time_window_hours,
            "total_evaluations": len(recent_results),
            "metrics_summary": summary,
            "overall_health_score": overall_health,
            "timestamp": datetime.now().isoformat()
        }
    
    def add_evaluation_results(self, results: List[MetricResult]):
        """Add evaluation results to history"""
        self.evaluation_history.extend(results)