import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
import wave
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file, send_from_directory

if getattr(sys, "frozen", False):
    BASE = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)).resolve()
    APP_DIR = Path(sys.executable).parent.resolve()
else:
    BASE = Path(__file__).parent.resolve()
    APP_DIR = BASE

bin_dir = BASE / "bin"
app_bin = APP_DIR / "bin"
os.environ["PATH"] = f"{bin_dir};{app_bin};{BASE};{APP_DIR};{os.environ.get('PATH', '')}"
WORK = APP_DIR / "work"          # hier komen de clips en bewerkte bestanden (per job een map)
WORK.mkdir(exist_ok=True)

# tiny / base / small / medium - groter = nauwkeuriger maar trager op CPU
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")

# Ondertitels komen in korte stukjes in beeld. Pas deze twee aan naar smaak:
MAX_WORDS = 3                 # maximaal zoveel woorden tegelijk
MAX_CHARS = 20                # of zoveel tekens, wat het eerst bereikt wordt

VIDEO_EXT = {".mp4", ".mkv", ".webm", ".mov"}
LOGO_EXT = {".png", ".jpg", ".jpeg", ".webp"}
LOGO_MAX = 10 * 1024 * 1024   # logo mag maximaal 10 MB zijn

app = Flask(__name__)
# Geen limiet op de grootte van een request: de editor moet grote video's kunnen uploaden.
# (De limiet voor het logo controleren we in upload_logo zelf.)
app.config["MAX_CONTENT_LENGTH"] = None
_model = None                 # Whisper-model wordt pas geladen bij de eerste keer ondertitelen
_src_lock = threading.Lock()  # voorkomt dat twee uploads tegelijk sources.json overschrijven


def run(cmd, cwd=None):
    """Voer een commando uit; bij een fout krijg je de laatste regels van de foutmelding."""
    # PYTHONUTF8 + utf-8: anders gaan titels met bijzondere tekens fout op Windows
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONUTF8": "1"})
    if p.returncode != 0:
        # volledige fout in de terminal, zodat je kunt zien wat er precies misging
        print(f"\n[FOUT] {' '.join(str(c) for c in cmd[:8])} ...\n{p.stderr}", file=sys.stderr, flush=True)
        tail = "\n".join(p.stderr.strip().splitlines()[-5:]) or "commando mislukt"
        raise RuntimeError(tail)
    return p.stdout


# ---------- voortgang in de terminal ----------

_bar_open = False


def log(msg):
    """Regel met de tijd ervoor, zodat je in de terminal ziet wat er wanneer gebeurde."""
    end_bar()
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def show_bar(frac):
    """Voortgangsbalk die op dezelfde regel bijwerkt."""
    global _bar_open
    frac = max(0.0, min(1.0, frac))
    n = int(frac * 20)
    print(f"\r           [{'#' * n}{'-' * (20 - n)}] {int(frac * 100):3d}%", end="", flush=True)
    _bar_open = True


def end_bar():
    global _bar_open
    if _bar_open:
        print(flush=True)                      # naar een nieuwe regel na de balk
        _bar_open = False


def step(n, total, text):
    log(f"Stap {n}/{total}  {text}")
    return time.time()


def step_done(t0):
    log(f"          klaar in {time.time() - t0:.0f} s")


