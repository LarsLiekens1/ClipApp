import glob
import json
import os
import subprocess
import sys
from collections import Counter

if len(sys.argv) < 2:
    print('Gebruik: python chatpieken.py "https://www.youtube.com/watch?v=VIDEO_ID" [venster_in_seconden]')
    sys.exit(1)

url = sys.argv[1]
venster = int(sys.argv[2]) if len(sys.argv) > 2 else 60

# Oude chatbestanden weghalen
for f in glob.glob("livechat*.live_chat.json"):
    os.remove(f)

result = subprocess.run(
    [
        "yt-dlp",
        "--skip-download",
        "--write-subs",
        "--sub-langs", "live_chat",
        "-o", "livechat",
        url,
    ],
    capture_output=True,
    text=True,
    encoding="utf-8",
)

bestanden = glob.glob("livechat*.live_chat.json")
if not bestanden:
    print("Geen chat replay gevonden. Dit werkt alleen bij afgelopen livestreams met chat replay.")
    if result.stderr:
        print(result.stderr)
    sys.exit(1)

tellers = Counter()

with open(bestanden[0], encoding="utf-8") as f:
    for regel in f:
        regel = regel.strip()
        if not regel:
            continue
        try:
            data = json.loads(regel)
        except json.JSONDecodeError:
            continue

        actie = data.get("replayChatItemAction")
        if not actie:
            continue

        offset = actie.get("videoOffsetTimeMsec")
        if offset is None:
            continue

        aantal = sum(1 for a in actie.get("actions", []) if "addChatItemAction" in a)
        if aantal == 0:
            continue

        seconden = int(offset) / 1000
        if seconden < 0:
            continue

        tellers[int(seconden // venster)] += aantal

if not tellers:
    print("Chat bestand gevonden, maar er stonden geen berichten in.")
    sys.exit()


def fmt(sec):
    sec = int(sec)
    uren = sec // 3600
    minuten = (sec % 3600) // 60
    s = sec % 60
    if uren:
        return f"{uren}:{minuten:02d}:{s:02d}"
    return f"{minuten}:{s:02d}"


top = tellers.most_common(5)

print(f"Top 5 drukste stukken (venster van {venster} seconden):")
for blok, aantal in sorted(top):
    start = blok * venster
    eind = start + venster
    print(f"{fmt(start)} - {fmt(eind)}  ({aantal} berichten)")
