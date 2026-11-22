"""Automatische TikTok-voorstellen zonder betaalde AI.

Alles draait lokaal. Elke mogelijke clip (altijd van zinsbegin tot zinseinde) krijgt een score uit:
- hook: begint de clip met een vraag, uitroep, getal of typische hook-woorden?
- tempo: wordt er sneller gesproken dan gemiddeld in de video?
- energie: is het geluid luider dan normaal (lachen, roepen, opwinding)?
- emotie: woorden als "haha", "wow", "echt niet"
- publiek: comment-timestamps en de YouTube-heatmap (alleen als die er zijn)
Strafpunten voor lange stiltes en voor clips die midden in een gedachte beginnen ("en", "maar", ...).
"""
import math
import re
from collections import Counter

MAX_CLIPS = 10
SENTENCE_MAX_SECONDS = 15      # een "zin" wordt nooit langer dan dit
SENTENCE_GAP = 1.0             # pauze die een nieuwe zin begint
MIN_SPACING = 3.0              # seconden tussen twee gekozen clips
CAPTION_MAX = 80

WEIGHTS = {"hook": 0.25, "tempo": 0.12, "energy": 0.2, "emotion": 0.1, "audience": 0.33}

HOOK_WORDS = {
    # nl
    "waarom", "hoe", "wat", "nooit", "altijd", "niemand", "iedereen", "geheim", "eigenlijk",
    "echt", "serieus", "stel", "wist", "fout", "beste", "slechtste", "grootste", "gek", "gekste",
    "probleem", "waarheid", "eerlijk", "moet", "moeten", "stop", "kijk", "luister", "let",
    # en
    "why", "how", "what", "never", "always", "nobody", "everyone", "secret", "actually",
    "really", "seriously", "imagine", "mistake", "best", "worst", "biggest", "crazy", "insane",
    "problem", "truth", "honestly", "must", "stop", "look", "listen", "wait",
}
EMOTION_RE = re.compile(
    r"\b(ha(ha)+|lol|wow|omg|oh my|jezus|echt niet|no way|what the|wtf|damn|holy|"
    r"niet normaal|bizar|insane|crazy)\b|!",
    re.IGNORECASE,
)
WEAK_STARTS = {
    "en", "maar", "dus", "want", "of", "ook", "dan", "die", "dat", "daarom", "nou", "eh", "uh",
    "and", "but", "so", "or", "because", "then", "which", "that", "also", "um", "uh",
}
STOPWORDS = {
    # nl
    "de", "het", "een", "en", "van", "ik", "je", "jij", "dat", "die", "is", "in", "niet", "op",
    "te", "zijn", "er", "met", "maar", "voor", "als", "dan", "wat", "aan", "om", "ook", "nog",
    "wel", "hij", "zij", "ze", "we", "wij", "jullie", "mijn", "jouw", "zo", "naar", "bij", "uit",
    "nu", "kan", "kun", "kunnen", "moet", "heb", "hebt", "heeft", "hebben", "was", "waren", "word",
    "wordt", "worden", "gaan", "gaat", "ga", "doen", "doe", "doet", "gewoon", "echt", "even",
    "heel", "veel", "meer", "geen", "alles", "iets", "niks", "hier", "daar", "deze", "dit",
    "omdat", "want", "dus", "toen", "nou", "ja", "nee", "zeg", "zegt", "weet", "denk", "eigenlijk",
    "allemaal", "andere", "mensen", "zeggen", "zou", "zouden", "door", "over", "tegen", "onder",
    # en
    "the", "a", "an", "and", "of", "to", "is", "it", "you", "that", "in", "i", "for", "on",
    "was", "with", "he", "she", "they", "we", "be", "are", "this", "have", "has", "had", "not",
    "but", "what", "all", "were", "when", "there", "can", "your", "just", "like", "so", "do",
    "about", "would", "if", "out", "get", "got", "know", "really", "think", "going", "gonna",
    "yeah", "right", "okay", "because", "then", "them", "these", "those", "some", "very",
    "from", "into", "than", "been", "being", "will", "could", "should", "people", "thing",
}
_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
_TIMESTAMP_RE = re.compile(r"(^|[^\d:])(?:\d{1,3}:)?\d{1,3}:[0-5]\d(?![\d:])")


