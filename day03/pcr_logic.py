#!/usr/bin/env python3
"""
Pure computation helpers for the PCR calculator.
Separated out so the main program only handles I/O / UI code.
"""

from __future__ import annotations

PER_SAMPLE_TOTAL = 11.0  # µL
PRIMER_PER = 0.5         # µL for each primer
DEFAULT_EXCESS = 10.0    # percent


def round_to_half(value: float) -> float:
    """Round any number to the nearest 0.5 µL increment."""
    return round(value * 2) / 2.0


def per_sample_volumes(mix_x: int) -> dict[str, float]:
    """
    Return the per-sample component volumes for the requested mix strength.

    mix_x must be 2 or 5 (representing 2X or 5X master mix).
    """
    if mix_x not in (2, 5):
        raise ValueError("mix_x must be 2 or 5")

    mix_volume = 6.0 * (2.0 / mix_x)
    primers_total = 2 * PRIMER_PER
    ddw_volume = PER_SAMPLE_TOTAL - (mix_volume + primers_total)
    if ddw_volume < 0:
        raise ValueError("Negative DDW volume calculated; check setup.")

    return {
        "DDW (µL)": ddw_volume,
        f"Mix {mix_x}X (µL)": mix_volume,
        "Primer F (µL)": PRIMER_PER,
        "Primer R (µL)": PRIMER_PER,
    }


def compute_totals(n_samples: int, excess_percent: float, mix_x: int):
    """
    Compute per-sample recipe, total volumes with excess, and total master mix.
    """
    if n_samples < 1:
        raise ValueError("n_samples must be >= 1")
    if excess_percent < 0:
        raise ValueError("excess_percent must be >= 0")

    per = per_sample_volumes(mix_x)
    factor = 1.0 + (excess_percent / 100.0)

    totals = {name: round_to_half(vol * n_samples * factor) for name, vol in per.items()}
    total_master_mix = round_to_half(sum(totals.values()))
    return per, totals, total_master_mix


def format_report(n_samples: int, excess_percent: float, mix_x: int,
                  per: dict[str, float], totals: dict[str, float],
                  total_master_mix: float) -> str:
    """Return a human-readable text table for CLI/STDOUT use."""
    lines = [
        f"Samples: {n_samples} | Excess: {excess_percent:.1f}% | Mix: {mix_x}X",
        f"Per-sample total volume: {PER_SAMPLE_TOTAL:.1f} µL",
        "-" * 46,
        "Per-sample recipe:",
    ]
    for name, vol in per.items():
        lines.append(f"  {name:<16} = {vol:.1f} µL")
    lines.extend([
        "-" * 46,
        "Totals to prepare (rounded to 0.5 µL):",
    ])
    for name in per.keys():
        lines.append(f"  {name:<16} = {totals[name]:.1f} µL")
    lines.extend([
        "-" * 46,
        f"TOTAL master mix       = {total_master_mix:.1f} µL",
    ])
    return "\n".join(lines)
