"""Alles wat ClipAPP in de terminal laat zien: banner, logregels, laadbalk en spinner.

Eén laadbalk werkt steeds dezelfde regel bij (met \\r), zodat de terminal niet volloopt.
Kleuren en Unicode vallen terug op gewone tekst als de terminal dat niet aankan.
"""
import os
import shutil
import sys
import threading
import time

from colorama import just_fix_windows_console

just_fix_windows_console()
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")       # nooit crashen op een raar teken
    except (AttributeError, ValueError):
        pass


def _supports_unicode():
    enc = (getattr(sys.stdout, "encoding", None) or "").lower()
    try:
        "█━╭│▸✔✖".encode(enc or "ascii")
        return True
    except (LookupError, UnicodeEncodeError):
        return False


COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
UNICODE = _supports_unicode()
_lock = threading.RLock()


# ---------- kleuren ----------

def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m" if COLOR else ""


RESET = "\033[0m" if COLOR else ""
BOLD = "\033[1m" if COLOR else ""
DIM = "\033[2m" if COLOR else ""

CYAN = rgb(34, 211, 238)
VIOLET = rgb(167, 139, 250)
PINK = rgb(244, 114, 182)
GREEN = rgb(52, 211, 153)
YELLOW = rgb(251, 191, 36)
RED = rgb(248, 113, 113)
GREY = rgb(107, 114, 128)
WHITE = rgb(243, 244, 246)

# kleurverloop van cyaan via paars naar roze (zelfde sfeer als de webpagina)
_GRADIENT = [(34, 211, 238), (99, 102, 241), (168, 85, 247), (236, 72, 153)]


def _blend(t):
    t = max(0.0, min(1.0, t)) * (len(_GRADIENT) - 1)
    i = min(int(t), len(_GRADIENT) - 2)
    f = t - i
    a, b = _GRADIENT[i], _GRADIENT[i + 1]
    return tuple(round(a[k] + (b[k] - a[k]) * f) for k in range(3))


def gradient(text, offset=0.0):
    """Tekst met een kleurverloop van links naar rechts."""
    if not COLOR:
        return text
    n = max(len(text) - 1, 1)
    out = []
    for i, ch in enumerate(text):
        out.append(rgb(*_blend((i / n + offset) % 1.0 if offset else i / n)) + ch if ch != " " else ch)
    return "".join(out) + RESET


SYM = {
    "info": "▸" if UNICODE else ">",
    "step": "◆" if UNICODE else "*",
    "ok": "✔" if UNICODE else "+",
    "err": "✖" if UNICODE else "x",
    "warn": "▲" if UNICODE else "!",
    "net": "⇄" if UNICODE else "~",
    "sep": "│" if UNICODE else "|",
    "line": "─" if UNICODE else "-",
    "full": "━" if UNICODE else "#",
    "empty": "─" if UNICODE else "-",
}
SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏" if UNICODE else "|/-\\"


def width():
    return max(40, min(shutil.get_terminal_size((100, 24)).columns, 140))


def _visible_len(s):
    import re
    return len(re.sub(r"\033\[[0-9;]*m", "", s))


# ---------- banner ----------