def mmss(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def run_ffmpeg(cmd, length, cwd=None):
    """Draai een ffmpeg-commando (cmd begint met 'ffmpeg') met een voortgangsbalk.
    length = lengte van de uitvoer in seconden."""
    full = [cmd[0], "-nostats", "-loglevel", "error", "-progress", "pipe:1", *cmd[1:]]
    p = subprocess.Popen(full, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace")
    errors = []
    for line in p.stdout:
        line = line.strip()
        if line.startswith("out_time_us="):
            try:
                show_bar(int(line.split("=")[1]) / 1_000_000 / max(length, 0.1))
            except ValueError:
                pass                           # "N/A" in het begin
        elif line and not re.match(r"^[a-z_0-9]+=", line):
            errors.append(line)                # alles wat geen voortgangsregel is, is een foutmelding
    p.wait()
    if p.returncode != 0:
        end_bar()
        print("\n[FOUT] ffmpeg ...\n" + "\n".join(errors), file=sys.stderr, flush=True)
        raise RuntimeError("\n".join(errors[-5:]) or "ffmpeg mislukt")
    show_bar(1.0)


def job_dir(job):
    """Geef de map van een job terug; alleen ids die wij zelf maken zijn toegestaan."""
    if not re.fullmatch(r"[0-9a-f]{12}", job):
        abort(404)
    d = WORK / job
    if not d.is_dir():
        abort(404)
    return d


def find_file(d, stem):
    """Zoek een bestand dat met 'stem' begint en een videobestand is (yt-dlp kan de naam aanvullen)."""
    for f in sorted(d.glob(f"{stem}*")):
        if f.suffix in VIDEO_EXT:
            return f
    return None


def find_logo(d):
    """Zoek het geuploade logo van deze job (logo.png, logo.jpg, ...)."""
    for f in sorted(d.glob("logo.*")):
        if f.suffix.lower() in LOGO_EXT:
            return f
    return None


def duration_of(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "csv=p=0", str(path)])
    return float(out.strip())


def video_size(path):
    """Breedte en hoogte van de video in pixels."""
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)])
    w, h = out.strip().split(",")[:2]
    return int(w), int(h)


def ytdlp(*args):
    if not getattr(sys, "frozen", False):
        return run([sys.executable, "-m", "yt_dlp", "--no-playlist", *args])

    import io
    from contextlib import redirect_stderr, redirect_stdout
    import yt_dlp

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    full_args = ["--no-playlist", *args]
    ret = 0
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        try:
            ret = yt_dlp._real_main(full_args)
        except SystemExit as se:
            ret = se.code or 0
        except Exception as e:
            ret = 1
            stderr_buf.write(str(e))

    out = stdout_buf.getvalue()
    err = stderr_buf.getvalue()
    if ret != 0:
        print(f"\n[FOUT] yt_dlp {' '.join(full_args[:8])} ...\n{err}", file=sys.stderr, flush=True)
        tail = "\n".join(err.strip().splitlines()[-5:]) or "yt-dlp mislukt"
        raise RuntimeError(tail)
    return out


# ---------- ondertitels ----------

def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def ass_time(t):
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"


def make_cues(words):
    """Groepeer woorden tot korte ondertitels: [[start, einde, tekst], ...]."""
    cues, cur = [], []

    def flush():
        if cur:
            cues.append([cur[0].start, cur[-1].end, "".join(w.word for w in cur).strip()])
            cur.clear()

    for w in words:
        text = ("".join(x.word for x in cur) + w.word).strip()
        pauze = bool(cur) and (w.start - cur[-1].end) > 0.6      # spreker pauzeert even
        if cur and (len(cur) >= MAX_WORDS or len(text) > MAX_CHARS or pauze):
            flush()
        cur.append(w)
        if w.word.strip().endswith((".", "!", "?", ",")):         # einde zin of komma: nieuw stukje
            flush()
    flush()

    # elk stukje blijft nog heel even staan, maar nooit tot over het volgende heen
    for i, c in enumerate(cues):
        hold = c[1] + 0.3
        c[1] = min(hold, cues[i + 1][0]) if i + 1 < len(cues) else hold
    return cues


