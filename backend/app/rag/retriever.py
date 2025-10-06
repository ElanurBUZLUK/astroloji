"""
Hybrid retrieval system (Dense + BM25) for astrological knowledge
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, replace
from enum import Enum
import asyncio
import math
from abc import ABC, abstractmethod
import os
import re
import uuid

from loguru import logger

from app.rag.embeddings import EMBEDDING_DIM, generate_embedding
from backend.app.config import settings

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

    def upsert(self, items: List[Tuple[str, str, Dict[str, Any]]]) -> None:
        """Optional synchronous ingestion hook."""
        raise NotImplementedError

class SparseStore(ABC):
    """Abstract sparse (BM25) store interface"""
    
    @abstractmethod
    async def search(self, query_text: str, top_k: int = 10,
                    filters: Dict[str, Any] = None) -> List[RetrievalResult]:
        """Search using BM25"""
        pass

    def upsert(self, items: List[Tuple[str, str, Dict[str, Any]]]) -> None:
        """Optional synchronous ingestion hook."""
        raise NotImplementedError

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

    def upsert(self, items: List[Tuple[str, str, Dict[str, Any]]]) -> None:
        for doc_id, content, metadata in items:
            self.documents.append({
                "id": doc_id,
                "content": content,
                "metadata": metadata,
            })

    def search_dense(
        self, query: str, top_k: int = 10, filters: Dict[str, Any] | None = None
    ) -> List[RetrievalResult]:
        query_vector = generate_embedding(query)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.search(query_vector, top_k, filters))
        else:
            raise RuntimeError("search_dense cannot be called from an active event loop")
    
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

    def upsert(self, items: List[Tuple[str, str, Dict[str, Any]]]) -> None:
        for doc_id, content, metadata in items:
            self.documents.append({
                "id": doc_id,
                "content": content,
                "metadata": metadata,
            })

    def search_sparse(
        self, query_text: str, top_k: int = 10, filters: Dict[str, Any] | None = None
    ) -> List[RetrievalResult]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.search(query_text, top_k, filters))
        else:
            raise RuntimeError("search_sparse cannot be called from an active event loop")


class QdrantVectorStore(VectorStore):
    """Qdrant backed vector store with synchronous ingestion support."""

    def __init__(self, url: str, api_key: str | None, collection: str, dim: int) -> None:
        if QdrantClient is None:
            raise RuntimeError("qdrant-client library not available")
        self.client = QdrantClient(url=url, api_key=api_key or None, timeout=30)
        self.collection = collection
        self.dim = dim

    def ensure_collection(self) -> None:
        if VectorParams is None or Distance is None:
            return
        try:
            self.client.get_collection(self.collection)
        except Exception:
            self.client.recreate_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE),
            )

    async def search(
        self, query_vector: List[float], top_k: int = 10, filters: Dict[str, Any] | None = None
    ) -> List[RetrievalResult]:
        def _search() -> List[Any]:
            self.ensure_collection()
            q_filter = self._build_filter(filters)
            return self.client.search(
                collection_name=self.collection,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
                query_filter=q_filter,
            )

        points = await asyncio.to_thread(_search)
        results: List[RetrievalResult] = []
        for point in points:
            payload = point.payload or {}
            metadata = payload if isinstance(payload, dict) else {}
            content = metadata.get("content") or payload.get("content") if isinstance(payload, dict) else ""
            if not content and "content" in payload:
                content = payload["content"]
            results.append(
                RetrievalResult(
                    content=content,
                    score=float(point.score),
                    source_id=str(point.id),
                    metadata=metadata,
                    method=RetrievalMethod.DENSE,
                )
            )
        return results

    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        def _upsert_docs():
            items = []
            for doc in documents:
                items.append((doc.get("id") or str(uuid.uuid4()), doc["content"], doc.get("metadata", {})))
            self.upsert(items)
        await asyncio.to_thread(_upsert_docs)
        return True

    def upsert(self, items: List[Tuple[str, str, Dict[str, Any]]]) -> None:
        if not items:
            return
        self.ensure_collection()
        points = []
        for doc_id, content, metadata in items:
            vector = generate_embedding(content)
            payload = {"doc_id": doc_id, "content": content, **metadata}
            points.append({
                "id": doc_id or str(uuid.uuid4()),
                "vector": vector,
                "payload": payload,
            })
        self.client.upsert(collection_name=self.collection, points=points)

    def search_dense(self, query: str, top_k: int = 10, filters: Dict[str, Any] | None = None) -> List[RetrievalResult]:
        query_vector = generate_embedding(query)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # no running loop
            return asyncio.run(self.search(query_vector, top_k, filters))  # pragma: no cover - sync helper
        else:  # pragma: no cover - conversion utility
            raise RuntimeError("search_dense cannot be called from an active event loop")

    def _build_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[Filter]:
        if not filters or Filter is None or FieldCondition is None or MatchValue is None:
            return None
        conditions = []
        for key, value in filters.items():
            conditions.append(FieldCondition(key=f"metadata.{key}", match=MatchValue(value=value)))
        return Filter(must=conditions) if conditions else None


class OpenSearchSparseStore(SparseStore):
    """OpenSearch backed sparse store with BM25 support."""

    def __init__(self, url: str, user: str, password: str, index: str, language: str = "turkish") -> None:
        if OpenSearch is None:
            raise RuntimeError("opensearch-py library not available")
        self.index = index
        self.language = language
        self.client = OpenSearch(
            hosts=[url],
            http_auth=(user, password),
            timeout=30,
            max_retries=3,
            retry_on_timeout=True,
        )

    def ensure_index(self) -> None:
        if self.client.indices.exists(self.index):
            return
        analyzer_name = f"{self.language}_bm25"
        body = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        analyzer_name: {
                            "type": "standard",
                            "stopwords": f"_{self.language}_",
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "doc_id": {"type": "keyword"},
                    "content": {"type": "text", "analyzer": analyzer_name},
                    "section": {"type": "integer"},
                    "line_start": {"type": "integer"},
                    "line_end": {"type": "integer"},
                    "tradition": {"type": "keyword"},
                    "language": {"type": "keyword"},
                    "source_url": {"type": "keyword"},
                }
            },
        }
        self.client.indices.create(index=self.index, body=body)

    async def search(
        self, query_text: str, top_k: int = 10, filters: Dict[str, Any] | None = None
    ) -> List[RetrievalResult]:
        return await asyncio.to_thread(self.search_sparse, query_text, top_k, filters)

    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        def _bulk_index():
            self.ensure_index()
            if bulk is None:
                raise RuntimeError("opensearch-py helpers not available")
            ops: List[Dict[str, Any]] = []
            for doc in documents:
                doc_id = doc.get("id") or str(uuid.uuid4())
                body = {"doc_id": doc_id, "content": doc["content"], **doc.get("metadata", {})}
                ops.append({"index": {"_index": self.index, "_id": doc_id}})
                ops.append(body)
            if ops:
                bulk(self.client, ops, refresh=True)
        await asyncio.to_thread(_bulk_index)
        return True

    def upsert(self, items: List[Tuple[str, str, Dict[str, Any]]]) -> None:
        if not items:
            return
        if bulk is None:
            raise RuntimeError("opensearch-py helpers not available")
        self.ensure_index()
        ops: List[Dict[str, Any]] = []
        for doc_id, content, metadata in items:
            doc_id = doc_id or str(uuid.uuid4())
            body = {"doc_id": doc_id, "content": content, **metadata}
            ops.append({"index": {"_index": self.index, "_id": doc_id}})
            ops.append(body)
        bulk(self.client, ops, refresh=True)

    def search_sparse(
        self, query_text: str, top_k: int = 10, filters: Dict[str, Any] | None = None
    ) -> List[RetrievalResult]:
        self.ensure_index()
        query_body: Dict[str, Any] = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": {"match": {"content": query_text}},
                    "filter": self._build_filters(filters),
                }
            },
        }
        response = self.client.search(index=self.index, body=query_body)
        hits = response.get("hits", {}).get("hits", [])
        results: List[RetrievalResult] = []
        for hit in hits:
            source = hit.get("_source", {})
            metadata = dict(source)
            metadata.pop("content", None)
            results.append(
                RetrievalResult(
                    content=source.get("content", ""),
                    score=float(hit.get("_score", 0.0)),
                    source_id=source.get("doc_id", hit.get("_id", "")),
                    metadata=metadata,
                    method=RetrievalMethod.SPARSE,
                )
            )
        return results

    def _build_filters(self, filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not filters:
            return []
        clauses: List[Dict[str, Any]] = []
        for key, value in filters.items():
            field_name = key if key.startswith("metadata.") else f"metadata.{key}"
            if isinstance(value, list):
                clauses.append({"terms": {field_name: value}})
            else:
                clauses.append({"term": {field_name: value}})
        return clauses

class HybridRetriever:
    """Hybrid retrieval system combining dense and sparse search"""
    
    def __init__(
        self,
        vector_store: Optional[VectorStore],
        sparse_store: Optional[SparseStore],
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
    ) -> None:
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
        if not self.vector_store:
            return []
        query_vector = generate_embedding(query.query_text)
        results = await self.vector_store.search(
            query_vector=query_vector,
            top_k=query.top_k,
            filters=query.filters
        )
        
        return results
    
    async def _sparse_retrieve(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """Sparse BM25 retrieval"""
        if not self.sparse_store:
            return []
        results = await self.sparse_store.search(
            query_text=query.query_text,
            top_k=query.top_k,
            filters=query.filters
        )
        
        return results
    
    async def _hybrid_retrieve(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """Hybrid retrieval combining dense and sparse"""

        return await search_hybrid(
            query.query_text,
            query.top_k,
            self.vector_store,
            self.sparse_store,
            alpha=self.dense_weight,
            filters=query.filters,
        )
    
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
            base_result = None
            for r in dense_results:
                if r.source_id == doc_id:
                    base_result = r
                    break
            if base_result is None:
                for r in sparse_results:
                    if r.source_id == doc_id:
                        base_result = r
                        break
            if base_result is None:
                continue

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
            "vector_store_type": type(self.vector_store).__name__ if self.vector_store else "None",
            "sparse_store_type": type(self.sparse_store).__name__ if self.sparse_store else "None",
        }


def _secret_value(secret: Optional[Any]) -> str:
    if secret is None:
        return ""
    if hasattr(secret, "get_secret_value"):
        return secret.get_secret_value()  # type: ignore[attr-defined]
    return str(secret)


def build_retriever_profile() -> Dict[str, Optional[Any]]:
    """Construct vector/sparse store instances based on configuration/env."""

    default_backend = getattr(settings, "SEARCH_BACKEND", "HYBRID") or "HYBRID"
    backend_choice = (os.getenv("SEARCH_BACKEND") or default_backend).upper()
    if backend_choice not in {"QDRANT", "OPENSEARCH", "HYBRID", ""}:
        logger.warning("Unsupported SEARCH_BACKEND '%s', falling back to HYBRID", backend_choice)
        backend_choice = "HYBRID"

    dense_store: Optional[VectorStore] = None
    sparse_store: Optional[SparseStore] = None

    def create_qdrant() -> Optional[VectorStore]:
        if QdrantClient is None:
            logger.warning("Qdrant client unavailable; skipping dense store")
            return None
        configured_url = str(settings.QDRANT_URL) if getattr(settings, "QDRANT_URL", None) else "http://localhost:6333"
        url = os.getenv("QDRANT_URL", configured_url)
        api_key = os.getenv("QDRANT_API_KEY") or _secret_value(settings.QDRANT_API_KEY)
        collection = os.getenv("QDRANT_COLLECTION", settings.QDRANT_COLLECTION)
        try:
            store = QdrantVectorStore(url=url, api_key=api_key, collection=collection, dim=EMBEDDING_DIM)
            store.ensure_collection()
            return store
        except Exception as exc:  # pragma: no cover - external dependency
            logger.warning(
                "Failed to initialise Qdrant store",
                extra={"url": url, "collection": collection, "error": str(exc)},
            )
            return None

    def create_opensearch() -> Optional[SparseStore]:
        if OpenSearch is None:
            logger.warning("OpenSearch client unavailable; skipping sparse store")
            return None
        configured_url = str(settings.OPENSEARCH_URL) if getattr(settings, "OPENSEARCH_URL", None) else "http://localhost:9200"
        url = os.getenv("OPENSEARCH_URL", configured_url)
        user = os.getenv("OPENSEARCH_USER", settings.OPENSEARCH_USER)
        password = os.getenv("OPENSEARCH_PASSWORD") or _secret_value(settings.OPENSEARCH_PASSWORD)
        index = os.getenv("OPENSEARCH_INDEX", settings.OPENSEARCH_INDEX)
        language = os.getenv("BM25_LANGUAGE", settings.BM25_LANGUAGE)
        try:
            store = OpenSearchSparseStore(url=url, user=user, password=password, index=index, language=language)
            store.ensure_index()
            return store
        except Exception as exc:  # pragma: no cover - external dependency
            logger.warning(
                "Failed to initialise OpenSearch store",
                extra={"url": url, "index": index, "error": str(exc)},
            )
            return None

    if backend_choice in {"", "HYBRID", "QDRANT"}:
        dense_store = create_qdrant()
    if backend_choice in {"", "HYBRID", "OPENSEARCH"}:
        sparse_store = create_opensearch()

    # Allow hybrid mode when Qdrant is primary but OpenSearch settings exist
    if backend_choice == "QDRANT" and sparse_store is None and (
        os.getenv("OPENSEARCH_URL") or getattr(settings, "OPENSEARCH_URL", None)
    ):
        sparse_store = create_opensearch()

    return {"dense": dense_store, "sparse": sparse_store}


async def search_hybrid(
    query: str,
    top_k: int,
    dense_store: Optional[VectorStore],
    sparse_store: Optional[SparseStore],
    *,
    alpha: Optional[float] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> List[RetrievalResult]:
    """Retrieve documents using dense/sparse stores and blend their scores."""

    filters = filters or {}
    default_alpha = getattr(settings, "HYBRID_ALPHA", 0.6)
    if alpha is not None:
        mixed_alpha = float(alpha)
    else:
        env_alpha = os.getenv("HYBRID_ALPHA")
        if env_alpha is not None:
            try:
                mixed_alpha = float(env_alpha)
            except ValueError:
                mixed_alpha = float(default_alpha)
        else:
            mixed_alpha = pick_alpha(query)
    mixed_alpha = max(0.0, min(1.0, mixed_alpha))

    dense_results: List[RetrievalResult] = []
    if dense_store:
        try:
            dense_results = dense_store.search_dense(query, top_k=top_k, filters=filters)
        except RuntimeError:
            query_vector = generate_embedding(query)
            dense_results = await dense_store.search(query_vector, top_k=top_k, filters=filters)
        except Exception as exc:  # pragma: no cover - external dependency failure
            logger.warning("Dense retrieval failed", extra={"error": str(exc)})
            dense_results = []

    sparse_results: List[RetrievalResult] = []
    if sparse_store:
        try:
            sparse_results = sparse_store.search_sparse(query, top_k=top_k, filters=filters)
        except RuntimeError:
            sparse_results = await sparse_store.search(query, top_k=top_k, filters=filters)
        except Exception as exc:  # pragma: no cover - external dependency failure
            logger.warning("Sparse retrieval failed", extra={"error": str(exc)})
            sparse_results = []

    if not dense_results and not sparse_results:
        return []

    if not sparse_results:
        return sorted(dense_results, key=lambda x: x.score, reverse=True)[:top_k]
    if not dense_results:
        return sorted(sparse_results, key=lambda x: x.score, reverse=True)[:top_k]

    entries: Dict[str, Dict[str, Any]] = {}
    for res in dense_results:
        entries[res.source_id] = {
            "dense": res,
            "sparse": None,
            "d_score": float(res.score),
            "s_score": 0.0,
        }
    for res in sparse_results:
        entry = entries.setdefault(
            res.source_id,
            {"dense": None, "sparse": None, "d_score": 0.0, "s_score": 0.0},
        )
        entry["sparse"] = res
        entry["s_score"] = float(res.score)

    dense_values = [entry["d_score"] for entry in entries.values() if entry["d_score"]]
    sparse_values = [entry["s_score"] for entry in entries.values() if entry["s_score"]]
    d_lo = min(dense_values, default=0.0)
    d_hi = max(dense_values, default=1.0)
    if abs(d_hi - d_lo) < 1e-9:
        d_hi = d_lo + 1.0
    s_lo = min(sparse_values, default=0.0)
    s_hi = max(sparse_values, default=1.0)
    if abs(s_hi - s_lo) < 1e-9:
        s_hi = s_lo + 1.0

    combined: List[RetrievalResult] = []
    for doc_id, entry in entries.items():
        dense_score = (entry["d_score"] - d_lo) / (d_hi - d_lo)
        sparse_score = (entry["s_score"] - s_lo) / (s_hi - s_lo)
        combined_score = mixed_alpha * dense_score + (1.0 - mixed_alpha) * sparse_score
        base_result = entry["dense"] or entry["sparse"]
        if base_result is None:
            continue
        updated = replace(base_result, score=float(combined_score), method=RetrievalMethod.HYBRID)
        metadata = dict(updated.metadata or {})
        metadata.setdefault("doc_id", metadata.get("doc_id") or updated.source_id)
        metadata.setdefault("hybrid_alpha", mixed_alpha)
        updated.metadata = metadata
        combined.append(updated)

    combined.sort(key=lambda x: x.score, reverse=True)
    return combined[:top_k]
TR_CHARS = set("ığüşöçİĞÜŞÖÇ")
ASPECT_TERMS = re.compile(r"\b(kare|üçgen|karşıt|sextile|trine|square|opposition)\b", re.IGNORECASE)
CLASSICAL_TERMS = re.compile(r"\b(zuhal|şems|satürn|mars|venüs|merkur|jüpiter|uranüs|neptün|plüton)\b", re.IGNORECASE)


def pick_alpha(query: str) -> float:
    """Choose an alpha that blends dense/sparse scores based on query hints."""

    stripped = (query or "").strip()
    if not stripped:
        return getattr(settings, "HYBRID_ALPHA", 0.6)

    base = 0.6 if any(ch in TR_CHARS for ch in stripped) else 0.75

    if ASPECT_TERMS.search(stripped):
        base -= 0.05
    if CLASSICAL_TERMS.search(stripped):
        base -= 0.05

    # Reward denser scores for longer analytical queries
    if len(stripped) > 120:
        base += 0.05

    return max(0.4, min(0.85, base))
