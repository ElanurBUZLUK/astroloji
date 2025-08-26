## /docs/README.md

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

---

## /docs/ARCHITECTURE.md

# Architecture

### Overview
- **API**: FastAPI (Python)
- **Compute**: Ephemeris & calculators as services (containerized)
- **Datastores**: PostgreSQL (users/requests/results), Neo4j (rules/graph), Vector DB (RAG), Redis (cache)
- **Workers**: Celery/RQ for long jobs (ZR timelines, batch notifications)
- **Telemetry**: OpenTelemetry → Prometheus → Grafana

### Components
- **Calculators Service**: Ephemeris, houses, almuten, lots, antiscia, midpoints, fixed stars, asteroids/TNO, Uranians, time-lords (ZR, Profection, Firdaria), progressions, solar arc, transits.
- **Interpreter**: scoring + conflict resolver + output composer + archetype layer.
- **RAG Layer**: hybrid retrieval, query expansion, reranker, citation management.
- **Orchestrator**: multi-hop pipeline: *compute → retrieve → synthesize → calibrate → format → store*.

### Data Flow
1. Client submits birth data → **/charts**
2. Jobs queue: compute natal & timelines
3. Interpreter builds evidence features → scoring → text
4. RAG augments with sources → citations
5. Result stored → **/results/{id}**

### Non-Functional
- Latency targets, cache strategy, horizontal scaling, rate limiting.

---

## /docs/RAG_SYSTEM.md

# RAG System

## Retrieval
- **Hybrid**: Dense embeddings + BM25. Collections: `kb_general`, `kb_templates`, `kb_cases`, `kb_sources_sparse`.
- **Query Expansion**: synonyms (TR/EN), HyDE for vague queries.
- **Filters**: (planet, house, aspect, method) tags; language; version.

## Ranking
- **Stage 1**: BM25 + vector ANN → union → top-100
- **Stage 2**: Cross-encoder/LLM reranker → top-20 context

## Context Assembly
- **Semantic chunking** to keep rule atomicity (e.g., “Mars square Moon”).
- **Citation**: attach `source_id`, `rule_id` (Neo4j).

## Calibration
- Confidence 1–5 from: dignity & resepsiyon score, orb tightness, time-lord alignment, number of confirmations, generational flags.

## Observability
- Recall@K, Groundedness, click-through on citations, cache hit/miss, latency.

---

## /docs/ASTROLOGY_ALGORITHMS.md

# Astrology Algorithms (Specs)

## 0) Config & Orbs
- Zodiacs: Tropical (Sidereal switch)
- Houses: Whole Sign (topical) + Placidus (accidental/cadence/corner)
- Aspects: 0/60/90/120/180; optional 150/45/135 with tight orbs
- Orbs: Sun 8°, Moon 7°, personals 6°, social/generational 5°
- Antiscia/Contra: ≤1° (major equivalence)
- Midpoints: ≤1.5° (SO/MO ≤2°)
- Fixed Stars: ≤1° (royals prioritized)
- Uranian TNPs: ≤0°30′ (supportive only)

## 1) Natal Priority
1. **Almuten Figurıs** (points: Sun, Moon, ASC, MC, Fortuna, Spirit; scoring 5/4/3/2/1). Tie-break: dignity > lights proximity > angles (Placidus) > sect.
2. Lights + ASC/MC
3. Sect & malefic/benefic status
4. House rulers & dispositors
5. Essential/accidental dignities + receptions
6. Hyleg/Alcocoden (optional)
7. Moon phase & next application
8. Lots (Fortuna/Spirit)
9. Antiscia/Contra-antiscia
10. Core midpoints (SO/MO, ASC/MC, VE/MA, SU/ME)
11. Fixed stars
12. Asteroids (Ceres, Pallas, Juno, Vesta)
13. TNOs (Eris, Sedna, Haumea, Makemake, Orcus, Quaoar)
14. Uranian (midpoint pictures, TNP)
15. Patterns (stellium, T-square, Yod, etc.)

## 2) Time-Lord Spine
- **ZR (from Spirit)**: L1–L4, peaks (Fortune 1/10/7/4, 10 strongest), LB (Cancer↔Capricorn jumps), **tone** from: natal dignity + sect + Almuten link + receptions with other lords.
- **Profection**, **Firdaria**, **Secondary Progressions**, **Solar Arc**, **Transits** (approaching only)
- **Support**: SSR/LR/Thirdary only as confirmations.

