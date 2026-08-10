# CyberGuard-ID — Product Requirements Document

## 1. Problem Statement

Kolom komentar YouTube dapat berisi ribuan komentar. Pemeriksaan manual sulit dilakukan secara cepat dan konsisten, terutama membedakan komentar normal, kritik wajar, bahasa kasar, penghinaan, ujaran kebencian, pelecehan seksual, dan ancaman. Cyberbullying harus dinilai melalui kombinasi konten, target, pengulangan, dan jumlah akun — bukan hanya satu komentar.

## 2. Goals

1. Mengambil komentar dari YouTube via API v3
2. Menyediakan alternatif unggah CSV
3. Membersihkan dan menganonimkan data
4. Mengklasifikasikan setiap komentar (IndoBERT)
5. Menampilkan confidence dan status verifikasi
6. Mendeteksi komentar serupa dan pola serangan berulang
7. Menghitung risk score transparan
8. Membentuk antrean human review
9. Menghasilkan dashboard dan laporan
10. Gemini opsional untuk narasi laporan agregat

## 3. Non-Goals

- Bukan alat vonis hukum
- Bukan alat diagnosis psikologis
- Bukan alat identifikasi identitas
- Bukan alat auto-delete/auto-report
- Bukan pengganti keputusan manusia

## 4. Actors

- **Primary:** Analis Pengendalian Ruang Digital / Media Monitoring
- **Supporting:** Koordinator, moderator kanal, OPD, petugas perlindungan anak

## 5. User Stories

- Sebagai analis, saya ingin memasukkan URL YouTube dan mendapatkan daftar komentar bermasalah secara otomatis
- Sebagai analis, saya ingin mengunggah CSV jika API tidak tersedia
- Sebagai analis, saya ingin melihat confidence dan risk level setiap komentar
- Sebagai analis, saya ingin melihat pola serangan berulang terhadap target yang sama
- Sebagai analis, saya ingin melakukan review manual dan mengubah kategori
- Sebagai analis, saya ingin mengunduh laporan lengkap

## 6. Requirements

### Functional
- Validasi URL YouTube (watch, youtu.be, shorts)
- Fetch komentar dan replies via API
- Anonimisasi author (salted SHA-256)
- Preprocessing teks (Unicode, slang, URL, mention)
- Klasifikasi 5 kategori C0-C4 (single-label multiclass)
- Confidence threshold dan C5 abstention
- Risk scoring (base + additional)
- Repetition detection (cosine similarity)
- Human review workflow
- Report generation (CSV, JSON, HTML)

### Non-Functional
- Satu perintah: `python run.py`
- Berjalan tanpa API key (CSV mode)
- Model lokal (tidak bergantung LLM)
- Privacy-first (anonimisasi, no auto-action)

## 7. Acceptance Criteria

Lihat bagian 29 dari master build prompt.

## 8. Risks & Limitations

- Model dilatih pada dataset terbatas
- Slang dan bahasa daerah tertentu mungkin tidak tercakup
- Sistem tidak menangkap konteks visual/video
- Confidence bukan ukuran bahaya
- Cyberbullying memerlukan verifikasi multi-faktor
