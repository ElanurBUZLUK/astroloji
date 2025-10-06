from __future__ import annotations

import glob
import os
from typing import Iterable, List

from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma

load_dotenv()


def load_plain_texts(patterns: Iterable[str]) -> List[Document]:
    documents: List[Document] = []
    for pattern in patterns:
        for file_path in glob.glob(pattern, recursive=True):
            if not os.path.isfile(file_path):
                continue
            with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                content = handle.read().strip()
            if not content:
                continue
            documents.append(
                Document(page_content=content, metadata={"source": file_path, "type": "text"})
            )
    return documents


def ingest() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY tanımlanmalı.")
    persist_dir = os.getenv("CHROMA_DIR", "./data/processed/vector_store")
    os.makedirs(persist_dir, exist_ok=True)

    seed_documents = load_plain_texts(
        [
            "data/external/**/*.txt",
            "data/external/*.txt",
        ]
    )

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(seed_documents)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)
    Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=persist_dir)
    print(f"Ingest tamamlandı. Parça sayısı: {len(chunks)} → {persist_dir}")


def main() -> None:
    ingest()


if __name__ == "__main__":
    main()
