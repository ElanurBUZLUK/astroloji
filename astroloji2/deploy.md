Süper. Aşağıda **tech stack**’e uyumlu, Jira/Linear’a direkt taşınabilir **ayrıntılı task listesi** var. 2 haftalık sprintler halinde ilerliyor; her görev için “Amaç”, “Adımlar”, “DoD (Definition of Done)”, “Kontroller/Notlar” verdim. İstersen başlıkları kopyalayıp issue/story oluşturabilirsin.

---

# Yol Haritası (Özet)

* **Sprint 0** – İskeletin sertleştirilmesi: ephemeris doğruluğu, API sözleşmesi, validasyon, temel metrikler, cache.
* **Sprint 1** – RAG altyapısı: Chroma + embeddings + KB builder, kaynaklı yanıt.
* **Sprint 2** – LLM & maliyet kontrolü: router, fallback, kalite doğrulama, güvenlik.
* **Sprint 3** – Performans & DevOps: load test, k6/Locust, CI/CD, K8s, canary + rollback.
* **Sürekli (opsiyonel)** – Kişiselleştirme, analitik, açık kaynak SFT (gerekirse).

---

# Sprint 0 — Çalışan Dikey Dilim (temel, 3–5 gün)

## S0-T1: Ephemeris çekirdeği + TTL cache

**Amaç:** Konum/zaman bazlı doğru gezegen konumları; tekrar hesaplamaları azalt.
**Adımlar**

* `src/data/ephemeris_calculator.py`

  * `calculate_planet_positions(now)` doğruluğunu sabitle (UTC, observer.date).
  * `calculate_aspects(positions, orb=6.0)` basit açılar.
  * `get_dominant_planets(burc, positions)` heuristik.
* 60 dakikalık **TTL cache** (in-memory): key = `(lat|lon|date-hour)`.
  **DoD**
* Aynı (lat,lon, saat) için ikinci çağrıda **cache hit** log’u görünüyor.
* Sabit tarih/konum için snapshot testleri geçiyor.
  **Kontroller/Notlar**
* Test: `tests/test_ephemeris.py` – sabit tarih için RA/DEC toleranslı karşılaştırma.

---

## S0-T2: API sözleşmesi & validasyon

**Amaç:** Stabil kontrat, güvenilir hata mesajları.
**Adımlar**

* `src/api/schemas.py`: `HoroscopeRequest/Response` şemalarını son haline getir.
* `src/api/main.py`:

  * Burç/gün whitelist (TR).
  * XSS strip, boyut limitleri.
  * Hatalı girişte 400 + anlaşılır mesaj.
    **DoD**
* Geçersiz `burc`/`gun` → 400 ve örnek hata gövdesi.
* `/docs`’ta örnek istek/yanıtlar görülebilir.
  **Kontroller/Notlar**
* Test: `tests/test_api.py` – invalid case, valid case örnekleri.

---

## S0-T3: Observability temel (Prometheus + JSON log)

**Amaç:** Sayılabilir, izlenebilir sistem.
**Adımlar**

* `src/monitoring/metrics.py`: `PREDICTION_COUNT`, `PREDICTION_LATENCY`, `MODEL_CONFIDENCE`.
* API’nin giriş/çıkışında yapılandırılmış JSON log + `request_id`.
* (Opsiyonel) Prometheus endpoint (ayrı port) veya exporter.
  **DoD**
* Metrikler scrape ediliyor; local dashboard basit grafik gösteriyor.
  **Kontroller/Notlar**
* Loglarda correlation-id, latency görünüyor.

---

## S0-T4: Docker Compose akışı

**Amaç:** Lokal dev tek komut.
**Adımlar**

* `infrastructure/docker-compose.yml`: API + Chroma (şimdilik boş) + (opsiyonel Redis).
* README’ye “quickstart” komutları.
  **DoD**
* `docker compose up --build` → `/health` 200.

---

# Sprint 1 — RAG Altyapısı (2–5 gün)

## S1-T1: Embeddings + Chroma kurulum (gerçek)

