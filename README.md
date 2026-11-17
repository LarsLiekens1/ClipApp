# ClipAPP

Een webapplicatie gebouwd met Flask voor het knippen, ondertitelen en bewerken van video's en audio.

## Mogelijkheden

- **Clipper**:
  - Download en preview video's via weblinks.
  - Kies specifieke fragmenten via een interactieve tijdlijn.
  - Automatische ondertiteling met faster-whisper.
  - Converteer naar 9:16 verticaal formaat met achtergrondblur en logo voor Shorts/Reels/TikTok.
- **Tijdlijn Editor**:
  - Voeg meerdere video- of audiobestanden toe.
  - Knip, splits, dupliceer en verplaats clips op een meersporige tijdlijn.
  - Exporteer als video (MP4) of puur audio (MP3).

## Vereisten

- Python 3.10 of nieuwer
- [FFmpeg](https://ffmpeg.org/download.html) geïnstalleerd en toegevoegd aan je systeem PATH.

## Installatie

1. Clone de repository:
   ```bash
   git clone https://github.com/jouw-gebruikersnaam/clipAPP.git
   cd clipAPP
   ```

2. Maak een virtuele omgeving aan en activeer deze:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. Installeer de vereiste packages:
   ```bash
   pip install -r requirements.txt
   ```

## Starten

Start de lokale ontwikkelserver:
```bash
python app.py
```

Open vervolgens je browser op `http://127.0.0.1:5050/`.

## Disclaimer & Fair Use

Deze software is ontwikkeld voor educatieve en persoonlijke doeleinden. Gebruikers zijn zelf verantwoordelijk voor het naleven van de toepasselijke wetgeving omtrent auteursrecht en de servicevoorwaarden van platforms waarvan media wordt verwerkt.
