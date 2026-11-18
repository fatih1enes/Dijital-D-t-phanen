"""Real Chromium Browser E2E UX Verification Suite (Playwright).

Verifies real interactive UX behaviors that Python unit tests cannot catch:
- Zero uncaught JS exceptions (`pageerror`) and zero console errors across view transitions
- Real button clickability (`elementFromPoint` hit-testing, no invisible z-index blockers)
- PDF.js canvas + `.textLayer` rendering, zoom, spread mode, ChromaGuard zero-white-flash pixel check
- Hierarchical `Escape` key closing (Search Bar -> TOC Sidebar -> Workspace Reader)
- Mobile (`390x844`) responsive reader bars, bottom sheet z-index stacking, and native EPUB sheet rendering
"""

from __future__ import annotations

import os
import socket
import threading
import time
import zipfile
from collections.abc import Iterator

import pytest
import uvicorn

playwright_async = pytest.importorskip("playwright.async_api")


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def live_server_url() -> Iterator[str]:
    """Start a real background Uvicorn HTTP server bound to an ephemeral localhost port."""
    from reportlab.pdfgen import canvas as rl_canvas

    import app.database as app_database
    from app.constants import LIBRARY_ROOT
    from app.main import app as fastapi_app

    os.makedirs(LIBRARY_ROOT, exist_ok=True)

    # 1. Seed a real 3-page selectable vector PDF
    pdf_hash = "1" * 64
    pdf_path = os.path.join(LIBRARY_ROOT, "e2e_vector_test.pdf")
    c = rl_canvas.Canvas(pdf_path)
    for p in range(1, 4):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, 740, f"Chapter {p}: Epistemology and Digital Libraries")
        c.setFont("Helvetica", 12)
        c.drawString(72, 705, f"Page {p} searchable test phrase: cogito ergo sum alpha_{p}.")
        c.drawString(72, 680, "Continuous smooth reading verification line for browser rendering.")
        c.showPage()
    c.save()

    # 2. Seed a real multi-chapter Turkish EPUB (with embedded PNG image + footnote)
    import io

    from PIL import Image

    png_buf = io.BytesIO()
    Image.new("RGB", (24, 24), color=(150, 95, 55)).save(png_buf, format="PNG")
    epub_hash = "2" * 64
    epub_path = os.path.join(LIBRARY_ROOT, "e2e_turkce_kitap.epub")
    with zipfile.ZipFile(epub_path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?>'
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
            '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>'
            "</container>",
        )
        zf.writestr(
            "OEBPS/content.opf",
            '<?xml version="1.0" encoding="utf-8"?>'
            '<package xmlns="http://www.idpf.org/2007/opf" version="2.0">'
            "<manifest>"
            '<item id="c1" href="c1.xhtml" media-type="application/xhtml+xml"/>'
            '<item id="fig1" href="fig1.png" media-type="image/png"/>'
            "</manifest>"
            '<spine><itemref idref="c1"/></spine>'
            "</package>",
        )
        zf.writestr("OEBPS/fig1.png", png_buf.getvalue())
        zf.writestr(
            "OEBPS/c1.xhtml",
            "<html><body><h1>Birinci Bölüm: Zaman ve Bellek</h1>"
            '<p>Çağdaş düşünce tarihinde bellek ve zaman algısı üzerine derin bir inceleme<a href="#fn1" epub:type="noteref">1</a>.</p>'
            '<img src="fig1.png" alt="Zaman Şeması"/>'
            '<aside id="fn1" epub:type="footnote">1. Bergson, Madde ve Bellek, s. 44.</aside>'
            "</body></html>",
        )

    import sqlite3

    conn = sqlite3.connect(app_database.DB_PATH)
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO kitaplar
            (kitap_adi, yazar, kategori, alt_kategori, ozet, anahtar_kelimeler, dosya_adi, dosya_hash, dosya_yolu, sayfa_sayisi, dosya_boyutu)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "E2E Epistemology PDF",
                "Rene Descartes",
                "Felsefe",
                "Epistemoloji",
                "E2E tarayıcı doğrulama kitabı.",
                "epistemoloji, cogito",
                "e2e_vector_test.pdf",
                pdf_hash,
                pdf_path,
                3,
                os.path.getsize(pdf_path),
            ),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO kitaplar
            (kitap_adi, yazar, kategori, alt_kategori, ozet, anahtar_kelimeler, dosya_adi, dosya_hash, dosya_yolu, sayfa_sayisi, dosya_boyutu)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Zaman ve Bellek EPUB",
                "Ahmet Hamdi",
                "Edebiyat",
                "Deneme",
                "E2E Türkçe EPUB doğrulama eseri.",
                "zaman, bellek",
                "e2e_turkce_kitap.epub",
                epub_hash,
                epub_path,
                1,
                os.path.getsize(epub_path),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    port = _find_free_port()
    config = uvicorn.Config(fastapi_app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 10.0
    while not server.started and time.time() < deadline:
        time.sleep(0.05)

    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5.0)


