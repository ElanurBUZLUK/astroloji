"""
Hybrid retrieval system (Dense + BM25) for astrological knowledge
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import math
from abc import ABC, abstractmethod
import uuid

from app.rag.embeddings import EMBEDDING_DIM, generate_embedding

try:  # pragma: no cover - optional dependency imports
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import (
        Distance,
        FieldCondition,
        Filter,
        MatchValue,
        PointStruct,
        VectorParams,
    )
except Exception:  # pragma: no cover
    QdrantClient = None
    Filter = None
    FieldCondition = None
    MatchValue = None
    PointStruct = None

try:  # pragma: no cover - optional dependency imports
    from opensearchpy import OpenSearch
    from opensearchpy.helpers import bulk
except Exception:  # pragma: no cover
    OpenSearch = None
    bulk = None

class RetrievalMethod(Enum):
    """Retrieval methods"""
    DENSE = "dense"
    SPARSE = "sparse"  # BM25
    HYBRID = "hybrid"

@dataclass
class RetrievalResult:
    """Single retrieval result"""
    content: str
    score: float
    source_id: str
    rule_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    method: RetrievalMethod = RetrievalMethod.HYBRID

@dataclass
class RetrievalQuery:
    """Retrieval query with context"""
    query_text: str
    filters: Dict[str, Any] = None
    top_k: int = 20
    method: RetrievalMethod = RetrievalMethod.HYBRID
    context: Dict[str, Any] = None

class VectorStore(ABC):
    """Abstract vector store interface"""
    
    @abstractmethod
    async def search(self, query_vector: List[float], top_k: int = 10, 
                    filters: Dict[str, Any] = None) -> List[RetrievalResult]:
        """Search for similar vectors"""
        pass
    
    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the store"""
        pass

class SparseStore(ABC):
    """Abstract sparse (BM25) store interface"""
    
    @abstractmethod
    async def search(self, query_text: str, top_k: int = 10,
                    filters: Dict[str, Any] = None) -> List[RetrievalResult]:
        """Search using BM25"""
        pass

