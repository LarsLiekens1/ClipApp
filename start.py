import hashlib
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Zorg dat Python altijd in de juiste map start
BASE_DIR = Path(__file__).parent.resolve()
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))


def prepare_environment():
    if getattr(sys, "frozen", False):
        return

    venv_dir = BASE_DIR / ".venv"
    venv_python = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    requirements = BASE_DIR / "requirements.txt"

    if not venv_python.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    requirements_hash = hashlib.sha256(requirements.read_bytes()).hexdigest()
    hash_file = venv_dir / ".requirements.sha256"
    if not hash_file.exists() or hash_file.read_text(encoding="ascii").strip() != requirements_hash:
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", str(requirements)],
            check=True,
            cwd=BASE_DIR,
        )
        hash_file.write_text(requirements_hash, encoding="ascii")

    if Path(sys.prefix).resolve() != venv_dir.resolve():
        script = str(Path(__file__).resolve())
        os.execv(str(venv_python), [str(venv_python), script, *sys.argv[1:]])


prepare_environment()

from colorama import Fore, Style, just_fix_windows_console

just_fix_windows_console()
os.environ["CLIPAPP_LOCAL_MODE"] = "1"

from app import app


missing_tools = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
if missing_tools:
    print(
        f"{Fore.RED}[ERROR] FFmpeg ontbreekt. Installeer FFmpeg (inclusief ffprobe) "
        f"en voeg het toe aan PATH.{Style.RESET_ALL} "
        f"Niet gevonden: {', '.join(missing_tools)}",
        file=sys.stderr,
    )
    raise SystemExit(1)

PORT = 5050
URL = f"http://127.0.0.1:{PORT}"

def run_server():
    app.run(host="127.0.0.1", port=PORT, threaded=True)


def print_banner():
    logo = r"""
   ____ _ _       _    ___  ___
  / ___| (_)_ __ | |  / _ \| _ \
 | |   | | | '_ \| | | | | |  _/
 | |___| | | |_) | |_| |_| | |
  \____|_|_| .__/ \___/___/|_|
           |_|
"""
    print(f"{Fore.CYAN}{logo}{Style.RESET_ALL}")
    print(f"  {Fore.MAGENTA}LOCAL VIDEO WORKSPACE{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}[SERVER]  http://127.0.0.1:{PORT}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}[CLIPPER] {URL}/{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}[EDITOR]  {URL}/editor{Style.RESET_ALL}")
    print(f"  {Fore.LIGHTBLACK_EX}{'-' * 52}{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}Stoppen: druk op Ctrl+C.{Style.RESET_ALL}", flush=True)


def open_browser():
    time.sleep(1.2)
    if webbrowser.open(URL):
        print(f"{Fore.GREEN}[OPEN] Browser geopend op {URL}{Style.RESET_ALL}", flush=True)
    else:
        print(f"{Fore.YELLOW}[OPEN] Open deze URL in je browser: {URL}{Style.RESET_ALL}", flush=True)


def main():
    print_banner()
    threading.Thread(target=open_browser, daemon=True).start()
    try:
        run_server()
    except KeyboardInterrupt:
        print(f"\n{Fore.CYAN}[STOP] ClipAPP is netjes afgesloten.{Style.RESET_ALL}", flush=True)

if __name__ == "__main__":
    main()
