---
title: ClipAPP
emoji: 🎬
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# ClipAPP

Een complete, privacy-vriendelijke video clipper en tijdlijn-editor gebouwd met Python Flask, FFmpeg, yt-dlp en faster-whisper.

---

## Systeemarchitectuur & Visuele Schema's

ClipAPP bestaat uit twee kernpipelines: de **Clipper Pipeline** (voor webvideo's) en de **Tijdlijn Editor Pipeline** (voor lokale mediabestanden).

### 1. Overzicht Architectuur

```mermaid
graph TD
    Client["💻 Webbrowser (Frontend GUI)"]
    Server["🐍 Flask Backend (app.py)"]
    Storage["📁 Lokale Opslag (work/{job_id}/)"]
    
    YTDLP["📥 yt-dlp (Extractor & Trimmer)"]
    Whisper["🤖 faster-whisper (AI Spraakmodel)"]
    FFmpeg["🎬 FFmpeg & ffprobe (Video Engine)"]

    Client <-->|"REST API & Stream /media/"| Server
    Server <-->|"Sessie-bestanden & metadata"| Storage
    Server -->|"CLI Commando's"| YTDLP
    Server -->|"In-Memory 16kHz Audio"| Whisper
    Server -->|"Filtergraphs & Concat"| FFmpeg
```

---

### 2. Clipper Pipeline (Weblink naar Shorts / Clips)

Dit schema toont hoe een externe video wordt geanalyseerd, doelgericht in fragmenten wordt opgehaald, door Whisper van ondertitels wordt voorzien en naar 9:16 verticaal formaat wordt geconverteerd:

```mermaid
flowchart TD
    A["🌐 Gebruiker voert URL in"] --> B["🐍 POST /api/load"]
    B --> C{"Welk platform?"}
    
    C -->|"YouTube"| D["▶️ YouTube IFrame Embed (Direct afspelen in browser)"]
    C -->|"Overige sites"| E["📥 yt-dlp maakt lage resolutie 360p preview"]
    
    D --> F["⏱️ Gebruiker markeert fragmenten (Start & Einde)"]
    E --> F
    
    F --> G["🚀 POST /api/render"]
    
    subgraph Processing ["⚙️ Verwerking per segment (work/{job_id}/)"]
        H["1. yt-dlp --download-sections (Alleen fragment in 1080p ophalen)"]
        H --> I{"Ondertitels gewenst?"}
        
        I -->|"Ja"| J["FFmpeg exporteert 16kHz WAV"]
        J --> K["🤖 faster-whisper genereert woord-timestamps"]
        K --> L["Schrijf gestylde .ass en .srt bestanden"]
        I -->|"Nee"| M["Geen ondertitels"]
        
        L --> N{"9:16 Verticaal?"}
        M --> N
        
        N -->|"Ja + Blur"| O["FFmpeg split -> scale/boxblur achtergrond + overlay"]
        N -->|"Ja + Zwart"| P["FFmpeg pad naar 1080x1920 met zwarte balken"]
        N -->|"Origineel"| Q["Originele beeldverhouding behouden"]
        
        O --> R{"Logo meegeleverd?"}
        P --> R
        Q --> S["FFmpeg x264/AAC definitieve render"]
        
        R -->|"Ja"| T["FFmpeg overlay logo onder ondertitels"]
        R -->|"Nee"| S
        T --> S
    end
    
    G --> Processing
    S --> U["📦 Output: clip_01.mp4 + clip_01.srt"]
    U --> V["💾 Download & preview in browser"]
```

---

### 3. Tijdlijn Editor Pipeline (Lokale Bestanden naar Geheel)

Dit schema toont hoe lokale video- en audiobestanden worden geüpload, op een interactieve tijdlijn worden gemanipuleerd en naadloos worden samengevoegd:

```mermaid
flowchart TD
    A1["📁 Gebruiker sleept video- of audiobestanden"] --> B1["🐍 POST /api/editor/upload"]
    B1 --> C1["🔍 ffprobe inspecteert streams, resolutie, rotatie & duur"]
    C1 --> D1["Opslaan in work/{job_id}/ & sources.json"]
    
    D1 --> E1["🎛️ Interactieve browser tijdlijn"]
    E1 --> E2["Knippen (S) • Wissen (Del) • Dupliceren (D) • Trimmen • Verslepen"]
    
    E2 --> F1["🚀 POST /api/editor/export met geordende clips"]
    
    subgraph Montage ["🎞️ Montage Pipeline (work/{job_id}/ed_tmp/)"]
        G1["Knip elk stuk met -ss en -t uit bronbestand"]
        G1 --> H1["Normaliseer resolutie, SAR en framerate (30fps)"]
        H1 --> I1["Tijdelijke segmenten seg_001.mkv aanmaken"]
        I1 --> J1["FFmpeg concat demuxer voegt alle stukken samen"]
    end
    
    F1 --> Montage
    J1 --> K1["📦 Eindresultaat: bewerkt_HHMMSS.mp4 of .mp3"]
    K1 --> L1["💾 Direct afspelen & downloaden"]
```

---

## Gebruikte Technologieën

| Component | Tool / Bibliotheek | Rol & Doel |
| :--- | :--- | :--- |
| **Webserver** | [Flask](https://flask.palletsprojects.com/) | Lokale server, API-routing en taakisolatie per sessie (`work/{job_id}/`). |
| **Media Downloader** | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Snel ophalen van metadata en doelgerichte fragment-extractie in 1080p. |
| **AI Ondertiteling** | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | CTranslate2 Whisper spraakherkenning met woord-voor-woord timestamps (100% lokaal). |
| **Video & Audio Engine** | [FFmpeg](https://ffmpeg.org/) & `ffprobe` | Transcoding, filtergraphs (boxblur, crop, scale), logo-overlays en concat montage. |
| **Frontend GUI** | HTML5 / Vanilla JS & CSS | Donkere Pro-Studio interface met multitrack-tijdlijn zonder zware frameworks. |

---

## Privacy & Lokale Verwerking

- **100% Lokaal**: Zowel spraakherkenning (`faster-whisper`) als videoverwerking (`ffmpeg`) draaien volledig op je eigen processor / videokaart.
- **Geen externe cloud uploads**: Er worden geen persoonlijke opnames of video's naar servers van derden verstuurd.

---

## Vereisten

- Python 3.10 of nieuwer
- [FFmpeg](https://ffmpeg.org/download.html) geïnstalleerd en bereikbaar via je systeem PATH.

---

## Installatie & Gebruik

1. **Clone de repository**:
   ```bash
   git clone https://github.com/jouw-gebruikersnaam/clipAPP.git
   cd clipAPP
   ```

2. **Maak een virtuele omgeving aan en activeer deze**:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Installeer de benodigde packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start de app**:
   ```bash
   python app.py
   ```

5. Open je browser op:
   - **Clipper**: `http://127.0.0.1:5050/`
   - **Tijdlijn Editor**: `http://127.0.0.1:5050/editor`

---

## Disclaimer & Fair Use

Deze software is uitsluitend ontwikkeld voor educatieve en persoonlijke doeleinden, voor eigen video's of voor media waarvan je toestemming hebt van de rechthebbende. De maker is niet aansprakelijk voor eventuele schendingen van auteursrechten of gebruiksvoorwaarden van externe platforms.

---

## Licentie & Externe Bibliotheken

Dit project is beschikbaar onder de [MIT Licentie](LICENSE).

Voor een volledig overzicht van alle gebruikte open-source bibliotheken, fonts en tools inclusief hun respectievelijke licenties (zoals Flask, yt-dlp, faster-whisper en FFmpeg), zie het document **[THIRD_PARTY.md](THIRD_PARTY.md)**.
