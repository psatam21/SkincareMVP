"""
Second pass: pull ALL India-tagged products from Open Beauty Facts (not
limited to the 45-brand list in fetch_obf.py), filter to skincare items with
usable ingredient lists, and merge into the same products_clean.csv, deduping
by barcode against what's already there.

Usage: python fetch_obf_india.py
"""
import json
import time
import urllib.request
import urllib.parse
import csv
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_obf import SKINCARE_KEYWORDS, HEADERS, looks_like_skincare  # reuse

FIELDS = "product_name,brands,ingredients_text,code,countries_tags,quantity"
BASE = "https://world.openbeautyfacts.org/api/v2/search"

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "obf_raw"
OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "products_clean.csv"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def fetch_country(country_tag: str) -> list[dict]:
    products = []
    page = 1
    while True:
        params = {
            "countries_tags": country_tag,
            "fields": FIELDS,
            "page_size": 100,
            "page": page,
            "json": "true",
        }
        url = f"{BASE}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=HEADERS)
        data = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read())
                break
            except Exception as e:
                if attempt == 2:
                    print(f"  page {page} failed after retries: {e}")
                    return products
                time.sleep(2 * (attempt + 1))
        products.extend(data.get("products", []))
        if page >= data.get("page_count", 1):
            break
        page += 1
        time.sleep(0.5)
    return products


def load_existing_codes() -> set[str]:
    if not OUT_CSV.exists():
        return set()
    with open(OUT_CSV, encoding="utf-8") as f:
        return {row["code"] for row in csv.DictReader(f)}


def main():
    existing_codes = load_existing_codes()
    print(f"Existing products in catalogue: {len(existing_codes)}")

    print("Fetching all India-tagged products ...")
    products = fetch_country("en:india")
    (RAW_DIR / "india_all.json").write_text(
        json.dumps(products, indent=2), encoding="utf-8"
    )
    print(f"  {len(products)} raw India-tagged records")

    new_rows = []
    for p in products:
        code = p.get("code", "")
        name = p.get("product_name", "").strip()
        ingredients = p.get("ingredients_text", "").strip()

        if not code or code in existing_codes:
            continue
        if not name or not ingredients or len(ingredients) < 15:
            continue
        if not looks_like_skincare(name):
            continue

        existing_codes.add(code)
        new_rows.append({
            "code": code,
            "brand": p.get("brands", ""),
            "product_name": name,
            "ingredients_text": ingredients,
            "countries_tags": ";".join(p.get("countries_tags", [])),
            "quantity": p.get("quantity", ""),
            "source_url": f"https://world.openbeautyfacts.org/product/{code}",
        })

    print(f"  {len(new_rows)} new products kept (not already in catalogue, skincare-matched, has ingredients)")

    if new_rows:
        with open(OUT_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "code", "brand", "product_name", "ingredients_text",
                "countries_tags", "quantity", "source_url",
            ])
            writer.writerows(new_rows)

    print(f"Total in catalogue now: {len(existing_codes)}")


if __name__ == "__main__":
    main()
