"""
imdb_data.py  - Business logic for the IMDB Movie Picker

This module is responsible for:
- Downloading raw data from IMDb public datasets (https://datasets.imdbws.com/)
- Combining the relevant fields from title.basics.tsv.gz and title.ratings.tsv.gz
- Saving the processed data to a local CSV file (e.g. data/imdb_movies.csv)
- Loading the saved CSV into Python
- Filtering movies according to user-defined criteria

NO UI CODE here (no Tkinter). This file can be imported by any front-end:
- Command-line script
- Tkinter GUI
- Web app
"""

import csv
import os
import urllib.request
import gzip
import io
import ssl


IMDB_BASICS_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"
IMDB_RATINGS_URL = "https://datasets.imdbws.com/title.ratings.tsv.gz"


def fetch_and_save_imdb_movies(
    output_path="data/imdb_movies.csv",
    max_movies=5000
):
    """
    Download IMDb basics + ratings, merge them, and save to a local CSV.

    :param output_path: Where to save the processed CSV file.
    :param max_movies:  Limit number of movies to keep the file manageable.
    :return: List of movie dicts with keys: Title, Genre, IMDB_Rating, Runtime, Year
    """
    # Make sure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Relaxed SSL context (so it works even if certificates aren't set up)
    context = ssl._create_unverified_context()

    # ----- Download basics -----
    basics_response = urllib.request.urlopen(IMDB_BASICS_URL, context=context)
    basics_data = basics_response.read()

    movies_by_id = {}

    with gzip.GzipFile(fileobj=io.BytesIO(basics_data)) as gz:
        header_line = gz.readline()  # skip header
        for line in gz:
            parts = line.decode("utf-8", errors="ignore").rstrip("\n").split("\t")
            if len(parts) < 9:
                continue

            (
                tconst,
                titleType,
                primaryTitle,
                originalTitle,
                isAdult,
                startYear,
                endYear,
                runtimeMinutes,
                genres,
            ) = parts

            # Keep only normal, non-adult movies with runtime and genres
            if titleType != "movie":
                continue
            if isAdult != "0":
                continue
            if runtimeMinutes == "\\N":
                continue
            if genres == "\\N":
                continue

            year_value = "" if startYear == "\\N" else startYear

            movies_by_id[tconst] = {
                "Title": primaryTitle,
                "Genre": genres.replace("\\N", "").strip(),
                "Runtime": runtimeMinutes,
                "Year": year_value,
                # rating will be filled from ratings file
            }

            if len(movies_by_id) >= max_movies:
                break

    # ----- Download ratings -----
    ratings_response = urllib.request.urlopen(IMDB_RATINGS_URL, context=context)
    ratings_data = ratings_response.read()

    with gzip.GzipFile(fileobj=io.BytesIO(ratings_data)) as gz:
        header_line = gz.readline()
        for line in gz:
            parts = line.decode("utf-8", errors="ignore").rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            tconst, averageRating, numVotes = parts
            if tconst in movies_by_id:
                movies_by_id[tconst]["IMDB_Rating"] = averageRating

    # Turn dict into list, keeping only entries with rating
    movies = [
        {
            "Title": v["Title"],
            "Genre": v["Genre"],
            "Runtime": v["Runtime"],
            "IMDB_Rating": v.get("IMDB_Rating", ""),
            "Year": v.get("Year", "")
        }
        for v in movies_by_id.values()
        if "IMDB_Rating" in v
    ]

    # ----- Save to CSV -----
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Genre", "IMDB_Rating", "Runtime", "Year"])
        for m in movies:
            writer.writerow([
                m["Title"],
                m["Genre"],
                m["IMDB_Rating"],
                m["Runtime"],
                m["Year"]
            ])

    return movies


def load_movies_from_csv(path="data/imdb_movies.csv"):
    """
    Load movies from a CSV file into a list of dicts.

    :param path: Path to the CSV file.
    :return: List of dicts with keys: Title, Genre, IMDB_Rating, Runtime, Year
    """
    movies = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            movies.append({
                "Title": row.get("Title", "").strip(),
                "Genre": row.get("Genre", "").strip(),
                "IMDB_Rating": row.get("IMDB_Rating", ""),
                "Runtime": row.get("Runtime", ""),
                "Year": row.get("Year", "")
            })
    return movies


def _parse_int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_float_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def filter_movies(movies,
                  genre=None,
                  min_year=None,
                  max_year=None,
                  min_rating=None,
                  max_duration=None):
    """
    Filter a list of movie dicts according to several criteria.

    :param movies: List of dicts from load_movies_from_csv or fetch_and_save_imdb_movies.
    :param genre: String or None. If given, movie's Genre must contain this string.
    :param min_year: Integer or None.
    :param max_year: Integer or None.
    :param min_rating: Float or None.
    :param max_duration: Integer (minutes) or None.
    :return: Filtered list of movie dicts.
    """
    filtered = []
    genre = (genre or "").strip()
    genre_lower = genre.lower()

    for m in movies:
        m_genre = m.get("Genre", "")
        m_rating = _parse_float_or_none(m.get("IMDB_Rating", ""))
        m_runtime = _parse_int_or_none(m.get("Runtime", ""))
        m_year = _parse_int_or_none(m.get("Year", ""))

        # Genre filter
        if genre_lower:
            if genre_lower not in m_genre.lower():
                continue

        # Rating filter
        if min_rating is not None:
            if m_rating is None or m_rating < min_rating:
                continue

        # Duration filter
        if max_duration is not None:
            if m_runtime is not None and m_runtime > max_duration:
                continue

        # Year filter
        if min_year is not None:
            if m_year is None or m_year < min_year:
                continue
        if max_year is not None:
            if m_year is None or m_year > max_year:
                continue

        filtered.append(m)

    return filtered