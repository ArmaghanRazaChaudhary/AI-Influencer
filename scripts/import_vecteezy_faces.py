from __future__ import annotations

import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urljoin

import requests


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "personas" / "batch_100_manifest.json"
FACES_DIR = ROOT / "assets" / "faces"
OUT_MANIFEST = FACES_DIR / "vecteezy_face_sources.json"

SEARCH_QUERIES = {
    "black": ["black ai face", "african ai face", "black man ai face", "black woman ai face"],
    "white": ["white ai face", "european ai face", "caucasian ai face"],
    "latino": ["latino ai face", "latina ai face", "hispanic ai face"],
    "middle_eastern": ["arab ai face", "middle eastern ai face"],
    "south_asian": ["indian ai face", "south asian ai face", "pakistani ai face"],
    "east_asian": ["asian ai face", "korean ai face", "japanese ai face", "chinese ai face"],
    "mixed": ["diverse ai face", "multicultural ai face", "ai face"],
}


def search_urls_for(query: str) -> list[str]:
    slug = quote(query.replace(" ", "-"))
    return [
        f"https://www.vecteezy.com/free-photos/{slug}",
        f"https://www.vecteezy.com/free-photos/{slug}?page=2",
    ]


def gender_word(gender: str) -> str:
    gender = gender.lower()
    if gender == "female":
        return "woman"
    if gender == "male":
        return "man"
    return "person"


class ImageLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.images: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {k: v or "" for k, v in attrs}
        if tag == "a":
            href = data.get("href", "")
            if "/photo/" in href:
                self.links.append(href)
        if tag in {"img", "source"}:
            for key in ("src", "data-src", "srcset", "data-srcset"):
                value = data.get(key, "")
                if value:
                    self.images.extend(extract_image_urls(value))


def extract_image_urls(value: str) -> list[str]:
    urls: list[str] = []
    for part in value.split(","):
        token = part.strip().split(" ")[0]
        if token.startswith("http") and any(ext in token.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            urls.append(token)
    return urls


def extract_from_scripts(html: str) -> list[str]:
    return re.findall(r"https://[^\"'\\]+?\.(?:jpg|jpeg|png|webp)(?:\?[^\"'\\]*)?", html, flags=re.I)


def collect_candidates(search_urls: list[str]) -> list[dict[str, str]]:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36",
    })
    candidates: list[dict[str, str]] = []
    seen_images: set[str] = set()

    for search_url in search_urls:
        response = session.get(search_url, timeout=30)
        response.raise_for_status()
        parser = ImageLinkParser()
        parser.feed(response.text)
        photo_links = [urljoin(search_url, href) for href in parser.links]
        image_urls = parser.images + extract_from_scripts(response.text)

        # Pair images with page links opportunistically. Search-result HTML exposes more image
        # URLs than detail links, so source_url is best-effort unless a detail page is nearby.
        for index, image_url in enumerate(image_urls):
            if image_url in seen_images:
                continue
            lower = image_url.lower()
            if not any(word in lower for word in ["vecteezy", "static", "cdn"]):
                continue
            seen_images.add(image_url)
            source_url = photo_links[index % len(photo_links)] if photo_links else search_url
            candidates.append({"image_url": image_url, "source_url": source_url})
        time.sleep(0.5)

    return candidates


def category_for(demography: str) -> str:
    demo = demography.lower()
    if any(word in demo for word in ["black", "nigerian", "ghanaian", "angolan", "somali", "jamaican", "african"]):
        return "black"
    if any(word in demo for word in ["mexican", "puerto", "brazil", "argentin", "latino", "hispanic"]):
        return "latino"
    if any(word in demo for word in ["arab", "egyptian", "moroccan", "palestinian", "jordanian", "israeli", "qatari", "turkish"]):
        return "middle_eastern"
    if any(word in demo for word in ["indian", "pakistani", "tamil", "singaporean"]):
        return "south_asian"
    if any(word in demo for word in ["korean", "japanese", "chinese", "taiwanese", "vietnamese", "malay", "filipino"]):
        return "east_asian"
    if any(word in demo for word in ["white", "british", "french", "danish", "scottish", "irish", "spanish", "norwegian", "finnish", "polish", "austrian", "czech", "serbian", "italian", "portuguese", "german"]):
        return "white"
    return "mixed"


def demography_for(persona: dict[str, object]) -> str:
    if persona.get("demography"):
        return str(persona["demography"])
    persona_path = ROOT / "personas" / str(persona["persona_id"]) / "persona.md"
    if not persona_path.exists():
        return ""
    text = persona_path.read_text(encoding="utf-8")
    match = re.search(r"\*\*Demography:\*\*\s*(.+)", text)
    return match.group(1).strip() if match else ""


