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

os.environ["CLIPAPP_LOCAL_MODE"] = "1"

import console
from app import app, cleanup_work, print_startup_banner


missing_tools = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
if missing_tools:
    console.line("FOUT  FFmpeg ontbreekt. Installeer FFmpeg (inclusief ffprobe) en voeg het toe aan PATH. "
                 f"Niet gevonden: {', '.join(missing_tools)}", kind="err", file=sys.stderr)
    raise SystemExit(1)

PORT = 5050
URL = f"http://127.0.0.1:{PORT}"


def run_server():
    app.run(host="127.0.0.1", port=PORT, threaded=True)


def open_browser():
    time.sleep(1.2)
    if webbrowser.open(URL):
        console.line(f"Browser geopend op {URL}", kind="ok")
    else:
        console.line(f"Open deze URL in je browser: {URL}", kind="warn")


def main():
    print_startup_banner(PORT)
    cleanup_work()
    threading.Thread(target=open_browser, daemon=True).start()
    try:
        run_server()
    except KeyboardInterrupt:
        console.clear_bar()
        print()
        console.line("ClipAPP is netjes afgesloten. Tot de volgende clip!", kind="ok")


if __name__ == "__main__":
    main()
