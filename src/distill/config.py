"""Typed, env-driven configuration — one place for every knob.

Filesystem paths, model ids, and pricing all come from the environment with safe
defaults, so the package imports and tests run with no setup and no network. Model ids
and pricing are placeholders here; each is locked by the phase that measures it (teacher
tier in Phase 1, student in Phase 3, real pricing in Phase 6).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# Repo root: this file is src/distill/config.py, so parents[2] is the project dir.
ROOT = Path(__file__).resolve().parents[2]


def _env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


@dataclass(frozen=True)
class Paths:
    """Filesystem layout. The data/model/run dirs are gitignored (see .gitignore)."""

    root: Path = ROOT
    data: Path = ROOT / "data"
    splits: Path = ROOT / "data" / "splits"
    models: Path = ROOT / "models"
    runs: Path = ROOT / "runs"
    artifacts: Path = ROOT / "artifacts"


@dataclass(frozen=True)
class Config:
    """The single config object. Access via the module-level ``CONFIG``."""

    paths: Paths = field(default_factory=Paths)
    # Model ids: placeholders, locked in later phases, overridable via env.
    teacher_model: str = ""
    student_model: str = ""
    # Pricing knobs for the Phase 6 break-even model (USD). 0.0 means "unset".
    teacher_input_usd_per_mtok: float = 0.0
    teacher_output_usd_per_mtok: float = 0.0
    gpu_usd_per_hour: float = 0.0


def load_config() -> Config:
    """Build the config from the environment with safe, offline defaults."""
    return Config(
        paths=Paths(),
        teacher_model=_env_str("TEACHER_MODEL", ""),
        student_model=_env_str("STUDENT_MODEL", ""),
        teacher_input_usd_per_mtok=_env_float("TEACHER_INPUT_USD_PER_MTOK", 0.0),
        teacher_output_usd_per_mtok=_env_float("TEACHER_OUTPUT_USD_PER_MTOK", 0.0),
        gpu_usd_per_hour=_env_float("GPU_USD_PER_HOUR", 0.0),
    )


CONFIG = load_config()
