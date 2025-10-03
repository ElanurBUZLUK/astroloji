"""Utilities for scoring claim-to-evidence alignment in the RAG pipeline."""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.schemas.interpretation import AnswerPayload, CitationEntry

_STOP_WORDS = {
    "this",
    "that",
    "with",
    "have",
    "from",
    "about",
    "your",
    "their",
    "will",
    "into",
    "over",
    "under",
    "above",
    "below",
    "through",
    "there",
    "which",
    "while",
    "where",
    "when",
    "also",
    "very",
    "much",
    "many",
    "some",
    "more",
    "less",
    "than",
    "such",
    "each",
    "other",
    "most",
    "like",
    "just",
    "even",
    "into",
    "because",
    "should",
    "could",
    "would",
    "might",
    "being",
    "having",
}
_MIN_TOKEN_LENGTH = 4
_SUPPORTED_THRESHOLD = 0.6


def score_claim_alignment(
    payload: AnswerPayload,
    documents: Sequence[Dict[str, Any]] | None,
    supported_threshold: float = _SUPPORTED_THRESHOLD,
) -> Dict[str, Any]:
    """Return aggregate and per-claim alignment scores."""
    claims = _extract_claims(payload)
    if not claims:
        return {
            "score": 0.0,
            "supported_ratio": 0.0,
            "claims": [],
            "threshold": supported_threshold,
            "reason": "no_claims",
        }

    citations = list(payload.citations or [])
    if not citations:
        return {
            "score": 0.0,
            "supported_ratio": 0.0,
            "claims": [
                {
                    "text": claim["text"],
                    "origin": claim["origin"],
                    "score": 0.0,
                    "citation_id": None,
                    "citation_n": None,
                    "doc_id": None,
                    "span": "",
                }
                for claim in claims
            ],
            "threshold": supported_threshold,
            "reason": "no_citations",
        }

    documents = list(documents or [])
    if not documents:
        return {
            "score": 0.0,
            "supported_ratio": 0.0,
            "claims": [
                {
                    "text": claim["text"],
                    "origin": claim["origin"],
                    "score": 0.0,
                    "citation_id": None,
                    "citation_n": None,
                    "doc_id": None,
                    "span": "",
                }
                for claim in claims
            ],
            "threshold": supported_threshold,
            "reason": "no_documents",
        }

    doc_lookup = _build_doc_lookup(documents)
    results: List[Dict[str, Any]] = []

    for claim in claims:
        best_score = 0.0
        best_span = ""
        best_doc_id: Optional[str] = None
        best_citation: Optional[CitationEntry] = None

        for citation in citations:
            doc = _resolve_doc_for_citation(citation, doc_lookup)
            if not doc:
                continue
            doc_content = doc.get("content") or ""
            score, span = _compare_claim_to_content(claim["text"], doc_content)
            if score > best_score:
                best_score = score
                best_span = span
                best_doc_id = doc.get("source_id") or doc.get("doc_id")
                best_citation = citation

        results.append(
            {
                "text": claim["text"],
                "origin": claim["origin"],
                "score": round(best_score, 3),
                "citation_id": getattr(best_citation, "doc_id", None),
                "citation_n": getattr(best_citation, "n", None),
                "doc_id": best_doc_id,
                "span": best_span,
            }
        )

    supported_count = sum(1 for item in results if item["score"] >= supported_threshold)
    total_claims = len(results) or 1
    overall_score = round(sum(item["score"] for item in results) / total_claims, 3)
    supported_ratio = round(supported_count / total_claims, 3)

    return {
        "score": overall_score,
        "supported_ratio": supported_ratio,
        "threshold": supported_threshold,
        "claims": results,
    }


