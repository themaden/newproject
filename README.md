# LocalDesk AI — Kurumsal Yerel RAG + SQL Demo

**Python · FastAPI · LangChain · Ollama · Qdrant · Docker · SQLite**

Mülakat için geliştirilmiş, yerel dil modeliyle çalışan **kaynak gösteren bir RAG prototipi**. PDF, TXT ve Markdown belgelerini yükler, embedding'lerini Qdrant'a kaydeder ve soruları belgelerden bulduğu içerikle yanıtlar. Ayrıca **örnek/sentetik** satış kayıtlarından SQL raporu üretir. Tarayıcı arayüzü ve Swagger dokümantasyonu içerir.

> **Sınır:** Bu bir MVP'dir; production-ready değildir. Gerçek şirket verileri, müşteri bilgileri veya API anahtarları GitHub'a yüklenmemelidir. Çok kullanıcılı SSO/RBAC, belge bazlı izinler, TLS, audit log, OCR ve RAG evaluation eklenmeden kurumsal kullanıma alınmamalıdır. AI Agent tool-calling henüz bu sürümde yok; SQL sorgulama yalnızca sabit ve güvenli bir endpoint ile yapılır.

## Mimari

```text
Tarayıcı → FastAPI (X-API-Key)
                  ├─ POST /api/ingest → PDF/TXT → chunking → Ollama BGE-M3 → Qdrant
                  ├─ POST /api/ask → LangChain retrieval → Qdrant → Ollama Qwen3 → kaynaklı yanıt
                  └─ GET /api/sales/summary → parameterized read-only SQLite → örnek satış raporu
```

## Hızlı başlangıç — Docker Compose (önerilen)

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) kur ve başlat.
2. Proje klasöründe `.env.example` dosyasını `.env` adıyla kopyala; `APP_API_KEY` değerini değiştir.
3. Terminal:

```bash
docker compose up -d --build
docker compose exec ollama ollama pull qwen3:4b-instruct
docker compose exec ollama ollama pull bge-m3
```

4. Tarayıcıdan **http://localhost:8000** aç; `.env` içindeki `APP_API_KEY` değerini arayüze gir.
5. `data/example_policy.txt` dosyasını yükle ve **"Stok sayımı hangi gün yapılır?"** sorusunu sor.
6. Soldaki SQL raporu için `2026-11` ayını seç.
7. Swagger: **http://localhost:8000/docs**.

> İlk model indirmesi internet gerektirir. GPU yoksa CPU ile çalışabilir ama yavaş olabilir. Model maliyet/VRAM testleri sunucuya göre yapılmalıdır. Docker Compose'taki Ollama servisi varsayılan olarak CPU odaklıdır. GPU kullanımında ayrıca NVIDIA Container Toolkit ve Compose GPU yapılandırması gerekir. Hafif model için `.env` içinde `LLM_MODEL=qwen3:1.7b` yazıp bu modeli de çekebilirsin.

## Yerel Python ile çalıştırma (Docker yalnızca Qdrant için)

Python 3.11+ ve Ollama kurulu olsun. Modelleri indir:

```bash
ollama pull qwen3:4b-instruct
ollama pull bge-m3
# PowerShell:
copy .env.example .env
# Linux/macOS:
# cp .env.example .env
```

`.env` dosyasındaki `APP_API_KEY` değerini değiştir. Ortam değişkenlerini yükleyen bir terminalde başlat:

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
# Qdrant:
docker run -d --name localdesk-qdrant -p 127.0.0.1:6333:6333 -v localdesk_qdrant:/qdrant/storage qdrant/qdrant:v1.15.5
python -m app.seed
uvicorn app.main:app --reload
```

**Not:** Uvicorn `.env` dosyasını kendiliğinden yüklemez; PowerShell'de `$env:APP_API_KEY="<anahtar>"`, bash'te `export APP_API_KEY="<anahtar>"` tanımla. Diğer varsayılan URL'ler localhost'tur. Alternatif olarak `uvicorn app.main:app --env-file .env --reload` kullan (uvicorn[standard] ile).

## Örnek API kullanımı

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "X-API-Key: <ANAHTAR>" -H 'Content-Type: application/json' \
  -d '{"question":"Stok sayımı ne zaman yapılır?"}'

curl -H "X-API-Key: <ANAHTAR>" 'http://localhost:8000/api/sales/summary?month=2026-11'
```

## Testler

```bash
pip install -r requirements.txt pytest httpx
python -m pytest -q
```

Testlerde sahte (fake) RAG servisi kullanılır; gerçek Ollama/Qdrant bağlantısını test etmek için Docker ile modelleri çalıştırıp tarayıcıda uçtan uca denemek gerekir. CI yalnızca birim ve HTTP sözleşme testlerini çalıştırır.

## Teknoloji kararları

| Gereksinim | Çözüm | Neden |
| --- | --- | --- |
| Yerel LLM | Ollama + Qwen3 | Kurum içinde inference |
| Türkçe embedding | Ollama + BGE-M3 | Çok dilli anlamsal arama |
| RAG kütüphanesi | LangChain | Modüler belge arama ve model entegrasyonu |
| Vektör veritabanı | Qdrant | Kalıcı belge indeksleme |
| API | FastAPI | Swagger, tip kontrolü |
| SQL | SQLite demo | Salt okunur parametrik sorgu örneği |
| Dağıtım | Docker Compose | Üç servisi birlikte başlatma |

## Üretime geçişte sıradaki adımlar

- SSO/OIDC ve kullanıcı/belge bazlı yetkilendirme; Qdrant metadata filtreleri.
- Güncellenen belgelerde atomik indeks yenileme ve sürümleme.
- Soru/cevap değerlendirmesi: Recall@K, faithfulness, kaynak doğruluğu.
- OCR ve PDF tablo çıkarımı; anti-prompt-injection değerlendirmeleri.
- Loglama, metrikler, hata izleme, rate limit, secret management, TLS.
- Gerçek ERP/CRM API bağlantısı: salt-okunur hesap, allowlist sorgular, audit.
- Hibrit LLM gateway: kurum dışına gönderimi yetki ve veri sınıflandırmasına göre kontrol etme.

## Mülakatta 30 saniyelik demo

1. Tarayıcıdan **LocalDesk AI** ekranını aç.
2. `example_policy.txt` yükle; "kaç parça indekslendi" mesajını göster.
3. "Stok sayımı ne zaman yapılır?" diye sor. Yanıttaki dosya adı ve parça numarasını göster.
4. `2026-11` SQL raporunu göster; `336.000 TL` sentetik toplamını açıklayabil.
5. RAG ile SQL farkını anlat: **dokümanlar → RAG; güncel rakamlar → kontrollü SQL**.

## Lisans

MIT. Demo amaçlıdır. Proje üzerinde gerçek kişisel veya gizli şirket verisi bulunmaz.
