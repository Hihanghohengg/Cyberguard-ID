# CyberGuard-ID — User Guide

## 1. Setup

### Prerequisites
- Python 3.10 atau lebih baru
- Koneksi internet (untuk install dependensi pertama kali)

### Instalasi
```bash
git clone <repository-url>
cd cyberguard-id
copy .env.example .env
```

### API Keys (Opsional)
Edit file `.env`:

```env
# Untuk mengambil komentar dari YouTube (opsional)
YOUTUBE_API_KEY=your-youtube-api-key-here

# Untuk narasi laporan AI (opsional)
GEMINI_API_KEY=your-gemini-api-key-here

# Ubah ke nilai acak (Hanya digunakan khusus untuk anonimisasi data pada analisis CSV)
ANONYMIZATION_SALT=ganti-dengan-nilai-acak
```

**Cara mendapatkan YouTube API Key:**
1. Buka [Google Cloud Console](https://console.cloud.google.com)
2. Buat project baru atau pilih yang sudah ada
3. Aktifkan YouTube Data API v3
4. Buat API Key di bagian Credentials

**Tanpa API key**, aplikasi tetap dapat digunakan dalam mode CSV.

### Menjalankan
```bash
python run.py
```

Aplikasi akan otomatis:
- Membuat virtual environment
- Menginstall dependensi
- Membuat database
- Membuka browser

## 2. Training Model
```bash
# Letakkan dataset di data/raw/ (CSV dengan kolom: text, label)
python run.py --train
```

Jika tidak ada dataset, sample data akan digunakan untuk demo.

## 3. Analisis YouTube

1. Buka halaman **Analisis Baru**
2. Beri nama analisis
3. Pilih "YouTube URL"
4. Masukkan URL video
5. Atur maksimum komentar
6. Klik **Mulai Analisis**

### Format URL yang Didukung
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`

## 4. Analisis CSV

1. Buka halaman **Analisis Baru**
2. Beri nama analisis
3. Pilih "Upload CSV"
4. Unggah file CSV dengan kolom `text`

### Kolom Opsional
- `author` — Nama penulis (akan dianonimkan berdasarkan ANONYMIZATION_SALT)
- `published_at` — Timestamp
- `is_reply` — 1 jika reply
- `parent_id` — ID komentar induk
- `like_count` — Jumlah like

## 5. Review Manual

1. Buka halaman **Review Manual**
2. Pilih analisis
3. Filter berdasarkan prioritas
4. Untuk setiap komentar, pilih tindakan:
   - **Setujui Hasil AI** — Konfirmasi klasifikasi model
   - **Ubah Kategori** — Ganti dengan kategori yang benar
   - **Tandai False Positive** — Tandai sebagai salah klasifikasi
   - **Pertahankan** — Tidak ada tindakan
   - **Rekomendasikan Hide** — Sarankan penyembunyian
   - **Rekomendasikan Report** — Sarankan pelaporan

## 6. Export

Buka halaman **Laporan** untuk:
- **CSV Semua Komentar** — Seluruh data prediksi
- **CSV Prioritas** — Hanya Critical/High/Mandatory/Uncertain
- **JSON** — Data lengkap terstruktur
- **HTML** — Laporan print-friendly

## 7. Troubleshooting

| Masalah | Solusi |
|---------|--------|
| App tidak terbuka | Cek Python version ≥ 3.10 |
| YouTube error | Periksa YOUTUBE_API_KEY di .env |
| Quota habis | Tunggu 24 jam atau gunakan CSV |
| Model not found | Jalankan `python run.py --train` |
| CSV error | Pastikan ada kolom `text` |
| Import error | Hapus `.venv` dan jalankan ulang `python run.py` |
