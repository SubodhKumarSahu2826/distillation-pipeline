#!/usr/bin/env python3
"""Convert the raw CORD corpus into internal ``{id, text, gold}`` JSONL, one file per split.

Deterministic and offline — no API calls, no cost. Reads (read-only)
``data/raw/cord/{train,dev,test}/json/*.json`` and writes
``data/cord/{train,dev,test}.jsonl``. Each output line is one record:
``{"id": "train/receipt_00000", "text": <ocr text>, "gold": <receipt-v1 object>}``.

    python scripts/convert_cord.py
"""

from __future__ import annotations

import json

from distill import dataset
from distill.config import CONFIG

RAW = CONFIG.paths.data / "raw" / "cord"
OUT = CONFIG.paths.data / "cord"
SPLITS = ("train", "dev", "test")


def convert_split(split: str) -> tuple[list[dict], list[tuple[str, str]]]:
    records: list[dict] = []
    fails: list[tuple[str, str]] = []
    for path in sorted((RAW / split / "json").glob("*.json")):
        rec_id = f"{split}/{path.stem}"
        try:
            doc = json.loads(path.read_text())
            records.append(dataset.convert_record(doc, rec_id))
        except Exception as e:  # a record that will not map is surfaced, not silently dropped
            fails.append((rec_id, str(e)))
    return records, fails


def main() -> None:
    if not RAW.exists():
        raise SystemExit(f"raw CORD not found at {RAW} — place train/dev/test there first.")
    OUT.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        records, fails = convert_split(split)
        out = OUT / f"{split}.jsonl"
        with out.open("w") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        items = sum(len(r["gold"]["line_items"]) for r in records)
        empty = sum(1 for r in records if not r["gold"]["line_items"])
        print(f"{split}: {len(records)} records, {items} line items "
              f"({empty} receipts with no line items) → {out}"
              + (f"  [{len(fails)} FAILED]" if fails else ""))
        for rid, err in fails[:5]:
            print(f"   FAIL {rid}: {err}")


if __name__ == "__main__":
    main()
