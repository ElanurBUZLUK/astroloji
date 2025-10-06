#!/usr/bin/env python3
"""Ingest markdown/text corpora into the configured retrieval backends."""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag.retriever import build_retriever_profile


def iter_documents(root: Path) -> Iterable[Path]:
    """Yield text-like files beneath the given directory."""
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".txt"}:
            yield path


HDR_PATTERN = re.compile(r"^(#+|\d+[\.)]|[IVX]+\.)\s")


def split_chunks(text: str, chunk_size: int, overlap: int) -> Iterator[Tuple[str, int, int]]:
    """Chunk text while preserving headings and approximate word windows."""

    lines = text.splitlines()
    buffer: List[Tuple[int, str, int]] = []
    word_count = 0

    def emit() -> Tuple[str, int, int] | None:
        if not buffer:
            return None
        chunk_text = "\n".join(line for _, line, _ in buffer).strip()
        if not chunk_text:
            return None
        start_line = buffer[0][0]
        end_line = buffer[-1][0]
        return chunk_text, start_line, end_line

    for idx, line in enumerate(lines, start=1):
        tokens = line.split()
        buffer.append((idx, line, len(tokens)))
        word_count += len(tokens)

        hit_boundary = word_count >= chunk_size
        hit_heading = bool(HDR_PATTERN.match(line.strip())) and word_count >= max(int(chunk_size * 0.6), 1)

        if hit_boundary or hit_heading:
            payload = emit()
            if payload:
                yield payload
            if overlap > 0:
                retained: List[Tuple[int, str, int]] = []
                retained_words = 0
                for entry in reversed(buffer):
                    retained.insert(0, entry)
                    retained_words += entry[2]
                    if retained_words >= overlap:
                        break
                buffer = retained
                word_count = sum(item[2] for item in buffer)
            else:
                buffer = []
                word_count = 0

    payload = emit()
    if payload:
        yield payload


def _first_heading(chunk: str) -> str | None:
    for raw in chunk.splitlines():
        stripped = raw.strip()
        if HDR_PATTERN.match(stripped):
            return stripped.lstrip("# ")
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest corpus into search backends")
    parser.add_argument("--path", required=True, help="Directory containing .md/.txt files")
    parser.add_argument("--chunk", type=int, default=600, help="Approximate words per chunk")
    parser.add_argument("--overlap", type=int, default=80, help="Word overlap between chunks")
    args = parser.parse_args()

    corpus_root = Path(args.path).resolve()
    if not corpus_root.exists():
        raise SystemExit(f"Path not found: {corpus_root}")

    profile = build_retriever_profile()
    dense_store = profile.get("dense")
    sparse_store = profile.get("sparse")
    if dense_store is None and sparse_store is None:
        raise SystemExit("No retrieval backend configured. Check SEARCH_BACKEND/QDRANT/OPENSEARCH settings.")

    language = os.getenv("INGEST_LANGUAGE", os.getenv("BM25_LANGUAGE", "TR")).upper()
    default_tradition = os.getenv("INGEST_TRADITION", "mixed")

    batch: List[Tuple[str, str, Dict[str, Any]]] = []
    for doc_path in iter_documents(corpus_root):
        try:
            raw_text = doc_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raw_text = doc_path.read_text(encoding="utf-8", errors="ignore")
        sections = split_chunks(raw_text, args.chunk, args.overlap)
        for section_idx, (chunk, line_start, line_end) in enumerate(sections):
            metadata = {
                "doc_id": doc_path.stem,
                "section": section_idx,
                "line_start": line_start,
                "line_end": line_end,
                "tradition": default_tradition,
                "language": language,
                "source_url": None,
            }
            heading = _first_heading(chunk)
            if heading:
                metadata["section_title"] = heading
            batch.append((doc_path.stem, chunk, metadata))

    if not batch:
        print("No documents discovered; nothing to ingest.")
        return

    if dense_store:
        try:
            dense_store.upsert(batch)
            print(f"[dense] upserted {len(batch)} chunks")
        except Exception as exc:  # pragma: no cover - backend failure
            print(f"[dense] failed to upsert chunks: {exc}")

    if sparse_store:
        try:
            sparse_store.upsert(batch)
            print(f"[sparse] upserted {len(batch)} chunks")
        except Exception as exc:  # pragma: no cover - backend failure
            print(f"[sparse] failed to upsert chunks: {exc}")


if __name__ == "__main__":
    main()
