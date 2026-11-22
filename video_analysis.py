import math
import re


_TIMESTAMP = re.compile(
    r"(?<![\d:])(?:"
    r"(?P<hours>\d{1,3}):(?P<hour_minutes>\d{1,3}):(?P<hour_seconds>[0-5]\d)"
    r"|(?P<minutes>\d{1,3}):(?P<seconds>[0-5]\d)"
    r")(?![\d:])"
)
_MAX_CHART_BINS = 240


def _comment_timestamps(text):
    for match in _TIMESTAMP.finditer(text):
        if match.group("hours") is not None:
            minutes = int(match.group("hour_minutes"))
            if minutes >= 60:
                continue
            yield (
                int(match.group("hours")) * 3600
                + minutes * 60
                + int(match.group("hour_seconds"))
            )
        else:
            yield int(match.group("minutes")) * 60 + int(match.group("seconds"))


def analyze_video_info(info):
    duration = info.get("duration")
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise ValueError("De videolengte ontbreekt of is ongeldig.")

    comments = info.get("comments") or []
    if not isinstance(comments, list):
        raise ValueError("De videocomments konden niet worden gelezen.")

    bin_seconds = max(30, math.ceil(duration / _MAX_CHART_BINS / 10) * 10)
    bins = [
        {
            "start": start,
            "end": min(start + bin_seconds, duration),
            "comment_mentions": 0,
            "viewer_score": None,
        }
        for start in range(0, math.ceil(duration), bin_seconds)
    ]

    for comment in comments:
        if not isinstance(comment, dict) or not isinstance(comment.get("text"), str):
            continue
        for timestamp in _comment_timestamps(comment["text"]):
            if timestamp < duration:
                bins[int(timestamp // bin_seconds)]["comment_mentions"] += 1

    heatmap = info.get("heatmap") or []
    if not isinstance(heatmap, list):
        heatmap = []
    weighted_scores = [[] for _ in bins]
    for point in heatmap:
        if not isinstance(point, dict):
            continue
        try:
            start = float(point["start_time"])
            end = float(point["end_time"])
            value = float(point["value"])
        except (KeyError, TypeError, ValueError):
            continue
        if not all(math.isfinite(value) for value in (start, end, value)) or end <= start:
            continue
        start = max(start, 0)
        end = min(end, duration)
        if end <= start:
            continue
        first_bin = int(start // bin_seconds)
        last_bin = min(math.ceil(end / bin_seconds) - 1, len(bins) - 1)
        for index in range(first_bin, last_bin + 1):
            overlap = min(end, bins[index]["end"]) - max(start, bins[index]["start"])
            if overlap > 0:
                weighted_scores[index].append((value, overlap))

    for chart_bin, scores in zip(bins, weighted_scores):
        if scores:
            total_weight = sum(weight for _, weight in scores)
            chart_bin["viewer_score"] = sum(
                value * weight for value, weight in scores
            ) / total_weight

    return {
        "duration": duration,
        "comment_count": len(comments),
        "timestamp_mentions": sum(chart_bin["comment_mentions"] for chart_bin in bins),
        "bin_seconds": bin_seconds,
        "bins": bins,
    }