## 3) Scoring
- Base: Almuten 6; Lights/ASC/MC & house almuten 5; angular rulers 4; standard 3.
- Multipliers: sect 1.2; dignity {rul 1.3/exalt 1.15/detr 0.85/fall 0.75}; accidental {angle 1.2/speed 1.1}; retro personals 0.85 (social/generational neutral); cazimi 1.3; under-beams 0.8; receptions {mutual 1.25, one-way 1.1}; orb {0–2° 1.25, 2–4° 1.1}; **approaching only for time methods** {1.1 vs 0.9}; antiscia 1.0; midpoints 1.2 (SO/MO 1.25); fixed star 1.15; asteroid/TNO 1.1; Uranian 1.1; time-lords {Profection 1.2, Firdaria major 1.2/minor 1.05, **ZR L1 1.3**, ZR L2 peak 1.15, ZR L2 LB 1.10}; SSR/LR/TP 1.05–1.08; 3+ confirmations 1.2.
- Thresholds: ≥7.5 main; 6.0–7.49 strong; 4.5–5.99 background; <4.5 drop.

## 4) Conflict Resolution
Almuten+Lights+Angles > rulers > others; dignity+reception > raw aspect; ZR/Profection/Firdaria alignment > single transit; approaching > separating (time); antiscia equal to major; support layers never override core; tie: Moon next application + Lots.

## 5) Generational vs Personal
Flag Uranus/Neptune/Pluto/TNO as **generational** in outputs; note: “do not over-personalize; background field.”

## 6) Archetype Layer
Small myth lines per planet/asteroid to humanize text.

---

## /docs/ZR_SPEC.md

# Zodiacal Releasing (ZR) – Detailed Spec

## Lots & Formulas
- Spirit (career), Fortune (circumstances), optional Eros (relations). Day/night formulas; use sign of the Lot (sign-based method).

## Period Durations (L1)
Aries/Scorpio 15; Taurus/Libra 8; Gemini/Virgo 20; Cancer 25; Leo 19; Sagittarius/Pisces 12; Capricorn 27; Aquarius 30. Sublevels: L2=1/12 year units (30d months), L3=2.5d, L4=5h.

## Mechanics
- Sequential zodiac order; apply **LB** jumps (Cancer→Capricorn, Capricorn→Cancer) when moving to Leo/Aquarius directions.
- **Peaks** from **Fortune’s angles** (1/10/7/4), with **10th** strongest.
- **Triad**: build-up → peak → carry-out.

## Tone Determination
Tone = f(dignity of period ruler, sect alignment, Almuten link (aspect/reception), receptions with active Profection/Firdaria rulers). Not “good/bad” → “intensity + valence.”

## Integration
- Provide L1–L2 tables with dates, peak badges, LB flags.
- Fuse with Profection/Firdaria/SP/SA/Transits; add SSR/LR/TP confirmations.

---

## /docs/DATA_MODEL.md

# Data Model

## PostgreSQL Tables
- users, profiles, birth_data, charts, requests, results, subscriptions, jobs, telemetry

### Example: `birth_data`
```sql
CREATE TABLE birth_data (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  birth_date DATE NOT NULL,
  birth_time TIME,
  place_name TEXT,
  lat DOUBLE PRECISION,
  lon DOUBLE PRECISION,
  tzid TEXT,
  accuracy_band TEXT CHECK (accuracy_band IN ('exact','±15m','±30m','unknown')),
  created_at TIMESTAMP DEFAULT now()
);
```

## Neo4j Graph
Nodes: (Planet),(House),(Sign),(Aspect),(Rule),(Lot),(Dignity),(Reception),(FixedStar),(Archetype)
Edges: `:RULES`, `:RULER`, `:HAS_DIGNITY`, `:RECEIVES`, `:APPLIES_TO`, `:ARCHETYPE`.

## Vector DB Collections
- kb_general, kb_templates, kb_cases, kb_sources_sparse

---

## /docs/API_SPEC.md

# API Spec (FastAPI)

## Auth & Profile
- `POST /auth/login`
- `GET /me`
- `PATCH /me/profile`

## Charts & Requests
- `POST /charts` → compute & persist natal/transit contexts
- `POST /requests` (chart_id, mode: natal|timing|today, focus_topic)
- `GET /requests/{id}`
- `GET /results/{request_id}` → `{ summary_md, confidence, evidence[] }`

## Alerts
- `POST /alerts` (windows)
- `GET /alerts`

## Data Rights
- `GET /data/export`, `DELETE /data`

---

## /docs/INGESTION_PIPELINE.md

# Ingestion & Transformation

1. Collect sources (PDF/HTML/MD) → normalize text
2. Semantic chunking (rule atomicity)
3. Tagging schema: planet/house/sign/aspect/dignity/reception/lot
4. Archetype snippets enrichment
5. Index to Vector DB (dense) + BM25 (sparse)
6. Link chunks to Neo4j `Rule` nodes
7. Version & audit trail

