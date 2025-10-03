"""Seed Qdrant and OpenSearch with mock astrology documents for local testing."""
from __future__ import annotations

import asyncio
from typing import Dict, List

from app.rag.core import RAGSystem


def load_mock_documents() -> List[Dict]:
    """Return a minimal set of documents to make search endpoints testable."""
    return [
        {
            "id": "almuten_001",
            "content": (
                "Almuten Figuris represents the planet with the strongest essential dignity among the significators. "
                "It indicates the core life direction and primary planetary influence in the chart."
            ),
            "metadata": {
                "topic": "almuten",
                "language": "en",
                "school": "traditional",
                "techniques": ["dignity"],
            },
        },
        {
            "id": "zr_001",
            "content": (
                "Zodiacal Releasing from the Lot of Spirit reveals the timing of career and life direction themes. "
                "Peak periods occur when the releasing sign is angular to the Lot of Fortune."
            ),
            "metadata": {
                "topic": "zodiacal_releasing",
                "language": "en",
                "school": "hellenistic",
                "techniques": ["timing"],
            },
        },
        {
            "id": "profection_001",
            "content": (
                "Annual profections activate a different house each year. The profected house and its ruler become "
                "the focus of the year's experiences and developments."
            ),
            "metadata": {
                "topic": "profection",
                "language": "en",
                "school": "traditional",
                "techniques": ["timing"],
            },
        },
    ]


async def main() -> None:
    documents = load_mock_documents()
    rag_system = RAGSystem()
    success = await rag_system.add_knowledge(documents)
    if success:
        print("✅ Mock documents ingested into vector/BM25 stores.")
    else:
        print("⚠️ Failed to ingest mock documents. Check service connectivity.")


if __name__ == "__main__":
    asyncio.run(main())
