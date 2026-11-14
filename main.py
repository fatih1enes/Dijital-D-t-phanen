"""
Dijital Kütüphane - Digital Library Management System

This is the application entry point.
The actual application logic resides in the 'app' package (app/main.py).
"""

import os
import sys
from pathlib import Path

BASE_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.main import app, open_browser  # noqa: E402, F401

if __name__ == "__main__":
    from threading import Timer

    import uvicorn

    from app.auth import _get_access_password
    from app.routers.settings import _get_local_ip

    active_pwd = _get_access_password()
    local_ip = _get_local_ip()
    port = int(os.environ.get("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    print("\n" + "=" * 62)
    print("           DIJITAL KUTUPHANE BASLATILDI")
    print("=" * 62)
    print(f" * Bilgisayar erisimi:  http://localhost:{port}")
    print(f" * Telefon / Yerel ag: http://{local_ip}:{port}")
    if active_pwd:
        print(" * Guvenlik Durumu:    [AKTIF] Sifre korumasi devrede.")
    else:
        print(" * Guvenlik Durumu:    [SERBEST/YEREL] Sifre henuz belirlenmedi.")
        print("   (Telefondan baglanmak icin web'de Ayarlar > Guvenlik & Telefon")
        print("    sekmesinden kolayca erisim sifresi belirleyebilirsiniz.)")
    print("=" * 62 + "\n")

    if os.getenv("AUTO_OPEN_BROWSER", "True").lower() == "true":
        timer = Timer(1.5, open_browser)
        timer.daemon = True
        timer.start()
    uvicorn.run(app, host=host, port=port)