---

## /docs/ORCHESTRATION_AGENTIC.md

# Orchestration / Agentic Flow

Pipeline: **calculate → retrieve → synthesize → calibrate → cite → format → store**
- Multi-Hop manager ensures task order and retries
- Idempotent job keys (same request → same result unless inputs change)
- Backoff & circuit-breaker on calculators/RAG

---

## /docs/TASKS_END_TO_END.md

# End-to-End Task List (Sprintable)

## Phase 0 – Foundations (Week 1)
- Infra provisioning, secrets, baseline CI/CD
- Base schemas (Postgres), indices
- Containerized ephemeris

## Phase 1 – Calculators (Weeks 2–3)
- Natal core (houses, aspects, dignities, receptions)
- Almuten, Lots (Fortuna/Spirit), Antiscia, Midpoints
- Fixed stars, Asteroids/TNO, Uranian
- Time-lords: **ZR**, Profection, Firdaria; Progressions; Solar Arc; Transits

## Phase 2 – Interpreter (Weeks 4–5)
- Evidence extraction → scoring engine
- Conflict resolver, archetype injector
- Output composer (+confidence)

## Phase 3 – RAG (Weeks 6–7)
- Hybrid retrieval, query expansion, reranker
- Citation builder, context filter

## Phase 4 – API & Mobile (Weeks 8–9)
- FastAPI endpoints; auth; alerts
- Mobile UI (timeline, peaks/LB badges, generational flags)

## Phase 5 – Eval & Obs (Weeks 10–11)
- Recall@K, Faithfulness, dashboards
- Error pool, A/B tests (reranker/HyDE)

## Phase 6 – Security & Launch (Week 12)
- GDPR endpoints, PII minimization
- Rate limits, penetration tests
- Playbooks & SLOs

---

## /docs/EVALUATION_OBSERVABILITY.md

# Evaluation & Observability

- **Intrinsic**: Recall@K, Precision@K, NDCG
- **Extrinsic**: Faithfulness/Groundedness (LLM judge), user CSAT
- **Telemetry**: latency p50/p95, cache hit, errors, abandonment
- **Error Pool**: hallucination cases, manual triage
- **Dashboards**: Grafana panels per module

---

## /docs/SECURITY_COMPLIANCE.md

# Security & Compliance

- OAuth2/OIDC; secure tokens; rate limits
- PII encryption (at-rest/in-transit); consent management
- Minimal logs; IP separate store; retention policies
- GDPR: export/delete; ToS/Privacy
- Safety: neutral language; disclaimers

---

## /docs/EDGE_CASES.md

# Edge Cases & Quality

- Uncertain birth time → ASC bands & multi-scenario outputs
- DST/TZ anomalies → tzdb validation & warnings
- Geocoding errors → user confirmation loop
- Ephemeris range guards
- Multi-language proofreading & tone control

---

## /docs/CHECKLIST_ACCEPTANCE.md

# Checklists & Acceptance Criteria

- Almuten + Lights + Angles precedence verified
- ZR L1/L2 with peaks & LB flags visible in UI timeline
- Tone computed from dignity+sect+almuten link+receptions
- Generational flag on Ura/Nep/Plu/TNO statements
- Confidence 1–5 + rationale list
- RAG citations attached to claims

---

## /docs/UI_UX.md

# UI/UX

- Onboarding with consent & uncertainty band input
- Profile: Almuten card; archetype snippets
- ZR Timeline: L1/L2 lanes, peak/LB badges, tone chip, evidence popover
- Today: approaching transits; support confirmations (SSR/LR/TP)
- Accessibility: VoiceOver/TalkBack

---

## /docs/TEMPLATES_RULES.md

# Templates & Rules

## Example Templates
```json
{
  "planet_in_house": "[planet] [house]. evde; bu, [house_keywords] alanında [planet_keywords] vurgusu getirir.",
  "rulership_chain": "[point] yöneticisi [ruler], [ruler_house]. evde, [ruler_sign] burcunda; [point_keywords] teması [ruler_house_keywords] ve [ruler_sign_keywords] üzerinden işler."
}
```

## Rule Node Example (Neo4j)
```json
{
  "id": "rule.ve_in_7",
  "title": "Venüs 7.evde",
  "weight": 0.9,
  "applies_to": {"planet":"Venus","house":7},
  "source": "Trad. corpus",
  "lang": "tr"
}
```

---

## /docs/GLOSSARY.md

# Glossary
- Almuten Figurıs, Hyleg, Alcocoden, Sect, Reception, Antiscia, Midpoint, ZR (L1–L4, Peaks, LB), Profection, Firdaria, Progressions, Solar Arc, SSR/LR/TP.

