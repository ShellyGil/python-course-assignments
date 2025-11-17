"""
Advanced IMDB Movie Picker GUI (no external libraries, IMDb fetch with relaxed SSL)

Features:
- Fetches real data directly from IMDb public datasets at https://datasets.imdbws.com/
  using urllib + an "unverified" SSL context (so it works even if certificates
  are not properly installed on the system). This is fine for a class project,
  but not recommended for secure production apps.

- OR loads a local CSV with columns: Title, Genre, IMDB_Rating, Runtime, Year
  (or compatible names like Series_Title, IMDB Rating, Runtime (Minutes)).

User chooses:
    * Genre          (dropdown, including "(Any genre)" and always "Horror")
    * Min / Max year (optional)
    * Max duration   (minutes)
    * Min IMDb rating

The app:
    * Filters the movie list according to these answers
    * Picks 3 random matching movies
    * Lets the user regenerate 3 new options based on the current filters
    * Lets the user save the 3 suggestions to a text file
    * Stores a history of all suggested movies and can show/save it
    * Adds a YouTube trailer button for each suggestion
    * Optional checkbox: auto-open the first trailer on YouTube after each search
    * Tries to show a simple “poster thumbnail” using an online placeholder PNG
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import random
import os
import urllib.request
import urllib.parse
import gzip
import io
import ssl   # relaxed SSL context for IMDb + thumbnails
import webbrowser


IMDB_BASICS_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"
IMDB_RATINGS_URL = "https://datasets.imdbws.com/title.ratings.tsv.gz"


class MovieRecommenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IMDB Movie Picker - Advanced")

        self.root.geometry("1000x600")
        self.root.configure(bg="black")

        # Data containers
        self.movies = []            # all movies (from IMDb or CSV)
        self.filtered_movies = []   # movies matching current filters
        self.current_suggestions = []
        self.history = []           # all movies ever suggested (by title)
        self.poster_images = []     # keep references to PhotoImage objects

        # Build UI
        self.create_header()
        self.create_controls()
        self.create_results_area()
        self.create_actions()

    # ---------- UI CREATION ----------

    def create_header(self):
        header_frame = tk.Frame(self.root, bg="#f5c518")
        header_frame.pack(fill="x")

        title_label = tk.Label(
            header_frame,
            text="IMDB Movie Picker",
            bg="#f5c518",
            fg="black",
            font=("Arial", 26, "bold")
        )
        title_label.pack(side="left", padx=20, pady=5)

        subtitle_label = tk.Label(
            header_frame,
            text="Choose your mood, we pick the movie",
            bg="#f5c518",
            fg="black",
            font=("Arial", 14)
        )
        subtitle_label.pack(side="left", padx=15)

    def create_controls(self):
        controls_frame = tk.Frame(self.root, bg="black")
        controls_frame.pack(fill="x", padx=20, pady=8)

        # ----- Dataset row -----
        ds_frame = tk.Frame(controls_frame, bg="black")
        ds_frame.grid(row=0, column=0, columnspan=6, sticky="w")

        ds_label = tk.Label(
            ds_frame,
            text="Local CSV (optional):",
            bg="black",
            fg="#f5c518",
            font=("Arial", 14, "bold")
        )
        ds_label.pack(side="left")

        self.dataset_path_var = tk.StringVar()
        ds_entry = tk.Entry(ds_frame, textvariable=self.dataset_path_var, width=35, font=("Arial", 13))
        ds_entry.pack(side="left", padx=10)

        ds_button = tk.Button(
            ds_frame,
            text="Browse",
            bg="#f5c518",
            fg="black",
            font=("Arial", 12, "bold"),
            command=self.browse_dataset
        )
        ds_button.pack(side="left")

        load_button = tk.Button(
            ds_frame,
            text="Load CSV",
            bg="#f5c518",
            fg="black",
            font=("Arial", 12, "bold"),
            command=self.load_dataset
        )
        load_button.pack(side="left", padx=8)

        online_button = tk.Button(
            ds_frame,
            text="Fetch from IMDb (online)",
            bg="#f5c518",
            fg="black",
            font=("Arial", 12, "bold"),
            command=self.fetch_from_imdb_online
        )
        online_button.pack(side="left", padx=8)

        # ----- Genre selection -----
        genre_label = tk.Label(
            controls_frame,
            text="Genre:",
            bg="black",
            fg="white",
            font=("Arial", 14)
        )
        genre_label.grid(row=1, column=0, sticky="w", pady=6)

        self.genre_var = tk.StringVar()
        self.genre_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.genre_var,
            state="readonly",
            width=25,
            font=("Arial", 13)
        )
        self.genre_combo.grid(row=1, column=1, padx=8, pady=6, sticky="w")
        self.genre_combo["values"] = ["(Load or fetch data first)"]

        # ----- Year range -----
        year_from_label = tk.Label(
            controls_frame,
            text="Year from:",
            bg="black",
            fg="white",
            font=("Arial", 14)
        )
        year_from_label.grid(row=1, column=2, sticky="w", padx=(20, 0))

        self.min_year_var = tk.StringVar()
        year_from_entry = tk.Entry(controls_frame, textvariable=self.min_year_var, width=6, font=("Arial", 13))
        year_from_entry.grid(row=1, column=3, padx=5, pady=6, sticky="w")

        year_to_label = tk.Label(
            controls_frame,
            text="to:",
            bg="black",
            fg="white",
            font=("Arial", 14)
        )
        year_to_label.grid(row=1, column=4, sticky="w")

        self.max_year_var = tk.StringVar()
        year_to_entry = tk.Entry(controls_frame, textvariable=self.max_year_var, width=6, font=("Arial", 13))
        year_to_entry.grid(row=1, column=5, padx=5, pady=6, sticky="w")

        # ----- Max duration -----
        dur_label = tk.Label(
            controls_frame,
            text="Max duration (min):",
            bg="black",
            fg="white",
            font=("Arial", 14)
        )
        dur_label.grid(row=2, column=0, sticky="w", pady=(6, 0))

        self.max_duration_var = tk.StringVar(value="180")
        dur_entry = tk.Entry(controls_frame, textvariable=self.max_duration_var, width=6, font=("Arial", 13))
        dur_entry.grid(row=2, column=1, padx=5, pady=(6, 0), sticky="w")

        # ----- Min rating slider -----
        rating_label = tk.Label(
            controls_frame,
            text="Min IMDB rating:",
            bg="black",
            fg="white",
            font=("Arial", 14)
        )
        rating_label.grid(row=2, column=2, sticky="w", pady=(6, 0))

        self.min_rating_var = tk.DoubleVar(value=7.0)
        rating_scale = tk.Scale(
            controls_frame,
            variable=self.min_rating_var,
            from_=0.0,
            to=10.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            length=250,
            bg="black",
            fg="white",
            highlightbackground="black",
            troughcolor="gray20",
            font=("Arial", 11)
        )
        rating_scale.grid(row=2, column=3, columnspan=2, sticky="w", pady=(0, 0))

        # ----- Auto trailer checkbox -----
        self.auto_trailer_var = tk.BooleanVar(value=False)
        auto_trailer_cb = tk.Checkbutton(
            controls_frame,
            text="Auto-open first trailer on YouTube after search",
            variable=self.auto_trailer_var,
            bg="black",
            fg="white",
            selectcolor="black",
            activebackground="black",
            activeforeground="white",
            font=("Arial", 11)
        )
        auto_trailer_cb.grid(row=3, column=0, columnspan=6, sticky="w", pady=(4, 0))

    def create_results_area(self):
        results_frame = tk.Frame(self.root, bg="black")
        results_frame.pack(fill="both", expand=True, padx=20, pady=5)

        results_label = tk.Label(
            results_frame,
            text="Suggestions:",
            bg="black",
            fg="#f5c518",
            font=("Arial", 16, "bold")
        )
        results_label.pack(anchor="w")

        self.cards_frame = tk.Frame(results_frame, bg="black")
        self.cards_frame.pack(fill="both", expand=True)

    def create_actions(self):
        actions_frame = tk.Frame(self.root, bg="black")
        actions_frame.pack(fill="x", padx=20, pady=8)

        self.find_button = tk.Button(
            actions_frame,
            text="Find Movies",
            bg="#f5c518",
            fg="black",
            font=("Arial", 14, "bold"),
            command=self.find_movies
        )
        self.find_button.pack(side="left", padx=5)

        self.regen_button = tk.Button(
            actions_frame,
            text="Regenerate 3 options",
            bg="#f5c518",
            fg="black",
            font=("Arial", 13, "bold"),
            command=self.regenerate_movies,
            state="disabled"
        )
        self.regen_button.pack(side="left", padx=5)

        self.save_button = tk.Button(
            actions_frame,
            text="Save suggestions",
            bg="#f5c518",
            fg="black",
            font=("Arial", 13, "bold"),
            command=self.save_results,
            state="disabled"
        )
        self.save_button.pack(side="left", padx=5)

        self.history_button = tk.Button(
            actions_frame,
            text="Show history",
            bg="#f5c518",
            fg="black",
            font=("Arial", 13, "bold"),
            command=self.show_history
        )
        self.history_button.pack(side="left", padx=5)

    # ---------- DATA LOADING (LOCAL CSV) ----------

    def browse_dataset(self):
        path = filedialog.askopenfilename(
            title="Select IMDB CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.dataset_path_var.set(path)

    def load_dataset(self):
        path = self.dataset_path_var.get().strip()
        if not path:
            messagebox.showwarning("No file", "Please choose a CSV file first.")
            return

        if not os.path.exists(path):
            messagebox.showerror("File not found", f"The file does not exist:\n{path}")
            return

        try:
            with open(path, newline='', encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception as e:
            messagebox.showerror("Error loading CSV", f"Could not load file:\n{e}")
            return

        movies = []
        for row in rows:
            title = row.get("Title") or row.get("Series_Title") or ""
            genre = row.get("Genre") or ""
            rating = row.get("IMDB_Rating") or row.get("IMDB Rating") or ""
            runtime = row.get("Runtime") or row.get("Runtime (Minutes)") or ""
            year = row.get("Year") or row.get("ReleaseYear") or ""

            if not title:
                continue

            movies.append({
                "Title": title.strip(),
                "Genre": genre.strip(),
                "IMDB_Rating": rating,
                "Runtime": runtime,
                "Year": year
            })

        if not movies:
            messagebox.showerror("No data", "No valid movie rows found in the CSV.")
            return

        self.movies = movies
        self.build_genre_list()
        messagebox.showinfo("Dataset loaded", "Local CSV data loaded successfully!")

    # ---------- DATA FETCHING (ONLINE FROM IMDB, RELAXED SSL) ----------

    def fetch_from_imdb_online(self):
        """
        Fetch movies from IMDb public datasets:
        - https://datasets.imdbws.com/title.basics.tsv.gz
        - https://datasets.imdbws.com/title.ratings.tsv.gz

        Uses an SSL context that does NOT verify certificates.
        This avoids CERTIFICATE_VERIFY_FAILED errors on some Mac setups.
        """
        confirm = messagebox.askyesno(
            "Fetch from IMDb",
            "This will download IMDb public datasets (a few MB) from datasets.imdbws.com.\n"
            "Do you want to continue?"
        )
        if not confirm:
            return

        try:
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

                    # We only want normal movies, non-adult, with runtime and genres
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

                    if len(movies_by_id) >= 5000:
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

            if not movies:
                messagebox.showerror(
                    "No data",
                    "Could not build movie list from IMDb datasets."
                )
                return

            self.movies = movies
            self.build_genre_list()
            messagebox.showinfo(
                "IMDb fetch complete",
                f"Fetched {len(self.movies)} movies from IMDb public datasets."
            )

        except Exception as e:
            messagebox.showerror(
                "Error fetching IMDb data",
                f"An error occurred while fetching from IMDb:\n{e}"
            )

    def build_genre_list(self):
        """Build genre dropdown values from self.movies."""
        genres_set = set()
        for m in self.movies:
            if m["Genre"]:
                parts = [g.strip() for g in m["Genre"].split(",")]
                genres_set.update(parts)

        # Ensure Horror is available even if rare
        genres_set.add("Horror")

        genre_list = sorted(list(genres_set))
        # Add an "any genre" option at the top
        genre_list.insert(0, "(Any genre)")

        if genre_list:
            self.genre_combo["values"] = genre_list
            self.genre_combo.current(0)
        else:
            self.genre_combo["values"] = ["(No genres found)"]
            self.genre_combo.current(0)

    # ---------- FILTERING & SELECTION ----------

    @staticmethod
    def parse_runtime_to_minutes(runtime_str):
        if not runtime_str:
            return None
        s = str(runtime_str).lower().replace("min", "").strip()
        try:
            return int(s)
        except ValueError:
            return None

    @staticmethod
    def parse_year(year_str):
        if not year_str:
            return None
        try:
            return int(year_str)
        except ValueError:
            return None

    def filter_movies(self):
        if not self.movies:
            messagebox.showwarning("No data", "Please load or fetch IMDb data first.")
            return []

        genre_choice = self.genre_var.get().strip()
        if genre_choice == "(Any genre)" or not genre_choice:
            genre_choice = ""

        # Year filters (optional)
        min_year = self.parse_year(self.min_year_var.get().strip())
        max_year = self.parse_year(self.max_year_var.get().strip())

        # Duration
        max_dur_str = self.max_duration_var.get().strip()
        try:
            max_dur = int(max_dur_str)
        except ValueError:
            max_dur = None

        min_rating = self.min_rating_var.get()

        filtered = []
        for m in self.movies:
            genre = m["Genre"]
            rating_str = m["IMDB_Rating"]
            runtime_str = m["Runtime"]
            year_str = m.get("Year", "")

            # Genre filter
            if genre_choice and genre_choice.lower() not in genre.lower():
                continue

            # Rating filter
            try:
                rating_val = float(rating_str)
            except (ValueError, TypeError):
                continue
            if rating_val < min_rating:
                continue

            # Duration filter
            if max_dur is not None:
                minutes = self.parse_runtime_to_minutes(runtime_str)
                if minutes is not None and minutes > max_dur:
                    continue

            # Year filter
            this_year = self.parse_year(year_str)
            if min_year is not None and (this_year is None or this_year < min_year):
                continue
            if max_year is not None and (this_year is None or this_year > max_year):
                continue

            filtered.append(m)

        self.filtered_movies = filtered
        return filtered

    def choose_three_movies(self):
        if not self.filtered_movies:
            return []

        if len(self.filtered_movies) <= 3:
            return list(self.filtered_movies)

        return random.sample(self.filtered_movies, 3)

    # ---------- BUTTON ACTIONS ----------

    def update_history(self):
        """Add current suggestions to history (by title, avoiding duplicates)."""
        known_titles = {m["Title"] for m in self.history}
        for m in self.current_suggestions:
            if m["Title"] not in known_titles:
                self.history.append(m)
                known_titles.add(m["Title"])

    def find_movies(self):
        filtered = self.filter_movies()
        if not filtered:
            messagebox.showinfo(
                "No matches",
                "No movies match your filters. Try changing genre, rating, year or duration."
            )
            self.current_suggestions = []
            self.update_cards()
            self.regen_button.config(state="disabled")
            self.save_button.config(state="disabled")
            return

        self.current_suggestions = self.choose_three_movies()
        self.update_history()
        self.update_cards()

        self.regen_button.config(state="normal")
        self.save_button.config(state="normal")

        # Auto-open first trailer if requested
        if self.auto_trailer_var.get() and self.current_suggestions:
            first_title = self.current_suggestions[0]["Title"]
            self.open_trailer_on_youtube(first_title)

    def regenerate_movies(self):
        filtered = self.filter_movies()
        if not filtered:
            messagebox.showinfo(
                "No matches",
                "No movies match your filters. Try changing genre, rating, year or duration."
            )
            self.current_suggestions = []
            self.update_cards()
            self.regen_button.config(state="disabled")
            self.save_button.config(state="disabled")
            return

        if len(self.filtered_movies) == 0:
            self.current_suggestions = []
            self.update_cards()
            self.regen_button.config(state="disabled")
            self.save_button.config(state="disabled")
            return

        old_titles = {m["Title"] for m in self.current_suggestions} if self.current_suggestions else set()

        if len(self.filtered_movies) <= 3:
            self.current_suggestions = random.sample(self.filtered_movies, len(self.filtered_movies))
        else:
            new_set = self.choose_three_movies()
            if old_titles:
                for _ in range(10):
                    new_set = self.choose_three_movies()
                    new_titles = {m["Title"] for m in new_set}
                    if new_titles != old_titles:
                        break
            self.current_suggestions = new_set

        self.update_history()
        self.update_cards()
        self.regen_button.config(state="normal")
        self.save_button.config(state="normal")

        # Auto-open first trailer if requested
        if self.auto_trailer_var.get() and self.current_suggestions:
            first_title = self.current_suggestions[0]["Title"]
            self.open_trailer_on_youtube(first_title)

    def save_results(self):
        if not self.current_suggestions:
            messagebox.showwarning("No suggestions", "There are no movie suggestions to save.")
            return

        path = filedialog.asksaveasfilename(
            title="Save suggestions",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("IMDB Movie Picker - Current Suggestions\n")
                f.write("----------------------------------------\n\n")

                for i, m in enumerate(self.current_suggestions, start=1):
                    title = m.get("Title", "Unknown title")
                    genre = m.get("Genre", "N/A")
                    rating = m.get("IMDB_Rating", "N/A")
                    runtime = m.get("Runtime", "N/A")
                    year = m.get("Year", "N/A")

                    f.write(f"{i}. {title} ({year})\n")
                    f.write(f"   Genre: {genre}\n")
                    f.write(f"   Rating: {rating}\n")
                    f.write(f"   Runtime: {runtime} min\n\n")

            messagebox.showinfo("Saved", f"Suggestions saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error saving file", f"Could not save file:\n{e}")

    # ---------- HISTORY ----------

    def show_history(self):
        if not self.history:
            messagebox.showinfo("History", "No movies in history yet.")
            return

        win = tk.Toplevel(self.root)
        win.title("Movie History")
        win.configure(bg="black")
        win.geometry("600x400")

        lbl = tk.Label(
            win,
            text=f"Movies suggested so far: {len(self.history)}",
            bg="black",
            fg="#f5c518",
            font=("Arial", 14, "bold")
        )
        lbl.pack(pady=5)

        text = tk.Text(win, bg="#1f1f1f", fg="white", font=("Arial", 11))
        text.pack(fill="both", expand=True, padx=10, pady=5)

        for i, m in enumerate(self.history, start=1):
            title = m.get("Title", "Unknown title")
            genre = m.get("Genre", "N/A")
            rating = m.get("IMDB_Rating", "N/A")
            year = m.get("Year", "N/A")
            text.insert(
                "end",
                f"{i}. {title} ({year}) | Genre: {genre} | Rating: {rating}\n"
            )

        text.config(state="disabled")

        btn = tk.Button(
            win,
            text="Save history to text file",
            bg="#f5c518",
            fg="black",
            font=("Arial", 12, "bold"),
            command=self.save_history
        )
        btn.pack(pady=5)

    def save_history(self):
        if not self.history:
            messagebox.showinfo("History", "No movies in history yet.")
            return

        path = filedialog.asksaveasfilename(
            title="Save history",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("IMDB Movie Picker - History\n")
                f.write("---------------------------\n\n")

                for i, m in enumerate(self.history, start=1):
                    title = m.get("Title", "Unknown title")
                    genre = m.get("Genre", "N/A")
                    rating = m.get("IMDB_Rating", "N/A")
                    runtime = m.get("Runtime", "N/A")
                    year = m.get("Year", "N/A")

                    f.write(f"{i}. {title} ({year})\n")
                    f.write(f"   Genre: {genre}\n")
                    f.write(f"   Rating: {rating}\n")
                    f.write(f"   Runtime: {runtime} min\n\n")

            messagebox.showinfo("Saved", f"History saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error saving file", f"Could not save history:\n{e}")

    # ---------- YOUTUBE TRAILER HELPER ----------

    def open_trailer_on_youtube(self, title: str):
        """Open a YouTube search for '<title> trailer' in the default browser."""
        query = urllib.parse.quote_plus(f"{title} trailer")
        url = f"https://www.youtube.com/results?search_query={query}"
        webbrowser.open(url)

    # ---------- POSTER THUMBNAIL HELPER ----------

    def fetch_poster_thumbnail(self, title: str):
        """
        Try to fetch a simple placeholder PNG with the movie title text.
        Uses https://via.placeholder.com which returns PNG images.
        This avoids external libraries like Pillow.
        """
        try:
            context = ssl._create_unverified_context()
            short_title = title[:12]
            text_param = urllib.parse.quote_plus(short_title)
            url = f"https://via.placeholder.com/160x90.png?text={text_param}"

            with urllib.request.urlopen(url, context=context) as resp:
                data = resp.read()

            # PhotoImage supports PNG in modern Tk builds
            img = tk.PhotoImage(data=data)
            return img
        except Exception:
            return None

    # ---------- UI UPDATE ----------

    def update_cards(self):
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        self.poster_images = []  # prevent old references from piling up

        if not self.current_suggestions:
            label = tk.Label(
                self.cards_frame,
                text="No suggestions yet. Fetch from IMDb or load a CSV,\nthen set your filters and click 'Find Movies'.",
                bg="black",
                fg="white",
                font=("Arial", 14)
            )
            label.pack(pady=12)
            return

        for m in self.current_suggestions:
            card = tk.Frame(self.cards_frame, bg="#1f1f1f", bd=2, relief="groove")
            card.pack(fill="x", pady=5)

            top_row = tk.Frame(card, bg="#1f1f1f")
            top_row.pack(fill="x")

            # Poster thumbnail (placeholder)
            title = m.get("Title", "Unknown title")
            poster_img = self.fetch_poster_thumbnail(title)
            if poster_img is not None:
                poster_label = tk.Label(top_row, image=poster_img, bg="#1f1f1f")
                poster_label.image = poster_img
                poster_label.pack(side="left", padx=8, pady=4)
                self.poster_images.append(poster_img)  # keep reference

            text_frame = tk.Frame(top_row, bg="#1f1f1f")
            text_frame.pack(side="left", fill="x", expand=True)

            genre = m.get("Genre", "N/A")
            rating = m.get("IMDB_Rating", "N/A")
            runtime = m.get("Runtime", "N/A")
            year = m.get("Year", "N/A")

            title_label = tk.Label(
                text_frame,
                text=f"{title} ({year})",
                bg="#1f1f1f",
                fg="#f5c518",
                font=("Arial", 16, "bold")
            )
            title_label.pack(anchor="w", padx=4, pady=(4, 0))

            info_label = tk.Label(
                text_frame,
                text=f"Genre: {genre}   |   Rating: {rating}   |   Runtime: {runtime} min",
                bg="#1f1f1f",
                fg="white",
                font=("Arial", 13)
            )
            info_label.pack(anchor="w", padx=4, pady=(0, 4))

            trailer_button = tk.Button(
                card,
                text="Watch trailer on YouTube",
                bg="#f5c518",
                fg="black",
                font=("Arial", 11, "bold"),
                command=lambda t=title: self.open_trailer_on_youtube(t)
            )
            trailer_button.pack(anchor="w", padx=10, pady=(0, 6))


if __name__ == "__main__":
    root = tk.Tk()
    app = MovieRecommenderApp(root)
    root.mainloop()