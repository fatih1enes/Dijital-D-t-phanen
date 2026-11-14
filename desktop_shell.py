"""Native Desktop Shell for Dijital Kütüphane.

Provides a standalone Windows desktop application window using Edge WebView2 (PyWebView)
with system tray integration (Pystray) while simultaneously serving the local network
FastAPI backend for mobile and OPDS e-reader connections.
"""

import os
import sys
import threading
import time
import urllib.request
import webbrowser
from typing import Any

from PIL import Image, ImageDraw


def create_tray_icon_image() -> Image.Image:
    """Create a crisp 64x64 PIL icon representing a book in brand colors for the system tray."""
    size = (64, 64)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer rounded rectangle (brand background)
    brand_color = (192, 82, 46, 255)  # #c0522e
    draw.rounded_rectangle([4, 4, 60, 60], radius=14, fill=brand_color)

    # Book pages motif (cream/white)
    page_color = (250, 248, 244, 255)
    # Left page
    draw.rounded_rectangle([14, 18, 30, 46], radius=3, fill=page_color)
    # Right page
    draw.rounded_rectangle([34, 18, 50, 46], radius=3, fill=page_color)
    # Spine center
    draw.line([32, 17, 32, 47], fill=(220, 210, 195, 255), width=2)

    return img


class DesktopShell:
    """Orchestrates the background FastAPI server and the native PyWebView desktop window."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        self.host = host
        self.port = port
        scheme = "http"
        self.url = f"{scheme}://{host}:{port}"  # NOSONAR
        self.server_thread: threading.Thread | None = None
        self.server_instance: Any = None
        self.window: Any = None
        self.tray_icon: Any = None
        self._is_running = True

    def _run_server(self) -> None:
        """Run Uvicorn server in a dedicated background thread."""
        import uvicorn

        from app.main import app

        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="warning",
            access_log=False,
            lifespan="on",
        )
        self.server_instance = uvicorn.Server(config)
        self.server_instance.run()

    def wait_for_server(self, timeout: float = 15.0) -> bool:
        """Poll the /ready endpoint until the server is ready or timeout expires."""
        start = time.time()
        ready_url = f"{self.url}/ready"
        while time.time() - start < timeout:
            try:
                req = urllib.request.Request(ready_url, headers={"User-Agent": "DesktopShell"})
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                time.sleep(0.2)
        return False

    def _setup_tray(self) -> None:
        """Initialize Pystray system tray icon with context menu."""
        try:
            import pystray

            def on_open(icon: Any, item: Any) -> None:
                if self.window:
                    try:
                        self.window.show()
                        self.window.restore()
                    except Exception:
                        pass

            def on_browser(icon: Any, item: Any) -> None:
                webbrowser.open(self.url)

            def on_quit(icon: Any, item: Any) -> None:
                self.quit()

            menu = pystray.Menu(
                pystray.MenuItem("Kütüphaneyi Aç", on_open, default=True),
                pystray.MenuItem("Tarayıcıda Aç", on_browser),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Çıkış", on_quit),
            )

            icon_img = create_tray_icon_image()
            self.tray_icon = pystray.Icon("DijitalKutuphane", icon_img, "Dijital Kütüphane", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            print(f"System tray icon could not be initialized: {e}")

    def quit(self) -> None:
        """Gracefully shut down window, tray icon, and Uvicorn server."""
        self._is_running = False
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass
        if self.server_instance:
            self.server_instance.should_exit = True

    def launch(self) -> None:
        """Start server and present native desktop window or fallback browser."""
        print(f"[*] Dijital Kütüphane başlatılıyor: {self.url}")

        # Disable main.py auto browser opener so shell handles presentation
        os.environ["AUTO_OPEN_BROWSER"] = "False"

        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()

        if not self.wait_for_server():
            print("[!] Sunucu zaman aşımına uğradı, başlatılamadı.")
            sys.exit(1)

        print("[+] Sunucu hazır. Yerel masaüstü arayüzü açılıyor...")

        # Try pywebview for native Windows Edge Chromium WebView2 window
        try:
            import webview

            self._setup_tray()

            self.window = webview.create_window(
                title="Dijital Kütüphane",
                url=self.url,
                width=1280,
                height=840,
                min_size=(960, 640),
                confirm_close=False,
                text_select=True,
            )

            # Start webview loop (blocks until window is closed)
            webview.start(gui="edgechromium")

            # After window closes, perform clean exit
            self.quit()

        except Exception as err:
            print(f"[*] PyWebView kullanılamadı ({err}). Varsayılan tarayıcı moduna geçiliyor.")
            webbrowser.open(self.url)
            try:
                while self._is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.quit()


if __name__ == "__main__":
    shell = DesktopShell()
    shell.launch()
