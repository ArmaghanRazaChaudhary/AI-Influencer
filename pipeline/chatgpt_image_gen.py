from __future__ import annotations

"""
ChatGPT web image generation — Playwright browser automation.
Step-by-step explicit flow:
  1. Open visible browser
  2. Go to chatgpt.com — detect if logged out by checking for the Log In button
  3. If logged out: fill email → Continue → fill password → Continue → wait for chat UI
  4. Upload face image → wait 5 seconds
  5. Write prompt → press Enter
  6. Wait for generated image (blob URL)
  7. Extract via canvas → save to disk
"""

import base64
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, Page

from config.settings import BASE_DIR, RAW_DIR, CHATGPT_EMAIL, CHATGPT_PASSWORD

CHATGPT_URL = "https://chatgpt.com"
_PROFILE_DIR = BASE_DIR / ".chatgpt_profile"

_PROMPT_TEMPLATE = (
    "Generate a photorealistic image. "
    "Use the person in the attached photo as the subject — preserve their exact face, skin tone, "
    "hair colour, eye colour, and facial features precisely. Do not alter their appearance. "
    "{scene_prompt} "
    "Must look like a real candid lifestyle photo of this person. Shot on iPhone, natural lighting."
)


# ---------------------------------------------------------------------------
# Step 1 — Launch browser
# ---------------------------------------------------------------------------

def _launch(p, headless: bool = True):
    """
    Launch a persistent-profile browser.

    headless=True (default): no window at all. Works because the saved profile
    already holds a valid ChatGPT session, so Cloudflare treats it as a returning
    user. A stealth init-script (added in the batch fn) hides the automation flag.

    headless=False: visible window — only used as a fallback for first-time login
    if the headless session has expired and needs fresh credentials.
    """
    _PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    args = [
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-dev-shm-usage",
    ]
    # NOTE: do NOT force a custom user_agent — real Chrome invalidates the saved
    # session if the UA differs from when the profile was created.
    kwargs = dict(
        headless=headless,
        viewport={"width": 1280, "height": 900},
        args=args,
    )
    try:
        return p.chromium.launch_persistent_context(str(_PROFILE_DIR), channel="chrome", **kwargs)
    except Exception:
        return p.chromium.launch_persistent_context(str(_PROFILE_DIR), **kwargs)