**Amaç:** Kalıcı vektör deposu ve retriever.
**Adımlar**

* `AstrologyRAGSystem.setup_rag()`

  * `text-embedding-3-small` (OpenAI)
  * Chroma persist: `CHROMA_DIR`
  * Retriever: MMR (`k=5, fetch_k=10`)
    **DoD**
* `setup_rag()` çağrısı hata vermeden hazır hale gelir.
  **Kontroller/Notlar**
* Env: `OPENAI_API_KEY`, `CHROMA_DIR`.

---

## S1-T2: KB Builder (ingest → split → persist)

**Amaç:** Astroloji içeriklerinin vektörleştirilmesi.
**Adımlar**

* `src/models/knowledge_base_builder.py`

  * PDF/HTML ingest (pdfplumber/requests + readability).
  * `RecursiveCharacterTextSplitter` ile bölme.
  * Chroma’ya persist.
* CLI komutu: `python -m src.models.knowledge_base_builder`
  **DoD**
* `data/processed/vector_store/` dolu; tekrar çağrıldığında incremental çalışabiliyor.
  **Kontroller/Notlar**
* Basit kaynak meta: `{"source": "...", "type": "web/pdf"}`.

---

## S1-T3: /horoscope → kaynaklı yanıt

**Amaç:** RAG bağlamı ile anlamlı ve referanslı yanıt.
**Adımlar**

* `/horoscope` içinde RAG çağrısı; `kaynaklar` alanını yanıt gövdesine ekle.
  **DoD**
* Yanıtta `kaynaklar` listesi dolu (1–3 öğe).
  **Kontroller/Notlar**
* Test: “response contains kaynaklar”.

---

# Sprint 2 — LLM & Maliyet Kontrolü (3–6 gün)

## S2-T1: Model router + feature flag

**Amaç:** Maliyet/kalite dengesi.
**Adımlar**

* `src/models/cost_optimized_system.py`:

  * Rutin (`bugün/yarın/hafta`) → **gpt-3.5**
  * Karmaşık (`aylık/yıllık/kariyer/aşk/detaylı`) → **gpt-4o**
* `.env`: `ENABLE_LLM=true/false`, `LLM_TIMEOUT_MS`, `MAX_TOKENS`.
  **DoD**
* Loglarda “seçilen model” görülebilir; flag kapalıyken şablon + RAG döner.

---

## S2-T2: Fallback zinciri

**Amaç:** Dayanıklılık.
**Adımlar**

* LLM hata/timeout → template + ephemeris ile üretim.
* Yanıta (opsiyonel) `is_fallback=true` alanı.
  **DoD**
* Fail simülasyonunda 200 dönmeye devam eder; içerik degrade ama anlamlı.

---

## S2-T3: Kalite doğrulama (rule-based)

**Amaç:** LLM çıktısının asgari kalite filtresi.
**Adımlar**

* `VALIDATION_RULES`:

  * `len(text) > 100`
  * `text.count('.') >= 3`
  * Anahtar kelimelerden en az biri: `['tavsiye','dikkat','fırsat','öneri']`
* Rule fail → fallback metni.
  **DoD**
* Kötü/çok kısa üretim üretim hattına girmiyor.

---

## S2-T4: Güvenlik & Rate limit

**Amaç:** Prod’a açmadan önce temel güvenlik.
**Adımlar**

* API Key (header) veya JWT (şimdilik key).
* CORS allowlist.
* Rate limit: 10 req/dk (dev: memory, prod: Redis).
  **DoD**
* Yetkisiz 401; limit aşımında 429; CORS sadece allowlist’ten.

---

# Sprint 3 — Performans, CI/CD, K8s (4–7 gün)

## S3-T1: Performans profili + cache politikası

**Amaç:** p95 < 300ms (LLM hariç).
**Adımlar**

* Profiling: ephemeris ve RAG süreleri.
* Cache:

  * Ephemeris 60dk TTL
  * (Opsiyonel) Retriever sonuçlarına 5dk TTL
    **DoD**
