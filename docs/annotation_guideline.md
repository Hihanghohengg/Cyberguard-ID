# CyberGuard-ID — Annotation Guideline

## 1. Definisi Kategori

### C0 — Normal/Konstruktif
Komentar biasa, apresiasi, pertanyaan, informasi, diskusi, atau tanggapan yang tidak menyerang.

**Contoh Positif:**
- "Terima kasih informasinya."
- "Acara dimulai jam berapa?"
- "Videonya membantu."

**Contoh Negatif (bukan C0):**
- "Kontennya sampah semua" → C2
- "Muka lo jelek" → C3

### C1 — Kritik Wajar
Kritik terhadap isi, kebijakan, layanan, kualitas, atau penyajian tanpa menyerang martabat individu.

**Contoh Positif:**
- "Penjelasannya terlalu cepat."
- "Pelayanannya masih lambat."

**Contoh Negatif:**
- "Lo bodoh makanya ga ngerti" → C3 (menyerang individu)

### C2 — Bahasa Kasar
Makian atau profanity tanpa ancaman, pelecehan seksual, kebencian identitas, atau serangan personal yang dominan.

**Contoh Positif:**
- "Anjir apa banget dah."
- "Kontennya sampah."

**Contoh Negatif:**
- "Muka lo jelek, goblok" → C3 (serangan personal dominan)

### C3 — Penghinaan/Harassment Personal
Serangan terhadap individu, kemampuan, fisik, penampilan, martabat, atau atribut personal. Body shaming masuk di sini.

**Contoh Positif:**
- "Muka lo jelek."
- "Dasar bodoh."
- "Badan gendut gitu masih pede."

**Contoh Negatif:**
- "Orang suku itu rendahan" → C4 (menyerang identitas kelompok)

### C4 — Ujaran Kebencian
Serangan atau penghinaan terhadap kelompok atau identitas yang dilindungi (SARA, gender, disabilitas).

**Contoh Positif:**
- "Dasar orang kafir."
- "Orang suku itu emang rendahan."

### C5 — Pelecehan Seksual
Komentar seksual tidak pantas, objektifikasi, ajakan seksual, penghinaan seksual.

**Contoh Positif:**
- "Kirim foto tanpa baju dong."
- "Badannya enak buat di itu in."

### C6 — Ancaman/Intimidasi
Ancaman kekerasan, intimidasi, ajakan menyerang, ancaman doxxing.

**Contoh Positif:**
- "Gue bunuh lo kalau ketemu."
- "Ayo kita keroyok dia."

## 2. Hierarchy Priority

Jika komentar mengandung beberapa unsur, pilih kategori tertinggi:

```
C6 > C5 > C4 > C3 > C2 > C1 > C0
```

**Contoh:** "Dasar goblok, gue akan cari dan hajar lo" → **C6** (ancaman dominan)

## 3. Aturan Ambigu

- Makian umum tanpa target spesifik → C2
- Makian + serangan personal → C3
- Kritik + makian ringan → Lihat apakah serangan personal dominan
- Sarkasme/ironi → Label berdasarkan dampak potensial, bukan niat
- Bahasa campur (Inggris-Indonesia) → Tetap label berdasarkan konten

## 4. Inter-Annotator Process

1. Dua annotator melabel secara independen
2. Hitung agreement (Cohen's Kappa)
3. Diskusi resolusi untuk disagreement
4. Target Kappa ≥ 0.70
5. Adjudikator untuk kasus yang tidak terselesaikan
