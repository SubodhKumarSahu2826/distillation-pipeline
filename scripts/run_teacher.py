#!/usr/bin/env python3
"""Teacher pilot runner — the cost gate for Phase 1.

Default behaviour is a **dry run**: it prints exactly what would be called, the request
count, token estimates, and the projected USD, then exits WITHOUT spending. Actually
calling the paid API requires ``--confirm`` (and a real ``ANTHROPIC_API_KEY``).

Examples:
    # Estimate cost for 50 receipts, make no calls:
    python scripts/run_teacher.py --input data/raw/receipts.jsonl --limit 50

    # Actually run the 50-sample pilot (spends money — only after approval):
    python scripts/run_teacher.py --input data/raw/receipts.jsonl --limit 50 \\
        --out artifacts/pilot_opus.jsonl --confirm

Input format: JSONL, one object per line with at least a ``text`` field (the receipt
text); an ``id`` field is used if present. Guardrails per CLAUDE.md §3.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from distill import schema, teacher
from distill.config import CONFIG
from distill.logging import get_logger

log = get_logger("distill.run_teacher")

# Assumed per-request output size when we cannot measure it yet (see docs/cost-analysis.md).
DEFAULT_ASSUME_OUT_TOKENS = 300
DEFAULT_ASSUME_IN_TOKENS = 700


def _read_texts(path: Path, limit: int) -> list[dict]:
    rows: list[dict] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            rows.append(obj)
            if len(rows) >= limit:
                break
    return rows


def _guard_test_split(path: Path, allow_test: bool) -> None:
    """Refuse to touch the frozen test set for labelling unless explicitly allowed."""
    name = path.name.lower()
    if ("test" in name and path.suffix == ".jsonl") and not allow_test:
        sys.exit(
            f"REFUSED: {path} looks like the frozen test split. The test set is never used "
            f"for generation/tuning (it is read only in Phase 4). Pass --allow-test to override."
        )


def main() -> None:
    ap = argparse.ArgumentParser(description="Teacher pilot runner (dry-run by default).")
    ap.add_argument("--input", type=Path, help="JSONL of inputs with a 'text' field.")
    ap.add_argument("--limit", type=int, default=50, help="Max requests (pilot size).")
    ap.add_argument("--model", default=CONFIG.teacher_model, help="Teacher model id.")
    ap.add_argument("--effort", default="low", help="Reasoning effort for the teacher.")
    ap.add_argument("--out", type=Path, help="Where to write raw outputs (confirmed runs).")
    ap.add_argument("--allow-test", action="store_true", help="Permit reading a test split.")
    ap.add_argument("--confirm", action="store_true", help="Actually spend money (paid).")
    ap.add_argument("--assume-out-tokens", type=int, default=DEFAULT_ASSUME_OUT_TOKENS)
    args = ap.parse_args()

    # --- estimate (always) ---
    if args.input:
        _guard_test_split(args.input, args.allow_test)
        if not args.input.exists():
            sys.exit(f"input not found: {args.input}")
        rows = _read_texts(args.input, args.limit)
        if not rows:
            sys.exit(f"no rows in {args.input}")
        in_toks = [teacher.estimate_input_tokens(r["text"]) for r in rows]
        mean_in = sum(in_toks) / len(in_toks)
        n = len(rows)
        src = str(args.input)
    else:
        rows = []
        mean_in = float(DEFAULT_ASSUME_IN_TOKENS)
        n = args.limit
        src = f"(no --input; assuming {DEFAULT_ASSUME_IN_TOKENS} input tokens/request)"

    mean_out = float(args.assume_out_tokens)
    price_in = CONFIG.teacher_input_usd_per_mtok
    price_out = CONFIG.teacher_output_usd_per_mtok
    est = teacher.estimate_cost_usd(n, mean_in, mean_out, price_in, price_out)

    endpoint = os.environ.get("ANTHROPIC_BASE_URL", "default api.anthropic.com")
    print("=== Teacher pilot — plan ===")
    print(f"  endpoint (ANTHROPIC_BASE_URL): {endpoint}")
    print(f"  model:            {args.model or '(unset — set TEACHER_MODEL)'}")
    print(f"  requests:         {n}   source: {src}")
    print(f"  mean input tok:   {mean_in:.0f}   assumed output tok: {mean_out:.0f}")
    print(f"  price $/Mtok:     in={price_in}  out={price_out}"
          "  (labelled assumption; see cost-analysis.md)")
    print(f"  PROJECTED COST:   ${est:.4f}  (prompt {teacher.PROMPT_VERSION})")
    if price_in == 0.0 or price_out == 0.0:
        print("  WARNING: pricing is unset (0.0). Set "
              "TEACHER_INPUT/OUTPUT_USD_PER_MTOK for a real estimate.")

    if not args.confirm:
        print("\nDRY RUN — no API calls made. Re-run with --confirm to spend (after approval).")
        return

    # --- paid run (only with --confirm) ---
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set — cannot run a confirmed pilot.")
    if not args.input:
        sys.exit("--confirm requires --input (a real set of documents).")
    if not args.model:
        sys.exit("no model set — pass --model or set TEACHER_MODEL.")
    out_path = args.out or CONFIG.paths.artifacts / "pilot.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("running CONFIRMED pilot: %d requests to %s", n, args.model)
    total_cost, valid = 0.0, 0
    with out_path.open("w") as w:
        for i, row in enumerate(rows):
            res = teacher.extract(row["text"], model=args.model, effort=args.effort)
            total_cost += res.cost_usd
            ok = schema.is_valid(res.text)
            valid += int(ok)
            w.write(json.dumps({
                "id": row.get("id", i),
                "output": res.text,
                "valid": ok,
                "input_tokens": res.input_tokens,
                "output_tokens": res.output_tokens,
                "cost_usd": res.cost_usd,
            }) + "\n")
    print(f"\nDONE: {n} calls, schema-valid {valid}/{n}, actual cost ${total_cost:.4f}")
    print(f"outputs → {out_path}. Record the pilot cost in docs/cost-analysis.md.")


if __name__ == "__main__":
    main()
