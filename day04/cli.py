from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

# Support running as a script (python day04/cli.py) or as a module (python -m day04.cli)
if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from day04.imdb_client import IMDB_TOP_250_URL, download_and_store

app = typer.Typer(help="Download IMDb data and save it locally.")


@app.command("download")
def download(
    html_output: Path = typer.Option(
        Path("day04/data/imdb_top_250.html"),
        help="Where to store the raw IMDb HTML response.",
    ),
    parsed_output: Optional[Path] = typer.Option(
        Path("day04/data/imdb_top_250.json"),
        help="Where to write parsed titles (JSON).",
    ),
    parse: bool = typer.Option(
        True,
        "--parse/--no-parse",
        help="Toggle parsing into JSON alongside the raw HTML download.",
    ),
    limit: Optional[int] = typer.Option(
        None,
        min=1,
        max=250,
        help="Optionally limit how many titles are saved in the parsed output.",
    ),
    url: str = typer.Option(
        IMDB_TOP_250_URL,
        help="IMDb URL to download. Defaults to the Top 250 chart.",
    ),
    credentials_path: Optional[Path] = typer.Option(
        None,
        help="Path to credentials JSON containing optional user_agent/email values.",
    ),
):
    """
    Download the IMDb Top 250 page and save the raw HTML and an optional parsed JSON file.
    """
    parsed_path = parsed_output if parse else None
    summary = download_and_store(
        html_path=html_output,
        parsed_path=parsed_path,
        limit=limit,
        credentials_path=credentials_path,
        source_url=url,
    )

    typer.secho(f"HTML saved to: {summary['html_file']}", fg=typer.colors.GREEN)

    if parsed_path:
        typer.secho(
            f"Parsed {summary['parsed_count']} titles into: {summary['parsed_file']}",
            fg=typer.colors.BLUE,
        )
    else:
        typer.echo("Parsing skipped (no parsed_output path given).")


def main():
    app()


if __name__ == "__main__":
    main()
