# Externe Bibliotheken & Licenties (Third Party Notices)

Dit project (**ClipAPP**) maakt gebruik van open-source bibliotheken en externe tools. Dit document bevat een overzicht van deze componenten en hun respectievelijke licenties.

---

## 1. Python Bibliotheken & Dependencies

| Bibliotheek | Doel | Licentie | Broncode / Info |
| :--- | :--- | :--- | :--- |
| **Flask** | Web framework & API routing | BSD 3-Clause License | [Pallets Projects](https://github.com/pallets/flask) |
| **yt-dlp** | Metadata & video-extractie | The Unlicense (Public Domain) | [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp) |
| **faster-whisper** | Lokale AI spraakherkenning | MIT License | [SYSTRAN](https://github.com/SYSTRAN/faster-whisper) |
| **CTranslate2** | Fast inference engine voor Whisper | MIT License | [OpenNMT](https://github.com/OpenNMT/CTranslate2) |
| **NumPy** | Audio buffer verwerking | BSD 3-Clause License | [NumPy Developers](https://numpy.org/) |

---

## 2. AI Modellen & Gewichten

- **OpenAI Whisper Models**: De modelgewichten vallen onder de **MIT Licentie** van OpenAI.
- **Opslagbeleid**: Modelbestanden (`.bin`, `.onnx`, `.pt`) worden **niet** opgenomen in deze repository. Bij de eerste uitvoering worden de benodigde modellen automatisch gedownload en gecachet door `faster-whisper` via de Hugging Face Hub.

---

## 3. Externe Systeemtools (Niet gebundeld)

- **FFmpeg & ffprobe**:
  - **Licentie**: LGPL v2.1+ / GPL v3.0+ (afhankelijk van de gebruikte build).
  - **Integratiewijze**: FFmpeg en ffprobe worden **niet** meegeleverd in deze repository. ClipAPP roept FFmpeg uitsluitend aan als een extern CLI-proces via het besturingssysteem (`subprocess`). Gebruikers dienen FFmpeg zelfstandig te installeren volgens de toepasselijke licentievoorwaarden.

---

## 4. Typografie & Grafische Componenten

- **Plus Jakarta Sans**: Beschikbaar onder de [SIL Open Font License 1.1](https://scripts.sil.org/OFL) (Google Fonts).
- **JetBrains Mono**: Beschikbaar onder de [SIL Open Font License 1.1](https://scripts.sil.org/OFL) (JetBrains).
- **Inline SVG Iconen**: Vrije en publieke iconen (Material & Feather Icons).

---

## 5. Veiligheids- & Privacyrichtlijnen van deze Repository

1. **Geen persoonlijke of auteursrechtelijk beschermde media**: De `work/` map, geüploade logo's en gedownloade videoclips zijn opgenomen in `.gitignore` en worden nooit gecommit.
2. **Geen geheimen of tokens**: Er worden geen cookies (`cookies.txt`), API-sleutels of authenticatietokens bewaard of gecommit.
3. **Lokale verwerking**: Alle audio- en videoverwerking vindt 100% lokaal plaats op de machine van de gebruiker. Er worden geen audiostreams of beelden verzonden naar externe cloud-APIs.