* Rapor ve tespit edilen darboğazlara issue açıldı.

---

## S3-T2: Load test (k6/Locust)

**Amaç:** 1000 RPM hedefini stres altında doğrulamak.
**Adımlar**

* `load/` klasörü: k6 scripti; smoke/stress test senaryoları.
* CI job: “kısa smoke” (isteğe bağlı).
  **DoD**
* Rapor artefact olarak CI’da; hedefler belgelendi.

---

## S3-T3: CI/CD & Security scan

**Amaç:** Otomasyon ve güven.
**Adımlar**

* GitHub Actions: lint+test+docker build; `bandit` + `safety`.
* Docker image push (registry) – staging tag.
  **DoD**
* `main` push → pipeline yeşil; imaj yerinde.

---

## S3-T4: Kubernetes deploy + canary + rollback

**Amaç:** Kontrollü yayılım.
**Adımlar**

* `infrastructure/kubernetes/deployment.yml` + service + (opsiyonel Ingress/TLS).
* Canary: %10 → %50 → %100; rollback komutu ve runbook.
  **DoD**
* Staging çalışıyor; canary/rollback **denenmiş** durumda.

---

# Sürekli/İsteğe Bağlı Epikler

## E1: Kişiselleştirme & Paketler

* Response seviyeleri: **Temel / Gelişmiş / Premium**
* Kullanıcı profili (ilgi alanları, dil, geçmiş istekler).
* Feedback endpoint (memnuniyet puanı → metrik).

## E2: Analitik & Geri Bildirim

* PostHog/Amplitude entegrasyonu, event şeması.
* A/B test çerçevesi (şablon vs RAG+LLM).

## E3: Açık Kaynak SFT (gerekirse)

* Eval harness (statik test + otomatik skor).
* JSONL dataset şeması; LoRA/QLoRA SFT script (TRL/PEFT).
* vLLM/TGI ile servis; router: rutin→lokal, karmaşık→API.

---

# Ortak DoD (her sprint için)

* Testler yeşil (unit + basit integration).
* Metrikler ve loglar anlamlı (gözlemlenebilir).
* Güvenlik temel gereksinimleri sağlanmış.
* README ve `.env.example` güncel.

---

## Backlog / Sonraya Bırakılabilecekler

* OpenTelemetry tracing (OTLP → Tempo/Jaeger).
* Multi-tenant rate limit & usage quotas.
* Grafana dashboard JSON templateleri.
* Helm chart + GitOps (ArgoCD/Flux).
* Türkçe morfolojik analiz/normalizasyon (LLM öncesi preprocessing).

---

## Hızlı Başlangıç Komutları (hatırlatma)

```bash
# Lokal
cp .env.example .env
docker compose -f infrastructure/docker-compose.yml up --build

# Test
pip install -r requirements-dev.txt
pytest -q

# KB builder (örnek)
python -m src.models.knowledge_base_builder
```

---

İstersen sıradaki mesajda **Sprint 0 için PR/issue şablonlarını** (task başlıkları + kabul kriterleri + kontrol listeleri) direkt kopyala-yapıştır formatında göndereyim; ayrıca **RAG `setup_rag()` gerçek kodunu** ve **KB builder**’ı çalışır hâlde verebilirim.

Süper — burada iki şeyi veriyorum:

1. **Sprint 0** için kopyala-yapıştır **issue/PR şablonları + görev listeleri**
2. RAG tarafı için **çalışır kod**: `setup_rag()` ve `knowledge_base_builder.py`

İstersen aynen repo’na ekleyip ilerleyebilirsin.

---

# ✅ Sprint 0 – Issue / PR Şablonları

## S0-T1: Ephemeris + TTL Cache

**Amaç:** Konum/zaman bazlı deterministik hesap + 60dk TTL cache
**Acceptance Criteria**

* [ ] Aynı `(lat,lon,YYYY-MM-DD-HH)` için ikinci çağrıda **cache hit** metriği artıyor
* [ ] `calculate_planet_positions()` ve `calculate_aspects()` sabit tarih/konumda **snapshot** testini geçiyor
* [ ] `/horoscope` LLM kapalı olsa da anlamlı JSON dönüyor

