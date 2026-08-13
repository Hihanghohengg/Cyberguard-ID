# Dataset Sample — CyberGuard-ID

Folder ini menyimpan **data sampel kecil** yang dapat digunakan untuk:
- Testing fungsionalitas aplikasi tanpa dataset penuh
- Demo dan pengujian pipeline secara cepat
- Validasi format input sebelum memproses dataset besar

## File Sample

Tempatkan file `sample.csv` di sini dengan beberapa baris representatif (minimal 5–10 baris per kelas).

## Format

Sama dengan `data/processed/` — kolom `text` dan `label`:

```csv
text,label
"Terima kasih, videonya sangat informatif dan bermanfaat!",normal
"Konten yang bagus, terus berkarya kak!",normal
"Wkwk najis banget sih videonya",abusive
"Dasar bego, ga bisa kerja dengan bener",abusive
"Orang-orang kayak gitu emang pantas dihina",hate_speech_weak
"Ga usah hidup di negara ini kalau ga bisa menghargai",hate_speech_moderate
"Bunuh aja semuanya, nyebelin banget!",hate_speech_strong
```

## Penggunaan

Sample data dapat diupload langsung via fitur **CSV Upload** di dashboard CyberGuard-ID:

1. Jalankan: `python run.py`
2. Buka: http://localhost:8001
3. Pilih mode "Upload CSV"
4. Upload file `sample.csv` dari folder ini

## Catatan

- Data sample **tidak mengandung data nyata pengguna** — hanya data dummy/ilustrasi.
- Untuk evaluasi model yang valid, gunakan `data/processed/test.csv` (held-out test set).