def write_srt(path, cues):
    """Gewoon .srt om te downloaden (de video zelf gebruikt het .ass-bestand hieronder)."""
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, text) in enumerate(cues, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{text}\n\n")


def write_ass(path, cues, w, h, top=None):
    """Schrijf de ondertitels als .ass in echte pixels van het eindbeeld (w x h).
    top = afstand vanaf de bovenkant waar de tekst begint (voor in de zwarte balk).
    Zonder top staat de tekst onderaan het beeld."""
    size = round(min(w, h) * 0.065)
    if top is not None:
        align, margin_v = 8, top                 # 8 = bovenaan gecentreerd
    else:
        align, margin_v = 2, round(h * 0.08)     # 2 = onderaan gecentreerd
    header = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {w}\nPlayResY: {h}\nWrapStyle: 0\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,Arial,{size},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,"
        f"-1,0,0,0,100,100,0,0,1,4,0,{align},60,60,{margin_v},1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        for a, b, text in cues:
            text = text.replace("{", "(").replace("}", ")")      # accolades zijn opmaakcodes in .ass
            f.write(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Default,,0,0,0,,{text}\n")


def read_wav(path):
    """Lees onze 16 kHz mono wav in als float-array.
    Geven we faster-whisper een array, dan decodeert het zelf niets meer. Dat omzeilt
    de PyAV-versiefout (nieuwe av-versies kennen 'metadata_errors' niet meer)."""
    import numpy as np
    with wave.open(str(path), "rb") as w:
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def transcribe(wav, language, on_progress=None):
    """Zet spraak om naar korte ondertitelstukjes met faster-whisper (draait lokaal)."""
    global _model
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError("faster-whisper is niet geinstalleerd: pip install faster-whisper")
    if _model is None:
        log("Whisper-model laden (de eerste keer kan dit even duren)...")
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    audio = read_wav(wav)
    total = len(audio) / 16000                 # lengte van de audio in seconden
    # word_timestamps: per woord een tijd, zodat we zelf korte stukjes kunnen maken
    segments, _ = _model.transcribe(audio, language=language or None, word_timestamps=True)
    words = []
    for s in segments:                         # de segmenten komen een voor een binnen
        words.extend(s.words or [])
        if on_progress and total:
            on_progress(s.end / total)
    return make_cues(words)


# ---------- routes: clipper ----------

@app.get("/")
def index():
    return send_file(BASE / "index.html")


@app.post("/api/load")
def load():
    """Haal alleen informatie over de video op (duur, soort site). Er wordt niets groots gedownload."""
    url = (request.get_json(silent=True) or {}).get("url", "").strip()
    if not url.startswith(("http://", "https://")):
        return jsonify(error="Geef een geldige link op (begint met http of https)."), 400
    try:
        info = json.loads(ytdlp("-J", url))               # -J = alleen info, geen download
    except Exception as e:
        return jsonify(error=f"Laden mislukt: {e}"), 500

    duration = info.get("duration")
    job = uuid.uuid4().hex[:12]
    d = WORK / job
    d.mkdir()

    def save_meta(dur):
        (d / "meta.json").write_text(json.dumps({"url": url, "duration": dur}), encoding="utf-8")

    if info.get("extractor_key") == "Youtube":
        if not duration:
            return jsonify(error="Laden mislukt: kon de lengte van de video niet bepalen (livestream?)"), 500
        # YouTube spelen we in de pagina zelf af: dan hoeft er niets gedownload te worden
        save_meta(duration)
        return jsonify(job=job, mode="youtube", id=info["id"], duration=duration)

    # andere sites: een kleine preview in lage kwaliteit, alleen om in te kunnen kijken en spoelen
    try:
        ytdlp("-S", "res:360,vcodec:h264,acodec:aac", "--merge-output-format", "mp4",
              "-o", str(d / "preview.%(ext)s"), url)
        prev = find_file(d, "preview")
        if not prev:
            raise RuntimeError("geen preview gevonden na het downloaden")
        duration = duration or duration_of(prev)          # veel sites geven zelf geen duur op
    except Exception as e:
        return jsonify(error=f"Laden mislukt: {e}"), 500
    save_meta(duration)
    return jsonify(job=job, mode="preview", duration=duration, video=f"/media/{job}/{prev.name}")


@app.post("/api/logo")
def upload_logo():
    """Sla een logo op bij een job. Het komt later in de verticale clip onder de ondertitels."""
    d = job_dir(request.form.get("job", ""))
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(error="Geen bestand ontvangen."), 400
    ext = Path(f.filename).suffix.lower()
    if ext not in LOGO_EXT:
        return jsonify(error="Gebruik een PNG, JPG of WebP afbeelding."), 400
    for old in d.glob("logo.*"):                      # oud logo van deze job weg
        old.unlink(missing_ok=True)
    path = d / f"logo{ext}"
    f.save(path)
    if path.stat().st_size > LOGO_MAX:
        path.unlink(missing_ok=True)
        return jsonify(error="Het logo mag maximaal 10 MB zijn."), 400
    try:
        video_size(path)                              # ffprobe moet het als afbeelding kunnen lezen
    except Exception:
        path.unlink(missing_ok=True)
        return jsonify(error="Dit bestand is geen geldige afbeelding."), 400
    return jsonify(ok=True)


@app.post("/api/render")
def render():
    """Haal elk gekozen stuk apart op, maak (optioneel) ondertitels en (optioneel) 9:16."""
    data = request.get_json(silent=True) or {}
    d = job_dir(data.get("job", ""))
    try:
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return jsonify(error="Deze video moet opnieuw geladen worden."), 404
    url, total = meta["url"], meta["duration"]

    subs = bool(data.get("subtitles"))
    vertical = bool(data.get("vertical"))
    blur = vertical and bool(data.get("blur"))     # geblurde achtergrond kan alleen bij 9:16
    language = data.get("language") or None
    use_logo = vertical and bool(data.get("logo"))   # logo kan alleen bij 9:16
    logo_file = find_logo(d) if use_logo else None
    if use_logo and not logo_file:
        return jsonify(error="Het logo is niet gevonden. Kies het logo opnieuw."), 400
    clips = []
    wanted = data.get("segments", [])
    t_all = time.time()
    try:
        for i, seg in enumerate(wanted, 1):
            start = max(0.0, float(seg["start"]))
            end = min(float(total), float(seg["end"]))
            if end - start < 0.5:
                raise ValueError(f"Stuk {i} is te kort of ligt buiten de video.")
            name, stem = f"clip_{i:02}", f"part_{i:02}"
            srt, ass = d / f"{name}.srt", d / f"{name}.ass"
            srt.unlink(missing_ok=True)               # oude ondertitels van een eerdere run weg
            ass.unlink(missing_ok=True)

            n_steps = 3 if subs else 2                # ophalen, (ondertitels), renderen
            t_clip = time.time()
            log(f"=== Clip {i} van {len(wanted)}  ({mmss(start)} tot {mmss(end)}, {end - start:.0f} s) ===")
            try:
                # alleen dit stuk van de originele video ophalen (hoge kwaliteit)
                # force-keyframes zorgt dat het stuk precies op start en einde begint en stopt
                t = step(1, n_steps, "Stuk ophalen van de bron...")
                ytdlp("--download-sections", f"*{start:.2f}-{end:.2f}", "--force-keyframes-at-cuts",
                      "-S", "res:1080,vcodec:h264,acodec:aac", "--merge-output-format", "mp4",
                      "-o", str(d / f"{stem}.%(ext)s"), url)
                part = find_file(d, stem)
                if not part:
                    raise RuntimeError(f"stuk {i} kon niet worden opgehaald")
                step_done(t)
                sw, sh = video_size(part)

                filters = []
                ass_filter = None                     # komt er pas als er ondertitels zijn
                vid_bottom = None                     # onderkant van de video in het eindbeeld (9:16)
                out_w, out_h, top = sw, sh, None      # maat van het eindbeeld + waar de tekst komt
                if vertical:
                    out_w, out_h = 1080, 1920
                    # hele video in beeld houden: verkleinen tot hij past
                    fit = "scale=1080:1920:force_original_aspect_ratio=decrease:force_divisible_by=2"
                    if blur:
                        # dezelfde video nog een keer, ingezoomd tot hij het hele scherm vult,
                        # daarna geblurd en iets donkerder, als achtergrond achter de echte video
                        filters.append("split[a][b];"
                                       "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                                       "boxblur=25:3,eq=brightness=-0.12[bg];"
                                       f"[b]{fit}[fg];"
                                       "[bg][fg]overlay=(W-w)/2:(H-h)/2")
                    else:
                        # zwarte balken boven en onder
                        filters.append(fit + ",pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black")
                    factor = min(1080 / sw, 1920 / sh)
                    bottom = (1920 + sh * factor) / 2     # onderkant van de video in het eindbeeld
                    vid_bottom = round(bottom)
                    if 1920 - bottom >= 300:              # genoeg zwart eronder: tekst begint daar
                        top = round(bottom) + 50

                if subs:
                    # geluid van dit stuk eruit halen en transcriberen
                    t = step(2, n_steps, "Ondertitels maken (Whisper)...")
                    wav = d / f"{name}.wav"
                    run(["ffmpeg", "-y", "-i", str(part), "-vn", "-ac", "1", "-ar", "16000",
                         "-c:a", "pcm_s16le", str(wav)])       # 16-bit, dat verwacht read_wav()
                    try:
                        cues = transcribe(wav, language, show_bar)
                    finally:
                        wav.unlink(missing_ok=True)            # opruimen, ook als het misgaat
                    if cues:                                    # geen spraak = geen ondertitels
                        write_srt(srt, cues)
                        write_ass(ass, cues, out_w, out_h, top)
                        ass_filter = f"ass={name}.ass"
                    else:
                        log("Geen spraak gevonden, dus geen ondertitels.")
                    step_done(t)

                # logo: komt onder de ondertitels (of direct onder de video als er geen ondertitels zijn)
                logo_box = None
                if logo_file:
                    if ass_filter and top is not None:
                        y0 = top + round(min(out_w, out_h) * 0.065 * 1.7)    # onder de tekstregel
                    elif not ass_filter and vid_bottom is not None:
                        y0 = vid_bottom + 50
                    else:
                        y0 = 1720                     # geen zwart gebied: klein logo onderaan
                    max_h = min(260, 1920 - y0 - 40)
                    if max_h >= 60:
                        logo_box = (y0, max_h)
                    else:
                        print("[LET OP] Geen ruimte voor het logo, het wordt overgeslagen.",
                              file=sys.stderr, flush=True)

                t = step(n_steps, n_steps, "Clip renderen...")
                if logo_box:
                    y0, max_h = logo_box
                    fc = (f"[0:v]{','.join(filters)}[v0];"
                          f"[1:v]format=rgba,scale=700:{max_h}:force_original_aspect_ratio=decrease[lg];"
                          f"[v0][lg]overlay=(W-w)/2:{y0}+({max_h}-h)/2[v1];"
                          + (f"[v1]{ass_filter}[vout]" if ass_filter else "[v1]null[vout]"))
                    cmd = ["ffmpeg", "-y", "-i", str(part), "-i", str(logo_file),
                           "-filter_complex", fc, "-map", "[vout]", "-map", "0:a?"]
                else:
                    if ass_filter:
                        filters.append(ass_filter)
                    cmd = ["ffmpeg", "-y", "-i", str(part)]
                    if filters:
                        cmd += ["-vf", ",".join(filters)]
                cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                        "-movflags", "+faststart", f"{name}.mp4"]
                run_ffmpeg(cmd, duration_of(part), cwd=d)   # cwd=d zodat de .ass-naam simpel blijft
                step_done(t)
            finally:
                for f in d.glob(f"{stem}*"):           # het opgehaalde stuk is niet meer nodig
                    f.unlink(missing_ok=True)

            clips.append({"name": f"{name}.mp4",
                          "url": f"/media/{d.name}/{name}.mp4",
                          "srt": f"/media/{d.name}/{name}.srt" if srt.exists() else None})
            log(f"=== Clip {i} klaar: {name}.mp4 (totaal {time.time() - t_clip:.0f} s) ===")
    except Exception as e:
        log(f"MISLUKT: {e}")
        return jsonify(error=str(e)), 500
    log(f"ALLES KLAAR: {len(clips)} clip(s) in {time.time() - t_all:.0f} s. Je kunt ze nu downloaden in de browser.")
    return jsonify(clips=clips)


# ---------- routes: editor (knippen en plakken) ----------

def probe_media(path):
    """Lees uit wat voor bestand het is: video of audio, hoe lang, en of er geluid in zit."""
    info = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]))
    streams = info.get("streams", [])
    # het albumhoesje in een mp3 is technisch een videostream, maar telt niet als video
    video = [s for s in streams if s.get("codec_type") == "video"
             and not s.get("disposition", {}).get("attached_pic")]
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    if not video and not audio:
        raise RuntimeError("geen video of audio gevonden")
    duration = float(info.get("format", {}).get("duration") or 0)
    if duration <= 0:                                  # sommige containers geven de duur per stream
        duration = max([float(s.get("duration") or 0) for s in streams] or [0])
    if duration <= 0:
        raise RuntimeError("kon de lengte niet bepalen")
    w = h = 0
    if video:
        w, h = int(video[0]["width"]), int(video[0]["height"])
        rot = 0                                        # telefoonvideo's zijn vaak gedraaid opgeslagen
        for sd in video[0].get("side_data_list", []):
            if "rotation" in sd:
                rot = int(sd["rotation"])
        rot = rot or int(video[0].get("tags", {}).get("rotate", 0) or 0)
        if abs(rot) % 180 == 90:
            w, h = h, w
    return {"kind": "video" if video else "audio", "duration": duration,
            "has_audio": bool(audio), "width": w, "height": h}