**Görevler**

* [ ] `EphemerisCalculator`’a TTL cache ekle
* [ ] Cache için **metrics**: `CACHE_HIT_TOTAL`, `CACHE_MISS_TOTAL`
* [ ] `tests/test_ephemeris.py` snapshot

**Risk/Notlar**

* Ephem sonuçları floating; snapshot’ta küçük tolerans kullan

---

## S0-T2: API Sözleşmesi + Validasyon

**Amaç:** Stabil kontrat, temiz hata mesajları
**Acceptance Criteria**

* [ ] Geçersiz `burc`/`gun` → **400** + açıklayıcı mesaj
* [ ] `/docs`’ta örnek request/response açık
* [ ] XSS/HTML tag temizliği uygulanıyor

**Görevler**

* [ ] `schemas.py` finalize
* [ ] `validate_request` dependency (burç/gün whitelist, HTML strip)
* [ ] Negatif/pozitif testler `tests/test_api.py`

---

## S0-T3: Observability (Prometheus + JSON log)

**Amaç:** Erken görünürlük
**Acceptance Criteria**

* [ ] `PREDICTION_COUNT` ve `PREDICTION_LATENCY` artıyor
* [ ] Loglarda `request_id` görünüyor
* [ ] (Opsiyonel) `CACHE_HIT_RATIO` Gauge/Counter mevcut

**Görevler**

* [ ] Metrikleri FastAPI handler’larına ekle
* [ ] JSON log formatı + correlation id middleware

---

## S0-T4: Docker Compose Akışı

**Amaç:** Tek komutla lokal ortam
**Acceptance Criteria**

* [ ] `docker compose up --build` sonrası `/health` 200
* [ ] Chroma konteyneri ayağa kalkıyor (boş da olabilir)

**Görevler**

* [ ] README quickstart güncelle
* [ ] Compose servisleri: api + chroma (+redis opsiyonel)

---

## PR Template ( `.github/pull_request_template.md` )

```markdown
## Özet
- [x] Ne değişti, neden?

## Kapsam
- [ ] Kod
- [ ] Test
- [ ] Doküman
- [ ] Altyapı

## Test Planı
- [ ] Unit test
- [ ] Manuel smoke: `/health`, `/horoscope`

## Metrikler / Risk
- [ ] PREDICTION_COUNT / LATENCY gözlendi
- [ ] Geri alma planı (rollback)
```

---

# 🧩 Kod – Sprint 0 Patch’leri

## 1) TTL Cache + Metrikler

**Dosya:** `src/data/ephemeris_calculator.py` (güncelle)

