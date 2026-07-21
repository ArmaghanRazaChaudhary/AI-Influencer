from __future__ import annotations
"""
ONE-TIME ChatGPT login. Run this yourself in your terminal:

    python scripts/chatgpt_login.py

A Chrome window opens. Credentials auto-fill. If Cloudflare shows a
"Verify you are human" checkbox, or asks for a 2FA code, complete it
YOURSELF in the window. The script waits until it sees the chat is ready,
then saves the session to .chatgpt_profile/.

After this succeeds once, generation runs fully headless (no window):
    python scripts/generate_face_variants.py --skip-existing
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright
from pipeline.chatgpt_image_gen import _launch, _STEALTH_JS, _login, _needs_login, CHATGPT_URL


def main() -> None:
    print("=" * 70)
    print(" ChatGPT one-time login")
    print(" A Chrome window will open. If you see a Cloudflare checkbox or a")
    print(" 2FA prompt, click/enter it YOURSELF in the window. Leave it open.")
    print("=" * 70)

    with sync_playwright() as p:
        ctx = _launch(p, headless=False)          # visible window
        ctx.add_init_script(_STEALTH_JS)
        page = ctx.new_page()

        page.goto(CHATGPT_URL, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(4000)

        if not _needs_login(page):
            print("\n[OK] Already logged in — session is valid. Nothing to do.")
            ctx.close()
            return

        # Best-effort auto-fill; then it waits up to 3 min for YOU to finish.
        try:
            _login(page)
        except Exception:
            # _login already waits for the composer; if it threw, give a final manual window
            print("\n[!] Auto-login didn't complete. Finish logging in MANUALLY in the window.")
            print("    Waiting up to 5 minutes for the chat to appear...")
            page.wait_for_selector("#prompt-textarea", timeout=300_000)

        # Confirm and let the session flush to disk
        page.wait_for_selector("#prompt-textarea", timeout=30_000)
        page.wait_for_timeout(3000)
        print("\n[OK] Logged in. Session saved to .chatgpt_profile/")
        print("[OK] You can now run generation headless:")
        print("     python scripts/generate_face_variants.py --skip-existing")
        ctx.close()


if __name__ == "__main__":
    main()