---

## /docs/CONTRIBUTING.md

# Contributing
- Conventional commits; PR templates
- Code style: black/ruff; mypy
- Tests: unit/property/integration; coverage gate
- Docs: keep specs in `/docs` up to date

---

## /docs/ROADMAP.md

# Roadmap
- v0.1 MVP: core calculators + interpreter + basic RAG + mobile alpha
- v0.2: reranker, query expansion, calibration UI
- v0.3: agentic multi-hop, ingestion tagging UI, enterprise SSO

---

## /docs/LICENSE.md

# License
Choose a license (e.g., Apache-2.0/MIT). Add full text here.

---

## /docs/BACKEND_STRUCTURE.md

# FastAPI Backend Folder Structure

Below is the proposed **modular backend layout** (mirrors the user-provided tree) with notes on responsibilities and cross-module dependencies.

```
astro-aa-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory, middleware, routers
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py             # OAuth2/OIDC, token endpoints
│   │   ├── charts.py           # Chart creation & compute triggers
│   │   ├── interpretations.py  # Interpretation retrieval/generation
│   │   ├── alerts.py           # Peak/LB/transit window alerts
│   │   └── admin.py            # Health, metrics, feature flags
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # SQLAlchemy models
│   │   ├── profile.py
│   │   ├── birth_data.py
│   │   ├── chart.py
│   │   ├── request.py
│   │   ├── result.py
│   │   └── subscription.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py             # Pydantic schemas
│   │   ├── chart.py
│   │   └── interpretation.py
│   ├── calculators/
│   │   ├── __init__.py
│   │   ├── ephemeris.py        # Swiss Ephemeris adapter + caching
│   │   ├── almuten.py
│   │   ├── zodiac_releasing.py
│   │   ├── profection.py
│   │   ├── firdaria.py
│   │   ├── progressions.py
│   │   ├── solar_arc.py
│   │   ├── transits.py
│   │   ├── antiscia.py
│   │   ├── midpoints.py
│   │   ├── fixed_stars.py
│   │   ├── asteroids_tno.py
│   │   └── uranian.py
│   ├── interpreters/
│   │   ├── __init__.py
│   │   ├── core.py             # Orchestrates calculators + RAG + scoring
│   │   ├── scoring.py          # Weights & multipliers per spec
│   │   ├── conflict_resolver.py
│   │   ├── output_composer.py
│   │   └── calibration.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── retriever.py        # Hybrid (dense+BM25)
│   │   ├── query_expansion.py
│   │   ├── re_ranker.py
│   │   ├── context_filter.py
│   │   └── citation.py
│   ├── databases/
│   │   ├── __init__.py
│   │   ├── postgres.py         # Engine/session, Alembic helpers
│   │   ├── neo4j.py            # Neo4j driver + cypher utils
│   │   └── vector_db.py        # Pinecone/Weaviate/OpenSearch
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── collector.py
│   │   ├── cleaner.py
│   │   ├── chunking.py
│   │   ├── tagging.py
│   │   ├── arketip.py          # Archetype glossary injection
│   │   └── indexing.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── date_time.py
│   │   ├── geo.py
│   │   ├── logging.py
│   │   └── cache.py            # Redis helpers
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── chart_calculation.py
│   │   ├── interpretation.py
│   │   └── alerts.py
│   └── config.py               # Settings (pydantic-settings)
├── tests/
│   ├── __init__.py
│   ├── test_api/
│   ├── test_calculators/
│   ├── test_interpreters/
│   ├── test_rag/
│   └── test_ingestion/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt | pyproject.toml
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
└── helm/
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
```

### Design Notes
- Calculators are **pure** (deterministic inputs → outputs). I/O & caching handled in `ephemeris.py` and `utils/cache.py`.
- `interpreters/core.py` is the only module allowed to **compose** multiple calculators.
- Every calculator returns a **typed payload**: `{features: [...], evidence: [...], diagnostics: {...}}`.

---

## /docs/CALCULATORS_TASKS.md

# Calculators — Detailed Tasks & Pseudocode

This file enumerates implementation checklists + pseudocode for **Almuten, ZR, Profection, Firdaria, Progressions, Solar Arc, Transits, Antiscia, Midpoints, Fixed Stars, Asteroids/TNO, Uranian**.

### 1) Almuten Figuris (`calculators/almuten.py`)
- **Points**: Sun, Moon, ASC, MC, Fortuna, Spirit.
- **Scores**: rulership=5, exalt=4, triplicity=3, term=2, face=1.
- **Tie-break**: total essential > proximity to Lights > angularity (Placidus) > sect.

