# Academic Dataset Provenance & Ingestion Report — CyberGuard-ID

**Audit Date**: 2026-08-10
**Standard**: Minimum 1,000 authentic human samples, verified academic provenance, zero synthetic AI generation, zero duplication.

---

## 1. Verified Primary Academic Sources

| Source ID | Paper Title | Authors & Year | Venue / DOI | Repository | Original Hash (SHA-256) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ibrohim_budi_2019** | *Multi-label Hate Speech and Abusive Language Detection in Indonesian Twitter* | Muhammad Okky Ibrohim & Indra Budi (2019) | ACL ALW3<br>DOI: [10.18653/v1/W19-3515](https://doi.org/10.18653/v1/W19-3515) | [GitHub](https://github.com/okkyibrohim/id-multi-label-hate-speech-and-abusive-language-detection) | `44c04e31ad4b7ee4a95f1884...` |
| **alfina_et_al_2017** | *Hate Speech Detection in the Indonesian Language on Social Media* | Ika Alfina, Rio Mulia, M. Ivan Fanany, Yudo Ekanata (2017) | IEEE ICITACEE<br>DOI: [10.1109/ICITACEE.2017.8257690](https://doi.org/10.1109/ICITACEE.2017.8257690) | [GitHub](https://github.com/ialfina/id-hatespeech-detection) | `4ee1d9cc1f1fdd27fb429820...` |
| **indonlu_smsa_2020** | *IndoNLU: Benchmark and Resources for Evaluating Indonesian Natural Language Understanding* | Bryan Wilie, Karissa Vincentio, Genta Indra Winata, et al. (2020) | AACL-IJCNLP<br>DOI: [10.18653/v1/2020.aacl-main.85](https://doi.org/10.18653/v1/2020.aacl-main.85) | [GitHub](https://github.com/indobenchmark/indonlu) | `50f38ceed9b31521bf1581e1...` |

---

## 2. Taxonomy Mapping (C0–C4)
We map the Ibrohim & Budi dataset to the C0-C4 taxonomy based on explicit combinations of `Abusive` and `HS_*` annotations:

1. **C0 (`normal`)**: Normal comments with no abusive or hate speech flags (`HS == 0 & Abusive == 0`).
2. **C1 (`abusive`)**: Profane/abusive language but not targeted hate speech (`Abusive == 1 & HS == 0`).
3. **C2 (`hate_speech_weak`)**: Hate speech categorized as Weak (`HS_Weak == 1`).
4. **C3 (`hate_speech_moderate`)**: Hate speech categorized as Moderate (`HS_Moderate == 1`).
5. **C4 (`hate_speech_strong`)**: Hate speech categorized as Strong (`HS_Strong == 1`).

---

## 3. Deprecation of Previous Benchmark

The preliminary 185-sample pilot dataset is marked as **UNVERIFIED / DEPRECATED** and has been completely replaced by this verified multi-source corpus of $\ge 1,400$ samples.