# Stealth script — hides the signals Cloudflare uses to detect headless automation
_STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
window.chrome = window.chrome || {runtime: {}};
"""


# ---------------------------------------------------------------------------
# Step 2 — Check login state
# ---------------------------------------------------------------------------

def _needs_login(page: Page) -> bool:
    """
    Returns True if we need to log in, False if the chat UI is ready.
    Waits up to 10 seconds for the composer to appear before deciding.
    When in doubt, returns True (login flow handles already-logged-in gracefully).
    """
    if any(k in page.url for k in ("login", "/auth/", "accounts.google", "auth0")):
        return True

    # Wait up to 10 seconds for the chat composer to appear
    try:
        page.wait_for_selector("#prompt-textarea", timeout=10_000)
        return False  # composer found — we're logged in
    except Exception:
        pass

    # Composer didn't appear — need login
    return True


# ---------------------------------------------------------------------------
# Step 3 — Login
# ---------------------------------------------------------------------------

def _try_click(page: Page, selectors: list[str]) -> bool:
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible():
                btn.click()
                return True
        except Exception:
            continue
    return False


def _try_fill(page: Page, selectors: list[str], value: str) -> bool:
    for sel in selectors:
        try:
            field = page.locator(sel).first
            if field.count() > 0 and field.is_visible():
                field.fill(value)
                return True
        except Exception:
            continue
    return False


def _login(page: Page) -> None:
    """
    Best-effort auto-login, then wait up to 3 minutes for the chat composer to appear.

    Every step is tolerant: it auto-fills whatever fields are present, but if Cloudflare,
    a captcha, 2FA, or a layout change blocks automation, the visible window lets YOU
    finish manually. Success = the #prompt-textarea composer becomes visible.
    """
    print("[ChatGPT] Logged out — starting login (auto-fill + manual fallback)...")

    # Click "Log in" on the landing page
    if _try_click(page, [
        "a[data-testid='login-button']",
        "button[data-testid='login-button']",
        "a:has-text('Log in')",
        "button:has-text('Log in')",
        "[href*='/auth/login']",
    ]):
        print("[ChatGPT] Clicked Log in.")
        page.wait_for_timeout(4000)

    # Email (best-effort — page may need a Cloudflare pass first)
    if _try_fill(page, ["input[name='username']", "input[type='email']", "input[autocomplete='username']"], CHATGPT_EMAIL):
        print("[ChatGPT] Email filled.")
        _try_click(page, ["button[type='submit']", "button:has-text('Continue')"])
        page.wait_for_timeout(3000)

    # Password (best-effort)
    if _try_fill(page, ["input[name='password']", "input[type='password']", "input[autocomplete='current-password']"], CHATGPT_PASSWORD):
        print("[ChatGPT] Password filled.")
        _try_click(page, ["button[type='submit']", "button:has-text('Continue')", "button:has-text('Sign in')"])
        page.wait_for_timeout(3000)

    # Handle 2FA if it appears
    try:
        mfa = page.locator(
            "input[name='code'], input[autocomplete='one-time-code'], input[inputmode='numeric']"
        ).first
        if mfa.count() > 0 and mfa.is_visible():
            code = input("\n[ChatGPT] 2FA code required — enter it now: ").strip()
            mfa.fill(code)
            page.locator("button[type='submit']").first.click()
            page.wait_for_timeout(3000)
    except Exception:
        pass

    # Wait for the chat composer — up to 3 min so you can finish any manual step
    # (Cloudflare checkbox, captcha, 2FA, "Verify you're human", etc.) in the window.
    print("[ChatGPT] Waiting for chat to be ready (finish any login step in the window if needed)...")
    page.wait_for_selector("#prompt-textarea", timeout=180_000)
    print("[ChatGPT] Login complete — session saved to profile.")


# ---------------------------------------------------------------------------
# Step 4 — Upload face image
# ---------------------------------------------------------------------------

def _upload_face(page: Page, face_path: Path) -> None:
    """Upload the face reference image and wait 5 seconds for it to process."""
    print(f"[ChatGPT] Uploading face: {face_path.name}")

    # Try the hidden file input first
    file_input = page.locator("input[type='file']").first
    if file_input.count() > 0:
        file_input.set_input_files(str(face_path.resolve()))
        print("[ChatGPT] Face uploaded via file input. Waiting 5 seconds...")
        page.wait_for_timeout(5000)
        return

    # Try clicking the attach/+ button to trigger a file chooser
    attach_selectors = [
        "button[aria-label='Attach files']",
        "button[aria-label='Add files and more']",
        "button[aria-label='Add attachments']",
        "button[aria-label*='ttach']",
        "button[data-testid='attach-button']",
        "button[data-testid='composer-attach-button']",
    ]
    for sel in attach_selectors:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible():
                with page.expect_file_chooser(timeout=5_000) as fc_info:
                    btn.click()
                fc_info.value.set_files(str(face_path.resolve()))
                print(f"[ChatGPT] Face uploaded via attach button. Waiting 5 seconds...")
                page.wait_for_timeout(5000)
                return
        except Exception:
            continue

    # Debug: show what buttons exist
    buttons = page.evaluate("""() =>
        Array.from(document.querySelectorAll('button,[role="button"]')).map(b => ({
            aria: b.getAttribute('aria-label'),
            testid: b.getAttribute('data-testid'),
            text: b.innerText.trim().slice(0, 30),
        })).filter(b => b.aria || b.testid)
    """)
    print("[ChatGPT] Upload button not found. Buttons with aria/testid:", buttons)
    raise RuntimeError("Could not find the ChatGPT file upload button.")


# ---------------------------------------------------------------------------
# Step 5 — Write prompt and send
# ---------------------------------------------------------------------------

def _send_prompt(page: Page, prompt: str) -> None:
    """Type the prompt into the composer and press Enter."""
    print("[ChatGPT] Writing prompt...")

    composer = None
    for sel in ["#prompt-textarea", "div[contenteditable='true'][role='textbox']", "div[contenteditable='true']"]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                composer = el
                break
        except Exception:
            continue

    if not composer:
        raise RuntimeError("Could not find the ChatGPT chat input.")

    composer.click()
    composer.fill(prompt)
    page.wait_for_timeout(500)

    # Try the Send button, fall back to Enter
    sent = False
    for sel in [
        "button[data-testid='send-button']",
        "button[aria-label='Send message']",
        "button[aria-label='Send prompt']",
    ]:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_enabled():
                btn.click()
                sent = True
                print("[ChatGPT] Prompt sent via send button.")
                break
        except Exception:
            continue

    if not sent:
        page.keyboard.press("Enter")
        print("[ChatGPT] Prompt sent via Enter.")


# ---------------------------------------------------------------------------
# Step 6 — Wait for generated image
# ---------------------------------------------------------------------------

def _wait_for_image(page: Page, timeout_ms: int = 180_000) -> str:
    """
    Poll for the generated image. Tries multiple src patterns.
    On timeout, dumps all img tags + page text so we can see exactly what ChatGPT returned.
    """
    print("[ChatGPT] Waiting for image generation (up to 3 min)...")
    selectors = [
        "img[src^='blob:https://chatgpt.com']",
        "img[src^='blob:']",
        "img[src*='oaiusercontent.com']",
        "img[src*='production-files']",
    ]
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if el.count() > 0 and el.is_visible():
                    src = el.get_attribute("src") or ""
                    if src:
                        print(f"[ChatGPT] Image found ({sel})")
                        return src
            except Exception:
                pass
        page.wait_for_timeout(3000)

    # Dump page state so we know what actually appeared
    imgs = page.evaluate("""() =>
        Array.from(document.querySelectorAll('img')).map(i => ({
            src: i.src.slice(0,120), visible: i.offsetWidth > 0
        }))""")
    snippet = page.evaluate("() => document.body.innerText.slice(0, 400)")
    print(f"[ChatGPT] TIMEOUT — imgs on page: {imgs}")
    print(f"[ChatGPT] TIMEOUT — page text: {snippet}")
    raise RuntimeError("Image generation timed out.")


# ---------------------------------------------------------------------------
# Step 7 — Download image via canvas
# ---------------------------------------------------------------------------

def _download(src: str, output_path: Path, page: Page) -> None:
    """
    Extract the generated image using canvas (avoids CORS block on blob fetch).
    Draws the <img> element onto a canvas and exports as base64 PNG.
    """
    b64: str = page.evaluate(
        """(url) => new Promise((resolve, reject) => {
            let img = document.querySelector('img[src="' + url + '"]');
            if (!img) {
                const all = document.querySelectorAll('img[src^="blob:https://chatgpt.com"]');
                if (!all.length) { reject(new Error('img not found')); return; }
                img = all[all.length - 1];
            }
            const done = () => {
                const c = document.createElement('canvas');
                c.width  = img.naturalWidth  || 1024;
                c.height = img.naturalHeight || 1024;
                c.getContext('2d').drawImage(img, 0, 0);
                resolve(c.toDataURL('image/png').split(',')[1]);
            };
            if (img.complete && img.naturalWidth > 0) { done(); }
            else { img.onload = done; img.onerror = () => reject(new Error('img load error')); }
        })""",
        src,
    )
    output_path.write_bytes(base64.b64decode(b64))


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def _new_chat(page: Page) -> None:
    """
    Start a fresh chat WITHOUT a full page reload (keeps the SPA hydrated — critical
    for headless, where reloads don't re-render reliably). Clicks the New Chat button;
    falls back to keyboard shortcut, then to navigation.
    """
    selectors = [
        "a[data-testid='create-new-chat-button']",
        "button[data-testid='create-new-chat-button']",
        "a[aria-label='New chat']",
        "button[aria-label='New chat']",
        "nav a[href='/']",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible():
                btn.click()
                page.wait_for_timeout(2000)
                return
        except Exception:
            continue

    # Fallback 1: Ctrl+Shift+O is ChatGPT's new-chat shortcut
    try:
        page.keyboard.press("Control+Shift+O")
        page.wait_for_timeout(2000)
        if page.locator("#prompt-textarea").first.is_visible():
            return
    except Exception:
        pass

    # Fallback 2: full navigation (last resort)
    page.goto(CHATGPT_URL, wait_until="networkidle")
    page.wait_for_timeout(2000)


def _ensure_composer(page: Page) -> None:
    """Make sure the chat input is present and ready."""
    page.wait_for_selector("#prompt-textarea", timeout=30_000)
    page.wait_for_timeout(1500)


def _generate_one(page: Page, scene_prompt: str, face_path: Path, output_path: Path) -> None:
    """Generate a single image. Assumes composer is already present (fresh chat)."""
    full_prompt = _PROMPT_TEMPLATE.format(scene_prompt=scene_prompt)
    _ensure_composer(page)
    _upload_face(page, face_path)
    _send_prompt(page, full_prompt)
    img_src = _wait_for_image(page)
    _download(img_src, output_path, page)
    print(f"[ChatGPT] Saved: {output_path.name}")


def generate_images_batch(
    tasks: list[tuple[str, Path, Path]],
) -> list[Path]:
    """
    Generate multiple images in ONE browser session — login happens once.

    Args:
        tasks: list of (scene_prompt, face_path, output_path)

    Returns:
        List of output_paths that were successfully saved.
    """
    results: list[Path] = []

    with sync_playwright() as p:
        # --- Try headless first (no window) ---
        ctx = _launch(p, headless=True)
        ctx.add_init_script(_STEALTH_JS)
        page = ctx.new_page()

        print("[ChatGPT] Opening ChatGPT (headless)...")
        page.goto(CHATGPT_URL, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(3000)

        if _needs_login(page):
            # Headless can't pass Cloudflare on the auth page — open a VISIBLE window
            # for login. This happens only when the saved session has expired.
            print("[ChatGPT] Session expired — opening a visible window to log in.")
            print("[ChatGPT] >>> Credentials auto-fill. Complete any captcha/2FA in the window. <<<")
            ctx.close()
            ctx = _launch(p, headless=False)
            ctx.add_init_script(_STEALTH_JS)
            page = ctx.new_page()
            page.goto(CHATGPT_URL, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_timeout(3000)
            if _needs_login(page):
                _login(page)
            print("[ChatGPT] Logged in. Continuing in this window (future runs go headless).")
        else:
            print("[ChatGPT] Already logged in (session from profile).")

        # --- Generate all images in the same session ---
        for i, (scene_prompt, face_path, output_path) in enumerate(tasks, 1):
            print(f"\n[ChatGPT] Image {i}/{len(tasks)}: {output_path.name}")
            try:
                if i > 1:
                    _new_chat(page)  # fresh chat between images (no full reload)
                _generate_one(page, scene_prompt, face_path, output_path)
                results.append(output_path)
            except Exception as e:
                print(f"[ChatGPT] FAILED: {e}")

            if i < len(tasks):
                time.sleep(3)

        ctx.close()

    return results


def generate_image(
    scene_prompt: str,
    face_path: str | Path,
    output_name: str | None = None,
) -> Path:
    """Generate a single image (opens its own session). Used by the main pipeline."""
    face_path = Path(face_path)
    output_name = output_name or f"chatgpt_{int(time.time())}.png"
    output_path = RAW_DIR / output_name

    results = generate_images_batch([(scene_prompt, face_path, output_path)])
    if not results:
        raise RuntimeError("Image generation failed — check logs above.")
    return results[0]