**Pseudocode**
```python
from typing import Dict, List

def almuten_figurıs(points: List[Point], tables: DignityTables, chart: Chart) -> AlmutenResult:
    totals: Dict[str, int] = defaultdict(int)
    for p in points:
        sign = p.sign
        for planet in tables.planets:
            totals[planet] += (
                5 if tables.is_ruler(planet, sign) else 0
                + 4 if tables.is_exalted(planet, sign) else 0
                + 3 if tables.in_triplicity(planet, sign, chart.is_day) else 0
                + 2 if tables.in_term(planet, p.degree) else 0
                + 1 if tables.in_face(planet, p.degree) else 0
            )
    winners = highest_planets(totals)
    if len(winners) == 1:
        return build_result(winners[0], totals)
    return tie_break(winners, chart, totals)
```

**Diagnostics**: return subtotals per point & rule table version.

---

### 2) Zodiacal Releasing (`calculators/zodiac_releasing.py`)
- **Lot**: Spirit (career) default. Day/Night formula; sign-based.
- **Durations (L1)**: Aries/Scorpio 15; Taurus/Libra 8; Gemini/Virgo 20; Cancer 25; Leo 19; Sagittarius/Pisces 12; Capricorn 27; Aquarius 30.
- **Sublevels**: L2=1/12 of L1 (month=30d), L3=2.5d, L4=5h.
- **LB**: Cancer→Leo or Capricorn→Aquarius → jump to opposite solstitial sign.
- **Peaks**: Fortune angles 1/10/7/4 (10th strongest).
- **Tone**: f(dignity(ruler), sect, almuten link, receptions with Profection/Firdaria lords).

**Pseudocode**
```python
def compute_zr_spirit(chart: Chart, start_date: date) -> ZRTimeline:
    lot = lot_of_spirit(chart)
    l1 = build_l1_periods(lot.sign, start_date)
    l2 = [subdivide(p, 12) for p in l1]
    apply_lb(l1); apply_lb(l2)
    peaks = mark_peaks(l1, l2, fortuna_sign(chart))
    tone = evaluate_tone(active_ruler, chart)
    return ZRTimeline(l1=l1, l2=l2, peaks=peaks, lb_flags=..., tone_map=tone)
```

**Outputs**: serialized tables with dates, `peak=True`, `lb=True`, `tone`.

---

### 3) Profection (`calculators/profection.py`)
- Year index = `age % 12`; profected sign = `asc_sign + index`.
- Year lord = ruler(profected_sign).
- Return `{sign, year_lord, activated_topics}`.

---

### 4) Firdaria (`calculators/firdaria.py`)
- Choose **diurnal/nocturnal** sequence; compute major/minor ranges.
- Emit `{major_lord, minor_lord, start, end}` list.

---

### 5) Secondary Progressions (`calculators/progressions.py`)
- Day-for-a-year; focus **progressed Moon** & **Sun**; detect sign changes & major aspects.

---

### 6) Solar Arc (`calculators/solar_arc.py`)
- Arc = longitude(progressed Sun) − longitude(natal Sun).
- Apply arc to all points; flag aspects to natal ≤1°.

---

### 7) Transits (`calculators/transits.py`)
- Current positions → aspects to natal within configured orbs.
- Filter **approaching** only; align with natal promises.

---

### 8) Antiscia (`calculators/antiscia.py`)
- Mirror around 0° Cancer/Capricorn (solstitial); contra around 0° Aries/Libra.
- Orb ≤1°; treat as major equivalence.

---

### 9) Midpoints (`calculators/midpoints.py`)
- Compute SO/MO (≤2°) and others (≤1.5°); check contacts.

---

### 10) Fixed Stars (`calculators/fixed_stars.py`)
- Check conjunction/opposition ≤1°; rank royals higher.

---

### 11) Asteroids & TNO (`calculators/asteroids_tno.py`)
- Track Ceres/Pallas/Juno/Vesta + selected TNOs; conj/opp ≤1°.

---

### 12) Uranian (`calculators/uranian.py`)
- TNP positions; midpoint pictures via 90° dial; orb ≤0°30′.

---

## Common Interfaces
- Each module exposes `compute(chart: Chart, when: datetime|date|None) -> Payload`.
- `Payload` includes: `features[]`, `evidence[]`, `diagnostics{}`.

## Testing Checklist (tests/test_calculators/)
- Determinism on identical inputs.
- Known charts regression (golden files).
- Property tests: antiscia symmetry, ZR LB jump invariants, Almuten tie-break ordering.

---

## Integration Notes
- `interpreters/core.py` composes calculator outputs → `scoring.py` multipliers → `conflict_resolver.py` → `output_composer.py`.
- Store raw results in PostgreSQL; persist rules/links in Neo4j; cache ephemeris in Redis.

