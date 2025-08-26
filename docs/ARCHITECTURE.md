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