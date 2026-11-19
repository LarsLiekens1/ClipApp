import os
import sys
import time
import threading
import webbrowser
from pathlib import Path

# Zorg dat Python altijd in de juiste map start
BASE_DIR = Path(__file__).parent.resolve()
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))

from app import app

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
