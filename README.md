# CyberGuard-ID

**Platform Skrining dan Prioritisasi Moderasi Komentar YouTube Indonesia Berbasis AI/ML (Production-Ready Architecture).**

CyberGuard-ID dirancang untuk membantu kreator konten, agensi, dan tim moderasi dalam menyaring, mengkategorisasikan, dan memprioritaskan penanganan komentar berbahaya (ujaran kebencian, pelecehan seksual, ancaman, kekerasan) serta mendeteksi serangan terkoordinasi/bot repetitif pada kolom komentar video YouTube.

---

## Arsitektur Sistem & Spesifikasi Penelitian

Aplikasi ini menggunakan arsitektur **Decoupled Client-Server**, yang merangkum kontribusi utama penelitian:
- **Model Utama**: **IndoBERT** (`indobenchmark/indobert-base-p1`)
- **Baseline Pembanding (RM2)**: **TF-IDF + LinearSVC**
- **Dataset Utama**: Ibrohim & Budi 2019 (13.169 raw → 12.934 usable) dengan split 9.053 (Train) / 1.940 (Validation) / 1.941 (Test).
- **Alur Inti**: YouTube URL Input → Preprocessing → Klasifikasi → Confidence Thresholding → Dashboard Hasil → Export PDF/CSV.

### Workflow & Data Pipeline
```mermaid
graph TD
    %% Input Sources
    subgraph Data Input
        A1[YouTube API (URL)] --> B{Data Ingestion}
    end

    %% Core Engine
    subgraph FastAPI Backend & AI Engine
        B --> C[Text Preprocessing & Sanitization]
        C --> D[IndoBERT Deep Learning Model]
        D --> E{Risk Engine & Thresholding}
        
        E -->|Risiko Tinggi| F[Kritis C3-C4]
        E -->|Risiko Sedang| G[Peringatan C1-C2]
        E -->|Aman| H[Normal C0]
        E -->|Ragu-ragu| I[Butuh Review Manual C5]
    end

    %% Storage and UI
    subgraph Storage & Presentation
        F --> J[(SQLite Database)]
        G --> J
        H --> J
        I --> J
        
        J --> K[Interactive Dashboard SPA]
        K --> L[Export PDF & Laporan CSV Mentah]
    end
```
> [!TIP]
> **Akurasi & Spesifikasi Model**
> Model IndoBERT ini telah disesuaikan secara khusus untuk menangani dinamika dan karakteristik bahasa pada **komentar YouTube berbahasa Indonesia**. Model mampu mengenali konteks ujaran kebencian, pelecehan, dan kata-kata kasar yang lazim muncul dalam ekosistem video YouTube dengan tingkat akurasi dan presisi yang tinggi.