def load_sources(d):
    f = d / "sources.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def find_editor_watermark(d):
    """Zoek het watermark dat voor de editor-export is geüpload."""
    for f in sorted(d.glob("watermark.*")):
        if f.suffix.lower() in LOGO_EXT:
            return f
    return None


def validate_watermark(path):
    """Controleer dat het bestand een ondersteunde stilstaande afbeelding is."""
    info = json.loads(run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                           "-show_entries", "stream=codec_name,width,height",
                           "-of", "json", str(path)]))
    streams = info.get("streams", [])
    if not streams or streams[0].get("codec_name") not in {"png", "mjpeg", "webp"}:
        raise ValueError("geen ondersteunde afbeelding")
    width, height = int(streams[0]["width"]), int(streams[0]["height"])
    if width <= 0 or height <= 0:
        raise ValueError("ongeldige afbeeldingsafmetingen")
    return width, height


@app.get("/editor")
def editor():
    return send_file(BASE / "editor.html")


@app.post("/api/editor/upload")
def editor_upload():
    """Sla een video- of audiobestand op voor de editor en geef zijn gegevens terug."""
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(error="Geen bestand ontvangen."), 400
    job = request.form.get("job", "")
    if job:
        d = job_dir(job)
    else:                                              # eerste upload: nieuwe editor-sessie
        job = uuid.uuid4().hex[:12]
        d = WORK / job
        d.mkdir()
    sid = uuid.uuid4().hex[:8]
    ext = re.sub(r"[^a-z0-9]", "", Path(f.filename).suffix.lower())[:5] or "bin"
    path = d / f"src_{sid}.{ext}"
    f.save(path)
    try:
        info = probe_media(path)
    except Exception:
        path.unlink(missing_ok=True)
        return jsonify(error="Dit bestand kan ik niet lezen als video of audio."), 400
    info.update(id=sid, name=Path(f.filename).name, file=path.name)
    with _src_lock:
        srcs = load_sources(d)
        srcs[sid] = info
        (d / "sources.json").write_text(json.dumps(srcs), encoding="utf-8")
    log(f"Editor: {info['name']} toegevoegd ({info['kind']}, {mmss(info['duration'])})")
    return jsonify(job=job, source={**info, "url": f"/media/{job}/{path.name}"})


