"""
imdb_gui.py - Tkinter GUI for the IMDb Movie Picker

UI layer only — all data download / save / load / filter logic
is done in imdb_data.py (business logic).
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random
import webbrowser   # <-- Needed for YouTube trailer links

from imdb_data import (
    fetch_and_save_imdb_movies,
    load_movies_from_csv,
    filter_movies
)


class MovieRecommenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IMDB Movie Picker - GUI")

        self.root.geometry("900x600")
        self.root.configure(bg="black")

        # Data
        self.movies = []
        self.filtered_movies = []
        self.current_suggestions = []

        # UI
        self.create_header()
        self.create_controls()
        self.create_results_area()
        self.create_actions()

    # ---------------- UI SECTIONS ----------------

    def create_header(self):
        header = tk.Frame(self.root, bg="#f5c518")
        header.pack(fill="x")

        tk.Label(
            header, text="IMDB Movie Picker",
            bg="#f5c518", fg="black",
            font=("Arial", 26, "bold")
        ).pack(side="left", padx=20, pady=5)

        tk.Label(
            header, text="Choose your mood, we pick the movie",
            bg="#f5c518", fg="black",
            font=("Arial", 14)
        ).pack(side="left", padx=15)

    def create_controls(self):
        controls = tk.Frame(self.root, bg="black")
        controls.pack(fill="x", padx=20, pady=8)

        # --- Buttons row ---
        row = tk.Frame(controls, bg="black")
        row.grid(row=0, column=0, columnspan=6, sticky="w")

        tk.Button(
            row, text="Fetch & save from IMDb (online)",
            bg="#f5c518", fg="black", font=("Arial", 12, "bold"),
            command=self.fetch_from_imdb
        ).pack(side="left", padx=4, pady=5)

        tk.Button(
            row, text="Load local CSV",
            bg="#f5c518", fg="black", font=("Arial", 12, "bold"),
            command=self.load_local_csv
        ).pack(side="left", padx=4)

        # --- Genre ---
        tk.Label(
            controls, text="Genre:",
            bg="black", fg="white", font=("Arial", 14)
        ).grid(row=1, column=0, sticky="w")

        self.genre_var = tk.StringVar()
        self.genre_combo = ttk.Combobox(
            controls, textvariable=self.genre_var,
            state="readonly", width=25,
            font=("Arial", 13)
        )
        self.genre_combo.grid(row=1, column=1, padx=8, pady=6)
        self.genre_combo["values"] = ["(Any genre)"]
        self.genre_combo.current(0)

        # --- Year Range ---
        tk.Label(
            controls, text="Year from:",
            bg="black", fg="white", font=("Arial", 14)
        ).grid(row=1, column=2, sticky="w", padx=(20, 0))

        self.min_year_var = tk.StringVar()
        tk.Entry(
            controls, textvariable=self.min_year_var, width=6,
            font=("Arial", 13)
        ).grid(row=1, column=3, padx=5)

        tk.Label(
            controls, text="to:", bg="black", fg="white",
            font=("Arial", 14)
        ).grid(row=1, column=4)

        self.max_year_var = tk.StringVar()
        tk.Entry(
            controls, textvariable=self.max_year_var,
            width=6, font=("Arial", 13)
        ).grid(row=1, column=5, padx=5)

        # --- Max Duration ---
        tk.Label(
            controls, text="Max duration (min):",
            bg="black", fg="white", font=("Arial", 14)
        ).grid(row=2, column=0, sticky="w", pady=6)

        self.max_duration_var = tk.StringVar(value="180")
        tk.Entry(
            controls, textvariable=self.max_duration_var,
            width=6, font=("Arial", 13)
        ).grid(row=2, column=1, padx=5)

        # --- Min Rating ---
        tk.Label(
            controls, text="Min IMDb rating:",
            bg="black", fg="white", font=("Arial", 14)
        ).grid(row=2, column=2, sticky="w")

        self.min_rating_var = tk.DoubleVar(value=7.0)
        tk.Scale(
            controls, from_=0.0, to=10.0,
            variable=self.min_rating_var, resolution=0.1,
            orient=tk.HORIZONTAL, length=250,
            bg="black", fg="white",
            troughcolor="gray20"
        ).grid(row=2, column=3, columnspan=2, sticky="w")

    def create_results_area(self):
        frame = tk.Frame(self.root, bg="black")
        frame.pack(fill="both", expand=True, padx=20, pady=5)

        tk.Label(
            frame, text="Suggestions:",
            bg="black", fg="#f5c518", font=("Arial", 16, "bold")
        ).pack(anchor="w")

        self.cards_frame = tk.Frame(frame, bg="black")
        self.cards_frame.pack(fill="both", expand=True)

    def create_actions(self):
        actions = tk.Frame(self.root, bg="black")
        actions.pack(fill="x", padx=20, pady=8)

        tk.Button(
            actions, text="Find Movies",
            bg="#f5c518", fg="black", font=("Arial", 14, "bold"),
            command=self.find_movies
        ).pack(side="left", padx=5)

        self.regen_button = tk.Button(
            actions, text="Regenerate 3 options",
            bg="#f5c518", fg="black", font=("Arial", 13, "bold"),
            command=self.regenerate_movies, state="disabled"
        )
        self.regen_button.pack(side="left", padx=5)

    # ---------------- DATA OPERATIONS ----------------

    def fetch_from_imdb(self):
        try:
            self.movies = fetch_and_save_imdb_movies(
                output_path="data/imdb_movies.csv",
                max_movies=5000
            )
            self.update_genre_list()
            messagebox.showinfo("IMDb", "Data downloaded and saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch IMDb data:\n{e}")

    def load_local_csv(self):
        path = filedialog.askopenfilename(
            title="Select IMDb CSV",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return
        try:
            self.movies = load_movies_from_csv(path)
            self.update_genre_list()
            messagebox.showinfo("Loaded", "CSV loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV:\n{e}")

    def update_genre_list(self):
        genres = set()
        for m in self.movies:
            g = m.get("Genre", "")
            if g:
                for part in g.split(","):
                    genres.add(part.strip())
        genres.add("Horror")
        genre_list = ["(Any genre)"] + sorted(genres)
        self.genre_combo["values"] = genre_list
        self.genre_combo.current(0)

    # ---------------- FILTERING ----------------

    def parse_int(self, value):
        try:
            return int(value.strip())
        except:
            return None

    def filter_current(self):
        genre = self.genre_var.get()
        if genre == "(Any genre)":
            genre = None
        min_year = self.parse_int(self.min_year_var.get())
        max_year = self.parse_int(self.max_year_var.get())
        max_dur = self.parse_int(self.max_duration_var.get())
        min_rating = self.min_rating_var.get()

        return filter_movies(
            self.movies,
            genre=genre,
            min_year=min_year,
            max_year=max_year,
            min_rating=min_rating,
            max_duration=max_dur
        )

    # ---------------- YOUTUBE TRAILER ----------------

    def open_trailer(self, title):
        """
        Open YouTube search for "<title> trailer"
        """
        query = title.replace(" ", "+")
        url = f"https://www.youtube.com/results?search_query={query}+trailer"
        webbrowser.open(url)

    # ---------------- FIND & DISPLAY MOVIES ----------------

    def choose_three(self, movies):
        if len(movies) <= 3:
            return list(movies)
        return random.sample(movies, 3)

    def find_movies(self):
        filtered = self.filter_current()
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
        self.find_movies()

    # ---------------- UI CARD DISPLAY ----------------

    def update_cards(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()

        if not self.current_suggestions:
            tk.Label(
                self.cards_frame,
                text="No suggestions yet.",
                bg="black", fg="white",
                font=("Arial", 14)
            ).pack(pady=10)
            return

        for m in self.current_suggestions:
            card = tk.Frame(self.cards_frame, bg="#1f1f1f", bd=2, relief="groove")
            card.pack(fill="x", pady=5)

            title = m["Title"]
            genre = m["Genre"]
            rating = m["IMDB_Rating"]
            runtime = m["Runtime"]
            year = m["Year"]

            tk.Label(
                card, text=f"{title} ({year})",
                bg="#1f1f1f", fg="#f5c518",
                font=("Arial", 16, "bold")
            ).pack(anchor="w", padx=8, pady=(4, 0))

            tk.Label(
                card,
                text=f"Genre: {genre}   |   Rating: {rating}   |   Runtime: {runtime} min",
                bg="#1f1f1f", fg="white",
                font=("Arial", 13)
            ).pack(anchor="w", padx=8, pady=(0, 6))

            # ---- YOUTUBE TRAILER BUTTON ----
            tk.Button(
                card,
                text="Watch trailer on YouTube",
                bg="#f5c518", fg="black",
                font=("Arial", 11, "bold"),
                command=lambda t=title: self.open_trailer(t)
            ).pack(anchor="w", padx=8, pady=(0, 8))


if __name__ == "__main__":
    root = tk.Tk()
    app = MovieRecommenderApp(root)
    root.mainloop()