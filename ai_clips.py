"""Automatische TikTok-voorstellen: Claude kiest momenten uit het transcript en schrijft captions."""
import json
import math
import os

AI_MODEL = os.environ.get("CLIPAPP_AI_MODEL", "claude-opus-5-5")
MAX_CLIPS = 10
LINE_MAX_SECONDS = 12          # transcriptregels worden zo lang mogelijk, maar niet langer
MAX_SIGNALS = 15               # zoveel "hete" momenten uit comments/heatmap sturen we mee

SYSTEM_PROMPT = """Je bent een ervaren editor van korte video's voor TikTok, Reels en Shorts.
Je krijgt het transcript van een lange video met tijdcodes in seconden. Kies de momenten die als
losse korte video het best werken.

Een goede clip:
- begint met een sterke hook: een prikkelende uitspraak, vraag, conflict of verrassing in de eerste seconden;
- is op zichzelf te begrijpen, zonder de rest van de video gezien te hebben;
- begint aan het begin van een zin en stopt net na de clou of punchline, niet midden in een gedachte;
- heeft een duidelijke emotie: grappig, verrassend, leerzaam, controversieel of herkenbaar.

Regels:
- Gebruik alleen tijden die in het transcript voorkomen; start en end zijn seconden vanaf het begin.
- Clips mogen elkaar niet overlappen.
- Schrijf caption, description en hashtags in dezelfde taal als de video, tenzij anders gevraagd.
- caption: korte hook-tekst die bovenin beeld komt (max. ~70 tekens), geen hashtags, geen emoji-spam,
  en niets beloven wat niet in de clip gebeurt.
- description: posttekst voor TikTok van 1-2 zinnen die nieuwsgierig maakt.
- hashtags: 3-5 relevante hashtags zonder het #-teken.
- reason: één zin waarom dit moment werkt.
- score: 1-100, hoe viraal je de clip inschat. Sorteer niet; dat doet de app."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "clips": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "caption": {"type": "string"},
                    "description": {"type": "string"},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                    "score": {"type": "integer"},
                },
                "required": ["start", "end", "caption", "description", "hashtags", "reason", "score"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["clips"],
    "additionalProperties": False,
}


class AIClipError(RuntimeError):
    pass


def build_transcript(cues):
    """Voeg korte ondertitelstukjes samen tot regels '[start-end] tekst' (minder tokens, meer context)."""
    lines, cur = [], []
    for start, end, text in cues:
        if cur and end - cur[0][0] > LINE_MAX_SECONDS:
            lines.append(cur)
            cur = []
        cur.append((start, end, text))
        if text.rstrip().endswith((".", "!", "?")):
            lines.append(cur)
            cur = []
    if cur:
        lines.append(cur)
    return "\n".join(
        f"[{line[0][0]:.1f}-{line[-1][1]:.1f}] {' '.join(t.strip() for _, _, t in line)}"
        for line in lines
    )


def _signal_lines(bins):
    """Zet de drukste intervallen uit de commentanalyse om naar tekst voor de prompt."""
    usable = []
    for b in bins or []:
        if not isinstance(b, dict):
            continue
        try:
            start, end = float(b["start"]), float(b["end"])
        except (KeyError, TypeError, ValueError):
            continue
        mentions = b.get("comment_mentions") or 0
        viewers = b.get("viewer_score")
        if not isinstance(mentions, (int, float)) or not math.isfinite(mentions):
            mentions = 0
        if not isinstance(viewers, (int, float)) or not math.isfinite(viewers):
            viewers = None
        if mentions > 0 or (viewers or 0) > 0:
            usable.append((start, end, mentions, viewers))
    max_m = max((u[2] for u in usable), default=0) or 1
    max_v = max((u[3] or 0 for u in usable), default=0) or 1
    usable.sort(key=lambda u: -(u[2] / max_m + (u[3] or 0) / max_v))
    out = []
    for start, end, mentions, viewers in sorted(usable[:MAX_SIGNALS]):
        parts = [f"{int(mentions)} comment-timestamps"]
        if viewers is not None:
            parts.append(f"heatmap {viewers:.2f}")
        out.append(f"- {start:.0f}-{end:.0f} s: {', '.join(parts)}")
    return "\n".join(out)


def _user_prompt(transcript, duration, count, min_len, max_len, signals, caption_language):
    parts = [
        f"Videolengte: {duration:.0f} seconden.",
        f"Kies maximaal {count} clips van elk {min_len:.0f} tot {max_len:.0f} seconden. "
        "Kies er minder als er niet genoeg sterke momenten zijn.",
    ]
    if caption_language:
        parts.append(f"Schrijf caption, description en hashtags in deze taal: {caption_language}.")
    if signals:
        parts.append(
            "Deze intervallen kregen veel aandacht van kijkers (comments die de tijd noemen en/of de "
            "YouTube-heatmap). Gebruik dit als extra signaal, maar beoordeel zelf of het moment "
            "als losse clip werkt:\n" + signals
        )
    parts.append(f"<transcript>\n{transcript}\n</transcript>")
    return "\n\n".join(parts)


def clean_clips(raw_clips, duration, count, min_len, max_len):
    """Controleer de AI-uitvoer: tijden binnen de video, juiste lengte, geen overlap, beste eerst."""
    clips = []
    for c in raw_clips if isinstance(raw_clips, list) else []:
        if not isinstance(c, dict):
            continue
        try:
            start, end = float(c["start"]), float(c["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if not (math.isfinite(start) and math.isfinite(end)):
            continue
        start = max(0.0, min(start, duration))
        end = max(0.0, min(end, duration))
        if end - start > max_len:          # te lang: afkappen
            end = start + max_len
        if end - start < min(min_len, duration) * 0.6:   # duidelijk te kort: overslaan
            continue
        hashtags = [
            "#" + str(h).strip().lstrip("#").replace(" ", "")
            for h in (c.get("hashtags") or []) if str(h).strip().lstrip("#")
        ][:5]
        try:
            score = int(c.get("score") or 0)
        except (TypeError, ValueError):
            score = 0
        clips.append({
            "start": round(start, 2),
            "end": round(end, 2),
            "caption": " ".join(str(c.get("caption") or "").split())[:120],
            "description": " ".join(str(c.get("description") or "").split())[:500],
            "hashtags": hashtags,
            "reason": " ".join(str(c.get("reason") or "").split())[:300],
            "score": max(0, min(100, score)),
        })

    chosen = []
    for c in sorted(clips, key=lambda c: -c["score"]):
        if any(c["start"] < o["end"] and c["end"] > o["start"] for o in chosen):
            continue
        chosen.append(c)
        if len(chosen) >= count:
            break
    return sorted(chosen, key=lambda c: c["start"])


def suggest_clips(cues, duration, count=5, min_len=20, max_len=60,
                  bins=None, caption_language=None, client=None):
    """Vraag Claude om de beste TikTok-momenten. Geeft een gecontroleerde lijst clips terug."""
    if not cues:
        raise AIClipError("Er is geen spraak gevonden in de video, dus de AI heeft niets om te lezen.")
    count = max(1, min(MAX_CLIPS, int(count)))
    try:
        import anthropic
    except ImportError:
        raise AIClipError("Het pakket 'anthropic' ontbreekt: pip install anthropic")
    if client is None:
        client = anthropic.Anthropic()

    prompt = _user_prompt(build_transcript(cues), duration, count, min_len, max_len,
                          _signal_lines(bins), caption_language)
    try:
        response = client.beta.messages.create(
            model=AI_MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            output_config={
                "effort": "high",
                "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
            },
        )
    except anthropic.AuthenticationError:
        raise AIClipError("Geen geldige Anthropic API-sleutel. Zet ANTHROPIC_API_KEY in het .env-bestand.")
    except anthropic.RateLimitError:
        raise AIClipError("De AI is even overbelast (rate limit). Probeer het zo opnieuw.")
    except anthropic.APIConnectionError:
        raise AIClipError("Kon de AI niet bereiken. Controleer je internetverbinding.")
    except anthropic.APIStatusError as e:
        raise AIClipError(f"AI-fout ({e.status_code}): {e.message}")
    except TypeError as e:              # de SDK geeft dit als er geen sleutel is ingesteld
        if "authentication" not in str(e):
            raise
        raise AIClipError("Geen Anthropic API-sleutel gevonden. Zet ANTHROPIC_API_KEY in het .env-bestand.")
    except anthropic.AnthropicError as e:
        raise AIClipError(f"AI niet beschikbaar: {e}")

    if response.stop_reason == "refusal":
        raise AIClipError("De AI weigerde deze video te verwerken.")
    if response.stop_reason == "max_tokens":
        raise AIClipError("Het AI-antwoord werd afgekapt. Probeer minder clips.")
    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise AIClipError("De AI gaf een onleesbaar antwoord terug.")
    clips = clean_clips(data.get("clips"), duration, count, min_len, max_len)
    if not clips:
        raise AIClipError("De AI vond geen geschikte momenten voor clips.")
    return clips