class MockVectorStore(VectorStore):
    """Mock vector store for development/testing"""
    
    def __init__(self):
        self.documents = []
        self._load_mock_data()
    
    def _load_mock_data(self):
        """Load mock astrological knowledge"""
        self.documents = [
            {
                "id": "almuten_001",
                "content": "Almuten Figuris represents the planet with the strongest essential dignity among the significators. It indicates the core life direction and primary planetary influence in the chart.",
                "metadata": {
                    "topic": "almuten",
                    "source": "traditional_astrology",
                    "language": "en",
                    "tags": ["dignity", "significator", "core_identity"]
                }
            },
            {
                "id": "zr_001", 
                "content": "Zodiacal Releasing from the Lot of Spirit reveals the timing of career and life direction themes. Peak periods occur when the releasing sign is angular to the Lot of Fortune.",
                "metadata": {
                    "topic": "zodiacal_releasing",
                    "source": "hellenistic_timing",
                    "language": "en",
                    "tags": ["timing", "career", "spirit", "fortune"]
                }
            },
            {
                "id": "profection_001",
                "content": "Annual profections activate different houses each year. The profected house and its ruler become the focus of the year's experiences and developments.",
                "metadata": {
                    "topic": "profection",
                    "source": "traditional_timing",
                    "language": "en", 
                    "tags": ["timing", "houses", "annual", "activation"]
                }
            },
            {
                "id": "antiscia_001",
                "content": "Antiscia are points of equal light, mirrored around the solstitial axis. They represent hidden connections and equivalences between planets.",
                "metadata": {
                    "topic": "antiscia",
                    "source": "traditional_techniques",
                    "language": "en",
                    "tags": ["antiscia", "solstitial", "hidden", "equivalence"]
                }
            },
            {
                "id": "dignity_001",
                "content": "Essential dignities show a planet's strength in a sign. Rulership provides the strongest dignity, followed by exaltation, triplicity, term, and face.",
                "metadata": {
                    "topic": "dignity",
                    "source": "essential_dignities",
                    "language": "en",
                    "tags": ["dignity", "rulership", "exaltation", "strength"]
                }
            },
            {
                "id": "sect_001",
                "content": "Sect divides planets into diurnal (Sun, Jupiter, Saturn) and nocturnal (Moon, Venus, Mars) teams. Planets are stronger when in their preferred sect.",
                "metadata": {
                    "topic": "sect",
                    "source": "hellenistic_foundations",
                    "language": "en",
                    "tags": ["sect", "diurnal", "nocturnal", "strength"]
                }
            },
            {
                "id": "firdaria_001",
                "content": "Firdaria are Persian periods that divide life into planetary periods. Each major period is subdivided into minor periods ruled by the same sequence of planets.",
                "metadata": {
                    "topic": "firdaria",
                    "source": "persian_periods",
                    "language": "en",
                    "tags": ["firdaria", "persian", "periods", "timing"]
                }
            }
        ]
    
    async def search(self, query_vector: List[float], top_k: int = 10,
                    filters: Dict[str, Any] = None) -> List[RetrievalResult]:
        """Mock vector search - returns documents based on keyword matching"""
        # In a real implementation, this would use actual vector similarity
        # For now, we'll do simple keyword matching as a placeholder
        
        results = []
        for doc in self.documents:
            # Simple scoring based on content length (mock similarity)
            score = min(len(doc["content"]) / 200.0, 1.0)
            
            # Apply filters if provided
            if filters:
                if not self._matches_filters(doc["metadata"], filters):
                    continue
            
            result = RetrievalResult(
                content=doc["content"],
                score=score,
                source_id=doc["id"],
                metadata=doc["metadata"],
                method=RetrievalMethod.DENSE
            )
            results.append(result)
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to mock store"""
        self.documents.extend(documents)
        return True
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document metadata matches filters"""
        for key, value in filters.items():
            if key not in metadata:
                return False
            
            if isinstance(value, list):
                # Check if any filter value matches
                if not any(v in metadata[key] for v in value):
                    return False
            else:
                if metadata[key] != value:
                    return False
        
        return True

