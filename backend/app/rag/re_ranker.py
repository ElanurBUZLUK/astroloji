"""
Re-ranking system for retrieved documents
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math
import re

from .retriever import RetrievalResult

class RerankingMethod(Enum):
    """Re-ranking methods"""
    CROSS_ENCODER = "cross_encoder"
    LLM_JUDGE = "llm_judge"
    RULE_BASED = "rule_based"
    COMBINED = "combined"

@dataclass
class RerankingResult:
    """Re-ranked retrieval result"""
    original_result: RetrievalResult
    rerank_score: float
    rerank_reason: str
    final_score: float
    rank_change: int = 0

class RuleBasedReranker:
    """Rule-based re-ranking for astrological content"""
    
    def __init__(self):
        self.relevance_rules = self._load_relevance_rules()
        self.quality_rules = self._load_quality_rules()
    
    def _load_relevance_rules(self) -> Dict[str, Any]:
        """Load relevance scoring rules"""
        return {
            # Topic-specific boosts
            "topic_boosts": {
                "almuten": 1.3,
                "zodiacal_releasing": 1.2,
                "profection": 1.2,
                "firdaria": 1.1,
                "dignity": 1.2,
                "sect": 1.1,
                "antiscia": 1.0,
                "aspect": 1.0
            },
            
            # Source credibility
            "source_credibility": {
                "traditional_astrology": 1.3,
                "hellenistic_timing": 1.2,
                "persian_periods": 1.1,
                "modern_synthesis": 0.9,
                "experimental": 0.8
            },
            
            # Language preference (can be adjusted per user)
            "language_preference": {
                "en": 1.0,
                "tr": 1.0  # Equal weight for now
            },
            
            # Content length optimization
            "length_optimization": {
                "min_length": 50,   # Too short = penalty
                "max_length": 500,  # Too long = penalty
                "optimal_min": 100,
                "optimal_max": 300
            }
        }
    
    def _load_quality_rules(self) -> Dict[str, Any]:
        """Load content quality rules"""
        return {
            # Technical term density (good for astrological content)
            "technical_terms": [
                "dignity", "rulership", "exaltation", "triplicity", "term", "face",
                "sect", "diurnal", "nocturnal", "malefic", "benefic",
                "almuten", "hyleg", "alcocoden", "reception", "antiscia",
                "profection", "firdaria", "zodiacal releasing", "progression",
                "transit", "aspect", "conjunction", "opposition", "trine", "square", "sextile"
            ],
            
            # Quality indicators
            "quality_indicators": [
                "according to", "traditional", "hellenistic", "medieval",
                "calculation", "method", "technique", "interpretation"
            ],
            
            # Negative quality indicators
            "quality_detractors": [
                "maybe", "possibly", "unclear", "uncertain", "vague"
            ]
        }
    
    def rerank(self, results: List[RetrievalResult], query: str, 
              context: Dict[str, Any] = None) -> List[RerankingResult]:
        """Re-rank results using rule-based scoring"""
        
        reranked_results = []
        
        for i, result in enumerate(results):
            # Calculate re-ranking score
            rerank_score = self._calculate_rerank_score(result, query, context)
            
            # Combine with original score
            final_score = self._combine_scores(result.score, rerank_score)
            
            # Create re-ranking result
            rerank_result = RerankingResult(
                original_result=result,
                rerank_score=rerank_score,
                rerank_reason=self._get_rerank_reason(result, rerank_score),
                final_score=final_score,
                rank_change=0  # Will be calculated after sorting
            )
            
            reranked_results.append(rerank_result)
        
        # Sort by final score
        reranked_results.sort(key=lambda x: x.final_score, reverse=True)
        
        # Calculate rank changes
        for new_rank, rerank_result in enumerate(reranked_results):
            original_rank = results.index(rerank_result.original_result)
            rerank_result.rank_change = original_rank - new_rank
        
        return reranked_results
    
    def _calculate_rerank_score(self, result: RetrievalResult, query: str,
                               context: Dict[str, Any] = None) -> float:
        """Calculate re-ranking score for a result"""
        score = 1.0  # Base score
        
        metadata = result.metadata or {}
        content = result.content.lower()
        query_lower = query.lower()
        
        # Topic relevance boost
        topic = metadata.get("topic", "")
        if topic in self.relevance_rules["topic_boosts"]:
            score *= self.relevance_rules["topic_boosts"][topic]
        
        # Source credibility
        source = metadata.get("source", "")
        if source in self.relevance_rules["source_credibility"]:
            score *= self.relevance_rules["source_credibility"][source]
        
        # Language preference
        language = metadata.get("language", "en")
        if language in self.relevance_rules["language_preference"]:
            score *= self.relevance_rules["language_preference"][language]
        
        # Content length optimization
        content_length = len(result.content)
        length_rules = self.relevance_rules["length_optimization"]
        
        if content_length < length_rules["min_length"]:
            score *= 0.7  # Too short penalty
        elif content_length > length_rules["max_length"]:
            score *= 0.8  # Too long penalty
        elif length_rules["optimal_min"] <= content_length <= length_rules["optimal_max"]:
            score *= 1.1  # Optimal length bonus
        
        # Technical term density
        technical_terms = self.quality_rules["technical_terms"]
        term_count = sum(1 for term in technical_terms if term in content)
        term_density = term_count / max(len(content.split()), 1)
        
        if term_density > 0.05:  # Good technical density
            score *= 1.2
        elif term_density > 0.02:
            score *= 1.1
        
        # Quality indicators
        quality_indicators = self.quality_rules["quality_indicators"]
        quality_count = sum(1 for indicator in quality_indicators if indicator in content)
        if quality_count > 0:
            score *= (1.0 + quality_count * 0.05)  # Small boost per indicator
        
        # Quality detractors
        quality_detractors = self.quality_rules["quality_detractors"]
        detractor_count = sum(1 for detractor in quality_detractors if detractor in content)
        if detractor_count > 0:
            score *= (1.0 - detractor_count * 0.1)  # Penalty per detractor
        
        # Query term matching (exact and partial)
        query_terms = query_lower.split()
        exact_matches = sum(1 for term in query_terms if term in content)
        partial_matches = sum(1 for term in query_terms 
                            if any(term in word for word in content.split()))
        
        match_score = (exact_matches * 2 + partial_matches) / max(len(query_terms), 1)
        score *= (1.0 + match_score * 0.3)
        
        # Context-specific boosts
        if context:
            # User preferences
            user_level = context.get("user_level", "intermediate")
            if user_level == "beginner" and "traditional" in content:
                score *= 1.1  # Boost traditional explanations for beginners
            elif user_level == "advanced" and "calculation" in content:
                score *= 1.1  # Boost technical content for advanced users
            
            # Chart context
            chart_elements = context.get("chart_elements", [])
            for element in chart_elements:
                if element.lower() in content:
                    score *= 1.05  # Small boost for chart-relevant content
        
        return score
    
    def _combine_scores(self, original_score: float, rerank_score: float) -> float:
        """Combine original retrieval score with re-ranking score"""
        # Weighted combination: 60% original, 40% rerank
        return 0.6 * original_score + 0.4 * rerank_score
    
    def _get_rerank_reason(self, result: RetrievalResult, rerank_score: float) -> str:
        """Generate explanation for re-ranking decision"""
        reasons = []
        
        metadata = result.metadata or {}
        
        # Topic boost
        topic = metadata.get("topic", "")
        if topic in self.relevance_rules["topic_boosts"]:
            boost = self.relevance_rules["topic_boosts"][topic]
            if boost > 1.1:
                reasons.append(f"High relevance topic: {topic}")
        
        # Source credibility
        source = metadata.get("source", "")
        if source in self.relevance_rules["source_credibility"]:
            credibility = self.relevance_rules["source_credibility"][source]
            if credibility > 1.1:
                reasons.append(f"Credible source: {source}")
        
        # Content quality
        content = result.content.lower()
        technical_terms = self.quality_rules["technical_terms"]
        term_count = sum(1 for term in technical_terms if term in content)
        
        if term_count > 3:
            reasons.append(f"Rich technical content ({term_count} terms)")
        
        # Overall score assessment
        if rerank_score > 1.3:
            reasons.append("High overall relevance")
        elif rerank_score < 0.8:
            reasons.append("Lower relevance factors")
        
        return "; ".join(reasons) if reasons else "Standard relevance"

class MockCrossEncoder:
    """Mock cross-encoder for development/testing"""
    
    def __init__(self):
        pass
    
    def score_pairs(self, query: str, documents: List[str]) -> List[float]:
        """Mock cross-encoder scoring"""
        scores = []
        
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        for doc in documents:
            doc_lower = doc.lower()
            doc_terms = set(doc_lower.split())
            
            # Simple Jaccard similarity as mock cross-encoder score
            intersection = len(query_terms & doc_terms)
            union = len(query_terms | doc_terms)
            
            jaccard_score = intersection / union if union > 0 else 0
            
            # Scale to reasonable cross-encoder range
            score = jaccard_score * 2.0  # 0-2 range
            scores.append(score)
        
        return scores

class HybridReranker:
    """Hybrid re-ranker combining multiple methods"""
    
    def __init__(self):
        self.rule_based_reranker = RuleBasedReranker()
        self.cross_encoder = MockCrossEncoder()
    
    def rerank(self, results: List[RetrievalResult], query: str,
              method: RerankingMethod = RerankingMethod.COMBINED,
              context: Dict[str, Any] = None) -> List[RerankingResult]:
        """Re-rank results using specified method"""
        
        if method == RerankingMethod.RULE_BASED:
            return self.rule_based_reranker.rerank(results, query, context)
        elif method == RerankingMethod.CROSS_ENCODER:
            return self._cross_encoder_rerank(results, query, context)
        elif method == RerankingMethod.LLM_JUDGE:
            return self._llm_judge_rerank(results, query, context)
        else:  # COMBINED
            return self._combined_rerank(results, query, context)
    
    def _cross_encoder_rerank(self, results: List[RetrievalResult], query: str,
                             context: Dict[str, Any] = None) -> List[RerankingResult]:
        """Re-rank using cross-encoder"""
        documents = [result.content for result in results]
        cross_encoder_scores = self.cross_encoder.score_pairs(query, documents)
        
        reranked_results = []
        
        for i, (result, ce_score) in enumerate(zip(results, cross_encoder_scores)):
            # Combine original score with cross-encoder score
            final_score = 0.5 * result.score + 0.5 * ce_score
            
            rerank_result = RerankingResult(
                original_result=result,
                rerank_score=ce_score,
                rerank_reason=f"Cross-encoder relevance: {ce_score:.3f}",
                final_score=final_score
            )
            
            reranked_results.append(rerank_result)
        
        # Sort by final score
        reranked_results.sort(key=lambda x: x.final_score, reverse=True)
        
        return reranked_results
    
    def _llm_judge_rerank(self, results: List[RetrievalResult], query: str,
                         context: Dict[str, Any] = None) -> List[RerankingResult]:
        """Re-rank using LLM judge (mock implementation)"""
        # Mock LLM judge - in reality would call an LLM API
        reranked_results = []
        
        for i, result in enumerate(results):
            # Mock LLM scoring based on content relevance
            content_lower = result.content.lower()
            query_lower = query.lower()
            
            # Simple relevance scoring
            relevance_score = 0.5  # Base score
            
            if any(term in content_lower for term in query_lower.split()):
                relevance_score += 0.3
            
            if len(result.content) > 100:  # Substantial content
                relevance_score += 0.2
            
            final_score = 0.7 * result.score + 0.3 * relevance_score
            
            rerank_result = RerankingResult(
                original_result=result,
                rerank_score=relevance_score,
                rerank_reason=f"LLM relevance assessment: {relevance_score:.3f}",
                final_score=final_score
            )
            
            reranked_results.append(rerank_result)
        
        reranked_results.sort(key=lambda x: x.final_score, reverse=True)
        return reranked_results
    
    def _combined_rerank(self, results: List[RetrievalResult], query: str,
                        context: Dict[str, Any] = None) -> List[RerankingResult]:
        """Combine multiple re-ranking methods"""
        
        # Get scores from different methods
        rule_based_results = self.rule_based_reranker.rerank(results, query, context)
        cross_encoder_results = self._cross_encoder_rerank(results, query, context)
        
        # Combine scores
        combined_results = []
        
        for i, result in enumerate(results):
            rule_based_score = rule_based_results[i].rerank_score
            cross_encoder_score = cross_encoder_results[i].rerank_score
            
            # Weighted combination: 60% rule-based, 40% cross-encoder
            combined_rerank_score = 0.6 * rule_based_score + 0.4 * cross_encoder_score
            
            # Final score combines original retrieval with combined re-ranking
            final_score = 0.5 * result.score + 0.5 * combined_rerank_score
            
            combined_result = RerankingResult(
                original_result=result,
                rerank_score=combined_rerank_score,
                rerank_reason=f"Combined: rule-based ({rule_based_score:.2f}) + cross-encoder ({cross_encoder_score:.2f})",
                final_score=final_score
            )
            
            combined_results.append(combined_result)
        
        # Sort by final score
        combined_results.sort(key=lambda x: x.final_score, reverse=True)
        
        # Calculate rank changes
        for new_rank, rerank_result in enumerate(combined_results):
            original_rank = results.index(rerank_result.original_result)
            rerank_result.rank_change = original_rank - new_rank
        
        return combined_results
    
    def get_reranking_stats(self, reranked_results: List[RerankingResult]) -> Dict[str, Any]:
        """Get re-ranking statistics"""
        if not reranked_results:
            return {}
        
        rank_changes = [abs(r.rank_change) for r in reranked_results]
        
        return {
            "total_results": len(reranked_results),
            "average_rank_change": sum(rank_changes) / len(rank_changes),
            "max_rank_change": max(rank_changes),
            "results_reordered": sum(1 for r in reranked_results if r.rank_change != 0),
            "average_rerank_score": sum(r.rerank_score for r in reranked_results) / len(reranked_results),
            "score_improvement": sum(1 for r in reranked_results if r.final_score > r.original_result.score)
        }