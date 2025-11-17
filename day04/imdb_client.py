from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


IMDB_TOP_250_URL = "https://www.imdb.com/chart/top"


@dataclass
class TitleRecord:
    rank: int
    title: str
    year: int
    url: str | None = None


class IMDbDownloadError(Exception):
    """Raised when a download from IMDb fails."""


def load_credentials(path: Path | None = None) -> dict:
    """
    Load optional credentials (e.g., user agent or contact email).

    The default location is a credentials.json file that sits next to this module.
    Missing or invalid files are treated as empty credentials.
    """
    credentials_path = Path(path) if path else Path(__file__).with_name("credentials.json")
    if not credentials_path.exists():
        return {}
    try:
        with credentials_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        # Swallow errors to avoid blocking normal runs when the optional file is broken.
        return {}


def _build_request(url: str, credentials: dict) -> Request:
    headers = {
        "User-Agent": credentials.get(
            "user_agent",
            "Mozilla/5.0 (compatible; IMDbDownloader/1.0; +https://imdb.com)",
        )
    }
    if credentials.get("email"):
        # IMDb does not require an email header, but we support passing one to comply with
        # sites that ask for contact information in automated access.
        headers["From"] = credentials["email"]
    return Request(url, headers=headers)


def fetch_top_250_html(
    url: str = IMDB_TOP_250_URL,
    *,
    credentials: Optional[dict] = None,
    timeout: int = 20,
) -> str:
    """Download the IMDb Top 250 HTML page."""
    creds = credentials or {}
    request = _build_request(url, creds)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            encoding = response.headers.get_content_charset() or "utf-8"
            return raw.decode(encoding, errors="replace")
    except (HTTPError, URLError) as exc:
        raise IMDbDownloadError(str(exc)) from exc


def parse_top_250_titles(html: str, *, limit: Optional[int] = None) -> List[TitleRecord]:
    """
    Parse IMDb Top 250 titles from the HTML content.

    The parser is deliberately simple (regex-based) to avoid third-party dependencies.
    It targets the common table layout on imdb.com/chart/top and degrades gracefully
    by returning an empty list if nothing matches.
    """
    pattern = re.compile(
        r'<td class="titleColumn">\s*(?P<rank>\d+)\.\s*'
        r'<a href="(?P<href>/title/tt\d+/)[^"]*"[^>]*>'
        r'(?P<title>[^<]+)</a>.*?'
        r'<span class="secondaryInfo">\((?P<year>\d{4})\)</span>',
        flags=re.DOTALL,
    )
    matches = pattern.finditer(html)
    records: List[TitleRecord] = []
    for match in matches:
        record = TitleRecord(
            rank=int(match.group("rank")),
            title=match.group("title").strip(),
            year=int(match.group("year")),
            url=f"https://www.imdb.com{match.group('href')}",
        )
        records.append(record)
        if limit is not None and len(records) >= limit:
            break
    return records


def save_text(content: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def save_records(records: Iterable[TitleRecord], path: Path) -> Path:
    serializable = [
        {"rank": record.rank, "title": record.title, "year": record.year, "url": record.url}
        for record in records
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
    return path


def download_and_store(
    *,
    html_path: Path,
    parsed_path: Optional[Path] = None,
    limit: Optional[int] = None,
    credentials_path: Optional[Path] = None,
    source_url: str = IMDB_TOP_250_URL,
) -> dict:
    """
    Fetch IMDb data and store it locally.

    Returns a summary with the paths that were written and how many titles were parsed.
    """
    credentials = load_credentials(credentials_path)
    html = fetch_top_250_html(source_url, credentials=credentials)
    save_text(html, html_path)

    parsed_count = 0
    parsed_file = None
    if parsed_path is not None:
        records = parse_top_250_titles(html, limit=limit)
        parsed_count = len(records)
        parsed_file = save_records(records, parsed_path)

    return {
        "html_file": str(html_path),
        "parsed_file": str(parsed_file) if parsed_file else None,
        "parsed_count": parsed_count,
    }