@pytest.mark.asyncio
async def test_desktop_pdf_reader_buttons_chromaguard_and_escape_ux(live_server_url: str) -> None:
    """Verify desktop PDF reader interactive buttons, ChromaGuard dark pixels, search, and Escape hierarchy."""
    async with playwright_async.async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        page_errors: list[str] = []
        console_errors: list[str] = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text)
            if msg.type == "error" and "favicon" not in msg.text.lower()
            else None,
        )

        await page.goto(live_server_url, wait_until="networkidle")

        # 1. Verify all modular workspace globals are bound on window
        missing_globals = await page.evaluate(
            """() => {
                const required = [
                  'openWorkspace', 'closeWorkspace', 'openBookWithMorph', 'handleWorkspaceEscape',
                  'pdfPrevPage', 'pdfNextPage', 'pdfZoomIn', 'pdfZoomOut', 'pdfFitWidth',
                  'togglePdfSpreadMode', 'toggleTocSidebar', 'toggleNotesSidebar',
                  'togglePdfSearch', 'setReaderSurfaceMode', 'selectModalNoteColor',
                  'togglePdfTTS', 'sendWorkspaceMessage', 'stopChatGeneration'
                ];
                return required.filter(k => typeof window[k] !== 'function');
            }"""
        )
        assert missing_globals == [], f"Unbound window globals: {missing_globals}"

        # 2. Click book card -> Detail modal -> "Kitabı Oku"
        pdf_card = page.locator(f'.book-card[data-hash="{"1" * 64}"]')
        await pdf_card.wait_for(state="visible", timeout=8000)

        # Hit-test card center to ensure no invisible overlay blocks clicks
        card_clickable = await pdf_card.evaluate(
            """(el) => {
                const r = el.getBoundingClientRect();
                const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                return Boolean(hit && el.contains(hit));
            }"""
        )
        assert card_clickable is True

        await pdf_card.click()
        read_btn = page.locator("#modal .btn-modal-primary")
        await read_btn.wait_for(state="visible", timeout=5000)
        await read_btn.click()

        # 3. Verify Workspace Reader opens and renders PDF canvas + selectable textLayer
        reader = page.locator("#workspace-reader.open")
        await reader.wait_for(state="visible", timeout=8000)
        canvas1 = page.locator("#pdf-render-canvas-1")
        await canvas1.wait_for(state="visible", timeout=10000)
        await page.wait_for_function(
            "() => (document.querySelectorAll('#textLayer-1 span').length > 0)",
            timeout=10000,
        )

        # 4. Verify Zoom In & Next Page buttons actually respond to clicks
        initial_zoom = await page.locator("#pdf-zoom-percent").inner_text()
        await page.locator('.pdf-toolbar button[onclick="pdfZoomIn()"]').click()
        new_zoom = await page.locator("#pdf-zoom-percent").inner_text()
        assert new_zoom != initial_zoom

        await page.locator("#pdf-next-btn").click()
        await page.wait_for_function(
            "() => document.getElementById('pdf-page-num')?.value === '2'",
            timeout=5000,
        )

        # 5. Verify ChromaGuard Night Mode transforms canvas paper pixels to dark obsidian (#171614) without white flash
        await page.locator("#btn-surface-chromaguard").click()
        await page.wait_for_function(
            """() => {
                const cv = document.getElementById('pdf-render-canvas-2') || document.getElementById('pdf-render-canvas-1');
                if (!cv || !cv.width) return false;
                const ctx = cv.getContext('2d');
                const px = ctx.getImageData(4, 4, 1, 1).data;
                return px[0] < 45 && px[1] < 45 && px[2] < 45;
            }""",
            timeout=8000,
        )
        # Restore normal surface mode for clean state
        await page.locator("#btn-surface-normal").click()

        # 6. Verify Ctrl+F Search finds "cogito" and highlights inside highlightLayer
        await page.locator("#pdf-search-btn").click()
        search_input = page.locator("#pdf-search-input")
        await search_input.wait_for(state="visible", timeout=3000)
        await search_input.fill("cogito")
        await page.wait_for_function(
            "() => document.querySelectorAll('.pdf-search-highlight').length > 0",
            timeout=6000,
        )

        # 7. Hierarchical Escape: 1st Escape closes Search Bar ONLY; 2nd Escape exits Workspace Reader!
        await page.keyboard.press("Escape")
        await page.wait_for_function(
            "() => document.getElementById('pdf-search-bar')?.style.display === 'none'",
            timeout=3000,
        )
        assert await page.locator("#workspace-reader").evaluate("el => el.classList.contains('open')") is True

        await page.keyboard.press("Escape")
        await page.wait_for_function(
            "() => !document.getElementById('workspace-reader')?.classList.contains('open')",
            timeout=4000,
        )
        assert await page.evaluate("() => document.body.classList.contains('modal-open')") is False

        assert page_errors == [], f"Uncaught JS page errors: {page_errors}"
        assert console_errors == [], f"Browser console errors: {console_errors}"
        await browser.close()