Ürün Tanımı & Kapsam

 Kapsam dokümanı: Almuten-merkezli çekirdek + ZR/Profection/Firdaria/Progress/SA/Transit omurgası + Antiscia + Midpoint + Sabit Yıldız + Asteroid/TNO + Uranyen (sıkı orb).

 Mod işleyişi:

Natal Yorum (profil)

Zamanlama (ZR/Profection/Firdaria vb. sentez)

Güncel Öngörü (Transit/Return/TP teyitli)

 Kullanım rehberi: “Ne zaman kullanmalı/kullanmamalı”, kolektif vs kişisel döngü etiketi, mitolojik/arşetipsel açıklama stili.

 Uyarılar: “Medikal/finansal tavsiye değildir”, veri gizliliği, belirsizlik/güven skoru.

B) Mimari & Altyapı
B1) Yüksek Seviye Mimarî

 İstemci: Mobil (Flutter/React Native), çok dilli (TR/EN).

 API Katmanı: FastAPI (Python).

 İşlevsel Depolar:

PostgreSQL: kullanıcılar, doğum verisi, oturumlar, iş kuyruğu, sonuçlar, abonelik.

Neo4j: astro “bilgi grafı” (gezegen-ev-açı kuralları, resepsiyon, dignity zinciri, kural düğümleri, kaynak).

Vector DB (Pinecone/Weaviate/OpenSearch Vector): domain-RAG ve kural/kaynak aramaları (dense + sparse hibrit için BM25 katmanı da entegrasyon).

 Efemeris/hesap: Swiss Ephemeris (veya benzeri) konteyneri; CPU vektörize.

 Önbellek: Redis (ephemeris sonuçları, hesaplanmış harita/yorum fragment cache).

 İşleyiciler: Celery/RQ/Arq (ZR/Return batch, push bildirim).

 Gözlemlenebilirlik: OpenTelemetry + Prometheus + Grafana (API latency, cache hit, recall@K).

 CI/CD: GitHub Actions/GitLab CI, birim/entegrasyon testleri, IaC (Terraform) + Helm chart.

B2) Güvenlik & Uyumluluk

 Auth: OAuth2/OIDC (Apple/Google), refresh tokens; mobil secure storage.

 PII koruması: Doğum verisi şifreli (at-rest KMS), minimize log, IP/konum ayrı saklama.

 Rol/izinler: Admin/moderator/analyst.

 Rate limit: Kullanıcı/endpoint bazlı.

 GDPR: Veri indirme/silme uçları, explicit consent, retention policy.

 İçerik güvenliği: “Tıbbi/finansal değildir” banner’ı; hassas alanlarda nötr dil.

C) Veri Modeli
C1) PostgreSQL (şema önerisi)

users(id, email, auth_provider, locale, created_at)

profiles(user_id FK, name, tz, lang_pref, notification_pref)

birth_data(id, user_id FK, birth_date, birth_time, place_name, lat, lon, tzid, accuracy_band)

charts(id, user_id, birth_data_id, system_flags JSONB, computed_at)

requests(id, user_id, mode, focus_topic, created_at, status)

results(request_id FK, summary_md, confidence, json_payload, created_at)

subscriptions(user_id, plan, renew_at)

jobs(id, type, payload JSONB, status, scheduled_for, attempts)

telemetry(event, user_id, meta JSONB, ts)

C2) Neo4j (graf düğümleri/ilişkiler)

(Planet {name}), (House {n}), (Sign {name}), (Aspect {type, orb})

(Rule {id, title, weight, source, lang}) ← yorum şablonları/kurallar

(Lot {type}), (Dignity {type, score}), (Reception {type}), (FixedStar {name, rank})

Kenarlar:

(Planet)-[:RULES]->(Rule)

(Sign)-[:RULER]->(Planet)

(Planet)-[:HAS_DIGNITY]->(Dignity)

(Planet)-[:RECEIVES]->(Planet) {type}

(Rule)-[:APPLIES_TO]->(House|Aspect|Lot|FixedStar)

(Arketip {myth}) bağlı düğüm: (Planet)-[:ARCHETYPE]->(Arketip)

C3) Vector DB (koleksiyonlar)

kb_general: klasik metinler, açıklamalar (parçalanmış semantic chunks).

kb_templates: cümle şablonları (HyDE destekli varyantlar).

kb_cases: anonimleştirilmiş örnek yorumlar (eval & few-shot).

kb_sources_sparse: BM25 için ham içerik.

