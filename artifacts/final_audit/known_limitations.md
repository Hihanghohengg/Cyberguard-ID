# Known Limitations & Boundary Constraints — CyberGuard-ID

Dokumen ini mendokumentasikan batasan teknis, asumsi arsitektural, dan limitasi operasional yang teridentifikasi selama pelaksanaan Final Audit pada sistem CyberGuard-ID.

---

## 1. Batasan Dataset & Korpus Pelatihan
- **Ukuran Korpus**: Korpus acuan saat ini terdiri dari 1.540 data teranotasi seimbang (220 sampel per kelas C0–C6) yang dihimpun dari 3 repositori akademik (Ibrohim & Budi 2019, Alfina et al. 2017, IndoNLU SmSA 2020). Meskipun memenuhi standar minimum akademik ($\ge 1.000$ sampel) dan bebas dari data leakage maupun duplikasi, ukuran korpus ini merupakan *curated research benchmark* untuk validasi pipeline, bukan korpus berskala industri raksasa (ratusan ribu data).
- **Ragam Bahasa & Dialek**: Korpus berfokus pada Bahasa Indonesia informal, slang digital populer, dan singkatan umum (rasio marker slang 59.3%). Ragam bahasa daerah (Jawa, Sunda, Minang, dll.) atau slang komunitas baru/sub-budaya digital mungkin belum terwakili secara mendalam.
- **Sarkasme Multilapis**: Komentar sarkastik halus tanpa leksikon negatif eksplisit masih memiliki probabilitas misklasifikasi sebagai `kritik_wajar` atau `normal_konstruktif`.

---

## 2. Batasan Model Machine Learning
- **Arsitektur Model (TF-IDF + Calibrated Linear SVM)**:
  - Model menggunakan n-gram karakter (3–5) & kata (1–2) dengan pembobotan TF-IDF yang sangat efisien dan berbobot ringan (~1.5 MB).
  - Model linier tidak memiliki mekanisme *self-attention* transformer mendalam untuk membedakan negasi ganda yang kompleks atau pembalikan konteks kalimat yang sangat panjang.
- **Tingkat Abstensi & Human-in-the-Loop**:
  - Dengan penerapan ambang batas kalibrasi optimal ($\tau_{\text{review}} = 0.45$, $\text{margin} = 0.06$), model mengarahkan ~21.55% sampel ambigu ke kelas C7 (Abstensi / Review Manusia).
  - Hal ini meningkatkan akurasi otomatis menjadi **89.01%**, namun memerlukan moderator manusia untuk memvalidasi antrean review manual.
- **Diferensiasi Bahasa Kasar vs Pelecehan Personal**:
  - Irisan leksikal antara makian umum (`bahasa_kasar`) dan hinaan fisik/karakter (`personal_harassment`) menimbulkan trade-off presisi/recall pada kedua kelas tersebut.

---

## 3. Batasan Integrasi & Eksternalitas
- **YouTube Data API v3**:
  - Memerlukan `YOUTUBE_API_KEY` yang valid dengan kuota harian standar Google Cloud (10.000 unit kuota/hari).
  - Status audit integrasi langsung berstatus `NOT VERIFIED` jika API key belum diisi pada file `.env`. Sistem secara *graceful* mengalihkan mode input ke unggah berkas CSV secara lokal.
- **LLM Synthesis (Google Gemini)**:
  - Fitur ringkasan naratif AI memerlukan `GEMINI_API_KEY`.
  - Status audit integrasi langsung berstatus `NOT VERIFIED` jika API key belum diisi. Sistem menggunakan `LocalReportGenerator` berbasis templat deterministik yang aman dan bebas halusinasi.

---

## 4. Batasan Infrastruktur & Skalabilitas
- **Penyimpanan SQLite**:
  - SQLite lokal sangat optimal untuk penggunaan desktop, server lokal, atau demonstrasi portabel tanpa ketergantungan server database eksternal.
  - Untuk lingkungan produksi multi-kontainer atau multi-moderator terdistribusi berskala besar (>1.000 komentar/detik konkuren), sistem direkomendasikan untuk dimigrasikan ke PostgreSQL/Cloud SQL.
- **Enkripsi & Salt Anonymization**:
  - Pengacakan identitas pengguna (`author_hash`) menggunakan SHA-256 tersensitisasi dengan `ANONYMIZATION_SALT`. Sistem memperingatkan pengguna jika salt default belum diubah di file `.env`.
