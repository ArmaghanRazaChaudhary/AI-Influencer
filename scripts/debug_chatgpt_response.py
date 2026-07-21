from __future__ import annotations
"""
Debug: sends a simple image generation request to ChatGPT and prints
the full HTML of the response area so we can find the correct image selector.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright
from pipeline.chatgpt_image_gen import _launch_context, _is_logged_in, _auto_login, CHATGPT_URL
from config.settings import CHATGPT_EMAIL, CHATGPT_PASSWORD, BASE_DIR

FACE = BASE_DIR / "assets/faces/face1.jpeg"

with sync_playwright() as p:
    ctx = _launch_context(p, headless=False)
    page = ctx.new_page()

    page.goto(CHATGPT_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)

    if not _is_logged_in(page):
        if CHATGPT_EMAIL and CHATGPT_PASSWORD:
            _auto_login(page, CHATGPT_EMAIL, CHATGPT_PASSWORD)
        else:
            input("Log in manually then press Enter...")

    # Fresh chat
    page.goto(CHATGPT_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # Upload face
    file_input = page.locator("input[type='file']").first
    if file_input.count() > 0:
        print("Found hidden file input, uploading...")
        file_input.set_input_files(str(FACE.resolve()))
    else:
        print("No hidden file input — trying attach button...")
        # Just skip upload for this debug and test text-only image gen
    page.wait_for_timeout(2000)

    # Simple explicit image generation prompt
    prompt = "Generate an image of a woman sitting at a café in Paris. Photorealistic, iPhone photo."
    box = page.locator("#prompt-textarea").first
    if box.count() == 0:
        box = page.locator("div[contenteditable='true']").first
    box.click()
    box.fill(prompt)
    page.wait_for_timeout(500)

    # Send
    send = page.locator("button[data-testid='send-button']").first
    if send.count() > 0 and send.is_enabled():
        send.click()
        print("Sent. Waiting 60s for response...")
    else:
        page.keyboard.press("Enter")
        print("Sent via Enter. Waiting 60s...")

    page.wait_for_timeout(60000)

    # Print all img tags in the page
    imgs = page.evaluate("""() =>
        Array.from(document.querySelectorAll('img')).map(img => ({
            src: img.src.slice(0, 80),
            alt: img.alt,
            parent: img.parentElement ? img.parentElement.className.slice(0,60) : '',
            grandparent: img.parentElement?.parentElement?.getAttribute('data-message-author-role') || '',
        }))
    """)
    print("\n=== IMG TAGS ===")
    for img in imgs:
        print(img)

    # Print assistant message HTML
    assistant_html = page.evaluate("""() => {
        const el = document.querySelector('[data-message-author-role="assistant"]');
        return el ? el.innerHTML.slice(0, 2000) : 'NOT FOUND';
    }""")
    print("\n=== ASSISTANT MESSAGE HTML ===")
    print(assistant_html)

    # All elements with data-message-author-role
    roles = page.evaluate("""() =>
        Array.from(document.querySelectorAll('[data-message-author-role]')).map(el => ({
            role: el.getAttribute('data-message-author-role'),
            tag: el.tagName,
            class: el.className.slice(0, 60),
        }))
    """)
    print("\n=== ELEMENTS WITH data-message-author-role ===")
    for r in roles:
        print(r)

    input("\nPress Enter to close...")
    ctx.close()
