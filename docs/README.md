# Astro-AA (AI Astrolog)

A production-ready, Almuten-centric astrology interpretation engine with time-lord omics (ZR/Profection/Firdaria), predictive stack (Progressions, Solar Arc, Transits), and a modern RAG layer. Server: **FastAPI**. Stores: **PostgreSQL** (OLTP), **Neo4j** (knowledge graph), **Vector DB** (hybrid retrieval), **Redis** (cache). Mobile clients: Flutter/React Native.

### Key Features
- **Almuten Figurıs**-centric core, Lights/ASC/MC priority
- **Zodiacal Releasing (ZR)** as primary time-lord (with tone rules)
- **Antiscia/Contra-Antiscia** as major links (≤1°)
- **Support**: SSR/LR/Thirdary progressions as confirmations
- **RAG** with hybrid retrieval, re-ranking, citations, calibration
- **End-to-end observability** & evaluation suite

### Quick Start
1. Provision infra (Postgres, Neo4j, Vector DB, Redis).
2. `poetry install && uvicorn app.main:app --reload` (example)
3. Create a chart: `POST /charts` → request interpretation `POST /requests`.

### Safety & Ethics
- Not medical/financial advice.
- PII minimized, consent required (GDPR-ready).