#!/usr/bin/env python3
"""Typer-based CLI wrapper around the PCR calculator business logic."""

from __future__ import annotations

from typing import Annotated

import typer

from pcr_logic import DEFAULT_EXCESS, compute_totals, format_report

app = typer.Typer(add_completion=False, help=__doc__)


def _validate_mix(value: int) -> int:
    if value not in (2, 5):
        raise typer.BadParameter("Mix must be either 2 (for 2X) or 5 (for 5X).")
    return value


@app.command()
def calculate(
    samples: Annotated[int, typer.Argument(min=1, help="Number of PCR reactions (>=1).")],
    excess: Annotated[
        float,
        typer.Option(
            "--excess",
            "-e",
            min=0.0,
            help=f"Percent excess to offset pipetting loss (default {DEFAULT_EXCESS}%).",
        ),
    ] = DEFAULT_EXCESS,
    mix: Annotated[
        int,
        typer.Option(
            "--mix",
            "-m",
            callback=_validate_mix,
            help="Master mix concentration to use (2 for 2X, 5 for 5X).",
        ),
    ] = 2,
) -> None:
    """Compute and display PCR component volumes."""
    per, totals, total_master_mix = compute_totals(
        n_samples=samples,
        excess_percent=excess,
        mix_x=mix,
    )
    typer.echo(format_report(samples, excess, mix, per, totals, total_master_mix))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