class AutoClipError(RuntimeError):
    pass


def _words(text):
    return _WORD_RE.findall(text.lower())


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def build_sentences(cues):
    """Voeg korte ondertitelstukjes samen tot zinnen: [{start, end, text}]."""
    sentences, cur = [], []

    def flush():
        if cur:
            sentences.append({"start": cur[0][0], "end": cur[-1][1],
                              "text": " ".join(t.strip() for _, _, t in cur).strip()})
            cur.clear()

    for start, end, text in cues:
        if cur and (start - cur[-1][1] > SENTENCE_GAP or end - cur[0][0] > SENTENCE_MAX_SECONDS):
            flush()
        cur.append((start, end, text))
        if text.rstrip().endswith((".", "!", "?")):
            flush()
    flush()
    return [s for s in sentences if s["text"]]


def build_transcript(cues):
    """Leesbaar transcript '[start-end] zin' (handig voor debuggen en export)."""
    return "\n".join(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in build_sentences(cues))


def hook_score(text):
    """0..1: hoe goed werkt deze zin als opening van een clip?"""
    words = _words(text)
    if not words:
        return 0.0
    score = 0.0
    if "?" in text:
        score += 0.35
    if "!" in text:
        score += 0.25
    score += min(0.4, 0.15 * sum(1 for w in words if w in HOOK_WORDS))
    if re.search(r"\d", text):
        score += 0.15
    if len(words) <= 12:
        score += 0.1
    if words[0] in WEAK_STARTS:
        score -= 0.3
    return _clamp(score)


def _range_mean(values, start, end):
    """Gemiddelde en maximum van een per-seconde-reeks tussen start en end."""
    a, b = int(start), max(int(start) + 1, int(math.ceil(end)))
    part = values[a:b]
    if not part:
        return 0.0, 0.0
    return sum(part) / len(part), max(part)


def _audience(bins, start, end):
    """Comment-vermeldingen (opgeteld) en heatmapscore (gewogen gemiddelde) in een tijdvak."""
    mentions, weighted, weight = 0.0, 0.0, 0.0
    for b in bins:
        overlap = min(end, b["end"]) - max(start, b["start"])
        if overlap <= 0:
            continue
        frac = overlap / max(1e-6, b["end"] - b["start"])
        mentions += b["mentions"] * frac
        if b["viewers"] is not None:
            weighted += b["viewers"] * overlap
            weight += overlap
    return mentions, (weighted / weight if weight else None)


def _clean_bins(bins):
    out = []
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
        if end > start:
            out.append({"start": start, "end": end, "mentions": max(0, mentions), "viewers": viewers})
    return out


def _candidates(sentences, duration, min_len, max_len):
    """Alle clips die op een zinsbegin starten en op een zinseinde stoppen."""
    out = []
    for i, first in enumerate(sentences):
        for j in range(i, len(sentences)):
            length = sentences[j]["end"] - first["start"]
            if length > max_len:
                break
            if length >= min_len:
                out.append((i, j))
    if out or not sentences:
        return out
    # korte video of lange zinnen: neem dan gewoon de langste stukken die passen
    for i in range(len(sentences)):
        j = i
        while j + 1 < len(sentences) and sentences[j + 1]["end"] - sentences[i]["start"] <= max_len:
            j += 1
        out.append((i, j))
    return out


def _caption_from_comments(comments, start, end):
    best = None
    for c in comments or []:
        if not isinstance(c, dict) or not isinstance(c.get("text"), str):
            continue
        stamps = c.get("timestamps") or []
        if not any(isinstance(t, (int, float)) and start <= t < end for t in stamps):
            continue
        likes = c.get("like_count") or 0
        text = _TIMESTAMP_RE.sub(r"\1", c["text"])
        text = re.sub(r"^[\s:;,.\-–—]+|[\s:;,.\-–—]+$", "", " ".join(text.split()))
        if text and likes >= 5 and (best is None or likes > best[0]):
            best = (likes, text)
    return best