D) Ingestion & Dönüştürme Hattı

 Collector: PDF/HTML/MD kaynakları içeri al.

 Cleaner: metin normalize (unicode, başlıklar).

 Semantic chunking: kurallar bozulmadan böl (gezegen-ev-açı blokları).

 Schema tagging: (planet, house, sign, aspect, dignity, reception, lot) etiketleri.

 Arketip sözlüğü: mitolojik kısa açıklamalar.

 Index: vector embed + sparse BM25; Neo4j kural düğümlerine link.

 Versioning: içerik sürüm numarası + kaynak atfı.

E) Astro Hesaplayıcılar (Calculators)

 Efemeris katmanı: doğum & transit & progres & solar arc koordinatları.

 Ev sistemleri: Whole Sign (topik) + Placidus (accidental/köşe).

 Almuten Figuris: Güneş/Ay/ASC/MC/Fortuna/Spirit için rulership(5)-exalt(4)-triplicity(3)-term(2)-face(1) + tie-break.

 Sect: diurnal/nocturnal + benefik/malefik uygunluğu.

 Lot hesapları: Fortuna/Spirit/Eros (gündüz/gece formülleri).

 Antiscia/Contra: solstitial/equinox aynalama, orb ≤1°.

 Midpoint: SO/MO (≤2°), diğerleri (≤1.5°).

 Sabit Yıldız: ≤1° kavuşum/karşıt, kraliyet öncelik.

 Asteroid/TNO: kavuşum/karşıt ≤1°.

 Uranyen: 90° dial midpoint resimleri, TNP’ler ≤0°30′.

 Zaman Omurgası:

ZR (Spirit/ops. Fortune/Eros): L1–L4, peaks (Fortune 1/10/7/4), LB sıçrama, ton= (dignity + sect + almuten bağı + diğer lordlarla resepsiyon).

Profection: yıl lordu/ev.

Firdaria: majör/minör.

Secondary Progressions: progres Ay/Güneş, büyük kavuşumlar.

Solar Arc: ASC/MC/Işık/almuten tetik ≤1°.

Transitler: yalnız yaklaşan; natal vaat filtresi.

Destek: SSR/LR/TP → yalnız teyit.

F) Yorum Motoru (Interpreter) & Orkestrasyon

 Feature extractor: hesap sonuçlarını “kanıt etiketleri”ne çevir (NS=skor).

 Scoring: Temel puan + çarpanlar (sect, dignity, resepsiyon, orb, ZR/Profection/Firdaria uyumları, peak/LB, antiscia, midpoint, sabit yıldız, vs.).

 Conflict resolver: öncelik kuralları (Almuten+Lights+ASC/MC > yöneticiler > diğerleri; zaman lordu uyumu > tek transit; yaklaşan > ayrılan).

 Kolektif/Kişisel notu: Uranüs/Neptün/Plüton/TNO için “jenerasyonel” etiketi.

 Arketip serpiştirme: kısa mitolojik referanslar.

 Output composer:

Genel Profil → Güçlü Yönler → Dikkat/Öneri → Zamanlama → Güven notu.

Her cümle arkası: [kanıt] etiketi + (isteğe bağlı) kaynak atfı (RAG cit.).

 Calibration: 1–5 güven skoru, nedenleri (ör. “çoklu teyit”, “geniş orb” vs.).

 When/Not kural katmanı: gereksiz ağır teknikler devre dışı.

G) RAG Alt Sistemi

 Retriever: Hybrid (dense + BM25).

 Query expansion: eşanlamlar (“ASC / Yükselen”), HyDE (belirsiz sorgu).

 Re-ranker: cross-encoder/LLM rerank (kritik sayfalarda).

 Context filtering: (planet, house, aspect, method) etiketleri.

 Citation: kaynak linkleri + neo4j rule id.

 Caching: embedding sonuçları ve top-K hitleri.

H) API Tasarımı (FastAPI)
H1) Auth & Profil

 POST /auth/login

 GET /me

 PATCH /me/profile (locale, tone, notification)

H2) Harita & Talep

 POST /charts (birth_data_id | raw birth data) → chart_id

 POST /requests (chart_id, mode, focus_topic) → request_id (enqueue job)

 GET /requests/{id} (status)

 GET /results/{request_id} (summary_md, confidence, evidence JSON)

H3) Zamanlama & Bildirim

 POST /alerts (windows from ZR/Profection/transit)

 GET /alerts (aktif pencereler)

 Push: FCM/APNs entegre, günlük özet.

H4) Veri Hakları

 GET /data/export (GDPR)

 DELETE /data (hesap silme)

H5) Gözlemlenebilirlik (internal/admin)

 GET /admin/metrics

 GET /admin/eval (Recall@K, faithfulness skoru)

