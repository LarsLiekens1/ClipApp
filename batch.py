"""ClipAPP zonder browser: maak automatisch TikToks van links, bestanden of een hele map.

Voorbeelden:
    python batch.py https://www.youtube.com/watch?v=...          # één link
    python batch.py links.txt                                     # één link per regel
    python batch.py C:\\Video's\\opnames --count 3 --subs          # alle video's in een map
    python batch.py C:\\Video's\\inbox --watch                     # blijf de map bewaken

De clips (en de posttekst als .txt) komen in de map `clips_output` (of --out).
Alles draait lokaal en is gratis.
"""
import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path

VIDEO_EXT = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Maak automatisch TikToks van links, bestanden of een map.")
    p.add_argument("sources", nargs="+", help="links, videobestanden, .txt-bestanden met links, of mappen")
    p.add_argument("--out", default="clips_output", help="map voor de resultaten (standaard: clips_output)")
    p.add_argument("--count", type=int, default=5, help="aantal clips per video (1-10, standaard 5)")
    p.add_argument("--length", default="20-60", help="lengte per clip in seconden, bv. 15-30 (standaard 20-60)")
    p.add_argument("--subs", action="store_true", help="ondertitels maken (gebruikt Whisper of YouTube-ondertitels)")
    p.add_argument("--language", choices=["nl", "en", "fr", "de"], help="taal van de video (standaard automatisch)")
    p.add_argument("--model", choices=["tiny", "base", "small", "medium"], help="Whisper-model")
    p.add_argument("--style", choices=["tiktok", "classic"], default="tiktok", help="stijl van de ondertitels")
    p.add_argument("--color", choices=["yellow", "green", "cyan", "pink", "white"], default="yellow")
    p.add_argument("--no-vertical", action="store_true", help="niet naar 9:16 omzetten")
    p.add_argument("--no-blur", action="store_true", help="zwarte balken i.p.v. geblurde achtergrond")
    p.add_argument("--face", action="store_true", help="9:16-crop die het gezicht volgt")
    p.add_argument("--caption", action="store_true", help="hook-caption bovenin beeld")
    p.add_argument("--jump-cuts", action="store_true", help="stiltes eruit knippen")
    p.add_argument("--watch", action="store_true", help="map blijven bewaken op nieuwe video's")
    p.add_argument("--interval", type=int, default=15, help="seconden tussen controles bij --watch")
    args = p.parse_args(argv)
    m = re.fullmatch(r"(\d+)-(\d+)", args.length)
    if not m or not (5 <= int(m.group(1)) <= int(m.group(2)) <= 180):
        p.error("--length moet iets zijn als 20-60 (tussen 5 en 180 seconden)")
    if not 1 <= args.count <= 10:
        p.error("--count moet tussen 1 en 10 liggen")
    if args.watch and not all(Path(s).is_dir() for s in args.sources):
        p.error("--watch werkt alleen met mappen")
    return args


def options_from(args):
    min_len, max_len = (int(x) for x in args.length.split("-"))
    vertical = not args.no_vertical
    return {
        "count": args.count, "min_len": min_len, "max_len": max_len,
        "subtitles": args.subs, "language": args.language, "whisper_model": args.model,
        "youtube_subs": True, "sub_style": args.style, "sub_color": args.color, "sub_upper": True,
        "jump_cuts": args.jump_cuts, "face_crop": args.face and vertical,
        "vertical": vertical, "blur": vertical and not args.no_blur,
        "caption": args.caption, "caption_position": "above",
    }


def expand_sources(sources):
    """Links, bestanden, .txt-lijsten en mappen omzetten naar een lijst links/paden."""
    out = []
    for s in sources:
        if s.startswith(("http://", "https://")):
            out.append(s)
            continue
        path = Path(s)
        if path.is_dir():
            out.extend(str(f) for f in sorted(path.iterdir()) if f.suffix.lower() in VIDEO_EXT)
        elif path.suffix.lower() == ".txt":
            out.extend(line.strip() for line in path.read_text(encoding="utf-8").splitlines()
                       if line.strip() and not line.strip().startswith("#"))
        elif path.is_file():
            out.append(str(path))
        else:
            print(f"[OVERGESLAGEN] {s}: bestaat niet", file=sys.stderr)
    return out


def safe_name(text):
    return re.sub(r"[^\w\- ]+", "", text).strip().replace(" ", "_")[:60] or "video"


def copy_results(result, out_dir, work):
    """Kopieer de clips en tekstbestanden naar de uitvoermap; geeft de nieuwe paden terug."""
    out_dir.mkdir(parents=True, exist_ok=True)
    base = safe_name(result.get("title") or result["source"])
    copied = []
    for clip in result.get("clips") or []:
        src = work / result["job"] / clip["name"]
        dst = out_dir / f"{base}_{clip['name']}"
        shutil.copyfile(src, dst)
        copied.append(dst)
        txt = src.with_suffix(".txt")
        if txt.exists():
            shutil.copyfile(txt, dst.with_suffix(".txt"))
    return copied


def run_batch(sources, options, out_dir, process_video, work, app):
    results = []
    for k, source in enumerate(sources, 1):
        print(f"\n=== Video {k} van {len(sources)}: {source} ===", flush=True)
        with app.app_context():
            try:
                result = process_video(source, options)
            except Exception as e:                 # één kapotte video stopt de rest niet
                result = {"source": source, "error": str(e)}
        if result.get("error"):
            print(f"[MISLUKT] {source}: {result['error']}", file=sys.stderr, flush=True)
        else:
            files = copy_results(result, out_dir, work)
            print(f"[KLAAR] {len(files)} clip(s) in {out_dir}", flush=True)
        results.append(result)
    return results


def watch(folders, options, out_dir, process_video, work, app, interval):
    """Bewaak mappen: elke nieuwe video die niet meer groeit, wordt verwerkt."""
    state_file = out_dir / ".verwerkt.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    done = set(json.loads(state_file.read_text(encoding="utf-8"))) if state_file.exists() else set()
    sizes = {}
    print(f"Bewaakt: {', '.join(folders)} (Ctrl+C om te stoppen)", flush=True)
    while True:
        for folder in folders:
            for f in sorted(Path(folder).iterdir()):
                key = str(f.resolve())
                if f.suffix.lower() not in VIDEO_EXT or key in done:
                    continue
                size = f.stat().st_size
                if sizes.get(key) != size:         # nog aan het kopiëren: volgende ronde opnieuw
                    sizes[key] = size
                    continue
                run_batch([str(f)], options, out_dir, process_video, work, app)
                done.add(key)
                state_file.write_text(json.dumps(sorted(done)), encoding="utf-8")
        time.sleep(interval)


def main(argv=None):
    args = parse_args(argv)
    from app import WORK, app, process_video      # pas na het lezen van de argumenten laden
    out_dir = Path(args.out)
    options = options_from(args)
    try:
        if args.watch:
            watch(args.sources, options, out_dir, process_video, WORK, app, args.interval)
        sources = expand_sources(args.sources)
        if not sources:
            print("Geen video's of links gevonden.", file=sys.stderr)
            return 1
        results = run_batch(sources, options, out_dir, process_video, WORK, app)
    except KeyboardInterrupt:
        print("\nGestopt.")
        return 130
    ok = sum(1 for r in results if not r.get("error"))
    print(f"\nKlaar: {ok} van {len(results)} video('s) gelukt. Resultaten in {out_dir.resolve()}")
    return 0 if ok == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