def _shorten(text, limit=CAPTION_MAX):
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit - 1].rsplit(" ", 1)[0].rstrip(",;:- ")
    return cut + "…"


def _hashtags(clip_text, doc_freq, n_docs):
    counts = Counter(w for w in _words(clip_text)
                     if len(w) >= 4 and w not in STOPWORDS and w not in HOOK_WORDS)
    ranked = sorted(
        counts.items(),
        key=lambda kv: -(kv[1] * math.log((n_docs + 1) / (1 + doc_freq.get(kv[0], 0))) + 1e-9 * len(kv[0])),
    )
    return ["#" + w for w, _ in ranked[:3]] + ["#fyp"]


def suggest_clips(cues, duration, count=5, min_len=20, max_len=60,
                  bins=None, comments=None, energy=None):
    """Kies de beste, niet-overlappende clips. Geeft [{start, end, caption, description,
    hashtags, reason, score}] terug, gesorteerd op starttijd."""
    count = max(1, min(MAX_CLIPS, int(count)))
    duration = float(duration)
    min_len = min(float(min_len), duration)
    max_len = max(min_len, min(float(max_len), duration))
    bins = _clean_bins(bins)
    energy = [float(e) for e in (energy or []) if isinstance(e, (int, float)) and math.isfinite(e)]
    sentences = build_sentences(cues or [])

    if not sentences and not energy and not bins:
        raise AutoClipError("Er is geen spraak gevonden in de video, dus er valt niets te kiezen.")

    # --- referentiewaarden voor de hele video ---
    def median(values):
        values = sorted(values)
        return values[len(values) // 2] if values else 0.0

    all_words = sum(len(_words(s["text"])) for s in sentences)
    spoken = sum(s["end"] - s["start"] for s in sentences) or 1.0
    avg_tempo = all_words / spoken
    med_energy = median([e for e in energy if e > 0]) or 1.0
    viewer_values = [b["viewers"] for b in bins if b["viewers"] is not None]
    min_view, max_view = (min(viewer_values), max(viewer_values)) if viewer_values else (0.0, 0.0)
    doc_freq = Counter(w for s in sentences for w in set(_words(s["text"])))

    # --- kandidaten: zinnen, of (zonder spraak) vaste vensters ---
    spans = []
    for i, j in _candidates(sentences, duration, min_len, max_len):
        spans.append((sentences[i]["start"], sentences[j]["end"], sentences[i:j + 1]))
    if not spans:
        window = (min_len + max_len) / 2
        t = 0.0
        while t + window <= duration + 0.01:
            spans.append((t, t + window, []))
            t += 5.0

    max_mentions = max((_audience(bins, a, b)[0] for a, b, _ in spans), default=0.0)

    def loud(start, end):
        mean_e, peak_e = _range_mean(energy, start, end)
        return max(0.0, mean_e / med_energy - 1), max(0.0, peak_e / med_energy - 1)

    loud_raw = [loud(a, b) for a, b, _ in spans] if energy else []
    max_loud_mean = max((m for m, _ in loud_raw), default=0.0) or 1.0
    max_loud_peak = max((p for _, p in loud_raw), default=0.0) or 1.0
    has = {
        "hook": bool(sentences), "tempo": bool(sentences), "emotion": bool(sentences),
        "energy": bool(energy), "audience": max_mentions > 0 or max_view > min_view,
    }

    scored = []
    for idx, (start, end, sents) in enumerate(spans):
        length = max(0.5, end - start)
        text = " ".join(s["text"] for s in sents)
        features, notes = {}, []

        if sents:
            opener = max(sents[:3], key=lambda s: hook_score(s["text"]))
            features["hook"] = max(hook_score(sents[0]["text"]), 0.8 * hook_score(opener["text"]))
            if features["hook"] >= 0.5:
                notes.append("sterke hook")
            n_words = len(_words(text))
            talk = sum(s["end"] - s["start"] for s in sents) or 1.0
            features["tempo"] = _clamp((n_words / talk) / (avg_tempo or 1) - 0.6)
            if features["tempo"] >= 0.7:
                notes.append("snel en levendig gesproken")
            emo = len(EMOTION_RE.findall(text))
            features["emotion"] = _clamp(emo / max(1.0, length / 15))
            if features["emotion"] >= 0.6:
                notes.append("veel emotie")
        if energy:
            raw_mean, raw_peak = loud_raw[idx]
            features["energy"] = 0.7 * raw_mean / max_loud_mean + 0.3 * raw_peak / max_loud_peak
            if features["energy"] >= 0.5:
                notes.append("luid/energiek moment")
        if has["audience"]:
            mentions, viewers = _audience(bins, start, end)
            parts = []
            if max_mentions > 0:
                parts.append(_clamp(mentions / max_mentions))
                if mentions >= 1:
                    notes.append(f"{round(mentions)} comment-timestamp(s)")
            if viewers is not None and max_view > min_view:
                parts.append(_clamp((viewers - min_view) / (max_view - min_view)))
                if parts[-1] >= 0.7:
                    notes.append("veel herbekeken (heatmap)")
            features["audience"] = sum(parts) / len(parts) if parts else 0.0

        used = {k: w for k, w in WEIGHTS.items() if has[k] and k in features}
        total = sum(used.values()) or 1.0
        score = sum(features[k] * w for k, w in used.items()) / total

        # strafpunten
        if sents:
            gaps = sum(max(0.0, b["start"] - a["end"] - 0.5) for a, b in zip(sents, sents[1:]))
            score -= 0.6 * _clamp(gaps / length)
            first_words = _words(sents[0]["text"])
            if first_words and first_words[0] in WEAK_STARTS:
                score -= 0.12
            if not sents[-1]["text"].rstrip().endswith((".", "!", "?")):
                score -= 0.05
        # lichte voorkeur voor het midden van de gevraagde lengte
        target = (min_len + max_len) / 2
        score -= 0.05 * abs(length - target) / max(1.0, max_len - min_len)

        scored.append({"start": start, "end": end, "sents": sents, "text": text,
                       "score": score, "notes": notes})

    # --- beste niet-overlappende clips kiezen ---
    chosen = []
    best = max((c["score"] for c in scored), default=0.0)
    for c in sorted(scored, key=lambda c: -c["score"]):
        if chosen and c["score"] < 0.25 * best:      # rest is veel zwakker: liever minder clips
            break
        if any(c["start"] < o["end"] + MIN_SPACING and c["end"] > o["start"] - MIN_SPACING
               for o in chosen):
            continue
        chosen.append(c)
        if len(chosen) >= count:
            break

    results = []
    for c in chosen:
        sents = c["sents"]
        comment = _caption_from_comments(comments, c["start"], c["end"])
        if sents:
            hook = max(sents[:3], key=lambda s: hook_score(s["text"]))["text"]
        else:
            hook = ""
        caption = comment[1] if comment and (not hook or hook_score(hook) < 0.5) else hook
        description = next((s["text"] for s in sents if s["text"] != caption), "") or caption
        results.append({
            "start": round(max(0.0, c["start"] - 0.15), 2),       # klein beetje lucht vooraan
            "end": round(min(duration, c["end"] + 0.4), 2),        # en de laatste woorden laten uitklinken
            "caption": _shorten(caption[:1].upper() + caption[1:]) if caption else "",
            "description": _shorten(description[:1].upper() + description[1:], 300),
            "hashtags": _hashtags(c["text"], doc_freq, len(sentences)) if sents else ["#fyp"],
            "reason": ", ".join(c["notes"][:3]).capitalize() or "Beste combinatie van signalen",
            "score": int(round(_clamp(c["score"]) * 100)),
        })
    if not results:
        raise AutoClipError("Geen geschikte momenten gevonden. Probeer een kortere cliplengte.")
    return sorted(results, key=lambda c: c["start"])


def loudness_per_second(samples, rate=16000):
    """RMS-luidheid per seconde uit een float-array (zoals read_wav() teruggeeft)."""
    import numpy as np
    n = len(samples) // rate
    if n == 0:
        return []
    frames = np.asarray(samples[: n * rate], dtype=np.float32).reshape(n, rate)
    return [round(float(v), 5) for v in np.sqrt((frames ** 2).mean(axis=1))]