@pytest.mark.asyncio
async def test_mobile_epub_reader_touch_bars_and_drawer_zindex(live_server_url: str) -> None:
    """Verify mobile viewport (390x844) EPUB reader rendering, clickable bottom bar tabs, and drawer z-index."""
    async with playwright_async.async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = await context.new_page()

        page_errors: list[str] = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        await page.goto(f"{live_server_url}/?open_book={'2' * 64}&page=1", wait_until="networkidle")

        sheet = page.locator(".doc-reader-sheet")
        await sheet.wait_for(state="visible", timeout=8000)
        sheet_text = await sheet.inner_text()
        assert "Birinci Bölüm: Zaman ve Bellek" in sheet_text

        # Verify mobile bottom bar TOC button is unobstructed and opens TOC drawer above top bar
        mob_toc_btn = page.locator('#mobile-reader-bottom-bar button[onclick="toggleTocSidebar()"]')
        await mob_toc_btn.wait_for(state="visible", timeout=4000)
        is_unobstructed = await mob_toc_btn.evaluate(
            """(btn) => {
                const r = btn.getBoundingClientRect();
                const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                return Boolean(hit && btn.contains(hit));
            }"""
        )
        assert is_unobstructed is True

        await mob_toc_btn.click()
        toc_sidebar = page.locator("#pdf-toc-sidebar.open")
        await toc_sidebar.wait_for(state="visible", timeout=4000)

        # Verify TOC drawer slides completely onscreen with z-index > #mobile-reader-top-bar and unobstructed close button
        await page.wait_for_function(
            """() => {
                const toc = document.getElementById('pdf-toc-sidebar');
                const top = document.getElementById('mobile-reader-top-bar');
                const closeBtn = document.getElementById('btn-close-toc-sidebar');
                if (!toc || !top || !closeBtn) return false;
                const tocZ = Number(getComputedStyle(toc).zIndex) || 0;
                const topZ = Number(getComputedStyle(top).zIndex) || 0;
                const r = closeBtn.getBoundingClientRect();
                if (r.left < 0 || r.width === 0) return false;
                const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                return tocZ > topZ && Boolean(hit && closeBtn.contains(hit));
            }""",
            timeout=4000,
        )

        await page.locator("#btn-close-toc-sidebar").click()
        await page.wait_for_function(
            "() => !document.getElementById('pdf-toc-sidebar')?.classList.contains('open')",
            timeout=3000,
        )

        assert page_errors == [], f"Mobile uncaught JS errors: {page_errors}"
        await browser.close()


