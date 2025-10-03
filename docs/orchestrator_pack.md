# Model Orchestrator Pack

Bu rehber, projeye entegre ettiğimiz **health-weighted model orkestrasyonu**, **otomatik degrade/upgrade politikaları**, **schema/citation guardrails** ve **A/B test altyapısı** hakkında hızlı bir özet sunar. İçerik, `model_orchestrator_pack_yaml_python_proje_adi.md` dokümanındaki şablon önerilerini mevcut kod tabanımızdaki gerçek modüllerle eşleştirir.

---

## Dizin Snapshot

```
backend/app/
├─ config.py                     # Orkestratör için konfig değerleri (LLM_ROUTER_*)
├─ core/
│  └─ llm/
│     ├─ orchestrator.py         # Intent classifier, health monitor, model selector, LoRA styler
│     ├─ provider_pool.py        # Sağlık ağırlıklı provider seçimi
│     └─ strategies/auto_repair.py
├─ pipelines/
│  ├─ degrade.py                 # Global degrade kararları
│  └─ rag_pipeline.py            # Orchestrator entegrasyonu ve telemetri kayıtları
└─ scripts/
   └─ tune_router_thresholds.py  # Telemetri tabanlı eşik ayarlama CLI
```

> Orijinal şablondaki `router.py`, `health.py`, `degrade.py`, `validators.py`, `citation.py`, `ab.py` bileşenleri proje içerisinde yukarıdaki modüllerle karşılanmaktadır.

---

## Konfigürasyon (settings)

`backend/app/config.py` içinde aşağıdaki parametreleri güncelleyerek orkestratörü ayarlayabilirsiniz:

```python
LLM_ROUTER_CONF_LOW = 0.55
LLM_ROUTER_CONF_HIGH = 0.75
LLM_ROUTER_POLICY_KEYWORDS = "medical,financial,privacy,confidential,legal,therapy"
LLM_ROUTER_LORA_ENABLED = False
LLM_ROUTER_SMALL_PROVIDER = "primary_openai"
LLM_ROUTER_MEDIUM_PROVIDER = "primary_openai"
LLM_ROUTER_LARGE_PROVIDER = "fallback_openai"
```

İhtiyaç duydukça bu değerleri `.env` üzerinden override edebilirsiniz. Degrade politikası eşiği (`RAG_DEGRADE_LATENCY_THRESHOLD_MS`, `RAG_DEGRADE_MIN_SAMPLES`, vb.) aynı dosyada yer alır.

---

## Orchestrator Akışı

`backend/app/core/llm/orchestrator.py` içerisinde:

1. **IntentComplexityClassifier**: Sorguyu basit/karmaşık/policy-risk olarak sınıflandırır.
2. **ConfidenceEstimator**: Coverage, rerank skorları ve citation çeşitliliğine göre 0-1 arası güven skoru üretir.
3. **ProviderHealthMonitor**: Son N istekten p95, hata sayısı ve latency ile health_score hesaplar.
4. **ModelSelector**: Sağlık/ağırlık & degrade durumuna göre small/medium/large profilini seçer.
5. **LoRAStyler**: Feature-flag ile aktif edilebilen ton/format düzenleyici.
6. **SchemaValidator**: `AnswerPayload` üzerinden JSON şeması doğrulaması yapar.

Pipeline (`rag_pipeline.py`) LLM revizyonu talep ettiğinde orchestrator’ı çağırarak bu adımları çalıştırır ve `debug.routing` alanına karar detaylarını yazar.

---

## Telemetri & Eşik Ayarı

Yeni telemetri kayıtları:

- `llm_router_confidence_metric` (tag: success/provider/model)
- `llm_provider_latency` (provider bazlı latency)
- `llm_provider_health_score` (rolling health_snapshot)

Bu verilerle eşiği ayarlamak için CLI:

```bash
python backend/scripts/tune_router_thresholds.py --target-precision 0.9
# veya NDJSON export ile
python backend/scripts/tune_router_thresholds.py --input telemetry.ndjson
```

Komut, önerilen `LLM_ROUTER_CONF_LOW/HIGH` ve provider sağlığına dair 10. yüzdelik taban değerlerini çıktılar.

### Tuning Checklist

1. **Veri Topla** – 24+ saatlik üretim telemetrisini sakla (`llm_router_confidence_metric`, `llm_provider_latency`).
2. **CLI Çalıştır** – Yukarıdaki komutu kullanarak yeni eşik önerilerini al (`--target-precision` hedefini gerekiyorsa değiştir).
3. **Sonuçları Değerlendir** – Çıktıdaki destek (support) ve precision değerleri SLO’larla uyumlu mu kontrol et; provider sağlığı düşükse circuit breaker eşiklerini gözden geçir.
4. **Konfig Güncelle** – `LLM_ROUTER_CONF_LOW/HIGH` ve gerekirse degrade eşiklerini `.env` veya konfig yönetimi üzerinden güncelle.
5. **Canary İzle** – Yeni değerleri kademeli yay ve p95/json_valid/citation_ok oranlarını 1-2 saat takip et.
6. **Belgele** – Yapılan ayarları SRE runbook’una ve bu dosyaya not düş.

---

## Guardrails & Upgrade Politikaları

- **Schema/JSON Repair**: `AutoRepair` + Pydantic doğrulaması ile tek tur onarım.
- **Citation Alignment**: `score_claim_alignment` fonksiyonu ile per-claim kontrol; ihlalde degrade notu.
- **Degrade/Upgrade**: `DegradePolicyManager` latency, provider hataları ve cost guardrail’lerine göre cache TTL, top-k ve model tercihini ayarlar.
- **Sanitization**: Retrieval snippet’ları HTML/JS’den arındırılır, dış linkler `[external-link]` olarak işaretlenir.
- **Provider Routing**: Aynı model boyutunda birden fazla provider varsa health-weighted seçim yapılıp circuit-breaker uygulanır.

---

## A/B Test Altyapısı

Rerank `k` değerleri için şimdilik sabit konfigürasyon (`settings.LLM_ROUTER_CONF_*`). Gerekirse `RerankAB` benzeri stateful bir yapı `orchestrator.py` içine taşınabilir. CLI ve telemetri çıktıları, farklı `rerank_k` varyantlarının etkisini ölçmek için temel sağlar.

---

## Doğrulama

Pytest kurulumu sonrası aşağıdaki testler orchestrator bileşenlerini kapsar:

```bash
pytest backend/tests/test_llm/test_orchestrator.py \
       backend/tests/test_pipelines/test_degrade_policy.py \
       backend/tests/test_rag/test_core.py::test_query_for_interpretation_policy_override
```

*(Ortamdaki Python dağıtımında pytest kurulu değilse `pip install pytest` çalıştırın.)*

### TODO
- CI/yerel ortamlarda pytest ve bağımlılıklarını etkinleştir ve yukarıdaki test paketini çalıştır.
- Telemetri eşiği güncellemelerini SRE runbook’una (ve gerekiyorsa `docs/orchestrator_pack.md`) düzenli olarak işle.

---

Bu doküman, orijinal şablon dokümanının içerdiği orkestrasyon paketini projedeki gerçek modüllere haritalandırır ve eklediğimiz telemetri/CLI araçlarıyla eşik tuning sürecini kolaylaştırır.
