"""
Pull skincare product + ingredient records from Open Beauty Facts for a fixed
brand list, filter to real skincare items with usable ingredient lists, dedupe,
and write a clean CSV ready for the RAGloader conversion step.

Usage: python fetch_obf.py
Output: ../data/obf_raw/<brand>.json  (raw API pages, for audit/re-runs)
        ../data/products_clean.csv    (deduped, filtered)
"""
import json
import time
import urllib.request
import urllib.parse
import csv
import re
from pathlib import Path

BRANDS = [
    # Batch 1: global drugstore, confirmed 9-Sep run
    "nivea", "garnier", "dove", "neutrogena", "vaseline", "aveeno",
    "cetaphil", "himalaya", "loreal", "simple", "ponds", "olay",
    "the-ordinary", "lakme", "biotique",
    # Batch 2: dermocosmetic / pharmacy brands (widely sold in India via
    # Nykaa/pharmacies), confirmed counts 20-400+
    "eucerin", "la-roche-posay", "bioderma", "avene", "clinique", "kiehl-s",
    "curel", "cerave", "st-ives", "yves-rocher", "the-body-shop", "innisfree",
    "missha", "cosrx", "some-by-mi", "laneige", "biore", "sebamed",
    "physiogel", "qv", "klorane", "uriage", "caudalie", "weleda", "nuxe",
    "embryolisse", "vichy", "roc", "no7", "elizabeth-arden", "estee-lauder",
    "differin",
    # Batch 3: mass-market + India-native, confirmed counts 8-65
    "johnson-s", "jergens", "lotus", "patanjali", "khadi", "vlcc", "nykaa",
    "dermalogica", "origins", "fresh", "drunk-elephant", "first-aid-beauty",
    "banana-boat", "hawaiian-tropic",
]

# Product-name keywords that indicate an actual skincare (not deodorant/
# shampoo/shower-gel/soap) item, since OBF category tags are unreliable.
SKINCARE_KEYWORDS = [
    "serum", "cream", "cleanser", "moistur", "lotion", "toner", "sunscreen",
    "spf", "gel", "oil", "essence", "mask", "exfoliat", "scrub", "facial",
    "face wash", "face cream", "eye cream", "retinol", "niacinamide",
    "vitamin c", "hyaluronic", "acid", "night cream", "day cream", "balm",
    "wash", "milk", "peel", "brightening", "anti-aging", "anti aging",
    "wrinkle", "spot", "acne", "sunblock", "after sun", "micellar", "foam",
    "cica", "hydrating", "renewal", "repair", "barrier", "cleansing",
]

FIELDS = "product_name,brands,ingredients_text,code,categories_tags,countries_tags,quantity,image_url,lang"
BASE = "https://world.openbeautyfacts.org/api/v2/search"
HEADERS = {"User-Agent": "BITSoM-MidtermProject-SkincareAssistant/1.0 (student project, contact via course)"}

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "obf_raw"
OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "products_clean.csv"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def fetch_brand(brand: str) -> list[dict]:
    products = []
    page = 1
    while True:
        params = {
            "brands_tags": brand,
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
                    raise
                print(f"  retry after error: {e}")
                time.sleep(2 * (attempt + 1))
        products.extend(data.get("products", []))
        if page >= data.get("page_count", 1):
            break
        page += 1
        time.sleep(0.5)  # be polite to a free community API
    return products


def looks_like_skincare(product_name: str) -> bool:
    name = (product_name or "").lower()
    return any(kw in name for kw in SKINCARE_KEYWORDS)


def main():
    all_rows = []
    seen_codes = set()

    for brand in BRANDS:
        print(f"Fetching {brand} ...")
        try:
            products = fetch_brand(brand)
        except Exception as e:
            print(f"  FAILED: {e}")
            continue

        (RAW_DIR / f"{brand}.json").write_text(
            json.dumps(products, indent=2), encoding="utf-8"
        )
        print(f"  {len(products)} raw records")

        kept = 0
        for p in products:
            code = p.get("code", "")
            name = p.get("product_name", "").strip()
            ingredients = p.get("ingredients_text", "").strip()

            if not code or code in seen_codes:
                continue
            if not name or not ingredients or len(ingredients) < 15:
                continue
            if not looks_like_skincare(name):
                continue

            seen_codes.add(code)
            kept += 1
            all_rows.append({
                "code": code,
                "brand": p.get("brands", brand),
                "product_name": name,
                "ingredients_text": ingredients,
                "countries_tags": ";".join(p.get("countries_tags", [])),
                "quantity": p.get("quantity", ""),
                "source_url": f"https://world.openbeautyfacts.org/product/{code}",
            })
        print(f"  {kept} kept after skincare + ingredient filter")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "code", "brand", "product_name", "ingredients_text",
            "countries_tags", "quantity", "source_url",
        ])
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nTotal clean products: {len(all_rows)}")
    print(f"Written to {OUT_CSV}")


if __name__ == "__main__":
    main()