def is_plausible_single_face(url: str, gender: str) -> bool:
    lower = url.lower()
    reject_words = [
        "group", "crowd", "people", "diverse-faces", "tapestry", "collage",
        "family", "generational", "couple", "two-", "three-", "many",
        "bottle", "lake", "landscape", "background", "icon", "logo",
    ]
    if any(word in lower for word in reject_words):
        return False
    if not any(word in lower for word in ["portrait", "face", "headshot", "person", "man", "woman"]):
        return False
    gender = gender.lower()
    tokens = re.split(r"[^a-z]+", lower)
    token_set = set(tokens)
    if gender == "female":
        if {"man", "male", "boy", "beard", "mustache"} & token_set and not ({"woman", "female", "girl", "lady"} & token_set):
            return False
    if gender == "male":
        if {"woman", "female", "girl", "lady"} & token_set and not ({"man", "male", "boy"} & token_set):
            return False
    return True


def download_image(session: requests.Session, url: str, out_path: Path) -> bool:
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        if "image" not in content_type and not url.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp")):
            return False
        if len(response.content) < 20_000:
            return False
        out_path.write_bytes(response.content)
        return True
    except requests.RequestException:
        return False


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    personas = manifest["personas"]
    candidates_by_key: dict[tuple[str, str], list[dict[str, str]]] = {}
    for category, queries in SEARCH_QUERIES.items():
        for g_word in ["woman", "man", "person"]:
            urls: list[str] = []
            for query in queries:
                urls.extend(search_urls_for(f"{query} {g_word} portrait"))
            print(f"collecting {category}/{g_word} candidates")
            candidates_by_key[(category, g_word)] = collect_candidates(urls)

    all_candidates: list[dict[str, str]] = []
    for candidates in candidates_by_key.values():
        all_candidates.extend(candidates)
    if len(all_candidates) < len(personas):
        raise RuntimeError(f"Only found {len(all_candidates)} candidates for {len(personas)} personas")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36",
    })

    assignments: list[dict[str, str]] = []
    used_images: set[str] = set()
    indexes = {key: 0 for key in candidates_by_key}
    fallback_index = 0
    for persona in personas:
        persona_id = persona["persona_id"]
        out_dir = FACES_DIR / persona_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "face_reference.jpg"

        saved = False
        demography = demography_for(persona)
        category = category_for(demography)
        g_word = gender_word(str(persona.get("gender", "")))
        key = (category, g_word)
        local_candidates = candidates_by_key.get(key, [])
        while indexes.get(key, 0) < len(local_candidates) and not saved:
            candidate = local_candidates[indexes[key]]
            indexes[key] += 1
            if candidate["image_url"] in used_images:
                continue
            if not is_plausible_single_face(candidate["image_url"], str(persona.get("gender", ""))):
                continue
            saved = download_image(session, candidate["image_url"], out_path)
            if saved:
                used_images.add(candidate["image_url"])
                assignments.append({
                    "persona_id": persona_id,
                    "name": persona["name"],
                    "demography": demography,
                    "assigned_category": category,
                    "local_path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
                    "image_url": candidate["image_url"],
                    "source_url": candidate["source_url"],
                    "license_note": "Vecteezy free photos generally require attribution unless covered by a Pro license. Verify each source page before public/commercial use.",
                })
                print(f"{len(assignments):03d} {persona_id} <- {out_path.relative_to(ROOT)}")
                time.sleep(0.1)

        while fallback_index < len(all_candidates) and not saved:
            candidate = all_candidates[fallback_index]
            fallback_index += 1
            if candidate["image_url"] in used_images:
                continue
            if not is_plausible_single_face(candidate["image_url"], str(persona.get("gender", ""))):
                continue
            saved = download_image(session, candidate["image_url"], out_path)
            if saved:
                used_images.add(candidate["image_url"])
                assignments.append({
                    "persona_id": persona_id,
                    "name": persona["name"],
                    "demography": demography,
                    "assigned_category": f"{category}:fallback",
                    "local_path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
                    "image_url": candidate["image_url"],
                    "source_url": candidate["source_url"],
                    "license_note": "Vecteezy free photos generally require attribution unless covered by a Pro license. Verify each source page before public/commercial use.",
                })
                print(f"{len(assignments):03d} {persona_id} <- {out_path.relative_to(ROOT)}")
                time.sleep(0.1)

    OUT_MANIFEST.write_text(json.dumps(assignments, indent=2), encoding="utf-8")
    print(f"saved {len(assignments)} faces")
    print(f"sources: {OUT_MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
