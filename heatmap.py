import json
import subprocess
import sys

if len(sys.argv) < 2:
    print('Gebruik: python heatmap.py "https://www.youtube.com/watch?v=VIDEO_ID"')
    sys.exit(1)

url = sys.argv[1]

result = subprocess.run(
    ["yt-dlp", "--skip-download", "--dump-json", url],
    capture_output=True,
    text=True,
    encoding="utf-8",
)

if result.returncode != 0:
    print("yt-dlp gaf een fout:")
    print(result.stderr)
    sys.exit(1)

info = json.loads(result.stdout)
heatmap = info.get("heatmap")

if not heatmap:
    print("Geen heatmap beschikbaar voor deze video.")
    sys.exit()

top = sorted(heatmap, key=lambda s: s["value"], reverse=True)[:5]


def fmt(sec):
    sec = int(sec)
    return f"{sec // 60}:{sec % 60:02d}"


for s in sorted(top, key=lambda s: s["start_time"]):
    print(f"{fmt(s['start_time'])} - {fmt(s['end_time'])}  (score {s['value']:.2f})")