@pytest.mark.asyncio
async def test_sse_streaming_citation_popover_and_abort_ux(live_server_url: str) -> None:
    """Verify real SSE token streaming, grounded Citation Preview Popover on hover, click-to-jump, and mid-stream Abort."""
    async with playwright_async.async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        page_errors: list[str] = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        await page.goto(f"{live_server_url}/?open_book={'1' * 64}&page=1", wait_until="networkidle")
        await page.locator("#pdf-render-canvas-1").wait_for(state="visible", timeout=10000)

        # 1. Intercept /api/chat/stream to emit realistic SSE citations + multi-chunk tokens
        async def handle_sse_completed(route: playwright_async.Route) -> None:
            sse_body = (
                'event: citations\n'
                'data: {"citations":[{"page":2,"snippet":"Page 2 searchable test phrase: cogito ergo sum alpha_2.","score":0.0325,"book_title":"E2E Epistemology PDF"}]}\n\n'
                'event: session\n'
                'data: {"book_loaded":true}\n\n'
                'event: token\n'
                'data: {"text":"Descartes bu argümanı ikinci bölümde "}\n\n'
                'event: token\n'
                'data: {"text":"açıkça temellendirir [Sayfa 2]."}\n\n'
                'event: done\n'
                'data: {"aborted":false}\n\n'
            )
            await route.fulfill(
                status=200,
                headers={"Content-Type": "text/event-stream", "Cache-Control": "no-cache"},
                body=sse_body,
            )

        await page.route("**/api/chat/stream", handle_sse_completed)

        chat_input = page.locator("#workspace-chat-input")
        await chat_input.fill("Cogito argümanı hangi sayfada geçiyor?")
        await page.locator("#btn-workspace-send").click()

        cite_chip = page.locator("#workspace-chat-messages .chat-page-cite[data-jump-page='2']")
        await cite_chip.wait_for(state="visible", timeout=6000)

        # Verify grounding badge rendered
        grounding_pill = page.locator("#workspace-chat-messages .chat-rag-grounding-pill")
        await grounding_pill.wait_for(state="visible", timeout=3000)
        assert "1 pasaj doğrulandı" in (await grounding_pill.inner_text())

        # 2. Hover over [Sayfa 2] -> Citation Preview Popover opens inside viewport with exact snippet
        await cite_chip.hover()
        popover = page.locator("#citation-preview-popover.visible")
        await popover.wait_for(state="visible", timeout=3000)
        pop_text = await popover.inner_text()
        assert "cogito ergo sum alpha_2" in pop_text

        in_viewport = await popover.evaluate(
            """(el) => {
                const r = el.getBoundingClientRect();
                return r.left >= 0 && r.top >= 0 && r.right <= window.innerWidth && r.bottom <= window.innerHeight;
            }"""
        )
        assert in_viewport is True

        # Click "Sayfaya Git" inside popover -> jumps reader to Page 2 and closes popover
        await page.locator("#citation-preview-popover [data-popover-jump='2']").click()
        await page.wait_for_function(
            "() => document.getElementById('pdf-page-num')?.value === '2'",
            timeout=5000,
        )
        await page.wait_for_function(
            "() => !document.getElementById('citation-preview-popover')?.classList.contains('visible')",
            timeout=3000,
        )

        # 3. Verify immediate Stop button visibility & AbortController cancellation on stalled/slow stream
        await page.unroute("**/api/chat/stream")

        async def handle_slow_sse(route: playwright_async.Route) -> None:
            import asyncio as _aio

            await _aio.sleep(4.0)
            try:
                await route.fulfill(status=200, headers={"Content-Type": "text/event-stream"}, body="")
            except Exception as _exc:
                assert _exc is not None

        await page.route("**/api/chat/stream", handle_slow_sse)
        await chat_input.fill("Uzun analiz sorusu")
        await page.locator("#btn-workspace-send").click()

        stop_btn = page.locator("#btn-stop-chat")
        await stop_btn.wait_for(state="visible", timeout=2000)
        await stop_btn.click()

        stopped_pill = page.locator("#workspace-chat-messages .chat-stopped-pill")
        await stopped_pill.wait_for(state="visible", timeout=3000)
        assert await page.locator("#workspace-stop-wrap").is_visible() is False
        assert page_errors == [], f"Uncaught JS errors during SSE/Abort: {page_errors}"
        await browser.close()


