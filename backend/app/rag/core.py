"""
Core RAG system that orchestrates retrieval, re-ranking, and citation
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .retriever import HybridRetriever, MockVectorStore, MockSparseStore, RetrievalQuery, RetrievalMethod
from .query_expansion import QueryExpander, ExpansionMethod
from .re_ranker import HybridReranker, RerankingMethod
from .citation import CitationManager, CitationStyle

@dataclass
class RAGQuery:
    """Complete RAG query with all parameters"""
    query: str
    context: Dict[str, Any] = None
    top_k: int = 10
    expand_query: bool = True
    rerank_results: bool = True
    include_citations: bool = True
    citation_style: CitationStyle = CitationStyle.INLINE
    filters: Dict[str, Any] = None

@dataclass
class RAGResponse:
    """Complete RAG response with retrieved content and metadata"""
    query: str
    retrieved_content: List[str]
    citations: List[Any] = None
    confidence_score: float = 0.0
    retrieval_stats: Dict[str, Any] = None
    expansion_stats: Dict[str, Any] = None
    reranking_stats: Dict[str, Any] = None
    processing_time: float = 0.0

class RAGSystem:
    """Main RAG system orchestrating all components"""
    
    def __init__(self):
        # Initialize components
        self.vector_store = MockVectorStore()
        self.sparse_store = MockSparseStore()
        self.retriever = HybridRetriever(self.vector_store, self.sparse_store)
        self.query_expander = QueryExpander()
        self.reranker = HybridReranker()
        self.citation_manager = CitationManager()
        
        # System stats
        self.query_count = 0
        self.total_processing_time = 0.0
    
    async def query(self, rag_query: RAGQuery) -> RAGResponse:
        """Process complete RAG query"""
        start_time = datetime.now()
        
        try:
            # Step 1: Query expansion
            expanded_query = None
            if rag_query.expand_query:
                expanded_query = self.query_expander.expand_query(
                    rag_query.query, 
                    method=ExpansionMethod.COMBINED
                )
                search_query = " ".join([rag_query.query] + expanded_query.expanded_terms[:5])
            else:
                search_query = rag_query.query
            
            # Step 2: Retrieval
            retrieval_query = RetrievalQuery(
                query_text=search_query,
                filters=rag_query.filters,
                top_k=rag_query.top_k * 2,  # Get more for re-ranking
                method=RetrievalMethod.HYBRID,
                context=rag_query.context
            )
            
            retrieval_results = await self.retriever.retrieve(retrieval_query)
            
            # Step 3: Re-ranking
            if rag_query.rerank_results and retrieval_results:
                reranked_results = self.reranker.rerank(
                    retrieval_results,
                    rag_query.query,
                    method=RerankingMethod.COMBINED,
                    context=rag_query.context
                )
                
                # Take top results after re-ranking
                final_results = [r.original_result for r in reranked_results[:rag_query.top_k]]
                reranking_stats = self.reranker.get_reranking_stats(reranked_results)
            else:
                final_results = retrieval_results[:rag_query.top_k]
                reranking_stats = {}
            
            # Step 4: Citation management
            citations = None
            if rag_query.include_citations and final_results:
                citations = self.citation_manager.create_citations(final_results)
            
            # Step 5: Compile response
            retrieved_content = [result.content for result in final_results]
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(final_results, rag_query)
            
            # Gather stats
            processing_time = (datetime.now() - start_time).total_seconds()
            
            expansion_stats = {}
            if expanded_query:
                expansion_stats = self.query_expander.get_expansion_stats(expanded_query)
            
            retrieval_stats = {
                "total_retrieved": len(retrieval_results),
                "final_count": len(final_results),
                "retrieval_method": "hybrid",
                "average_score": sum(r.score for r in final_results) / len(final_results) if final_results else 0
            }
            
            # Update system stats
            self.query_count += 1
            self.total_processing_time += processing_time
            
            return RAGResponse(
                query=rag_query.query,
                retrieved_content=retrieved_content,
                citations=citations,
                confidence_score=confidence_score,
                retrieval_stats=retrieval_stats,
                expansion_stats=expansion_stats,
                reranking_stats=reranking_stats,
                processing_time=processing_time
            )
            
        except Exception as e:
            # Return error response
            processing_time = (datetime.now() - start_time).total_seconds()
            return RAGResponse(
                query=rag_query.query,
                retrieved_content=[f"Error processing query: {str(e)}"],
                confidence_score=0.0,
                processing_time=processing_time
            )
    
    async def query_by_topic(self, topic: str, top_k: int = 5) -> RAGResponse:
        """Quick query by astrological topic"""
        rag_query = RAGQuery(
            query=topic,
            top_k=top_k,
            expand_query=True,
            rerank_results=True,
            include_citations=True,
            filters={"topic": topic}
        )
        
        return await self.query(rag_query)
    
    async def query_for_interpretation(self, chart_elements: List[str], 
                                     interpretation_context: Dict[str, Any]) -> RAGResponse:
        """Query RAG system for interpretation support"""
        
        # Build query from chart elements
        query_parts = []
        for element in chart_elements[:3]:  # Limit to top 3 elements
            query_parts.append(element)
        
        query = " ".join(query_parts)
        
        # Add interpretation context
        context = {
            "chart_elements": chart_elements,
            "user_level": interpretation_context.get("user_level", "intermediate"),
            "focus_areas": interpretation_context.get("focus_areas", [])
        }
        
        # Build filters from chart elements
        filters = {}
        if any("almuten" in elem.lower() for elem in chart_elements):
            filters["topic"] = "almuten"
        elif any("zr" in elem.lower() or "zodiacal" in elem.lower() for elem in chart_elements):
            filters["topic"] = "zodiacal_releasing"
        elif any("profection" in elem.lower() for elem in chart_elements):
            filters["topic"] = "profection"
        
        rag_query = RAGQuery(
            query=query,
            context=context,
            top_k=8,
            expand_query=True,
            rerank_results=True,
            include_citations=True,
            citation_style=CitationStyle.INLINE,
            filters=filters
        )
        
        return await self.query(rag_query)
    
    def _calculate_confidence_score(self, results: List[Any], rag_query: RAGQuery) -> float:
        """Calculate confidence score for RAG response"""
        if not results:
            return 0.0
        
        # Base confidence from retrieval scores
        avg_retrieval_score = sum(r.score for r in results) / len(results)
        base_confidence = min(avg_retrieval_score, 1.0)
        
        # Boost for multiple results
        result_count_boost = min(len(results) / 5.0, 0.2)  # Up to 20% boost
        
        # Boost for source diversity
        source_types = set()
        for result in results:
            if result.metadata and "source" in result.metadata:
                source_types.add(result.metadata["source"])
        
        diversity_boost = min(len(source_types) / 3.0, 0.1)  # Up to 10% boost
        
        # Penalty for very short content
        avg_content_length = sum(len(r.content) for r in results) / len(results)
        if avg_content_length < 50:
            length_penalty = 0.2
        else:
            length_penalty = 0.0
        
        final_confidence = base_confidence + result_count_boost + diversity_boost - length_penalty
        return max(0.0, min(1.0, final_confidence))
    
    async def get_related_content(self, content: str, top_k: int = 3) -> List[str]:
        """Get content related to given text"""
        # Extract key terms from content
        key_terms = self._extract_key_terms(content)
        query = " ".join(key_terms[:5])
        
        rag_query = RAGQuery(
            query=query,
            top_k=top_k,
            expand_query=False,  # Don't expand for related content
            rerank_results=True,
            include_citations=False
        )
        
        response = await self.query(rag_query)
        return response.retrieved_content
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key astrological terms from text"""
        # Simple keyword extraction
        astrological_terms = [
            "almuten", "dignity", "rulership", "exaltation", "sect",
            "zodiacal releasing", "profection", "firdaria", "transit",
            "aspect", "conjunction", "opposition", "trine", "square",
            "antiscia", "midpoint", "house", "sign", "planet"
        ]
        
        text_lower = text.lower()
        found_terms = []
        
        for term in astrological_terms:
            if term in text_lower:
                found_terms.append(term)
        
        return found_terms
    
    async def validate_response(self, response: RAGResponse) -> Dict[str, Any]:
        """Validate RAG response quality"""
        validation = {
            "is_valid": True,
            "issues": [],
            "quality_score": 0.0,
            "content_analysis": {}
        }
        
        # Check if we have content
        if not response.retrieved_content:
            validation["is_valid"] = False
            validation["issues"].append("No content retrieved")
            return validation
        
        # Check content quality
        total_length = sum(len(content) for content in response.retrieved_content)
        avg_length = total_length / len(response.retrieved_content)
        
        if avg_length < 30:
            validation["issues"].append("Content too short")
            validation["quality_score"] -= 0.2
        
        if total_length < 100:
            validation["issues"].append("Total content insufficient")
            validation["quality_score"] -= 0.3
        
        # Check confidence
        if response.confidence_score < 0.3:
            validation["issues"].append("Low confidence score")
            validation["quality_score"] -= 0.2
        
        # Check citations if included
        if response.citations:
            citation_validation = self.citation_manager.validate_citations(response.citations)
            if citation_validation["valid_citations"] < len(response.citations) * 0.8:
                validation["issues"].append("Citation quality issues")
                validation["quality_score"] -= 0.1
        
        # Calculate final quality score
        base_quality = response.confidence_score
        validation["quality_score"] = max(0.0, base_quality + validation["quality_score"])
        
        validation["content_analysis"] = {
            "total_content_length": total_length,
            "average_content_length": avg_length,
            "content_pieces": len(response.retrieved_content),
            "has_citations": response.citations is not None,
            "processing_time": response.processing_time
        }
        
        return validation
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        return {
            "total_queries": self.query_count,
            "total_processing_time": self.total_processing_time,
            "average_processing_time": self.total_processing_time / max(self.query_count, 1),
            "retriever_stats": self.retriever.get_retrieval_stats(),
            "vector_store_type": type(self.vector_store).__name__,
            "sparse_store_type": type(self.sparse_store).__name__
        }
    
    async def add_knowledge(self, documents: List[Dict[str, Any]]) -> bool:
        """Add new documents to the knowledge base"""
        try:
            # Add to both stores
            vector_success = await self.vector_store.add_documents(documents)
            sparse_success = True  # Mock sparse store doesn't need explicit adding
            
            return vector_success and sparse_success
        except Exception as e:
            print(f"Error adding knowledge: {e}")
            return False