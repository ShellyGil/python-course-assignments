"""
imdb_gui.py - Tkinter user interface for the IMDB Movie Picker

This file is the UI layer only. It uses the functions from imdb_data.py:
- fetch_and_save_imdb_movies
- load_movies_from_csv
- filter_movies

The user can:
- Download & save fresh IMDb data with a button (business logic is hidden inside imdb_data.py)
- Load the saved CSV
- Choose filters (genre, year range, min rating, max duration)
- See 3 random suggestions
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random

from imdb_data import (
    fetch_and_save_imdb_movies,
    load_movies_from_csv,
    filter_movies
)


class MovieRecommenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IMDB Movie Picker - GUI")

        self.root.geometry("900x550")
        self.root.configure(bg="black")

        # Data in memory (logic handled by imdb_data)
        self.movies = []
        self.filtered_movies = []
        self.current_suggestions = []

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

        # --- Data row ---
        data_frame = tk.Frame(controls_frame, bg="black")
        data_frame.grid(row=0, column=0, columnspan=6, sticky="w")

        fetch_button = tk.Button(
            data_frame,
            text="Fetch & save from IMDb (online)",
            bg="#f5c518",
            fg="black",
            font=("Arial", 12, "bold"),
            command=self.fetch_from_imdb
        )
        fetch_button.pack(side="left", padx=5, pady=5)

        load_button = tk.Button(
            data_frame,
            text="Load local CSV",
            bg="#f5c518",
            fg="black",
            font=("Arial", 12, "bold"),
            command=self.load_local_csv
        )
        load_button.pack(side="left", padx=5, pady=5)

        # --- Genre ---
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
        self.genre_combo["values"] = ["(Any genre)"]
        self.genre_combo.current(0)

        # --- Year range ---
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

        # --- Max duration ---
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

        # --- Min rating slider ---
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

    # ---------- DATA CONNECTIONS (CALLING BUSINESS LOGIC) ----------

    def fetch_from_imdb(self):
        try:
            movies = fetch_and_save_imdb_movies(output_path="data/imdb_movies.csv", max_movies=5000)
            self.movies = movies
            self.update_genre_list()
            messagebox.showinfo("IMDb", f"Fetched and saved {len(movies)} movies to data/imdb_movies.csv")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch IMDb data:\n{e}")

    def load_local_csv(self):
        path = filedialog.askopenfilename(
            title="Select IMDb CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            self.movies = load_movies_from_csv(path)
            self.update_genre_list()
            messagebox.showinfo("Loaded", f"Loaded {len(self.movies)} movies from {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV:\n{e}")

    def update_genre_list(self):
        genres_set = set()
        for m in self.movies:
            g = m.get("Genre", "")
            if g:
                for part in g.split(","):
                    genres_set.add(part.strip())
        genres_set.add("Horror")  # ensure horror present

        genres = sorted(list(genres_set))
        genres.insert(0, "(Any genre)")
        self.genre_combo["values"] = genres
        self.genre_combo.current(0)

    # ---------- FILTER & SUGGESTION ----------

    def parse_int_or_none(self, value):
        value = value.strip()
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def filter_current_movies(self):
        if not self.movies:
            messagebox.showwarning("No data", "Please fetch from IMDb or load a CSV first.")
            return []

        genre = self.genre_var.get()
        if genre == "(Any genre)":
            genre = None

        min_year = self.parse_int_or_none(self.min_year_var.get())
        max_year = self.parse_int_or_none(self.max_year_var.get())
        max_dur = self.parse_int_or_none(self.max_duration_var.get())
        min_rating = self.min_rating_var.get()

        return filter_movies(
            self.movies,
            genre=genre,
            min_year=min_year,
            max_year=max_year,
            min_rating=min_rating,
            max_duration=max_dur
        )

    def choose_three(self, movies):
        if len(movies) <= 3:
            return list(movies)
        return random.sample(movies, 3)

    def find_movies(self):
        filtered = self.filter_current_movies()
        if not filtered:
            messagebox.showinfo("No matches", "No movies match your filters.")
            self.current_suggestions = []
            self.update_cards()
            self.regen_button.config(state="disabled")
            return

        self.current_suggestions = self.choose_three(filtered)
        self.update_cards()
        self.regen_button.config(state="normal")

    def regenerate_movies(self):
        filtered = self.filter_current_movies()
        if not filtered:
            messagebox.showinfo("No matches", "No movies match your filters.")
            self.current_suggestions = []
            self.update_cards()
            self.regen_button.config(state="disabled")
            return

        old_titles = {m["Title"] for m in self.current_suggestions}
        if len(filtered) <= 3:
            self.current_suggestions = self.choose_three(filtered)
        else:
            for _ in range(10):
                new_set = self.choose_three(filtered)
                new_titles = {m["Title"] for m in new_set}
                if new_titles != old_titles:
                    self.current_suggestions = new_set
                    break
        self.update_cards()

    # ---------- UI UPDATE ----------

    def update_cards(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()

        if not self.current_suggestions:
            label = tk.Label(
                self.cards_frame,
                text="No suggestions yet.",
                bg="black",
                fg="white",
                font=("Arial", 14)
            )
            label.pack(pady=10)
            return

        for m in self.current_suggestions:
            card = tk.Frame(self.cards_frame, bg="#1f1f1f", bd=2, relief="groove")
            card.pack(fill="x", pady=4)

            title = m.get("Title", "Unknown title")
            genre = m.get("Genre", "N/A")
            rating = m.get("IMDB_Rating", "N/A")
            runtime = m.get("Runtime", "N/A")
            year = m.get("Year", "N/A")

            title_label = tk.Label(
                card,
                text=f"{title} ({year})",
                bg="#1f1f1f",
                fg="#f5c518",
                font=("Arial", 16, "bold")
            )
            title_label.pack(anchor="w", padx=8, pady=(4, 0))

            info_label = tk.Label(
                card,
                text=f"Genre: {genre}   |   Rating: {rating}   |   Runtime: {runtime} min",
                bg="#1f1f1f",
                fg="white",
                font=("Arial", 13)
            )
            info_label.pack(anchor="w", padx=8, pady=(0, 6))


if __name__ == "__main__":
    root = tk.Tk()
    app = MovieRecommenderApp(root)
    root.mainloop()