```python
# ... mevcut importların yanına:
from typing import Tuple
import time
from prometheus_client import Counter

CACHE_HIT_TOTAL = Counter("ephemeris_cache_hit_total", "Ephemeris cache hits")
CACHE_MISS_TOTAL = Counter("ephemeris_cache_miss_total", "Ephemeris cache misses")

class EphemerisCalculator:
    def __init__(self) -> None:
        self.observer = ephem.Observer()
        self.observer.elevation = 0
        # basit TTL cache
        self._cache: dict[Tuple[float, float, str], tuple[float, dict]] = {}
        self._ttl_sec = 60 * 60  # 60 dk

    def _cache_key(self, lat: float|None, lon: float|None, date: datetime) -> Tuple[float, float, str]:
        # saati yuvarlayıp (yıl-ay-gün-saat) key yapıyoruz
        kdate = date.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%HZ")
        return (round(lat or 0.0, 4), round(lon or 0.0, 4), kdate)

    def _get_cached_positions(self, key):
        item = self._cache.get(key)
        if not item:
            CACHE_MISS_TOTAL.inc(); return None
        ts, data = item
        if (time.time() - ts) > self._ttl_sec:
            # süresi dolmuş
            self._cache.pop(key, None)
            CACHE_MISS_TOTAL.inc(); return None
        CACHE_HIT_TOTAL.inc()
        return data

    def _set_cached_positions(self, key, data):
        self._cache[key] = (time.time(), data)

    def calculate_planet_positions(self, date: datetime) -> Dict[str, Dict[str, Any]]:
        # cache anahtarını oluştur
        try:
            lat = float(self.observer.lat)
            lon = float(self.observer.lon)
        except Exception:
            lat, lon = 0.0, 0.0
        key = self._cache_key(lat, lon, date)
        cached = self._get_cached_positions(key)
        if cached:
            return cached

        self.observer.date = date
        bodies = {
            "sun": ephem.Sun(), "moon": ephem.Moon(),
            "mercury": ephem.Mercury(), "venus": ephem.Venus(),
            "mars": ephem.Mars(), "jupiter": ephem.Jupiter(),
            "saturn": ephem.Saturn(), "uranus": ephem.Uranus(),
            "neptune": ephem.Neptune(), "pluto": ephem.Pluto(),
        }
        out: Dict[str, Dict[str, Any]] = {}
        for name, body in bodies.items():
            body.compute(self.observer)
            const = ephem.constellation(body)[1]
            out[name] = {
                "ra_deg": self._deg(body.a_ra),
                "dec_deg": self._deg(body.a_dec),
                "constellation": const,
            }
        self._set_cached_positions(key, out)
        return out
```

---

## 2) Validasyon Dependency

**Dosya:** `src/api/dependencies.py` (yeni)

```python
from fastapi import HTTPException, status
import re

VALID_BURCLAR = {'koç','boğa','ikizler','yengeç','aslan','başak','terazi','akrep','yay','oğlak','kova','balık'}
VALID_GUNLER = {'bugün','yarın','bu hafta','bu ay'}

TAG_RE = re.compile(r"<[^>]+>")

def sanitize(text: str) -> str:
    return TAG_RE.sub("", text or "").strip()

def validate_request(burc: str, gun: str):
    b = sanitize(burc).lower()
    g = sanitize(gun).lower()
    if b not in VALID_BURCLAR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error":"Geçersiz burç","allowed":sorted(list(VALID_BURCLAR))}
        )
    if g not in VALID_GUNLER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error":"Geçersiz gün","allowed":sorted(list(VALID_GUNLER))}
        )
    return b, g
```

**Dosya:** `src/api/main.py` (kısa ek)

```python
from src.api.dependencies import validate_request
# ...
@app.post("/horoscope", response_model=HoroscopeResponse)
@PREDICTION_LATENCY.time()
async def get_horoscope(req: HoroscopeRequest) -> HoroscopeResponse:
    PREDICTION_COUNT.inc()
    # VALIDASYON
    burc, gun = validate_request(req.burc, req.gun)
    # ... devam (burc/gun burada normalize edilmiş değişkenlerle kullanılabilir)
```

---

## 3) JSON Log + Request ID (basit middleware)

**Dosya:** `src/api/middleware.py` (yeni)

```python
import json, time, uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = str(uuid.uuid4())
        start = time.time()
        response = await call_next(request)
        dur = round((time.time() - start)*1000, 2)
        log = {
            "request_id": rid,
            "path": request.url.path,
            "method": request.method,
            "status": response.status_code,
            "duration_ms": dur,
        }
        print(json.dumps(log, ensure_ascii=False))
        response.headers["X-Request-ID"] = rid
        return response
```

**Dosya:** `src/api/main.py` (middleware ekle)

```python
from src.api.middleware import RequestLogMiddleware
app = FastAPI(title="Astroloji AI API", version="1.0.0")
app.add_middleware(RequestLogMiddleware)
```

---

# 🧠 RAG – Çalışır Kurulum (Sprint 1 başlangıcı)

## 4) `setup_rag()` gerçek implementasyon

**Dosya:** `src/models/astrology_rag_system.py` (tamamını değiştir)