I) Mobil Uygulama (UI/UX)

 Onboarding: veri izni, gizlilik, doğum verisi giriş (belirsizlik bandı seçici).

 Çekirdek ekranlar:

Profil (Genel Profil/Arketip kartları)

Zamanlama ZR akışı (L1–L2 timeline, peak/LB rozeti, ton/kanıt)

Güncel (Transit/Progres/SA + SSR/LR/TP teyidi)

 Güven skoru rozeti + “jenerasyonel etki” etiketi.

 Çok dilli metin + ton (nazik/teknik/kısa).

 Paylaşım: PDF/PNG rapor dışa aktarma.

J) Değerlendirme, Observability & A/B

 Eval set: el yapımı 100–200 vaka (anonim), sorgu→beklenen kaynak/yorum.

 Metrikler: Recall@K, Faithfulness/Groundedness, Latency, Cache hit, Abandon rate.

 Hata günlüğü: “hallucination” etiketli örnek havuzu.

 A/B: re-ranker açık/kapalı; HyDE açık/kapalı; template varyantı.

 Dashboard: Grafana panelleri.

K) Caching & Session Memory

 Redis cache: efemeris sonuçları, ZR periyotları, sık istenen yorum blokları.

 Kullanıcı hafızası: tercih edilen odak, ton, dil; en son okunan dönem; kişiselleştirme.

 Cache invalidation: içerik sürümü değişince etkilenen anahtarları boşalt.

L) Edge Cases & Kalite

 Belirsiz doğum saati: ASC bandı hesapla, çoklu senaryo + “güven bandı” ile sun.

 DST/TZ anomalileri: tzdb doğrulama, fallback uyarısı.

 Koordinat hataları: geocoder doğrulama + kullanıcı onayı.

 Out-of-range: efemeris/epoc sınır kontrolü.

 Metin kalitesi: dilbilgisi/ton lint (TR/EN).

 Accessibility: VoiceOver/TalkBack, yüksek kontrast.

M) Test & Kalite Güvencesi

 Unit: hesaplayıcı fonksiyonlar (almuten, lots, antiscia, ZR LB).

 Property tests: simetriler (antiscia çift yön), dignity toplamlarda determinism.

 Integration: end-to-end API → yorum çıktısı; RAG + Neo4j + Vector DB.

 Load tests: eşzamanlı istekler, cache davranışı.

 Security tests: auth bypass, rate limit, PII sızıntısı, SQL/Gremlin/OGM inj.

N) Yayınlama & Operasyon

 IaC: Terraform (VPC, DB, secrets), Helm (deploy).

 Sıcak yedek: Postgres read-replica, Neo4j cluster, Vector DB SLA’sı.

 Sürümleme: semver; migration script’leri (alembic + cypher).

 Runbooks: pager kuralları, incident playbook, rollback talimatı.

 Kullanıcı destek: raporla-geliştir; içerik düzeltme akışı.

✅ Kabul Kriterleri (Örnek)

 Almuten + ZR + Profection + Firdaria bir arada çalışıyor; L1/L2 peak & LB rozetli timeline üretiliyor.

 Ton belirleme: seçili ZR dönem yöneticisi için (dignity + sect + almuten ilişkisi + resepsiyon) hesaplanıyor ve metne yansıyor.

 Kolektif etiket: Uranüs/Neptün/Plüton/TNO etkilerinde “jenerasyonel” etiketi otomatik çıkıyor.

 Antiscia/Contra: majör açı kadar değerlendirilip skora yansıyor.

 Güven skoru: 1–5 bandında, neden listesi ile dönüyor.

 RAG: her iddia için en az 1 kaynak veya “iç kural” referansı; Recall@K hedef aralığında.

 Latency hedefi: (ürün kriteri) cold-start <-> warm-cache farkı dashboard’da izlenebilir.

 GDPR uçları: veri indirme/silme çalışır, loglar PII içermiyor.

 Çok dillilik: TR/EN çıktılar tutarlı; mitolojik/arketipsel snippet aktif.

🔌 Örnek İş Akışı (API düzeyi, özet)

POST /charts → efemeris & temel hesaplar → chart_id

POST /requests (mode: “timing”, focus: “kariyer”) → queue job

Job: calculators → ZR(L1/L2/peak/LB) + Profection + Firdaria + SP + SA + Transit + SSR/LR/TP

Interpreter: scoring + conflict resolver + arketip + kolektif etiketi + calibration

RAG: kural/sözlük/kaynak açıklaması çek → cite et

GET /results/{id} → “Genel profil / Güçlü yönler / Dikkat / Zamanlama / Güven”

Push: L2-peak/LB penceresine girince bildirim