class MockSparseStore(SparseStore):
    """Mock BM25 store for development/testing"""
    
    def __init__(self):
        self.documents = []
        self._load_mock_data()
    
    def _load_mock_data(self):
        """Load same mock data as vector store"""
        mock_vector_store = MockVectorStore()
        self.documents = mock_vector_store.documents
    
    async def search(self, query_text: str, top_k: int = 10,
                    filters: Dict[str, Any] = None) -> List[RetrievalResult]:
        """Mock BM25 search using simple text matching"""
        query_terms = query_text.lower().split()
        results = []
        
        for doc in self.documents:
            # Simple BM25-like scoring
            content_lower = doc["content"].lower()
            score = 0.0
            
            for term in query_terms:
                if term in content_lower:
                    # Simple term frequency
                    tf = content_lower.count(term)
                    # Mock BM25 score
                    score += math.log(1 + tf) * 2.0
            
            if score > 0:
                # Apply filters
                if filters and not self._matches_filters(doc["metadata"], filters):
                    continue
                
                result = RetrievalResult(
                    content=doc["content"],
                    score=score,
                    source_id=doc["id"],
                    metadata=doc["metadata"],
                    method=RetrievalMethod.SPARSE
                )
                results.append(result)
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document metadata matches filters"""
        for key, value in filters.items():
            if key not in metadata:
                return False
            
            if isinstance(value, list):
                if not any(v in metadata[key] for v in value):
                    return False
            else:
                if metadata[key] != value:
                    return False
        
        return True

    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        self.documents.extend(documents)
        return True


class QdrantVectorStore(VectorStore):
    """Qdrant backed vector store."""

    def __init__(self, client: QdrantClient, collection_name: str) -> None:
        if not QdrantClient:
            raise RuntimeError("qdrant-client library not available")
        self.client = client
        self.collection_name = collection_name

    async def search(
        self, query_vector: List[float], top_k: int = 10, filters: Dict[str, Any] | None = None
    ) -> List[RetrievalResult]:
        search_filter = self._build_filter(filters)
        results = await self.client.async_search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            search_params={"hnsw_ef": 128},
            query_filter=search_filter,
        )

        retrieval_results: List[RetrievalResult] = []
        for point in results:
            payload = point.payload or {}
            retrieval_results.append(
                RetrievalResult(
                    content=payload.get("content", ""),
                    score=point.score,
                    source_id=str(point.id),
                    metadata=payload.get("metadata", {}),
                    method=RetrievalMethod.DENSE,
                )
            )
        return retrieval_results

    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        vectors = [generate_embedding(doc["content"]) for doc in documents]
        payloads = []
        ids = []
        for doc, vector in zip(documents, vectors):
            payloads.append({"content": doc["content"], "metadata": doc.get("metadata", {})})
            ids.append(doc.get("id") or str(uuid.uuid4()))
        points = [
            PointStruct(id=doc_id, vector=vector, payload=payload)
            for doc_id, vector, payload in zip(ids, vectors, payloads)
        ]
        await self.client.async_upsert(collection_name=self.collection_name, points=points)
        return True

    def _build_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[Filter]:
        if not filters:
            return None
        if not Filter or not FieldCondition or not MatchValue:
            return None
        conditions = []
        for key, value in filters.items():
            conditions.append(
                FieldCondition(key=f"metadata.{key}", match=MatchValue(value=value))
            )
        if not conditions:
            return None
        return Filter(must=conditions)


class OpenSearchSparseStore(SparseStore):
    """OpenSearch backed sparse store."""

    def __init__(self, client: OpenSearch, index_name: str) -> None:
        if not OpenSearch:
            raise RuntimeError("opensearch-py library not available")
        self.client = client
        self.index = index_name

    async def search(
        self, query_text: str, top_k: int = 10, filters: Dict[str, Any] | None = None
    ) -> List[RetrievalResult]:
        query_body: Dict[str, Any] = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": {"match": {"content": query_text}},
                    "filter": self._build_filters(filters),
                }
            },
        }
        response = await asyncio.to_thread(
            self.client.search, index=self.index, body=query_body
        )
        hits = response.get("hits", {}).get("hits", [])
        results: List[RetrievalResult] = []
        for hit in hits:
            source = hit.get("_source", {})
            results.append(
                RetrievalResult(
                    content=source.get("content", ""),
                    score=hit.get("_score", 0.0),
                    source_id=hit.get("_id", ""),
                    metadata=source.get("metadata", {}),
                    method=RetrievalMethod.SPARSE,
                )
            )
        return results

    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        if not bulk:
            raise RuntimeError("opensearch-py helpers not available")
        actions = []
        for doc in documents:
            actions.append(
                {
                    "_op_type": "index",
                    "_index": self.index,
                    "_id": doc.get("id"),
                    "content": doc["content"],
                    "metadata": doc.get("metadata", {}),
                }
            )
        await asyncio.to_thread(bulk, self.client, actions)
        return True

    def _build_filters(self, filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not filters:
            return []
        filter_blocks: List[Dict[str, Any]] = []
        for key, value in filters.items():
            if isinstance(value, list):
                filter_blocks.append({"terms": {f"metadata.{key}": value}})
            else:
                filter_blocks.append({"term": {f"metadata.{key}": value}})
        return filter_blocks

class HybridRetriever:
    """Hybrid retrieval system combining dense and sparse search"""
    
    def __init__(self, vector_store: VectorStore, sparse_store: SparseStore,
                 dense_weight: float = 0.6, sparse_weight: float = 0.4):
        self.vector_store = vector_store
        self.sparse_store = sparse_store
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
    
    async def retrieve(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """Perform hybrid retrieval"""
        
        if query.method == RetrievalMethod.DENSE:
            return await self._dense_retrieve(query)
        elif query.method == RetrievalMethod.SPARSE:
            return await self._sparse_retrieve(query)
        else:  # HYBRID
            return await self._hybrid_retrieve(query)
    
    async def _dense_retrieve(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """Dense vector retrieval"""
        query_vector = generate_embedding(query.query_text)
        results = await self.vector_store.search(
            query_vector=query_vector,
            top_k=query.top_k,
            filters=query.filters
        )
        
        return results
    
    async def _sparse_retrieve(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """Sparse BM25 retrieval"""
        results = await self.sparse_store.search(
            query_text=query.query_text,
            top_k=query.top_k,
            filters=query.filters
        )
        
        return results
    
    async def _hybrid_retrieve(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """Hybrid retrieval combining dense and sparse"""
        
        # Get results from both methods
        dense_results = await self._dense_retrieve(query)
        sparse_results = await self._sparse_retrieve(query)
        
        # Combine and re-score
        combined_results = self._combine_results(dense_results, sparse_results)
        
        # Sort by combined score and return top_k
        combined_results.sort(key=lambda x: x.score, reverse=True)
        return combined_results[:query.top_k]
    
    def _combine_results(self, dense_results: List[RetrievalResult], 
                        sparse_results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Combine dense and sparse results with weighted scoring"""
        
        # Create lookup for sparse scores
        sparse_scores = {result.source_id: result.score for result in sparse_results}
        dense_scores = {result.source_id: result.score for result in dense_results}
        
        # Get all unique document IDs
        all_ids = set(sparse_scores.keys()) | set(dense_scores.keys())
        
        combined_results = []
        
        for doc_id in all_ids:
            # Get scores (0 if not found in one method)
            dense_score = dense_scores.get(doc_id, 0.0)
            sparse_score = sparse_scores.get(doc_id, 0.0)
            
            # Normalize scores to 0-1 range
            dense_norm = min(dense_score, 1.0)
            sparse_norm = min(sparse_score / 10.0, 1.0)  # BM25 scores can be higher
            
            # Weighted combination
            combined_score = (self.dense_weight * dense_norm + 
                            self.sparse_weight * sparse_norm)
            
            # Get the document content (prefer dense result, fallback to sparse)
            if doc_id in dense_scores:
                base_result = next(r for r in dense_results if r.source_id == doc_id)
            else:
                base_result = next(r for r in sparse_results if r.source_id == doc_id)
            
            # Create combined result
            combined_result = RetrievalResult(
                content=base_result.content,
                score=combined_score,
                source_id=doc_id,
                rule_id=base_result.rule_id,
                metadata=base_result.metadata,
                method=RetrievalMethod.HYBRID
            )
            
            combined_results.append(combined_result)
        
        return combined_results
    
    async def search_by_topic(self, topic: str, top_k: int = 10) -> List[RetrievalResult]:
        """Search for documents by topic"""
        query = RetrievalQuery(
            query_text=topic,
            filters={"topic": topic},
            top_k=top_k,
            method=RetrievalMethod.HYBRID
        )
        
        return await self.retrieve(query)
    
    async def search_by_tags(self, tags: List[str], top_k: int = 10) -> List[RetrievalResult]:
        """Search for documents by tags"""
        query = RetrievalQuery(
            query_text=" ".join(tags),
            filters={"tags": tags},
            top_k=top_k,
            method=RetrievalMethod.HYBRID
        )
        
        return await self.retrieve(query)
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval system statistics"""
        return {
            "dense_weight": self.dense_weight,
            "sparse_weight": self.sparse_weight,
            "vector_store_type": type(self.vector_store).__name__,
            "sparse_store_type": type(self.sparse_store).__name__
        }