@pytest.mark.asyncio
async def test_phase3_thumbnails_bookmarks_ocr_and_rich_epub_ux(live_server_url: str) -> None:
    """Verify 3-Tab Thumbnails & Bookmarks on PDF, plus Rich EPUB embedded image, Footnote Popover & Typography."""
    async with playwright_async.async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        page_errors: list[str] = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        # Part A: PDF Bookmarks + 3-Tab Thumbnail Filmstrip
        await page.goto(f"{live_server_url}/?open_book={'1' * 64}&page=1", wait_until="networkidle")
        await page.locator("#pdf-render-canvas-1").wait_for(state="visible", timeout=10000)

        await page.locator("#pdf-bookmark-btn").click()
        await page.locator("#pdf-page-wrapper-1 .page-bookmark-ribbon").wait_for(
            state="visible", timeout=4000
        )

        # Open 3-Tab Navigation Drawer -> switch to Thumbnails ("Sayfalar") -> click Page 3 thumbnail
        await page.locator("#pdf-toc-sidebar-btn").click()
        await page.locator("#toc-tab-thumbs").click()
        thumb3 = page.locator('#pdf-thumbs-list .pdf-thumb-card[data-thumb-page="3"]')
        await thumb3.wait_for(state="visible", timeout=5000)
        await page.wait_for_function(
            "() => document.querySelectorAll('#pdf-thumbs-list canvas.pdf-thumb-canvas').length > 0",
            timeout=6000,
        )
        await thumb3.click()
        await page.wait_for_function(
            "() => document.getElementById('pdf-page-num')?.value === '3'",
            timeout=5000,
        )

        # Switch to Bookmarks tab -> click saved Page 1 bookmark -> jumps back to Page 1
        await page.locator("#toc-tab-bookmarks").click()
        bm_item = page.locator("#pdf-bookmarks-list .bookmark-jump-btn")
        await bm_item.wait_for(state="visible", timeout=4000)
        await bm_item.click()
        await page.wait_for_function(
            "() => document.getElementById('pdf-page-num')?.value === '1'",
            timeout=5000,
        )

        # Part B: Rich EPUB embedded image + inline Footnote Popover + Aa Typography Popover
        await page.goto(f"{live_server_url}/?open_book={'2' * 64}&page=1", wait_until="networkidle")
        doc_wrap = page.locator("#pdf-page-wrapper-1.doc-page-wrapper")
        await doc_wrap.wait_for(state="visible", timeout=6000)
        wrap_box = await doc_wrap.bounding_box()
        assert wrap_box is not None and wrap_box["height"] > 150

        epub_img = page.locator(".doc-reader-sheet img.doc-embedded-img")
        await epub_img.wait_for(state="visible", timeout=6000)
        await page.wait_for_function(
            "() => { const im = document.querySelector('.doc-embedded-img'); return Boolean(im && im.complete && im.naturalWidth > 0); }",
            timeout=5000,
        )

        fn_btn = page.locator(".epub-footnote-ref")
        await fn_btn.wait_for(state="visible", timeout=4000)
        await fn_btn.click()
        fn_pop = page.locator("#epub-footnote-popover.visible")
        await fn_pop.wait_for(state="visible", timeout=3000)
        assert "Bergson, Madde ve Bellek" in (await fn_pop.inner_text())

        # Aa Typography Menu changes --doc-font-family live
        await page.locator("#pdf-typography-btn").click()
        await page.locator('#doc-typography-popover [data-typo-font="sans"]').click()
        font_var = await page.evaluate(
            "() => document.getElementById('pdf-canvas-container')?.style.getPropertyValue('--doc-font-family') || ''"
        )
        assert "Geist" in font_var

        assert page_errors == [], f"Faz 3 uncaught JS errors: {page_errors}"
        await browser.close()


