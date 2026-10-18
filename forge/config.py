"""Paths, model catalog and the published assumptions used by the economics engine."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
BENCH = ROOT / "bench"
BRIEFS = ROOT / "briefs"


def portable(path) -> str:
    """Repo-relative path for recorded artifacts, so run JSON carries no machine-specific prefix."""
    p = Path(path).resolve()
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


BENCH_HOME = Path(os.environ.get("FORGE_LLAMA_HOME", Path.home() / "Local-AI-Bench"))
LLAMA_SERVER = BENCH_HOME / "tools" / "llama" / "llama-server.exe"
MODEL_INDEX = BENCH_HOME / "models" / "installed.json"

DEFAULT_MODEL = "qwen3-coder-30b"
PORT = int(os.environ.get("FORGE_PORT", "8811"))
CONTEXT = 32768


def model_path(model_id):
    index = json.loads(MODEL_INDEX.read_text(encoding="utf-8"))
    if model_id not in index:
        raise KeyError(f"Model {model_id} is not installed in {MODEL_INDEX}")
    entry = index[model_id]
    first = sorted(f["filename"] for f in entry["files"])[0]
    return BENCH_HOME / "models" / model_id / first, entry


# Economics and sustainability assumptions. Every number shown in a benchmark is computed
# from these constants plus measured run telemetry; change them here, not in report text.
ASSUMPTIONS = {
    "electricity_usd_per_kwh": 0.13,          # US commercial average, EIA 2025 (order of magnitude)
    "grid_kgco2e_per_kwh": 0.367,             # US average location-based grid intensity (EIA 2023)
    "platform_overhead_w": 10.0,              # CPU, memory, SSD, display beyond the GPU rail (assumption)
    "cloud_wh_per_1k_tokens": 1.1,            # GPT-4o-class token-level estimate (Vanderbilt YSJ / Epoch AI)
    "cloud_ml_water_per_1k_tokens": 3.6,      # same source; data-center cooling water
    "local_ml_water_per_1k_tokens": 0.0,      # no on-site evaporative cooling (grid water excluded for both)
    "chars_per_token": 4.0,                   # used only when a provider does not return token counts
    "pricing_usd_per_mtok": {                 # list prices, October 2026 (standard tier)
        "claude-opus-5.5": {"in": 4.0, "out": 20.0},
        "gpt-6-astra": {"in": 10.0, "out": 50.0},
    },
}