def _extract_claims(payload: AnswerPayload) -> List[Dict[str, str]]:
    """Collect candidate claims from the generated answer."""
    answer = payload.answer
    claims: List[Dict[str, str]] = []

    claims.extend(
        {
            "text": sentence,
            "origin": "general_profile",
        }
        for sentence in _split_sentences(answer.general_profile)
    )

    claims.extend(
        {
            "text": item,
            "origin": f"strengths[{idx}]",
        }
        for idx, item in enumerate(answer.strengths)
        if item
    )

    claims.extend(
        {
            "text": item,
            "origin": f"watchouts[{idx}]",
        }
        for idx, item in enumerate(answer.watchouts)
        if item
    )

    for idx, timing in enumerate(answer.timing):
        candidate = timing.note or timing.range
        if candidate:
            claims.append({"text": candidate, "origin": f"timing[{idx}]"})

    claims.extend(
        {
            "text": item,
            "origin": f"mythic_refs[{idx}]",
        }
        for idx, item in enumerate(answer.mythic_refs)
        if item
    )

    # Filter near-empty strings
    normalized = []
    seen = set()
    for claim in claims:
        text = claim["text"].strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append({"text": text, "origin": claim["origin"]})
    return normalized


def _split_sentences(text: str) -> List[str]:
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [sentence.strip() for sentence in sentences if sentence and sentence.strip()]


def _build_doc_lookup(documents: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    exact: Dict[str, Dict[str, Any]] = {}
    source_map: Dict[str, Dict[str, Any]] = {}
    alt_keys: List[Tuple[str, Dict[str, Any]]] = []

    for doc in documents:
        if not isinstance(doc, dict):
            continue
        doc_id = doc.get("doc_id")
        if doc_id:
            exact[doc_id] = doc
        source_id = doc.get("source_id")
        if source_id:
            source_map[source_id] = doc
        metadata = doc.get("metadata") or {}
        for key_name in ("doc_id", "chunk_id", "source_id"):
            alt = metadata.get(key_name)
            if isinstance(alt, str):
                alt_keys.append((alt, doc))

    return {
        "exact": exact,
        "source": source_map,
        "alt": alt_keys,
    }


def _resolve_doc_for_citation(
    citation: CitationEntry,
    lookup: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    doc_id = getattr(citation, "doc_id", "") or ""
    if doc_id in lookup["exact"]:
        return lookup["exact"][doc_id]

    for source_id, doc in lookup["source"].items():
        if source_id and source_id in doc_id:
            return doc
        if source_id and doc_id.endswith(source_id):
            return doc

    for alt_id, doc in lookup["alt"]:
        if alt_id and alt_id in doc_id:
            return doc

    return None


def _compare_claim_to_content(claim: str, content: str) -> Tuple[float, str]:
    tokens = _tokenize(claim)
    normalized_tokens = set(tokens)
    lowered_content = content.lower()
    claim_lower = claim.lower()

    matches: List[Tuple[int, int]] = []
    found_tokens = set()

    for token in normalized_tokens:
        position = lowered_content.find(token)
        if position != -1:
            found_tokens.add(token)
            matches.append((position, position + len(token)))

    token_score = len(found_tokens) / len(normalized_tokens) if normalized_tokens else 0.0

    window = 420
    step = 160
    best_ratio = 0.0
    best_span = ""
    if lowered_content:
        for start in range(0, len(lowered_content), step):
            snippet = lowered_content[start : start + window]
            if not snippet:
                continue
            ratio = SequenceMatcher(None, claim_lower, snippet).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_span = content[start : start + window].strip()

    combined = max(token_score, best_ratio)
    span_text = best_span if combined >= token_score else _build_span(content, matches)
    return min(combined, 1.0), span_text


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"\b[\w']+\b", text.lower())
    tokens = [word for word in words if len(word) >= _MIN_TOKEN_LENGTH and word not in _STOP_WORDS]
    return tokens


def _build_span(content: str, matches: List[Tuple[int, int]]) -> str:
    if not matches:
        return ""
    start = min(match[0] for match in matches)
    end = max(match[1] for match in matches)
    # Expand window for readability
    pad = 60
    start = max(0, start - pad)
    end = min(len(content), end + pad)
    snippet = content[start:end].strip()
    return snippet