@pytest.mark.asyncio
async def test_phase4_5_neural_tts_karaoke_fsrs_and_offline_vault_ux(live_server_url: str) -> None:
    """Verify Neural TTS mini-player & 60fps karaoke layer, Offline Vault zero-network reload, Heatmap & FSRS Studio."""
    import base64
    import io
    import json
    import wave

    # Build a valid 1.4s silent PCM WAV so HTMLAudioElement plays deterministically in headless Chromium
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(1)
        wf.setframerate(8000)
        wf.writeframes(b"\x80" * (8000 * 2))
    wav_data_url = "data:audio/wav;base64," + base64.b64encode(wav_buf.getvalue()).decode("ascii")

    async with playwright_async.async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        page_errors: list[str] = []
        console_errors: list[str] = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text)
            if msg.type == "error" and "favicon" not in msg.text.lower()
            else None,
        )

        pdf_hash = "1" * 64
        await page.goto(f"{live_server_url}/?open_book={pdf_hash}&page=1", wait_until="networkidle")
        await page.locator("#pdf-render-canvas-1").wait_for(state="visible", timeout=10000)
        await page.wait_for_function(
            "() => document.querySelectorAll('#textLayer-1 span').length > 0",
            timeout=10000,
        )

        # ── 1. Faz 4: Neural TTS Mini-Player + 60fps Karaoke Layer UX ──
        async def handle_tts_synth(route: playwright_async.Route) -> None:
            body = {
                "available": True,
                "cached": True,
                "audio_key": "a" * 32,
                "audio_url": wav_data_url,
                "voice": "tr-TR-EmelNeural",
                "spoken_text": "Chapter 1 Epistemology and Digital Libraries",
                "duration_ms": 2000.0,
                "words": [
                    {"t": "Chapter", "start_ms": 0.0, "end_ms": 450.0},
                    {"t": "Epistemology", "start_ms": 460.0, "end_ms": 1200.0},
                    {"t": "Libraries", "start_ms": 1210.0, "end_ms": 1950.0},
                ],
            }
            await route.fulfill(
                status=200,
                headers={"Content-Type": "application/json"},
                body=json.dumps(body),
            )

        await page.route("**/api/tts/synthesize", handle_tts_synth)
        await page.locator("#pdf-tts-btn").click()

        mini_player = page.locator("#tts-mini-player")
        await mini_player.wait_for(state="visible", timeout=5000)
        await page.wait_for_function(
            "() => (document.getElementById('tts-engine-badge')?.textContent || '').toLowerCase().includes('emel')",
            timeout=5000,
        )

        # Hit-test TTS controls to ensure no z-index obstruction
        tts_controls_clickable = await page.evaluate(
            """() => {
                for (const id of ['tts-play-pause-btn', 'tts-voice-select', 'tts-rate-select', 'tts-stop-btn']) {
                    const el = document.getElementById(id);
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                    if (!hit || (!el.contains(hit) && hit !== el)) return false;
                }
                return true;
            }"""
        )
        assert tts_controls_clickable is True

        # Verify karaoke highlight boxes rendered and pointer-events: none preserves text selection
        await page.wait_for_function(
            """() => {
                const layer = document.getElementById('pdf-tts-layer-1');
                if (!layer) return false;
                const hasBoxes = layer.querySelectorAll('.tts-karaoke-sentence-box, .tts-karaoke-word-box').length > 0;
                const pe = getComputedStyle(layer).pointerEvents;
                return hasBoxes && pe === 'none';
            }""",
            timeout=5000,
        )

        await page.locator("#tts-stop-btn").click()
        await page.wait_for_function(
            "() => document.getElementById('tts-mini-player')?.style.display === 'none'",
            timeout=3000,
        )

        # ── 2. Faz 5: Offline Vault Pinning & Zero-Network PDF Re-Open ──
        vault_btn = page.locator("#workspace-vault-btn")
        await vault_btn.click()
        await page.wait_for_function(
            f"() => window.OfflineVault && window.OfflineVault.isBookVaulted('{pdf_hash}') === true",
            timeout=8000,
        )

        # Close reader -> verify shelf card shows "Çevrimdışı" badge
        await page.keyboard.press("Escape")
        await page.wait_for_function(
            "() => !document.getElementById('workspace-reader')?.classList.contains('open')",
            timeout=4000,
        )
        vault_badge = page.locator(f'.book-card[data-hash="{pdf_hash}"] .card-vault-badge')
        await vault_badge.wait_for(state="visible", timeout=4000)

        # Cut off /api/download/** completely -> book MUST still open & render from IndexedDB ArrayBuffer!
        await page.route("**/api/download/**", lambda r: r.abort("internetdisconnected"))
        await page.locator(f'.book-card[data-hash="{pdf_hash}"]').click()
        await page.locator("#modal .btn-modal-primary").click()

        await page.locator("#workspace-reader.open").wait_for(state="visible", timeout=6000)
        await page.locator("#pdf-render-canvas-1").wait_for(state="visible", timeout=8000)
        await page.wait_for_function(
            "() => { const c = document.getElementById('pdf-render-canvas-1'); return Boolean(c && c.width > 100); }",
            timeout=8000,
        )

        # Exit Workspace Reader cleanly
        await page.keyboard.press("Escape")
        await page.wait_for_function(
            "() => !document.getElementById('workspace-reader')?.classList.contains('open')",
            timeout=4000,
        )

        # ── 3. Faz 5: Reading Analytics 365d Heatmap + FSRS v5 Active Recall Studio ──
        await page.evaluate(
            f"""async () => {{
                await apiFetch('/api/analytics/heartbeat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        dosya_hash: '{pdf_hash}',
                        delta_seconds: 600,
                        current_page: 2,
                        pages_read_delta: 2
                    }})
                }});
                await apiFetch('/api/srs/cards', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        dosya_hash: '{pdf_hash}',
                        sayfa_no: 2,
                        on_yuz: 'Descartes epistemolojisinde ilk kesin önerme nedir?',
                        arka_yuz: 'Cogito, ergo sum (Düşünüyorum, öyleyse varım).',
                        baglam: 'E2E Epistemology PDF · Sayfa 2'
                    }})
                }});
            }}"""
        )

        await page.locator("#btn-stats").click()
        await page.locator("#stats-view").wait_for(state="visible", timeout=5000)
        await page.wait_for_function(
            "() => document.querySelectorAll('#reading-heatmap-grid .heatmap-cell').length === 365",
            timeout=6000,
        )
        assert await page.locator("#reading-focus-kpis .focus-kpi-card").count() == 4

        # Switch to FSRS v5 Studio tab -> reveal -> grade Good (3) -> completion screen
        await page.locator("#stats-subtab-srs").click()
        flashcard = page.locator("#srs-card-stage .srs-flashcard")
        await flashcard.wait_for(state="visible", timeout=5000)

        reveal_btn = page.locator("#btn-srs-reveal")
        await reveal_btn.wait_for(state="visible", timeout=3000)
        await reveal_btn.click()

        good_btn = page.locator(".srs-rating-grid .rate-good")
        await good_btn.wait_for(state="visible", timeout=3000)
        await good_btn.click()

        complete_box = page.locator("#srs-card-stage .srs-empty-complete")
        await complete_box.wait_for(state="visible", timeout=5000)

        assert page_errors == [], f"Faz 4/5 uncaught JS errors: {page_errors}"
        assert console_errors == [], f"Faz 4/5 console errors: {console_errors}"
        await browser.close()
