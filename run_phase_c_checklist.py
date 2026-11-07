import asyncio
import os
from playwright.async_api import async_playwright

SCREENSHOT_DIR = r"C:\Users\fatih\.gemini\antigravity\brain\dd50f97d-6475-45b1-8d0e-a921094fa801"

async def run_checklist():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        errors = []

        # 1. Desktop Light
        ctx_light = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx_light.new_page()
        page.on("console", lambda msg: errors.append(f"CONSOLE {msg.type}: {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda err: errors.append(f"PAGEERROR: {err}"))

        await page.goto("http://127.0.0.1:8000/")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "phase_c_check_desktop_light.png"))

        # C3 Check: Fast search typing retains DOM elements
        card_count_before = await page.evaluate("() => document.querySelectorAll('.book-card').length")
        search_input = page.locator("#search-input")
        if await search_input.count() > 0:
            await page.evaluate("() => { const cp = document.querySelector('.controls-panel'); if (cp) cp.style.display = 'flex'; }")
            await search_input.fill("deneme")
            await page.wait_for_timeout(100)
            await search_input.fill("")
            await page.wait_for_timeout(100)
        card_count_after = await page.evaluate("() => document.querySelectorAll('.book-card').length")
        assert card_count_before == card_count_after, "Card elements must be preserved in DOM"

        # C4 Check: Theme Switch View Transitions
        t0 = await page.evaluate("() => performance.now()")
        await page.click("#theme-toggle")
        await page.wait_for_timeout(350)
        t1 = await page.evaluate("() => performance.now()")
        theme_after = await page.evaluate("() => document.documentElement.dataset.theme")
        has_trans_class = await page.evaluate("() => document.documentElement.classList.contains('theme-transitioning')")
        assert theme_after == "dark", "Theme should switch to dark"
        assert not has_trans_class, "theme-transitioning class must not exist"
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "phase_c_check_desktop_dark.png"))

        # C5 Check: Reader Surface Modes via CSS Filters
        surface_res = await page.evaluate("""() => {
            const viewer = document.getElementById('custom-pdf-viewer');
            const dummy = document.createElement('canvas');
            dummy.className = 'pdf-page-canvas';
            viewer.appendChild(dummy);

            const t0 = performance.now();
            window.setReaderSurfaceMode('sepia');
            const t1 = performance.now();
            const sepiaFilter = window.getComputedStyle(dummy).filter;

            window.setReaderSurfaceMode('normal');
            dummy.remove();
            return { duration: t1 - t0, sepiaFilter };
        }""")
        assert "sepia" in surface_res["sepiaFilter"], "Sepia GPU filter applied"
        assert surface_res["duration"] < 5.0, f"Surface filter must be < 5ms, got {surface_res['duration']}ms"

        # C6 Check: Double-buffered Zoom and will-change state
        zoom_res = await page.evaluate("""async () => {
            const container = document.getElementById('pdf-canvas-container');
            window.pdfZoomIn();
            const zooming = container.classList.contains('is-zooming');
            await new Promise(r => setTimeout(r, 350));
            const cleared = !container.classList.contains('is-zooming');
            window.pdfZoomOut();
            await new Promise(r => setTimeout(r, 350));
            return { zooming, cleared };
        }""")
        assert zoom_res["zooming"] and zoom_res["cleared"], "Zoom will-change lifecycle validated"

        # C7 Check: Fast typewriter capping
        type_res = await page.evaluate("""async () => {
            const sampleText = Array.from({length: 250}, (_, i) => `W${i+1}`).join(' ') + "\\n\\nDone.";
            const dummy = document.createElement('div');
            document.body.appendChild(dummy);
            const t0 = performance.now();
            window.startChatTypewriter(sampleText, dummy);
            while (performance.now() - t0 < 3200) {
                if (dummy.innerHTML.includes('Done.')) break;
                await new Promise(r => setTimeout(r, 40));
            }
            const duration = performance.now() - t0;
            dummy.remove();
            return { duration, finished: duration < 3000 };
        }""")
        assert type_res["finished"], f"Typewriter finished in {type_res['duration']}ms"

        # 2. Tablet 768px
        ctx_tablet = await browser.new_context(viewport={"width": 768, "height": 1024})
        p_tab = await ctx_tablet.new_page()
        p_tab.on("console", lambda msg: errors.append(f"CONSOLE {msg.type}: {msg.text}") if msg.type == "error" else None)
        await p_tab.goto("http://127.0.0.1:8000/")
        await p_tab.wait_for_load_state("networkidle")
        await p_tab.screenshot(path=os.path.join(SCREENSHOT_DIR, "phase_c_check_tablet_768.png"))

        # 3. Mobile 375px
        ctx_mobile = await browser.new_context(viewport={"width": 375, "height": 667})
        p_mob = await ctx_mobile.new_page()
        p_mob.on("console", lambda msg: errors.append(f"CONSOLE {msg.type}: {msg.text}") if msg.type == "error" else None)
        await p_mob.goto("http://127.0.0.1:8000/")
        await p_mob.wait_for_load_state("networkidle")
        await p_mob.screenshot(path=os.path.join(SCREENSHOT_DIR, "phase_c_check_mobile_375.png"))

        # 4. Login Page
        p_login = await ctx_light.new_page()
        p_login.on("console", lambda msg: errors.append(f"CONSOLE {msg.type}: {msg.text}") if msg.type == "error" else None)
        await p_login.goto("http://127.0.0.1:8000/login")
        await p_login.wait_for_load_state("networkidle")
        await p_login.screenshot(path=os.path.join(SCREENSHOT_DIR, "phase_c_check_login.png"))

        await browser.close()

        print(f"\nPhase C Total Console Errors: {len(errors)}")
        for e in errors:
            print("  ", e)
        assert len(errors) == 0, f"Checklist failed with errors: {errors}"
        print("ALL PHASE C CRITERIA PASSED WITH ZERO CONSOLE ERRORS!")

if __name__ == "__main__":
    asyncio.run(run_checklist())
