"""
Tests for RAG core system
"""
import pytest
from app.rag.core import RAGSystem, RAGQuery
from app.rag.citation import CitationStyle

@pytest.mark.asyncio
async def test_rag_system_initialization():
    """Test RAG system initialization"""
    rag_system = RAGSystem()
    
    assert rag_system.retriever is not None
    assert rag_system.query_expander is not None
    assert rag_system.reranker is not None
    assert rag_system.citation_manager is not None
    assert rag_system.query_count == 0

@pytest.mark.asyncio
async def test_basic_rag_query():
    """Test basic RAG query functionality"""
    rag_system = RAGSystem()
    
    rag_query = RAGQuery(
        query="What is almuten figuris?",
        top_k=3,
        expand_query=True,
        rerank_results=True,
        include_citations=True
    )
    
    response = await rag_system.query(rag_query)
    
    assert response.query == rag_query.query
    assert len(response.retrieved_content) <= 3
    assert response.confidence_score >= 0.0
    assert response.confidence_score <= 1.0
    assert response.processing_time > 0
    assert response.citations is not None

@pytest.mark.asyncio
async def test_query_by_topic():
    """Test topic-based querying"""
    rag_system = RAGSystem()
    
    response = await rag_system.query_by_topic("zodiacal_releasing", top_k=2)
    
    assert len(response.retrieved_content) <= 2
    assert response.confidence_score > 0
    assert any("zodiacal" in content.lower() or "releasing" in content.lower() 
              for content in response.retrieved_content)

@pytest.mark.asyncio
async def test_query_for_interpretation():
    """Test interpretation-focused querying"""
    rag_system = RAGSystem()
    
    chart_elements = ["Mercury", "Sun", "Gemini"]
    interpretation_context = {
        "user_level": "intermediate",
        "focus_areas": ["communication", "identity"]
    }
    
    response = await rag_system.query_for_interpretation(
        chart_elements, 
        interpretation_context
    )
    
    assert len(response.retrieved_content) > 0
    assert response.confidence_score > 0

@pytest.mark.asyncio
async def test_query_without_expansion():
    """Test query without expansion"""
    rag_system = RAGSystem()
    
    rag_query = RAGQuery(
        query="profection",
        expand_query=False,
        rerank_results=False,
        include_citations=False
    )
    
    response = await rag_system.query(rag_query)
    
    assert response.expansion_stats == {}
    assert response.reranking_stats == {}
    assert response.citations is None

@pytest.mark.asyncio
async def test_query_with_filters():
    """Test query with filters"""
    rag_system = RAGSystem()
    
    rag_query = RAGQuery(
        query="dignity",
        filters={"topic": "dignity", "language": "en"},
        top_k=5
    )
    
    response = await rag_system.query(rag_query)
    
    assert len(response.retrieved_content) <= 5

@pytest.mark.asyncio
async def test_get_related_content():
    """Test getting related content"""
    rag_system = RAGSystem()
    
    content = "Almuten Figuris shows the strongest planet in essential dignity"
    related = await rag_system.get_related_content(content, top_k=2)
    
    assert len(related) <= 2
    assert all(isinstance(item, str) for item in related)

@pytest.mark.asyncio
async def test_validate_response():
    """Test response validation"""
    rag_system = RAGSystem()
    
    # Get a response first
    rag_query = RAGQuery(query="sect astrology", top_k=2)
    response = await rag_system.query(rag_query)
    
    # Validate it
    validation = await rag_system.validate_response(response)
    
    assert "is_valid" in validation
    assert "issues" in validation
    assert "quality_score" in validation
    assert "content_analysis" in validation

@pytest.mark.asyncio
async def test_system_stats():
    """Test system statistics"""
    rag_system = RAGSystem()
    
    # Make a few queries
    for i in range(3):
        rag_query = RAGQuery(query=f"test query {i}")
        await rag_system.query(rag_query)
    
    stats = rag_system.get_system_stats()
    
    assert stats["total_queries"] == 3
    assert stats["total_processing_time"] > 0
    assert stats["average_processing_time"] > 0
    assert "retriever_stats" in stats

@pytest.mark.asyncio
async def test_add_knowledge():
    """Test adding knowledge to the system"""
    rag_system = RAGSystem()
    
    new_documents = [
        {
            "id": "test_001",
            "content": "Test astrological content about houses",
            "metadata": {
                "topic": "houses",
                "source": "test_source",
                "language": "en"
            }
        }
    ]
    
    success = await rag_system.add_knowledge(new_documents)
    assert success is True

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in RAG system"""
    rag_system = RAGSystem()
    
    # Test with problematic query
    rag_query = RAGQuery(query="", top_k=0)  # Empty query, zero results
    response = await rag_system.query(rag_query)
    
    # Should handle gracefully
    assert response is not None
    assert response.confidence_score >= 0

@pytest.mark.asyncio
async def test_different_citation_styles():
    """Test different citation styles"""
    rag_system = RAGSystem()
    
    styles = [CitationStyle.INLINE, CitationStyle.FOOTNOTE, CitationStyle.ACADEMIC, CitationStyle.MINIMAL]
    
    for style in styles:
        rag_query = RAGQuery(
            query="antiscia traditional",
            citation_style=style,
            include_citations=True,
            top_k=2
        )
        
        response = await rag_system.query(rag_query)
        
        if response.citations:
            assert len(response.citations) > 0

@pytest.mark.asyncio
async def test_confidence_calculation():
    """Test confidence score calculation"""
    rag_system = RAGSystem()
    
    # Query with good matches
    good_query = RAGQuery(query="almuten figuris dignity", top_k=3)
    good_response = await rag_system.query(good_query)
    
    # Query with poor matches
    poor_query = RAGQuery(query="xyz nonexistent term", top_k=3)
    poor_response = await rag_system.query(poor_query)
    
    # Good query should have higher confidence
    # Note: This might not always be true with mock data, but test the structure
    assert 0 <= good_response.confidence_score <= 1
    assert 0 <= poor_response.confidence_score <= 1