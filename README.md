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

**Maak clips van online video's of bewerk je eigen media op een tijdlijn.**

ClipAPP is een browserapp met twee onderdelen:

- **Clipper (URL):** laad een video, selecteer fragmenten en exporteer ze met optionele ondertitels en een verticaal formaat.
- **Tijdlijneditor:** knip en combineer lokale video- en audiobestanden en exporteer het resultaat.

De interface is beschikbaar in het Nederlands en Engels.

## Inhoud

- [Functies](#functies)
- [Snel starten](#snel-starten)
- [Clipper](#clipper)
- [Tijdlijneditor](#tijdlijneditor)
- [Video mailen](#video-mailen)
- [Privacy en bestanden](#privacy-en-bestanden)
- [Opdrachtregelhulpmiddelen](#opdrachtregelhulpmiddelen)
- [Ontwikkelen en testen](#ontwikkelen-en-testen)
- [Projectstructuur](#projectstructuur)
- [Problemen oplossen](#problemen-oplossen)
- [Licentie](#licentie)

## Functies

| Onderdeel | Wat je ermee kunt |
| --- | --- |
| Automatische TikToks | Kiest lokaal en gratis de beste momenten uit transcript, geluid en (bij YouTube) comments, met hook-caption, posttekst en hashtags; optioneel direct exporteren als 9:16. |
| Clipper | Fragmenten selecteren uit YouTube-video's en andere door `yt-dlp` ondersteunde videobronnen. |
| Commentanalyse | YouTube-commenttijdstempels vergelijken met een beschikbare kijkersheatmap. |
| Clipvoorstellen | Niet-overlappende fragmenten voorstellen rond activiteit in comments en heatmap. |
| Commentcaptions | Optioneel de best gewaardeerde timestamp-comment als tekstoverlay op YouTube-clips zetten. |
| Tijdlijneditor | Lokale video- en audiobestanden knippen, verplaatsen, trimmen en samenvoegen. |
| Export | Video exporteren als 9:16, 16:9, vierkant of in het formaat van de eerste videobron; optioneel met geblurde achtergrond of watermark. |

## Snel starten

### Vereisten

- Python 3.10 of hoger
- FFmpeg en `ffprobe`, beschikbaar via `PATH`
- Internetverbinding bij de eerste start om Python-pakketten te installeren; ook het Whisper-model wordt bij de eerste ondertitelgeneratie opgehaald

Controleer na de installatie van FFmpeg of beide opdrachten werken:

```text
ffmpeg -version
ffprobe -version
```

### Windows

1. Installeer Python en [FFmpeg](https://ffmpeg.org/download.html).
2. Clone de repository en open de map in PowerShell:

   ```powershell
   git clone https://github.com/LarsLiekens1/ClipApp.git
   cd ClipApp
   ```

3. Start de app:

   ```powershell
   python start.py
   ```

   Je kunt ook `ClipAPP.bat` starten.

### macOS of Linux

Installeer eerst Python en FFmpeg, clone daarna de repository en start de app:

```bash
git clone https://github.com/LarsLiekens1/ClipApp.git
cd ClipApp
python3 start.py
```

`start.py` maakt zo nodig een virtuele Python-omgeving, installeert de pakketten uit [`requirements.txt`](requirements.txt), controleert FFmpeg en opent de browser. De lokale app is beschikbaar op <http://127.0.0.1:5050>. Stop de server met `Ctrl+C` in de terminal.

### Docker en Hugging Face Spaces

De meegeleverde Dockerfile gebruikt poort `7860`. Bouw en start de container zo:

```bash
docker build -t clipapp .
docker run --rm -p 7860:7860 clipapp
```

Open daarna <http://127.0.0.1:7860>. `python app.py` gebruikt eveneens poort `7860` als `PORT` niet is ingesteld. `python app.py` is standaard alleen bereikbaar vanaf je eigen computer (`HOST=127.0.0.1`); de Docker-image zet `HOST=0.0.0.0`. Zie [Privacy en bestanden](#privacy-en-bestanden) voordat je hem via een netwerk bereikbaar maakt. De e-mailintegratie wordt alleen door de lokale startmethode ingeschakeld.

## Clipper

1. Open **Clipper (URL)** en plak een videolink, of klik op **Of kies een video van je computer** om een eigen MP4-, MOV-, MKV-, WebM- of M4V-bestand te gebruiken.
2. Laad de video. YouTube wordt in de pagina afgespeeld. Voor andere bronnen maakt de app een kleine preview om te kunnen zoeken en afspelen.
3. Stel start- en eindtijden in en voeg fragmenten toe, of analyseer een YouTube-video om fragmenten voor te laten stellen.
4. Controleer de selectie en kies eventuele exportopties.
5. Maak de clips en bekijk of download de resultaten. Tijdens het maken zie je in de browser welke clip en stap bezig is, met een voortgangsbalk en een knop **Annuleren**.

De beschikbare bronnen zijn afhankelijk van wat `yt-dlp` kan uitlezen en wat de videosite toestaat.

### Automatisch TikToks maken

Laad een video en klik bovenaan op **Maak TikToks**. Alles draait lokaal en is gratis; er is geen API-sleutel nodig.

1. De app meet de luidheid per seconde. Alleen als **Ondertitels maken** aanstaat, wordt ook de tekst van de hele video gebruikt; anders wordt Whisper niet geladen of gedownload. Bij YouTube-video's gebruikt de app dan eerst de ondertitels van YouTube zelf (handgemaakt of automatisch, in de gekozen taal of de taal van de video). Dat is veel sneller; alleen als die er niet zijn, transcribeert Whisper de video. Zet dit uit met **gebruik de ondertitels van YouTube zelf**. Het resultaat wordt per taak bewaard in `work/<taak>/transcript.json`, dus een tweede poging is direct klaar.
2. Met spraakherkenning begint elke mogelijke clip op een zinsbegin en eindigt hij op een zinseinde (standaard **5 clips van 20–60 seconden**). Zonder spraakherkenning kiest de app op luidheid, comments en heatmap, en komt de caption alleen uit comments. Per clip telt de app:
   - **hook**: begint de clip met een vraag, uitroep, getal of typische hook-woorden (“waarom”, “niemand”, “geheim”, “wait”, …)?
   - **energie**: is het geluid luider dan normaal in de video (lachen, roepen)?
   - **tempo** en **emotie**: wordt er snel gesproken, vallen er woorden als “haha” of “wow”?
   - **publiek**: comment-timestamps en de YouTube-heatmap, als je eerst de commentanalyse hebt gedraaid.
   - strafpunten voor lange stiltes en voor clips die midden in een gedachte beginnen (“en…”, “maar…”).
3. Per clip krijg je een **caption** (de sterkste hook-zin, of een populaire comment), een **posttekst met hashtags** uit de typische woorden van die clip, een score en de reden van de keuze. De captions kun je in de lijst aanpassen.
4. Met **Meteen exporteren** (standaard aan) worden de clips direct gemaakt met de opties die jij hebt aangevinkt (ondertitels, 9:16, blur, caption); de app verandert zelf niets aan je keuzes. Bij elke clip staat de posttekst met een kopieerknop en als `.txt`-download.

### Comments, heatmap en clipvoorstellen

De analysefunctie is bedoeld voor YouTube-video's. ClipAPP vraagt maximaal **1.000 comments** op en telt herkenbare tijdstempels in de commenttekst, zoals `1:23` en `1:02:03`. De tijdlijn wordt in intervallen ingedeeld; bij lange video's worden die intervallen groter.

Als YouTube een kijkersheatmap beschikbaar stelt, toont de app daarnaast een **relatieve heatmapscore** per interval. Dat is geen absoluut aantal kijkers. Sommige video's hebben geen heatmap, geen toegankelijke comments of onvoldoende gegevens; in dat geval kan de analyse beperkt zijn.

Bij een **afgelopen livestream** kun je ook **de live-chat analyseren** aanvinken. De app haalt dan de chat-replay op en telt per interval hoeveel berichten er werden gestuurd (oranje stippellijn in de grafiek en een extra kolom in de tabel). Drukke momenten in de chat tellen mee in de clipvoorstellen en in de TikTok-maker. Het ophalen van de chat kan bij lange streams enkele minuten duren.

Na de analyse kun je clipvoorstellen genereren:

- Standaard: **3 clips van 30 seconden**.
- Instelbaar: **1–5 clips** van **15, 30, 45 of 60 seconden**.
- Als zowel comments als heatmap beschikbaar zijn, tellen beide signalen even zwaar mee in de rangschikking. Zonder heatmap gebruikt de app alleen de commentactiviteit.
- Voorstellen overlappen elkaar niet. Je kunt ze vooraf bekijken en ongewenste voorstellen verwijderen. Voor een andere selectie kun je de start- en eindtijd handmatig instellen.

Een voorstel is geen garantie dat een fragment inhoudelijk interessant is; controleer de preview voordat je exporteert.

Na de commentanalyse kun je bij het clip-exporteren **Caption bovenin** inschakelen. Per clip gebruikt ClipAPP de best gewaardeerde comment die een timestamp in dat fragment noemt; timestamptekst wordt uit de overlay verwijderd. Dit is een commentselectie, geen AI-herschrijving. Je kunt de overlay bovenin, midden of onderin plaatsen. Voor een aparte bovenbalk boven de video kies je ook **Verticaal 9:16** en **Geblurde achtergrond**.

### Exportopties van de Clipper

- **Ondertitels:** optioneel, met automatische taalherkenning of Nederlands, Engels, Frans en Duits. De Whisper-modellen draaien lokaal; het gekozen model wordt bij het eerste gebruik gedownload. Kies bij **Nauwkeurigheid** tussen `tiny` (snelst) en `medium` (nauwkeurigst). Bij **Stijl** kies je **TikTok (woord voor woord)**: grote vette letters waarbij het woord dat gezegd wordt oplicht in een kleur naar keuze (optioneel in hoofdletters), of **Klassiek** (witte tekst). Heb je een NVIDIA-videokaart met CUDA, dan gebruikt Whisper die automatisch en is het vele malen sneller (`WHISPER_DEVICE=cpu` in `.env` zet dat uit).
- **Stiltes eruit knippen:** pauzes van meer dan ~0,6 seconde worden uit de clip geknipt (jump cuts), met een klein beetje marge zodat woorden niet worden afgekapt. De ondertitels schuiven automatisch mee.
- **Verticaal 9:16:** maak een formaat voor bijvoorbeeld Shorts of Reels.
- **Geblurde achtergrond:** vul de verticale beeldruimte met een vervaagde versie van de video.
- **Volg het gezicht:** in plaats van balken of blur wordt het beeld ingezoomd tot het het hele 9:16-scherm vult, met het gezicht in beeld. De app kijkt elke 2 seconden waar het gezicht staat (lokaal met OpenCV) en stuurt alleen bij als het duidelijk verschuift. Staat er geen duidelijk gezicht in, dan valt hij terug op blur of balken.
- **Logo:** voeg bij verticale clips een PNG-, JPG- of WebP-logo toe.
- Je gekozen opties (ook die van de TikTok-maker) worden in je browser onthouden voor de volgende keer.

## Tijdlijneditor

Open **Tijdlijn Editor** om lokale bestanden toe te voegen. De editor accepteert video- en audioformaten die FFmpeg kan lezen; veelgebruikte formaten zijn MP4, MOV, MKV, WebM, MP3, WAV, M4A, FLAC, OGG en Opus. Bij audiobestanden met een geluidsspoor kan de app een golfvorm tonen.

### Bewerken

- Sleep fragmenten op de tijdlijn om ze te verplaatsen.
- Sleep de randen om fragmenten bij te snijden.
- Gebruik de afspeelkop om een fragment te selecteren of te splitsen.
- Zoom in of uit om nauwkeuriger te werken.

| Sneltoets | Actie |
| --- | --- |
| Spatie | Afspelen of pauzeren |
| `S` | Splitsen bij de afspeelkop |
| `Delete` of `Backspace` | Geselecteerd fragment verwijderen |
| `D` | Fragment dupliceren |
| `Ctrl+Z` / `Ctrl+Y` | Ongedaan maken / opnieuw |

### Exportformaten

- **Automatisch:** gebruik het formaat van de eerste videobron.
- **Verticaal:** 9:16, 1080 × 1920.
- **Liggend:** 16:9, 1920 × 1080.
- **Vierkant:** 1080 × 1080.
- **Alleen audio:** exporteer als MP3.
- **Geblurde achtergrond:** vul het gekozen videoformaat met een vervaagde achtergrond.
- **Watermark:** plaats een afbeelding op de video; deze optie is beschikbaar voor video-export in 9:16.

## Video mailen

Video mailen is optioneel en werkt alleen met de lokale desktopstart via `python start.py` of `ClipAPP.bat`. Het gebruikt Google OAuth; ClipAPP vraagt niet om je Google-wachtwoord.

1. Maak een lokaal `.env`-bestand op basis van [`.env.example`](.env.example).
2. Vul `GMAIL_FROM` in met het Google-adres waarmee je wilt verzenden.
3. Maak in Google Cloud een OAuth-client van het type **Desktop-app** en schakel de Gmail API in. Bij een OAuth-app in testmodus moet je je Google-account als testgebruiker toevoegen.
4. Plaats het OAuth-clientbestand standaard als `google_oauth_client.json` in de map `.clipapp` in je thuismap. Je kunt het pad aanpassen met `GOOGLE_OAUTH_CLIENT_FILE`.
5. Start ClipAPP lokaal en kies de e-mailoptie bij een geëxporteerde video. Bij het eerste gebruik opent Google de OAuth-toestemming.

Video's tot en met **17 MiB** worden als bijlage verstuurd. Voor grotere MP4-bestanden gebruikt ClipAPP Google Drive en deelt het bestand privé met het opgegeven e-mailadres; daarvoor moet ook de Drive API ingeschakeld zijn. De OAuth-tokens worden lokaal in de map `.clipapp` in je thuismap bewaard. Deel of commit je `.env`, OAuth-bestand of tokens niet.

## Privacy en bestanden

- Videoverwerking, cliprendering en ondertitelgeneratie gebeuren lokaal met FFmpeg en Whisper.
- De app maakt wel netwerkverbindingen: `yt-dlp` haalt videogegevens, comments of videofragmenten bij de bron op; de YouTube-speler wordt in de browser geladen. De interface gebruikt ook Google Fonts.
- Bestanden en resultaten worden per taak opgeslagen in `work/` in de projectmap. Bij het starten verwijdert de app taakmappen waar al **7 dagen** niets aan veranderd is. Download dus wat je wilt bewaren. Stel dit in met `CLIPAPP_KEEP_DAYS` in `.env` (`0` = nooit automatisch verwijderen).
- In Docker staat `work/` in de container. Met `docker run --rm` verdwijnen die bestanden wanneer de container wordt verwijderd, tenzij je een volume voor `work/` koppelt.
- E-mailen verstuurt het gekozen bestand via Google. Bestanden boven 17 MiB worden via Google Drive privé gedeeld met de ontvanger.
- Zet `CLIPAPP_PASSWORD` in `.env` (of als omgevingsvariabele in Docker) zodra de server via een netwerk bereikbaar is; de browser vraagt dan om dat wachtwoord. Zonder wachtwoord kan iedereen die de server bereikt hem gebruiken. Verwerk er ook dan geen gevoelige bestanden mee.

## Opdrachtregelhulpmiddelen

Naast de webapp zijn er twee losse scripts:

- `heatmap.py` haalt heatmapgegevens voor een video op en toont drukke intervallen, als die gegevens beschikbaar zijn.
- `chatpieken.py` zoekt drukke intervallen in de chatreplay van een livestream. Dit is niet hetzelfde als commentanalyse.

De scripts gebruiken de `yt-dlp`-opdracht. Activeer daarom eerst de virtuele omgeving die `start.py` heeft gemaakt:

```powershell
.\.venv\Scripts\Activate.ps1
python heatmap.py "https://www.youtube.com/watch?v=VIDEO_ID"
python chatpieken.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Op macOS of Linux:

```bash
source .venv/bin/activate
python heatmap.py "https://www.youtube.com/watch?v=VIDEO_ID"
python chatpieken.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Let op:** `chatpieken.py` verwijdert bestaande `livechat*.live_chat.json`-bestanden in de huidige werkmap voordat het een nieuwe chatreplay ophaalt. Voer het script uit in een aparte map als je zulke bestanden wilt bewaren.

## Ontwikkelen en testen

Na de eerste start kun je de tests uitvoeren met:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Of, op macOS en Linux:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## Projectstructuur

| Bestand of map | Doel |
| --- | --- |
| `app.py` | Flask-server, API-routes en media-export |
| `index.html`, `static/clipper.*` | Interface (HTML, CSS, JS) voor de URL-clipper, commentanalyse en TikTok-maker |
| `editor.html`, `static/editor.*` | Interface (HTML, CSS, JS) voor de tijdlijneditor |
| `face_crop.py` | Gezichtsdetectie voor de 9:16-crop die het gezicht volgt |
| `auto_clips.py` | Automatische keuze van TikTok-momenten, captions en hashtags |
| `video_analysis.py` | Verwerking van commenttijdstempels en heatmapintervallen |
| `delivery.py` | Optionele Gmail- en Drive-integratie |
| `start.py` | Lokale start, virtuele omgeving en controles |
| `heatmap.py`, `chatpieken.py` | Losse opdrachtregelhulpmiddelen (de live-chatanalyse zit nu ook in de app) |
| `tests/` | Geautomatiseerde tests |
| `work/` | Tijdelijke taakbestanden en exports |

## Problemen oplossen

### FFmpeg of ffprobe wordt niet gevonden

Installeer FFmpeg, voeg de map met `ffmpeg` en `ffprobe` toe aan `PATH` en open daarna een nieuwe terminal. Controleer beide opdrachten met `-version`.

### De app start niet op poort 5050

Controleer of er al een ClipAPP-server draait en stop die met `Ctrl+C` in de bijbehorende terminal. De lokale startmethode gebruikt poort `5050`; de Docker-/`app.py`-methode gebruikt standaard `7860`.

### Comments of heatmap ontbreken

Comments kunnen uitgeschakeld, beperkt of niet beschikbaar zijn. Een heatmap is niet voor elke video beschikbaar. De commentgrafiek kan daarom wel resultaten tonen terwijl de heatmap ontbreekt.

### Ondertitels genereren duurt lang

De eerste keer wordt het Whisper-model gedownload. De verwerking draait op de lokale computer; een groter model kan nauwkeuriger maar ook trager zijn.

### E-mailen is niet beschikbaar

Start de app met `python start.py` of `ClipAPP.bat` en controleer de Google OAuth-configuratie. De e-mailfunctie is standaard niet ingeschakeld bij `python app.py` of in Docker.

## Licentie

ClipAPP wordt uitgebracht onder de MIT-licentie. Zie [`LICENSE`](LICENSE) en [`THIRD_PARTY.md`](THIRD_PARTY.md) voor de licentie- en bibliotheekinformatie.
