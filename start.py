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

from app import app


missing_tools = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
if missing_tools:
    print(
        "FFmpeg ontbreekt. Installeer FFmpeg (inclusief ffprobe) en voeg het toe aan PATH. "
        f"Niet gevonden: {', '.join(missing_tools)}",
        file=sys.stderr,
    )
    raise SystemExit(1)

PORT = 5050
URL = f"http://127.0.0.1:{PORT}"

def run_server():
    app.run(host="127.0.0.1", port=PORT, threaded=True)

def main():
    print("=" * 50)
    print("  ClipAPP Desktop App wordt gestart...")
    print(f"  URL: {URL}")
    print("=" * 50)

    # Kijk of pywebview geinstalleerd is voor een echt app-venster
    has_webview = False
    if sys.platform != "linux":
        try:
            import webview
            has_webview = True
        except ImportError:
            pass

    if has_webview:
        # Start de Flask backend op de achtergrond
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(1.0)
        # Toon native desktop venster
        import webview
        webview.create_window(
            title="ClipAPP",
            url=URL,
            width=1280,
            height=820,
            min_size=(960, 640)
        )
        webview.start()
    else:
        # Fallback: open automatisch je standaard webbrowser
        def open_browser():
            time.sleep(1.2)
            webbrowser.open(URL)

        threading.Thread(target=open_browser, daemon=True).start()
        run_server()

if __name__ == "__main__":
    main()