*Fitur Non-Core (Pendukung)*: Risk scoring, integrasi Gemini (AI Summarization), dan Adaptive Learning adalah fitur tambahan dan **bukan kontribusi metodologis utama**.

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Async REST API, SSE streaming, SQLite WAL mode, **IndoBERT Pipeline**)
- **Frontend**: **Modern Single Page Application (SPA)** murni (Vanilla HTML5 / Modern CSS / Vanilla JavaScript ES6+) yang mengedepankan fungsionalitas minimalis (URL-only) dengan desain responsif multiplatform, visualisasi [Chart.js](https://www.chartjs.org/), dan ikonik [Lucide Icons](https://lucide.dev/).

```
cyberguard-id/
├── server/                     # FastAPI Backend Application
│   ├── main.py                 # FastAPI app entry point & static file server
│   ├── dependencies.py         # Singleton dependency injection
│   └── api/
│       ├── analysis.py         # Analisis YouTube + real-time SSE progress
│       ├── reports.py          # Generator & download laporan (PDF, CSV)
│       └── system.py           # Health check & schema taksonomi label
│
├── frontend/                   # Modern SPA Frontend (No build step required)
│   ├── index.html              # Shell HTML utama
│   ├── css/style.css           # Design system (Adaptif, Multiplatform, Dark Mode)
│   └── js/
│       ├── app.js              # SPA Router & state manager
│       ├── api.js              # Fetch client & SSE wrapper
│       ├── components/         # Reusable UI (Toast, Progress, Charts, DataTable)
│       └── pages/              # Halaman SPA (Dashboard, Analyze, Results, Report)
│
├── src/                        # Core Engine & Services
│   ├── core/                   # Schemas, Config, Exceptions, Logging
│   ├── services/               # Preprocessor, Classifier, Repetition, Risk, YouTube, Reports, Storage
│   └── workflow/               # Analysis Orchestration Engine
│
├── config/                     # Konfigurasi Taksonomi & Model (YAML)
├── models/                     # Model Klasifikasi (IndoBERT HuggingFace) & Metadata
├── artifacts/                  # Database SQLite (cyberguard.db), Hasil Analisis & Laporan
├── scripts/                    # Script Training, Evaluasi & Audit
├── run.py                      # One-command cross-platform launcher
└── requirements.txt            # Dependensi Python
```

---

## Taksonomi Kategori Label (C0 - C5)

Sistem menggunakan 6 kategori klasifikasi (5 kategori model terlatih + 1 kategori ketidakpastian):
1. **C0: Normal** — Komentar biasa, apresiasi, pertanyaan, informasi, diskusi.
2. **C1: Abusive** — Makian atau kata kasar tanpa target individu langsung.
3. **C2: Hate Speech (Weak)** — Ujaran kebencian ringan, penghinaan/ejekan berisiko rendah.
4. **C3: Hate Speech (Moderate)** — Ujaran kebencian sedang (serangan agresif, pencemaran nama baik).
5. **C4: Hate Speech (Strong)** — Ujaran kebencian ekstrem (ancaman, kekerasan, rasisme, radikalisme).
6. **C5: Tidak Pasti** — Komentar ambigu yang memerlukan *human review* (bukan kelas training).

---

## Panduan Penggunaan Cepat

### 1. Prasyarat
- Python 3.10+
- (Opsional) Google YouTube Data API v3 Key
- (Opsional) Google Gemini API Key (untuk ringkasan eksekutif AI)

### 2. Menjalankan Aplikasi
Cukup jalankan satu perintah di terminal:
```bash
python run.py
```
Perintah ini akan secara otomatis:
1. Menyiapkan virtual environment `.venv` jika belum ada.
2. Menginstal seluruh dependensi yang diperlukan.
3. Menginisialisasi basis data SQLite dan struktur folder.
4. Menjalankan server aplikasi di **http://localhost:8000**.

Buka peramban Anda di: **[http://localhost:8000](http://localhost:8000)**

### 3. Konfigurasi Lingkungan (`.env`)
Salin atau edit file `.env`:
```ini
YOUTUBE_API_KEY=your_youtube_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
ANONYMIZATION_SALT=rahasia-salt-unik
APP_PORT=8000
LOG_LEVEL=INFO
```

---

## Perintah CLI & Otomatisasi

| Perintah | Deskripsi |
|---|---|
| `python run.py` | Menjalankan server web produksi di port 8000 |
| `python scripts/train_bert.py` | Melatih ulang (fine-tuning) model IndoBERT Deep Learning |
| `python run.py --test` | Menjalankan unit test & integration test suite |
| `python run.py --check` | Menjalankan audit kesehatan dan konfigurasi sistem |

---

## Dokumentasi REST API

Setelah server berjalan, dokumentasi interaktif Swagger UI tersedia di:
- **Swagger Docs**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **ReDoc**: [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

---

## Keunggulan Desain & Transparansi Data
- **Keutuhan Konteks & Audit**: Nama asli pengguna pengirim komentar (YouTube username) terekam sepenuhnya dan ditampikan dalam Dashboard maupun Laporan (PDF/CSV) untuk keperluan audit keamanan dan pelacakan pelanggar secara akurat.
- **Deteksi Serangan Terkoordinasi**: Memiliki modul *Repetition Detector* dengan MinHash LSH / TF-IDF Cosine Similarity untuk mendeteksi gelombang bot atau spam brigade.
- **Explainability**: Setiap prediksi menyertakan skor keyakinan terkalibrasi (*calibrated probability*), margin keputusan, dan penanda verifikasi kepastian.
- **Adaptif**: Dibangun dengan antarmuka CSS kustom (tanpa library berat), sangat responsif dan aman digunakan untuk ukuran layar mulai dari Monitor Desktop hingga Layar Mobile berukuran kecil.
