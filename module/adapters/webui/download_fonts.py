#!/usr/bin/env python3
"""Download Google Fonts CSS and font files, produce a self-contained local CSS.

Only keeps Latin, Latin-ext, and Vietnamese unicode ranges (sufficient for CJK UIs).
Output: static/fonts.css with local file references.
Font files go to static/fonts/.
"""

import hashlib
import os
import re
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATIC_DIR = HERE / "static"
FONTS_DIR = STATIC_DIR / "fonts"
OUTPUT_FILE = STATIC_DIR / "fonts.css"

GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Open+Sans:wght@300;400;500;600;700"
    "&family=Poppins:wght@400;500;600;700;800"
    "&display=swap"
)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# We only need Latin + Latin-ext + Vietnamese for a CJK web UI
KEEP_BLOCKS = {"latin", "latin-ext", "vietnamese"}


def fetch(url: str, retries: int = 3) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    for attempt in range(retries):
        try:
            with opener.open(req, timeout=30) as resp:
                return resp.read()
        except Exception as e:
            if attempt == retries - 1:
                raise
            print(f"    retry {attempt + 1}/{retries}: {e}")
            time.sleep(2)


def extract_font_face_blocks(css: str) -> list[tuple[str | None, str]]:
    """Return list of (block_name_or_None, full_@font-face_text) pairs.

    Named blocks: /* latin */\n@font-face { ... }
    Unnamed (fallback): @font-face { ... } with no preceding comment.
    """
    # Split by @font-face boundaries
    parts = re.split(r'(@font-face\s*\{[^}]+\})', css)
    blocks = []
    i = 0
    while i < len(parts):
        chunk = parts[i]
        if i + 1 < len(parts):
            ff_text = parts[i + 1]
            # Check for preceding comment like /* latin */
            name_match = re.search(r'/\*\s*([\w-]+)\s*\*/\s*$', chunk)
            name = name_match.group(1) if name_match else None
            blocks.append((name, ff_text))
            i += 2
        else:
            i += 1
    return blocks


def main():
    # 1. Fetch the CSS from Google Fonts
    print(f"[fonts] Fetching CSS from Google Fonts...")
    css_text = fetch(GOOGLE_FONTS_URL).decode("utf-8")
    print(f"[fonts] CSS fetched ({len(css_text)} bytes)")

    # 2. Extract @font-face blocks and filter
    blocks = extract_font_face_blocks(css_text)
    print(f"[fonts] Found {len(blocks)} @font-face blocks")

    # Keep named blocks we want, plus all unnamed (fallback) blocks
    kept_blocks = [(name, text) for name, text in blocks
                   if name is None or name in KEEP_BLOCKS]
    skipped = [name for name, text in blocks
               if name is not None and name not in KEEP_BLOCKS]
    kept_names = [n for n, _ in kept_blocks]
    print(f"[fonts] Keeping {len(kept_blocks)} blocks "
          f"(named: {', '.join(sorted(set(n for n in kept_names if n)))} + {sum(1 for n in kept_names if n is None)} fallback), "
          f"skipping {len(skipped)} ({', '.join(sorted(set(skipped)))})")

    # 3. Extract unique font URLs from kept blocks
    font_urls: list[str] = list(dict.fromkeys(
        url for _, text in kept_blocks
        for url in re.findall(r"url\((https://[^)]+)\)", text)
    ))
    print(f"[fonts] {len(font_urls)} unique font files to download")

    # 4. Download font files
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    font_hashes: dict[str, str] = {}  # url -> local filename
    for i, url in enumerate(font_urls):
        orig_filename = url.split("/")[-1]
        print(f"  [{i+1}/{len(font_urls)}] {orig_filename} ...", end=" ", flush=True)
        data = fetch(url)
        # Use content hash as filename to avoid collisions
        content_hash = hashlib.sha256(data).hexdigest()[:12]
        ext = orig_filename.rsplit(".", 1)[-1]
        local_name = f"{content_hash}.{ext}"
        local_path = FONTS_DIR / local_name
        if not local_path.exists():
            local_path.write_bytes(data)
            print(f"{len(data)} bytes -> {local_name}")
        else:
            print(f"already cached as {local_name}")
        font_hashes[url] = local_name
        time.sleep(0.2)

    total_bytes = sum(
        (FONTS_DIR / name).stat().st_size
        for name in set(font_hashes.values())
        if (FONTS_DIR / name).exists()
    )
    print(f"[fonts] Total font data on disk: {total_bytes / 1024:.0f} KB")

    # 5. Build output CSS (kept blocks only, with local URLs)
    output_css = "\n".join(text for _, text in kept_blocks)
    for url, local_name in font_hashes.items():
        output_css = output_css.replace(url, f"/fonts/{local_name}")

    OUTPUT_FILE.write_text(output_css, encoding="utf-8")
    print(f"[fonts] Written {OUTPUT_FILE} ({len(output_css)} bytes)")
    print(f"[fonts] Font files in {FONTS_DIR}:")
    for f in sorted(FONTS_DIR.iterdir()):
        print(f"  {f.name} ({f.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
