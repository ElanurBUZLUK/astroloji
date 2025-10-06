from __future__ import annotations

from typing import Any, Dict, List, Sequence

from langchain.chains import RetrievalQA
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.vectorstores import Chroma
from langchain_openai import ChatOpenAI

from astroloji_ai.config.settings import Settings


class RAGClient:
    """RAG altyapısını yöneten yardımcı sınıf."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY tanımlanmalı.")
        self._embeddings = OpenAIEmbeddings(
            model=settings.rag.embed_model,
            api_key=settings.openai_api_key,
        )
        self._vector_store = Chroma(
            persist_directory=settings.rag.persist_dir,
            embedding_function=self._embeddings,
        )
        self._retriever = self._vector_store.as_retriever(
            search_type=settings.rag.retriever_type,
            search_kwargs={"k": settings.rag.k, "fetch_k": settings.rag.fetch_k},
        )
        prompt_template = PromptTemplate(
            template=(
                "Profesyonel bir astrolog gibi konuş. "
                "Aşağıdaki bağlam ve ephemeris verisi ile soruyu cevapla.\n\n"
                "Bağlam:\n{context}\n\n"
                "Ephemeris:\n{ephemeris_data}\n\n"
                "Soru:\n{question}\n\n"
                "Kurallar:\n"
                "- Astroloji terminolojisini doğru kullan.\n"
                "- Olasılık ve eğilim dilini benimse.\n"
                "- Somut, güvenli pratik tavsiyeler üret.\n"
                "- Kaynaklara aykırı iddialardan kaçın.\n\n"
                "Yanıt:"
            ),
            input_variables=["context", "ephemeris_data", "question"],
        )
        self._qa_chain = RetrievalQA.from_chain_type(
            llm=self._build_llm_client(),
            chain_type="stuff",
            retriever=self._retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt_template},
        )

    def _build_llm_client(self) -> Any:
        return ChatOpenAI(
            model_name=self._settings.llm.routine_model,
            temperature=self._settings.llm.temperature,
            max_tokens=self._settings.llm.max_tokens,
            api_key=self._settings.openai_api_key,
        )

    def query(self, prompt: str, ephemeris_data: Dict[str, Any]) -> Dict[str, Any]:
        response = self._qa_chain({"query": prompt, "ephemeris_data": str(ephemeris_data)})
        result = response.get("result", "")
        documents: Sequence[Document] = response.get("source_documents", [])
        sources: List[Dict[str, str]] = []
        for doc in documents:
            metadata = {**doc.metadata}
            src_type = metadata.get("type", "text")
            src = metadata.get("source", "unknown")
            sources.append({"source": src, "type": src_type})
        return {"text": result, "sources": sources}
