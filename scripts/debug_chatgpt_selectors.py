from __future__ import annotations
"""Quick debug: opens ChatGPT, prints all buttons and inputs so we can find the upload selector."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright
from pipeline.chatgpt_image_gen import _load_cookies, _save_cookies, CHATGPT_URL, _SESSION_PATH

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    _load_cookies(ctx)
    page = ctx.new_page()
    page.goto(CHATGPT_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)
    _save_cookies(ctx)

    # Dump all buttons
    buttons = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('button, [role="button"]')).map(b => ({
            tag: b.tagName,
            id: b.id,
            ariaLabel: b.getAttribute('aria-label'),
            dataTestId: b.getAttribute('data-testid'),
            title: b.title,
            text: b.innerText.trim().slice(0, 40),
            classes: b.className.slice(0, 80),
        }));
    }""")

    print("\n=== BUTTONS ===")
    for b in buttons:
        if any(v for v in b.values() if v):
            print(b)

    # Dump all file inputs
    inputs = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('input')).map(i => ({
            type: i.type,
            name: i.name,
            id: i.id,
            accept: i.accept,
            ariaLabel: i.getAttribute('aria-label'),
        }));
    }""")
    print("\n=== INPUTS ===")
    for i in inputs:
        print(i)

    input("\nPress Enter to close browser...")
    browser.close()