@app.post("/api/editor/watermark")
def editor_upload_watermark():
    """Sla een watermarkafbeelding op voor verticale editor-exports."""
    d = job_dir(request.form.get("job", ""))
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(error="Geen bestand ontvangen."), 400
    ext = Path(f.filename).suffix.lower()
    if ext not in LOGO_EXT:
        return jsonify(error="Gebruik een PNG, JPG of WebP afbeelding."), 400

    temp = d / f".watermark-{uuid.uuid4().hex}{ext}"
    destination = d / f"watermark{ext}"
    try:
        f.save(temp)
        if temp.stat().st_size > LOGO_MAX:
            return jsonify(error="Het watermark mag maximaal 10 MB zijn."), 400
        validate_watermark(temp)
        os.replace(temp, destination)
    except (RuntimeError, ValueError, KeyError, json.JSONDecodeError):
        return jsonify(error="Dit bestand is geen geldige afbeelding."), 400
    finally:
        temp.unlink(missing_ok=True)

    for old in d.glob("watermark.*"):
        if old != destination:
            old.unlink(missing_ok=True)
    return jsonify(ok=True)


def pick_size(fmt, items):
    """Kies de afmeting van de video: een vaste keuze, of die van het eerste videostuk."""
    if fmt == "vertical":
        return 1080, 1920
    if fmt == "square":
        return 1080, 1080
    if fmt == "landscape":
        return 1920, 1080
    first = next(s for s, _, _ in items if s["kind"] == "video")
    w, h = first["width"], first["height"]
    f = min(1.0, 1920 / max(w, h))                     # nooit groter dan 1920 pixels
    return max(2, round(w * f / 2) * 2), max(2, round(h * f / 2) * 2)


