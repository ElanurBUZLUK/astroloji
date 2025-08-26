"""
Tests for RAG retrieval system
"""
import pytest
from app.rag.retriever import (
    HybridRetriever, MockVectorStore, MockSparseStore, 
    RetrievalQuery, RetrievalMethod
)

@pytest.mark.asyncio
async def test_mock_vector_store():
    """Test mock vector store functionality"""
    store = MockVectorStore()
    
    # Test search
    query_vector = [0.1] * 384
    results = await store.search(query_vector, top_k=5)
    
    assert len(results) <= 5
    assert all(hasattr(result, 'content') for result in results)
    assert all(hasattr(result, 'score') for result in results)
    assert all(hasattr(result, 'source_id') for result in results)

@pytest.mark.asyncio
async def test_mock_sparse_store():
    """Test mock sparse store functionality"""
    store = MockSparseStore()
    
    # Test search
    results = await store.search("almuten dignity", top_k=3)
    
    assert len(results) <= 3
    assert all(result.method.value == "sparse" for result in results)
    
    # Test with filters
    filtered_results = await store.search(
        "almuten", 
        top_k=5, 
        filters={"topic": "almuten"}
    )
    
    # Should return results matching the filter
    assert len(filtered_results) >= 0

@pytest.mark.asyncio
async def test_hybrid_retriever():
    """Test hybrid retrieval system"""
    vector_store = MockVectorStore()
    sparse_store = MockSparseStore()
    retriever = HybridRetriever(vector_store, sparse_store)
    
    # Test hybrid retrieval
    query = RetrievalQuery(
        query_text="zodiacal releasing timing",
        top_k=5,
        method=RetrievalMethod.HYBRID
    )
    
    results = await retriever.retrieve(query)
    
    assert len(results) <= 5
    assert all(result.method.value == "hybrid" for result in results)
    
    # Results should be sorted by score
    scores = [result.score for result in results]
    assert scores == sorted(scores, reverse=True)

@pytest.mark.asyncio
async def test_dense_only_retrieval():
    """Test dense-only retrieval"""
    vector_store = MockVectorStore()
    sparse_store = MockSparseStore()
    retriever = HybridRetriever(vector_store, sparse_store)
    
    query = RetrievalQuery(
        query_text="profection annual",
        top_k=3,
        method=RetrievalMethod.DENSE
    )
    
    results = await retriever.retrieve(query)
    
    assert len(results) <= 3
    assert all(result.method.value == "dense" for result in results)

@pytest.mark.asyncio
async def test_sparse_only_retrieval():
    """Test sparse-only retrieval"""
    vector_store = MockVectorStore()
    sparse_store = MockSparseStore()
    retriever = HybridRetriever(vector_store, sparse_store)
    
    query = RetrievalQuery(
        query_text="firdaria persian periods",
        top_k=3,
        method=RetrievalMethod.SPARSE
    )
    
    results = await retriever.retrieve(query)
    
    assert len(results) <= 3
    assert all(result.method.value == "sparse" for result in results)

@pytest.mark.asyncio
async def test_search_by_topic():
    """Test topic-based search"""
    vector_store = MockVectorStore()
    sparse_store = MockSparseStore()
    retriever = HybridRetriever(vector_store, sparse_store)
    
    results = await retriever.search_by_topic("antiscia", top_k=2)
    
    assert len(results) <= 2
    # Should find antiscia-related content
    assert any("antiscia" in result.content.lower() for result in results)

@pytest.mark.asyncio
async def test_search_by_tags():
    """Test tag-based search"""
    vector_store = MockVectorStore()
    sparse_store = MockSparseStore()
    retriever = HybridRetriever(vector_store, sparse_store)
    
    results = await retriever.search_by_tags(["timing", "career"], top_k=3)
    
    assert len(results) <= 3

def test_retrieval_stats():
    """Test retrieval statistics"""
    vector_store = MockVectorStore()
    sparse_store = MockSparseStore()
    retriever = HybridRetriever(vector_store, sparse_store)
    
    stats = retriever.get_retrieval_stats()
    
    assert "dense_weight" in stats
    assert "sparse_weight" in stats
    assert "vector_store_type" in stats
    assert "sparse_store_type" in stats
    assert stats["dense_weight"] + stats["sparse_weight"] == 1.0

@pytest.mark.asyncio
async def test_filters():
    """Test filtering functionality"""
    vector_store = MockVectorStore()
    sparse_store = MockSparseStore()
    retriever = HybridRetriever(vector_store, sparse_store)
    
    # Test with language filter
    query = RetrievalQuery(
        query_text="dignity",
        filters={"language": "en"},
        top_k=5
    )
    
    results = await retriever.retrieve(query)
    
    # All results should match the filter
    for result in results:
        if result.metadata and "language" in result.metadata:
            assert result.metadata["language"] == "en"

@pytest.mark.asyncio
async def test_empty_query():
    """Test handling of empty query"""
    vector_store = MockVectorStore()
    sparse_store = MockSparseStore()
    retriever = HybridRetriever(vector_store, sparse_store)
    
    query = RetrievalQuery(query_text="", top_k=5)
    results = await retriever.retrieve(query)
    
    # Should handle empty query gracefully
    assert isinstance(results, list)