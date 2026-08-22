#!/usr/bin/env python3
"""Freeze the CORD test split into ``data/splits/test.jsonl`` (offline, deterministic, $0).

Before freezing, it runs the deterministic safety checks that decide whether CORD's own
held-out test split can serve as the project's untouched test set:
  * record count per split;
  * empty inputs;
  * intra-split duplicate inputs;
  * the critical **cross-split input leakage** check — a test input that also appears in
    train/val would inflate the Phase-4 comparison.

The test set is frozen **as-is** (it is internally clean) and its normalized-input hashes
are written to a manifest. Any leakage is fixed later on the *train/val* side (Phase 2
drops any train/val input whose hash is in this manifest) — never by mutating the test
set, which is the measurement anchor.

    python scripts/freeze_test_set.py            # check, then write the frozen artifact
    python scripts/freeze_test_set.py --check    # report only, write nothing

Reads ``data/cord/{train,dev,test}.jsonl`` read-only; writes only under ``data/splits/``.
"""

from __future__ import annotations

import argparse
import hashlib
import json

from distill import dataset
from distill.config import CONFIG
from distill.schema import SCHEMA_VERSION

CORD = CONFIG.paths.data / "cord"
SPLITS = ("train", "dev", "test")


def _load(split: str) -> list[dict]:
    path = CORD / f"{split}.jsonl"
    if not path.exists():
        raise SystemExit(f"missing {path} — run scripts/convert_cord.py first.")
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="Freeze + leakage-check the CORD test split.")
    ap.add_argument("--check", action="store_true", help="Report only; write nothing.")
    args = ap.parse_args()

    records = {s: _load(s) for s in SPLITS}
    hashes = {s: [dataset.input_hash(r["text"]) for r in records[s]] for s in SPLITS}

    print("=== split summary ===")
    for s in SPLITS:
        recs, hs = records[s], hashes[s]
        empty = sum(1 for r in recs if not r["text"].strip())
        print(f"  {s:5s}: {len(recs):4d} records | {len(set(hs)):4d} unique inputs "
              f"| {len(hs) - len(set(hs))} duplicate input(s) | {empty} empty")

    print("\n=== cross-split input leakage (normalized) ===")
    te, tr, dv = set(hashes["test"]), set(hashes["train"]), set(hashes["dev"])
    contaminated = (te & tr) | (te & dv)
    print(f"  test ∩ train: {len(te & tr)}")
    print(f"  test ∩ dev  : {len(te & dv)}")
    print(f"  train ∩ dev : {len(tr & dv)}")
    print(f"  → {len(contaminated)} of {len(te)} test inputs also appear in train/val; "
          "Phase 2 drops those train/val inputs (never the test records).")

    if args.check:
        print("\nCHECK ONLY — no artifact written.")
        return

    out_dir = CONFIG.paths.splits
    out_dir.mkdir(parents=True, exist_ok=True)
    test_path = out_dir / "test.jsonl"
    manifest_path = out_dir / "test.manifest.json"

    with test_path.open("w") as f:
        for r in records["test"]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    test_hashes = sorted(set(hashes["test"]))
    aggregate = hashlib.sha256("\n".join(test_hashes).encode("utf-8")).hexdigest()
    if manifest_path.exists():
        prev = json.loads(manifest_path.read_text()).get("aggregate")
        if prev and prev != aggregate:
            print(f"\nWARNING: frozen test set changed (was {prev[:12]}…, now {aggregate[:12]}…).")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "source": "data/cord/test.jsonl",
        "n_records": len(records["test"]),
        "hash_recipe": "sha256(casefold(collapse_whitespace(text)))",
        "aggregate": aggregate,
        "input_hashes": test_hashes,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"\nFROZEN: {len(records['test'])} test records → {test_path}")
    print(f"manifest: {len(test_hashes)} input hashes, "
          f"aggregate {aggregate[:12]}… → {manifest_path}")
    print("Do NOT read these until Phase 4. Phase 2 excludes any train/val input whose "
          "hash is in this manifest.")


if __name__ == "__main__":
    main()
