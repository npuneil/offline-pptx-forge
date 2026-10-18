"""Cost, energy, carbon and water for local vs cloud generation. All constants live in config.ASSUMPTIONS."""
from __future__ import annotations

from .config import ASSUMPTIONS as A


def local(measured_wh: float, prompt_tokens: int, completion_tokens: int) -> dict:
    kwh = measured_wh / 1000
    return {
        "lane": "local", "energy_wh": round(measured_wh, 3),
        "cost_usd": round(kwh * A["electricity_usd_per_kwh"], 6),
        "co2e_g": round(kwh * A["grid_kgco2e_per_kwh"] * 1000, 3),
        "water_ml": round((prompt_tokens + completion_tokens) / 1000 * A["local_ml_water_per_1k_tokens"], 2),
        "basis": "measured GPU board power (nvidia-smi, 250 ms) + 10 W platform allowance; electricity only",
    }


def cloud(model: str, input_tokens: int, output_tokens: int) -> dict:
    price = A["pricing_usd_per_mtok"][model]
    wh = output_tokens / 1000 * A["cloud_wh_per_1k_tokens"]
    return {
        "lane": "cloud", "energy_wh": round(wh, 3),
        "cost_usd": round(input_tokens / 1e6 * price["in"] + output_tokens / 1e6 * price["out"], 6),
        "co2e_g": round(wh / 1000 * A["grid_kgco2e_per_kwh"] * 1000, 3),
        "water_ml": round(output_tokens / 1000 * A["cloud_ml_water_per_1k_tokens"], 2),
        "basis": "API list price x tokens; energy/water = published per-1k-output-token estimate",
    }


def per_thousand(row: dict) -> dict:
    return {k + "_per_1k_decks": round(row[k] * 1000, 2) for k in ("cost_usd", "energy_wh", "co2e_g", "water_ml")}