def video_graph(w, h, blur):
    """Filter die elk stuk op dezelfde maat zet: hele beeld zichtbaar, zwart of geblurd eromheen."""
    fit = f"scale={w}:{h}:force_original_aspect_ratio=decrease:force_divisible_by=2"
    tail = ",setsar=1,fps=30,format=yuv420p"           # zelfde beeldsnelheid voor alle stukken
    if blur:
        return (f"[0:v]split[a][b];"
                f"[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                f"boxblur=25:3,eq=brightness=-0.12[bg];[b]{fit}[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2{tail}[v]")
    return f"[0:v]{fit},pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black{tail}[v]"


@app.post("/api/editor/export")
def editor_export():
    """Knip elk stuk uit zijn bronbestand, zet ze op dezelfde maat en plak ze aan elkaar."""
    data = request.get_json(silent=True) or {}
    d = job_dir(data.get("job", ""))
    srcs = load_sources(d)
    items = []
    try:
        for c in data.get("clips") or []:
            s = srcs[str(c["src"])]
            start = max(0.0, float(c["start"]))
            end = min(float(s["duration"]), float(c["end"]))
            if end - start < 0.05:
                raise ValueError("Een stuk is te kort of ligt buiten het bestand.")
            items.append((s, start, end))
    except KeyError:
        return jsonify(error="Een bronbestand is niet gevonden. Voeg het opnieuw toe."), 400
    except (ValueError, TypeError) as e:
        return jsonify(error=str(e)), 400
    if not items:
        return jsonify(error="De tijdlijn is leeg."), 400

    # alleen audio als er alleen audiostukken zijn, of als je dat zelf kiest
    audio_only = bool(data.get("audio_only")) or not any(s["kind"] == "video" for s, _, _ in items)
    blur = bool(data.get("blur")) and not audio_only
    crossfade = bool(data.get("crossfade")) and len(items) > 1
    crossfade_duration = 0.0
    if crossfade:
        try:
            crossfade_duration = float(data.get("crossfade_duration", 0.5))
        except (TypeError, ValueError):
            return jsonify(error="Kies een geldige duur voor de overgangen."), 400
        shortest_clip = min(end - start for _, start, end in items)
        if not (0.1 <= crossfade_duration <= 3 and crossfade_duration * 2 <= shortest_clip):
            return jsonify(error="De overgang moet maximaal de helft van de kortste clip duren (maximaal 3 seconden)."), 400
    watermark = None
    if data.get("watermark"):
        if audio_only or data.get("format") != "vertical":
            return jsonify(error="Een watermark kan alleen bij video-export in 9:16 worden gebruikt."), 400
        watermark = find_editor_watermark(d)
        if not watermark:
            return jsonify(error="Upload eerst een watermarkafbeelding."), 400
        try:
            watermark_x = float(data.get("watermark_x", 0.5))
            watermark_y = float(data.get("watermark_y", 0.75))
        except (TypeError, ValueError):
            return jsonify(error="Kies een geldige positie voor het watermark."), 400
        if not (0 <= watermark_x <= 1 and 0 <= watermark_y <= 1):
            return jsonify(error="De positie van het watermark valt buiten de video."), 400
    out_name = f"bewerkt_{time.strftime('%H%M%S')}.{'mp3' if audio_only else 'mp4'}"
    tmp = d / "ed_tmp"                                 # tussenbestanden, worden daarna weggegooid
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    n, t_all = len(items), time.time()
    total_len = sum(e - s for _, s, e in items)
    output_len = total_len - crossfade_duration * (n - 1) if crossfade else total_len
    try:
        w, h = (0, 0) if audio_only else pick_size(data.get("format"), items)
        log(f"=== Editor: {n} stuk(ken) samenvoegen tot {out_name} ({mmss(total_len)}) ===")
        lines = []
        for k, (s, start, end) in enumerate(items, 1):
            length = end - start
            src = d / s["file"]
            ss = ["-ss", f"{start:.3f}", "-i", str(src)]     # -ss voor -i = snel naar de juiste plek
            silence = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
            t = step(k, n + 1, f"Stuk {k} van {n}: {s['name']} ({mmss(start)} tot {mmss(end)})...")
            if audio_only:
                seg = f"seg_{k:03}.wav"
                if s["has_audio"]:
                    cmd = ["ffmpeg", "-y", *ss, "-t", f"{length:.3f}", "-vn"]
                else:                                       # video zonder geluid: stilte
                    cmd = ["ffmpeg", "-y", *silence, "-t", f"{length:.3f}"]
                cmd += ["-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", seg]
            else:
                seg = f"seg_{k:03}.mkv"
                if s["kind"] == "video":
                    cmd = ["ffmpeg", "-y", *ss]
                    if not s["has_audio"]:
                        cmd += silence                      # stille video krijgt stilte als geluid
                    cmd += ["-filter_complex", video_graph(w, h, blur), "-map", "[v]",
                            "-map", "0:a:0" if s["has_audio"] else "1:a"]
                else:                                       # audiobestand in een video: zwart beeld
                    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r=30",
                           *ss, "-map", "0:v", "-map", "1:a", "-vf", "format=yuv420p"]
                cmd += ["-t", f"{length:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                        "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", seg]
            run_ffmpeg(cmd, length, cwd=tmp)
            step_done(t)
            lines.append(f"file '{seg}'")

        (tmp / "list.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        t = step(n + 1, n + 1, "Stukken samenvoegen...")
        if crossfade:
            segments = [f"seg_{k:03}.{'wav' if audio_only else 'mkv'}" for k in range(1, n + 1)]
            final = ["ffmpeg", "-y"]
            for segment in segments:
                final += ["-i", segment]

            filters = []
            audio_label = "[0:a]"
            for k in range(1, n):
                next_audio = f"[a{k}]"
                filters.append(
                    f"{audio_label}[{k}:a]acrossfade=d={crossfade_duration:.3f}:c1=tri:c2=tri{next_audio}"
                )
                audio_label = next_audio

            if audio_only:
                filters.append(f"{audio_label}anull[aout]")
                final += ["-filter_complex", ";".join(filters), "-map", "[aout]",
                          "-c:a", "libmp3lame", "-q:a", "2"]
            else:
                for k in range(n):
                    filters.append(f"[{k}:v]settb=AVTB,setpts=PTS-STARTPTS[v{k}]")
                video_label = "[v0]"
                for k in range(1, n):
                    next_video = f"[v{k}]"
                    offset = sum(end - start for _, start, end in items[:k]) - crossfade_duration * k
                    filters.append(
                        f"{video_label}[v{k}]xfade=transition=fade:duration={crossfade_duration:.3f}:"
                        f"offset={offset:.6f}{next_video}"
                    )
                    video_label = next_video
                if watermark:
                    watermark_index = n
                    final += ["-loop", "1", "-i", str(watermark)]
                    filters.append(
                        f"[{watermark_index}:v]format=rgba,scale=420:420:"
                        "force_original_aspect_ratio=decrease[wm]"
                    )
                    filters.append(
                        f"{video_label}[wm]overlay=(W-w)*{watermark_x:.6f}:"
                        f"(H-h)*{watermark_y:.6f}:format=auto[vout]"
                    )
                    video_label = "[vout]"
                final += ["-filter_complex", ";".join(filters), "-map", video_label,
                          "-map", audio_label, "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "18", "-c:a", "aac", "-b:a", "192k",
                          "-shortest", "-movflags", "+faststart"]
        else:
            final = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt"]
            if audio_only:
                final += ["-c:a", "libmp3lame", "-q:a", "2"]
            elif watermark:
                final += ["-loop", "1", "-i", str(watermark),
                          "-filter_complex",
                          "[1:v]format=rgba,scale=420:420:force_original_aspect_ratio=decrease[wm];"
                          f"[0:v][wm]overlay=(W-w)*{watermark_x:.6f}:(H-h)*{watermark_y:.6f}:format=auto[v]",
                          "-map", "[v]", "-map", "0:a:0", "-c:v", "libx264",
                          "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
                          "-shortest", "-movflags", "+faststart"]
            else:                                           # beeld kopieren, geluid een keer netjes coderen
                final += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]
        run_ffmpeg(final + [str(d / out_name)], output_len, cwd=tmp)
        step_done(t)
    except Exception as e:
        log(f"MISLUKT: {e}")
        return jsonify(error=str(e)), 500
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    log(f"ALLES KLAAR: {out_name} in {time.time() - t_all:.0f} s. Je kunt hem nu downloaden in de browser.")
    return jsonify(url=f"/media/{d.name}/{out_name}", name=out_name,
                   kind="audio" if audio_only else "video")


@app.get("/media/<job>/<name>")
def media(job, name):
    return send_from_directory(job_dir(job), name, conditional=True)   # conditional = spoelen in de preview


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port, threaded=True)
