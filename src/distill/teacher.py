"""Teacher: the versioned extraction prompt + a thin, cost-aware Claude client.

Two clearly separated concerns:
- **Offline** (safe to import and unit-test with no network): the prompt template,
  message construction, a rough token estimator, and the cost arithmetic.
- **Paid** (only reached from scripts/run_teacher.py behind an explicit ``--confirm``):
  :func:`extract`, which makes one real API call and captures token usage + cost.

``anthropic`` is imported lazily inside the paid functions so this module — and the
tests — import with a bare interpreter and no key set (Phase 0 / D-004 philosophy).
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import CONFIG

# Bump when the prompt text changes so labels stay attributable to a prompt version.
PROMPT_VERSION = "extract-v1"

SYSTEM_PROMPT = """\
You extract structured data from a single receipt into a fixed JSON object.

Output ONLY a JSON object — no prose, no markdown fences. Use exactly these keys:
  vendor       string | null   the merchant/store name
  date         string | null   purchase date as ISO 8601 "YYYY-MM-DD"
  currency     string | null   ISO 4217 code, uppercase (e.g. "USD"); null if unclear
  line_items   array           one object per purchased line, each with:
                 description  string        the item text as printed
                 quantity     number | null
                 unit_price   number | null price per unit
                 total_price  number | null line total
  subtotal     number | null   pre-tax total
  tax          number | null   tax amount
  total        number | null   grand total actually charged

Rules:
- Report what is printed; do not compute or "correct" totals.
- Use null for any field not present on the receipt. line_items may be an empty array.
- Numbers must be plain JSON numbers (no currency symbols, no thousands separators).
"""

USER_TEMPLATE = "Receipt text:\n<<<\n{doc}\n>>>\n\nReturn the JSON object."


def build_messages(doc_text: str) -> list[dict]:
    """The user turn for one document. System prompt is passed separately."""
    return [{"role": "user", "content": USER_TEMPLATE.format(doc=doc_text)}]


# --- offline estimation ----------------------------------------------------------

# ~4 characters per token is the usual English rough-guide; good enough for a pilot
# projection. The real number is measured with count_tokens (free) or from the pilot.
_CHARS_PER_TOKEN = 4.0


def estimate_tokens(text: str) -> int:
    """Rough offline token estimate for ``text``. Labelled assumption, not exact."""
    return max(1, round(len(text) / _CHARS_PER_TOKEN))


def estimate_input_tokens(doc_text: str) -> int:
    """Estimated prompt tokens for one request (system + user template + document)."""
    filled = SYSTEM_PROMPT + USER_TEMPLATE.format(doc=doc_text)
    return estimate_tokens(filled)


def estimate_cost_usd(
    n: int,
    mean_input_tokens: float,
    mean_output_tokens: float,
    price_in_per_mtok: float | None = None,
    price_out_per_mtok: float | None = None,
) -> float:
    """Projected USD for ``n`` requests. Prices default to CONFIG (list-price assumption)."""
    price_in = CONFIG.teacher_input_usd_per_mtok if price_in_per_mtok is None else price_in_per_mtok
    price_out = (
        CONFIG.teacher_output_usd_per_mtok if price_out_per_mtok is None else price_out_per_mtok
    )
    per_request = (mean_input_tokens * price_in + mean_output_tokens * price_out) / 1_000_000
    return n * per_request


# --- paid path (lazy anthropic import; only called behind --confirm) -------------

@dataclass
class TeacherResult:
    text: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    model: str
    prompt_version: str = PROMPT_VERSION


def _client():
    """Construct the default Anthropic client (reads ANTHROPIC_API_KEY / _BASE_URL)."""
    import anthropic  # lazy: keeps the module importable offline

    return anthropic.Anthropic()


def count_input_tokens(doc_text: str, model: str, client=None) -> int:
    """Exact prompt token count via the free count_tokens endpoint (sharpens estimates)."""
    client = client or _client()
    resp = client.messages.count_tokens(
        model=model, system=SYSTEM_PROMPT, messages=build_messages(doc_text)
    )
    return resp.input_tokens


def extract(
    doc_text: str,
    model: str | None = None,
    max_tokens: int = 1500,
    effort: str = "low",
    client=None,
) -> TeacherResult:
    """One real, billable extraction call. Captures token usage and computes cost.

    Extraction is not reasoning-heavy, so ``effort="low"`` keeps the pilot cheap; raise
    it only if pilot quality is below the ceiling we need. Output is validated by the
    caller with schema.parse_and_validate (deterministic).
    """
    model = model or CONFIG.teacher_model
    client = client or _client()
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=build_messages(doc_text),
        output_config={"effort": effort},
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    in_tok, out_tok = resp.usage.input_tokens, resp.usage.output_tokens
    cost = estimate_cost_usd(1, in_tok, out_tok)
    return TeacherResult(
        text=text, input_tokens=in_tok, output_tokens=out_tok, cost_usd=cost, model=model
    )
