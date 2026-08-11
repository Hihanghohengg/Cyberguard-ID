# CyberGuard-ID — Model Card

## Model Details
- **Name:** IndoBERT (`indobenchmark/indobert-base-p1`)
- **Version:** 1.0.0
- **Type:** Single-label multiclass text classifier
- **Framework:** Transformers (HuggingFace) / PyTorch
- **Architecture:** IndoBERT Base (Sequence Classification)

## Intended Use
- Skrining dan prioritisasi komentar YouTube berbahasa Indonesia
- Alat bantu moderasi untuk analis
- Bukan pengganti keputusan manusia

## Out-of-Scope Use
- Vonis hukum atau tuduhan
- Diagnosis psikologis
- Identifikasi identitas asli
- Tindakan moderasi otomatis
- Bahasa selain Bahasa Indonesia
- Platform selain YouTube (Lihat batasan metodologis)

## Training Data
- Bahasa Indonesia bersumber dari Twitter/X (Ibrohim & Budi 2019)
- 5 kategori: C0 Normal, C1 Abusive, C2 Hate Speech Weak, C3 Hate Speech Moderate, C4 Hate Speech Strong
- Stratified train/val/test split (9.053 / 1.940 / 1.941)
- Duplikasi dihapus sebelum split

## Metrics
- **Primary:** Macro F1, Recall kelas high-risk
- **Additional:** Accuracy, Macro Precision, Macro Recall, Weighted F1
- **Per-class:** Precision, Recall, F1, Support untuk setiap kategori

## Limitations
1. Model dilatih pada dataset terbatas dan mungkin tidak menangkap seluruh variasi bahasa Indonesia
2. Slang daerah, bahasa gaul baru, atau code-switching mungkin tidak tercakup
3. Konteks visual dan nada bicara tidak dapat dianalisis dari teks
4. Sarkasme dan ironi sulit dideteksi
5. Confidence bukan ukuran bahaya — confidence rendah pada ancaman tetap berbahaya
6. Model mungkin bias terhadap pola dalam training data

## Ethical Considerations
- Privasi: username dianonimkan, raw text tidak dikirim ke API eksternal
- Bias: model mungkin underperform pada dialek tertentu
- Transparansi: confidence, margin, dan risk score selalu ditampilkan
- Human-in-the-loop: semua temuan memerlukan verifikasi manusia
- Tidak ada tindakan otomatis: sistem tidak menghapus atau melaporkan komentar

## Recommendations
- Gunakan dataset yang lebih besar dan beragam untuk training yang lebih baik
- Lakukan evaluasi berkala terhadap performa model
- Update slang dictionary secara rutin
- Libatkan ahli bahasa dan moderasi dalam evaluasi
