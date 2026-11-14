# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec Configuration for Dijital Kütüphane
Produces a high-performance, directory-based distribution (--onedir)
ensuring that user data in veriler/ and configurations are fully persistent.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect hidden modules and submodules
hidden_imports = [
    # Uvicorn core & auto-discovery protocols
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    # FastAPI & Starlette
    "fastapi",
    "starlette",
    "starlette.middleware",
    "starlette.middleware.sessions",
    "fastapi_cache",
    "fastapi_cache.backends.inmemory",
    "jinja2",
    "itsdangerous",
    # Database & async
    "aiosqlite",
    "sqlite3",
    # Document & PDF parsing
    "pdfplumber",
    "pdf2image",
    "PIL",
    "pytesseract",
    "pypdfium2",
    "defusedxml",
    # AI Providers
    "google.genai",
    "openai",
    # Telegram & Networking
    "telethon",
    "cryptg",
    "python-multipart",
    # Internal application routers & services
    "app.routers.auth",
    "app.routers.books",
    "app.routers.chat",
    "app.routers.collections",
    "app.routers.settings",
    "app.routers.tasks",
    "app.routers.telegram",
    "app.routers.opds",
    "app.routers.debate",
    "app.services.pkm_exporter",
    "app.event_bus",
    "app.durable_queue",
    "app.services.chunking_service",
    "app.services.embedding_service",
    "app.services.hybrid_search",
    "app.services.knowledge_graph",
    "app.services.multi_agent_debate",
    "app.services.serendipity_engine",
    "webview",
    "pystray",
]

# Assets and templates bundled into read-only internal directory
datas = [
    ("templates", "templates"),
    ("static", "static"),
    (".env.example", "."),
]

a = Analysis(
    ["main.py"],
    pathex=[os.path.abspath(".")],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tests", "docs", "pytest", "_pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DijitalKutuphane",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to True for initial release to allow viewing logs and server status
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DijitalKutuphane",
)
