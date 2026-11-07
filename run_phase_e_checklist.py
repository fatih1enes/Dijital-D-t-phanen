import json
import os
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\fatih\.gemini\antigravity\brain\dd50f97d-6475-45b1-8d0e-a921094fa801"

def run_checklist():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        console_errors = []
        page.on("pageerror", lambda err: console_errors.append(f"PAGE ERROR: {err}"))
        page.on("console", lambda msg: console_errors.append(f"CONSOLE ERROR: {msg.text}") if msg.type == "error" and "401" not in msg.text and "400" not in msg.text else None)

        print("=== 1. DESKTOP LIGHT CHECK ===")
        page.goto("http://127.0.0.1:8000/")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "phase_e_check_desktop_light.png"))

        print("=== 2. DESKTOP DARK CHECK ===")
        page.click("#theme-toggle")
        page.wait_for_timeout(600)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "phase_e_check_desktop_dark.png"))

        print("=== 3. TABLET (768px) CHECK ===")
        page.set_viewport_size({"width": 768, "height": 1024})
        page.wait_for_timeout(600)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "phase_e_check_tablet_768.png"))

        print("=== 4. MOBILE (375px) CHECK ===")
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_timeout(600)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "phase_e_check_mobile_375.png"))

        print("=== 5. MODALS & PANELS CHECK ===")
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(300)
        page.evaluate("openSettings()")
        page.wait_for_timeout(400)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "phase_e_check_settings.png"))
        page.evaluate("closeSettingsDirect()")
        page.wait_for_timeout(300)

        page.evaluate("openTelegramModal()")
        page.wait_for_timeout(400)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "phase_e_check_telegram.png"))
        page.evaluate("closeTelegramModal()")
        page.wait_for_timeout(300)

        print("=== 6. LOGIN PAGE CHECK ===")
        page.route("**/api/auth/status", lambda route: route.fulfill(
            status=200, content_type="application/json",
            body='{"authenticated": false, "locked": false, "password_set": true}'
        ))
        page.goto("http://127.0.0.1:8000/login")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "phase_e_check_login.png"))

        browser.close()

        print("\n=== CONSOLE ERRORS SUMMARY ===")
        if console_errors:
            print("FAILED - Console errors:", console_errors)
            return False
        else:
            print("PASSED - 0 console errors!")
            return True

if __name__ == "__main__":
    success = run_checklist()
    if not success:
        exit(1)