_LETTERS = {
    "C": [" ██████╗", "██╔════╝", "██║     ", "██║     ", "╚██████╗", " ╚═════╝"],
    "L": ["██╗     ", "██║     ", "██║     ", "██║     ", "███████╗", "╚══════╝"],
    "I": ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
    "P": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔═══╝ ", "██║     ", "╚═╝     "],
    "A": [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
}

_ASCII_LOGO = [
    r"   ____ _     ___ ____     _    ____  ____  ",
    r"  / ___| |   |_ _|  _ \   / \  |  _ \|  _ \ ",
    r" | |   | |    | || |_) | / _ \ | |_) | |_) |",
    r" | |___| |___ | ||  __/ / ___ \|  __/|  __/ ",
    r"  \____|_____|___|_|   /_/   \_\_|   |_|    ",
]


def logo_lines(word="CLIPAPP"):
    if not UNICODE:
        return _ASCII_LOGO
    return ["".join(_LETTERS[c][row] for c in word) for row in range(6)]


def set_title(title):
    print(f"\033]0;{title}\007", end="", flush=True)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        except Exception:
            pass


def banner(port, extra=None):
    """Grote startbanner met het logo en de adressen."""
    set_title("ClipAPP - Local Video Studio")
    url = f"http://127.0.0.1:{port}"
    lines = logo_lines()
    print()
    for row, line in enumerate(lines):
        print("  " + BOLD + gradient(line, offset=row * 0.04 if COLOR else 0.0))
    tagline = "L O C A L   V I D E O   S T U D I O"
    pad = max(0, (_visible_len(lines[0]) - len(tagline)) // 2)
    print("  " + " " * pad + GREY + tagline + RESET)
    print()

    rows = [
        (GREEN, "●" if UNICODE else "*", "SERVER", url),
        (CYAN, SYM["info"], "CLIPPER", f"{url}/"),
        (VIOLET, SYM["info"], "EDITOR", f"{url}/editor"),
    ]
    for label, value in (extra or []):
        rows.append((GREY, SYM["info"], label, value))
    inner = max(len(f"  x  {lab:<9}{val}  ") for _, _, lab, val in rows)
    inner = max(inner, 46)
    tl, tr, bl, br, h, v = ("╭", "╮", "╰", "╯", "─", "│") if UNICODE else ("+", "+", "+", "+", "-", "|")
    print(f"  {GREY}{tl}{h * inner}{tr}{RESET}")
    for color, sym, lab, val in rows:
        text = f"  {sym}  {lab:<9}{val}"
        fill = " " * (inner - len(text))
        print(f"  {GREY}{v}{RESET}  {color}{sym}{RESET}  {BOLD}{WHITE}{lab:<9}{RESET}"
              f"{CYAN}{val}{RESET}{fill}{GREY}{v}{RESET}")
    print(f"  {GREY}{bl}{h * inner}{br}{RESET}")
    print(f"  {GREY}Stoppen: druk op {WHITE}Ctrl+C{GREY}.{RESET}")
    print(flush=True)


# ---------- logregels ----------

_bar_open = False
_last_draw = 0.0
_spin_i = 0


def _clear_bar():
    global _bar_open
    if _bar_open:
        sys.stdout.write("\r\033[2K" if COLOR else "\r" + " " * (width() - 1) + "\r")
        _bar_open = False


def _kind_of(msg):
    if "MISLUKT" in msg or "[FOUT]" in msg or msg.startswith("FOUT"):
        return "err"
    if "ALLES KLAAR" in msg or "KLAAR:" in msg:
        return "ok"
    if msg.startswith(("LET OP", "[LET OP]")) or "mislukt" in msg:
        return "warn"
    if msg.startswith("Stap"):
        return "step"
    if msg.startswith("==="):
        return "head"
    if msg.strip().startswith("klaar in"):
        return "done"
    return "info"


def line(msg, kind=None, file=None):
    """Eén nette logregel: tijd, symbool en tekst in kleur."""
    kind = kind or _kind_of(msg)
    stamp = f"{GREY}{time.strftime('%H:%M:%S')}{RESET}"
    sep = f"{GREY}{SYM['sep']}{RESET}"
    if kind == "head":
        title = msg.strip("= ").strip()
        room = max(4, width() - len(title) - 18)
        text = f"{BOLD}{WHITE}{title}{RESET} {gradient(SYM['line'] * room)}"
        out = f"\n  {stamp} {sep} {text}"
    elif kind == "done":
        out = f"  {stamp} {sep}   {GREEN}{SYM['ok']}{RESET} {GREY}{msg.strip()}{RESET}"
    else:
        color, sym = {
            "err": (RED, SYM["err"]), "ok": (GREEN, SYM["ok"]), "warn": (YELLOW, SYM["warn"]),
            "step": (VIOLET, SYM["step"]), "net": (GREY, SYM["net"]), "info": (CYAN, SYM["info"]),
        }.get(kind, (CYAN, SYM["info"]))
        body = f"{BOLD}{color}{msg}{RESET}" if kind in ("ok", "err") else (
            f"{WHITE}{msg}{RESET}" if kind == "step" else f"{GREY if kind == 'net' else ''}{msg}{RESET}")
        out = f"  {stamp} {sep} {color}{sym}{RESET} {body}"
    with _lock:
        _clear_bar()
        print(out, file=file or sys.stdout, flush=True)


def error_block(title, text):
    """Volledige foutmelding (bv. van ffmpeg) zodat je kunt zien wat er precies misging."""
    with _lock:
        _clear_bar()
        print(f"\n  {RED}{BOLD}{SYM['err']} {title}{RESET}", file=sys.stderr)
        for ln in (text or "").strip().splitlines()[-30:]:
            print(f"  {RED}{SYM['sep']}{RESET} {GREY}{ln}{RESET}", file=sys.stderr)
        print(file=sys.stderr, flush=True)


# ---------- laadbalk ----------

def bar(frac, label="", detail="", force=False):
    """Teken de laadbalk opnieuw op dezelfde regel. frac=None geeft een spinner."""
    global _bar_open, _last_draw, _spin_i
    now = time.time()
    if not force and now - _last_draw < 0.08:
        return                                        # niet vaker dan ~12 keer per seconde
    _last_draw = now
    _spin_i += 1
    cols = width()
    label = (label or "").strip()
    if frac is None:
        spin = SPINNER[_spin_i % len(SPINNER)]
        head = f"  {VIOLET}{spin}{RESET} "
        rest = f"{WHITE}{label}{RESET}" + (f"  {GREY}{detail}{RESET}" if detail else "")
        text = head + rest
    else:
        frac = max(0.0, min(1.0, frac))
        size = max(10, min(36, cols - 60))
        n = int(round(frac * size))
        if COLOR:
            filled = "".join(rgb(*_blend(i / max(size - 1, 1))) + SYM["full"] for i in range(n))
            empty = GREY + SYM["empty"] * (size - n) + RESET
        else:
            filled, empty = SYM["full"] * n, SYM["empty"] * (size - n)
        pct = f"{BOLD}{YELLOW}{int(frac * 100):3d}%{RESET}"
        short = label if len(label) <= 28 else label[:27] + "…"
        text = f"  {VIOLET}{SYM['step']}{RESET} {WHITE}{short:<28}{RESET} {filled}{empty} {pct}"
        if detail:
            text += f"  {GREY}{detail}{RESET}"
    # nooit breder dan de terminal, anders loopt de regel door en werkt \r niet meer
    if _visible_len(text) > cols - 1:
        import re
        plain = re.sub(r"\033\[[0-9;]*m", "", text)[: cols - 2]
        text = plain
    with _lock:
        sys.stdout.write(("\r\033[2K" if COLOR else "\r") + text)
        sys.stdout.flush()
        _bar_open = True


def end_bar():
    """Sluit de laadbalk af zodat hij als laatste stand blijft staan."""
    global _bar_open
    with _lock:
        if _bar_open:
            sys.stdout.write("\n")
            sys.stdout.flush()
            _bar_open = False


def clear_bar():
    with _lock:
        _clear_bar()
        sys.stdout.flush()