```python
import os
from typing import Any, Dict
from dotenv import load_dotenv
load_dotenv()

from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

class AstrologyRAGSystem:
    def __init__(self, vector_store_path: str | None = None) -> None:
        self.vector_store_path = vector_store_path or os.getenv("CHROMA_DIR", "./data/processed/vector_store")
        self.emb = None
        self.vs = None
        self.retriever = None
        self.qa = None
        self.setup_rag()

    def setup_rag(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY missing")
        self.emb = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)
        self.vs = Chroma(persist_directory=self.vector_store_path, embedding_function=self.emb)
        self.retriever = self.vs.as_retriever(search_type="mmr", search_kwargs={"k": 5, "fetch_k": 10})

        llm = OpenAI(model_name="gpt-4o-mini", temperature=0.7, max_tokens=700, api_key=api_key)

        template = (
            "Profesyonel bir astrolog gibi konuş. Aşağıdaki bağlamı ve gezegen konumlarını kullan.\n\n"
            "Bağlam:\n{context}\n\nGezegen Konumları:\n{ephemeris_data}\n\n"
            "Soru:\n{question}\n\n"
            "Kurallar:\n"
            "1) Astroloji terminolojisini doğru kullan\n"
            "2) Pozitif ve yapıcı dil\n"
            "3) Somut pratik tavsiyeler ver\n"
            "4) Kaynaklara aykırı iddiadan kaçın\n\n"
            "Yanıt:"
        )
        prompt = PromptTemplate(template=template, input_variables=["context", "ephemeris_data", "question"])

        self.qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt},
        )

    def generate_horoscope(self, burc: str, gun: str, ephemeris_data: Dict[str, Any]) -> Dict[str, Any]:
        q = f"{burc} burcu için {gun} yorumu. Ephemeris verisini açıklamada kullan."
        res = self.qa({"query": q, "ephemeris_data": str(ephemeris_data)})
        return {
            "burc": burc,
            "gun": gun,
            "yorum": res["result"],
            "confidence": 0.82,
            "gezegen_konumlari": ephemeris_data,
            "dominant_enerjiler": [],
            "pratik_tavsiyeler": [],
            "kaynaklar": [d.metadata for d in res.get("source_documents", [])],
        }
```

---

## 5) KB Builder – ingest → split → persist

**Dosya:** `src/models/knowledge_base_builder.py` (yeni)

```python
import os, glob
from typing import List
from dotenv import load_dotenv
load_dotenv()

from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

def load_plain_texts(paths: List[str]) -> List[Document]:
    docs = []
    for p in paths:
        for fp in glob.glob(p, recursive=True):
            if not os.path.isfile(fp): continue
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read()
                if txt.strip():
                    docs.append(Document(page_content=txt, metadata={"source": fp, "type": "text"}))
    return docs

def run_ingest():
    api_key = os.getenv("OPENAI_API_KEY")
    chroma_dir = os.getenv("CHROMA_DIR", "./data/processed/vector_store")
    os.makedirs(chroma_dir, exist_ok=True)

    # 1) Örnek: data/external içindeki .txt dosyalarını al (istenirse PDF/HTML eklenir)
    seed_docs = load_plain_texts(["data/external/**/*.txt", "data/external/*.txt"])

    # 2) Böl
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(seed_docs)

    # 3) Persist
    emb = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)
    Chroma.from_documents(documents=chunks, embedding=emb, persist_directory=chroma_dir)
    print(f"Ingest tamamlandı. Parça sayısı: {len(chunks)} → {chroma_dir}")

if __name__ == "__main__":
    run_ingest()
```

**Kullanım**

```bash
# .env içinde OPENAI_API_KEY ve CHROMA_DIR ayarlı olmalı
python -m src.models.knowledge_base_builder
```

---

# 🎯 Sonraki adım

* İstersen **Sprint 0** için *tek tek issue başlıklarını* (Jira/Linear formatında) JSON/YAML olarak da çıkarırım.
* Ya da `/horoscope` içine **router + feature flag + fallback** patch’ini ekleyip göndereyim (Sprint 2’nin yarısı biter).

