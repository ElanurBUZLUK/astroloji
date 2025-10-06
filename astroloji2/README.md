# Astroloji AI

Astroloji AI, doğum bilgileri ve güncel gökyüzünden hareketle kişiselleştirilmiş astrolojik yorumlar üreten üretim odaklı bir servis iskeletidir. Proje; ephemeris hesapları, RAG tabanlı bilgi geri getirimi ve LLM yönlendirmesini birlikte ele alır.

## Başlangıç

### Önkoşullar
- Python 3.11
- OpenAI API anahtarı (`OPENAI_API_KEY`)

### Kurulum
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
```

### Geliştirme Sunucusu
```bash
astroloji-api
```

### Bilgi Bankası Oluşturma
```bash
kb-ingest
```

## Klasör Yapısı
```
src/
  astroloji_ai/
    api/         # FastAPI uygulaması ve HTTP katmanı
    config/      # Konfigürasyon modelleri / yükleyicileri
    core/        # Ephemeris, astroloji hesapları, cache
    monitoring/  # Metrikler ve loglama altyapısı
    rag/         # RAG entegrasyonu ve bilgi bankası
    schemas/     # Pydantic şemaları
    utils/       # Yardımcı fonksiyonlar
data/
  external/      # Kaynak dosyalar (ingest öncesi)
  processed/
    vector_store # Chroma persist dizini
tests/           # Birim ve entegrasyon testleri
```

## Lisans
Bu proje şimdilik kapalı kaynak olarak başlatılmıştır. Lisans kararı netleşene kadar izinsiz kullanım önerilmez.
