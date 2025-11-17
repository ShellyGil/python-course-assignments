"""
IMDB Movie Picker GUI

- Uses an IMDB-based CSV (e.g. Kaggle "IMDB Top 1000" which is scraped from imdb.com).
- Lets the user choose:
    * Genre (dropdown, taken from the dataset)
    * Max duration in minutes
    * Minimum IMDB rating
- Suggests 3 movies that match these filters.
- Allows:
    * Regenerating 3 new random options from the filtered pool.
    * Saving the 3 current suggestions to a text file (user chooses where).
    * Optionally showing movie poster previews in a small window (if Poster_Link exists).

Visual style is inspired by the IMDB website colors: yellow (#f5c518), black, dark gray.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random
import pandas as pd

# Optional: for poster previews (if your CSV has Poster_Link URLs)
try:
    from PIL import Image, ImageTk
    import io
    import requests
    POSTER_SUPPORT = True
except ImportError:
    POSTER_SUPPORT = False


class MovieRecommenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IMDB Movie Picker")
        self.root.geometry("900x600")
        self.root.configure(bg="black")

        # Data-related attributes
        self.df = None           # full dataframe
        self.filtered_df = None  # filtered movies
        self.current_suggestions = []  # list of dicts (3 movies)

        # Build GUI
        self.create_header()
        self.create_controls()
        self.create_results_area()
        self.create_actions()

    # ----------------- UI SECTIONS -----------------

    def create_header(self):
        """Top yellow header bar (IMDB style)."""
        header_frame = tk.Frame(self.root, bg="#f5c518")
        header_frame.pack(fill="x")

        title_label = tk.Label(
            header_frame,
            text="IMDB Style Movie Picker",
            bg="#f5c518",
            fg="black",
            font=("Arial", 20, "bold")
        )
        title_label.pack(side="left", padx=20, pady=10)

        subtitle_label = tk.Label(
            header_frame,
            text="Answer a few questions and get your next movie",
            bg="#f5c518",
            fg="black",
            font=("Arial", 11)
        )
        subtitle_label.pack(side="left", padx=10)

    def create_controls(self):
        """Controls: dataset selection + filters."""
        controls_frame = tk.Frame(self.root, bg="black")
        controls_frame.pack(fill="x", padx=20, pady=10)

        # --- Dataset selection row ---
        ds_frame = tk.Frame(controls_frame, bg="black")
        ds_frame.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        ds_label = tk.Label(
            ds_frame,
            text="IMDB CSV file (e.g. imdb_top_1000.csv):",
            bg="black",
            fg="#f5c518",
            font=("Arial", 10, "bold")
        )
        ds_label.pack(side="left")

        self.dataset_path_var = tk.StringVar()
        ds_entry = tk.Entry(ds_frame, textvariable=self.dataset_path_var, width=50)
        ds_entry.pack(side="left", padx=8)

        ds_button = tk.Button(
            ds_frame,
            text="Browse...",
            bg="#f5c518",
            fg="black",
            command=self.browse_dataset
        )
        ds_button.pack(side="left")

        load_button = tk.Button(
            ds_frame,
            text="Load",
            bg="#f5c518",
            fg="black",
            command=self.load_dataset
        )
        load_button.pack(side="left", padx=5)

        # --- Genre selection ---
        genre_label = tk.Label(
            controls_frame,
            text="Genre:",
            bg="black",
            fg="white",
            font=("Arial", 10)
        )
        genre_label.grid(row=1, column=0, sticky="w")

        self.genre_var = tk.StringVar()
        self.genre_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.genre_var,
            state="readonly",
            width=25
        )
        self.genre_combo.grid(row=1, column=1, padx=5, pady=3, sticky="w")
        self.genre_combo["values"] = ["(Load dataset first)"]

        # --- Max duration ---
        dur_label = tk.Label(
            controls_frame,
            text="Max duration (min):",
            bg="black",
            fg="white",
            font=("Arial", 10)
        )
        dur_label.grid(row=1, column=2, sticky="w", padx=(20, 0))

        self.max_duration_var = tk.StringVar(value="180")  # default 3 hours
        dur_entry = tk.Entry(controls_frame, textvariable=self.max_duration_var, width=6)
        dur_entry.grid(row=1, column=3, padx=5, pady=3, sticky="w")

        # --- Min rating (slider) ---
        rating_label = tk.Label(
            controls_frame,
            text="Min IMDB rating:",
            bg="black",
            fg="white",
            font=("Arial", 10)
        )
        rating_label.grid(row=2, column=0, sticky="w", pady=(5, 0))

        self.min_rating_var = tk.DoubleVar(value=7.0)
        rating_scale = tk.Scale(
            controls_frame,
            variable=self.min_rating_var,
            from_=0.0,
            to=10.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            length=200,
            bg="black",
            fg="white",
            highlightbackground="black"
        )
        rating_scale.grid(row=2, column=1, sticky="w", pady=(5, 0))

    def create_results_area(self):
        """Area where the 3 movie cards will appear."""
        results_frame = tk.Frame(self.root, bg="black")
        results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        results_label = tk.Label(
            results_frame,
            text="Suggestions:",
            bg="black",
            fg="#f5c518",
            font=("Arial", 12, "bold")
        )
        results_label.pack(anchor="w")

        self.cards_frame = tk.Frame(results_frame, bg="black")
        self.cards_frame.pack(fill="both", expand=True, pady=5)

    def create_actions(self):
        """Buttons at the bottom: find, regenerate, save, previews."""
        actions_frame = tk.Frame(self.root, bg="black")
        actions_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.find_button = tk.Button(
            actions_frame,
            text="Find Movies",
            bg="#f5c518",
            fg="black",
            font=("Arial", 11, "bold"),
            command=self.find_movies
        )
        self.find_button.pack(side="left", padx=5)

        self.regen_button = tk.Button(
            actions_frame,
            text="Regenerate 3 options",
            bg="#f5c518",
            fg="black",
            font=("Arial", 10),
            command=self.regenerate_movies,
            state="disabled"
        )
        self.regen_button.pack(side="left", padx=5)

        self.save_button = tk.Button(
            actions_frame,
            text="Save results to text file",
            bg="#f5c518",
            fg="black",
            font=("Arial", 10),
            command=self.save_results,
            state="disabled"
        )
        self.save_button.pack(side="left", padx=5)

        if POSTER_SUPPORT:
            self.preview_button = tk.Button(
                actions_frame,
                text="Show poster previews",
                bg="#f5c518",
                fg="black",
                font=("Arial", 10),
                command=self.show_posters,
                state="disabled"
            )
            self.preview_button.pack(side="left", padx=5)

        info_label = tk.Label(
            actions_frame,
            text="Tip: adjust filters and click 'Find Movies' again if you get too few results.",
            bg="black",
            fg="white",
            font=("Arial", 9)
        )
        info_label.pack(side="right")

    # ----------------- DATA HANDLING -----------------

    def browse_dataset(self):
        """Let user choose a CSV file from disk."""
        path = filedialog.askopenfilename(
            title="Select IMDB CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.dataset_path_var.set(path)

    def load_dataset(self):
        """Load CSV into pandas and prepare columns."""
        path = self.dataset_path_var.get().strip()
        if not path:
            messagebox.showwarning("No file", "Please choose a CSV file first.")
            return

        try:
            df = pd.read_csv(path)
        except Exception as e:
            messagebox.showerror("Error loading CSV", f"Could not load file:\n{e}")
            return

        # Some Kaggle IMDB datasets use 'Series_Title' instead of 'Title'
        if "Title" not in df.columns and "Series_Title" in df.columns:
            df["Title"] = df["Series_Title"]

        # Required columns
        required_cols = ["Title", "Genre", "IMDB_Rating"]
        for col in required_cols:
            if col not in df.columns:
                messagebox.showerror(
                    "Missing columns",
                    f"Required column '{col}' not found in CSV.\n"
                    f"Available columns: {', '.join(df.columns)}"
                )
                return

        # Parse runtime into minutes if possible
        if "Runtime" in df.columns:
            df["Runtime_Min"] = df["Runtime"].apply(self.parse_runtime)
        else:
            df["Runtime_Min"] = None  # will skip dur filter if missing

        self.df = df

        # Build genre list from all rows
        genres = set()
        for g in df["Genre"].dropna():
            parts = [x.strip() for x in str(g).split(",")]
            genres.update(parts)

        genre_list = sorted(list(genres))
        self.genre_combo["values"] = genre_list if genre_list else ["(No genres found)"]
        if genre_list:
            self.genre_combo.current(0)

        messagebox.showinfo("Dataset loaded", "IMDB data loaded successfully!")

    @staticmethod
    def parse_runtime(x):
        """
        Convert '142 min' or '142' to an int (minutes), otherwise None.
        E.g. '175 min' -> 175
        """
        if pd.isna(x):
            return None
        s = str(x)
        s = s.replace("min", "").strip()
        try:
            return int(s)
        except ValueError:
            return None

    # ----------------- MOVIE SELECTION LOGIC -----------------

    def filter_movies(self):
        """
        Apply filters:
        - Genre contains chosen genre
        - IMDB_Rating >= chosen minimum
        - Runtime_Min <= chosen max duration (if available)
        """
        if self.df is None:
            messagebox.showwarning("No data", "Please load an IMDB CSV file first.")
            return None

        genre = self.genre_var.get().strip()
        max_dur_str = self.max_duration_var.get().strip()
        try:
            max_dur = int(max_dur_str)
        except ValueError:
            max_dur = None

        min_rating = self.min_rating_var.get()

        df = self.df.copy()

        # Filter by genre (partial match, because many rows have multiple genres)
        if genre:
            df = df[df["Genre"].fillna("").str.contains(genre, case=False, na=False)]

        # Filter by rating
        df["IMDB_Rating"] = pd.to_numeric(df["IMDB_Rating"], errors="coerce")
        df = df[df["IMDB_Rating"] >= min_rating]

        # Filter by duration if we have runtime info
        if max_dur is not None and "Runtime_Min" in df.columns:
            df["Runtime_Min"] = pd.to_numeric(df["Runtime_Min"], errors="coerce")
            df = df[df["Runtime_Min"] <= max_dur]

        df = df.dropna(subset=["Title"])  # ensure titles are not NaN

        if df.empty:
            return None

        self.filtered_df = df.reset_index(drop=True)
        return self.filtered_df

    def pick_three_movies(self):
        """Randomly pick 3 movies from filtered_df."""
        if self.filtered_df is None or self.filtered_df.empty:
            return []

        df = self.filtered_df

        if len(df) <= 3:
            chosen = df
        else:
            indices = random.sample(range(len(df)), 3)
            chosen = df.iloc[indices]

        return chosen.to_dict(orient="records")

    # ----------------- BUTTON ACTIONS -----------------

    def find_movies(self):
        """Main button: filter and pick 3 movies."""
        filtered = self.filter_movies()
        if filtered is None or filtered.empty:
            messagebox.showinfo("No matches", "No movies match your filters. Try relaxing them.")
            self.current_suggestions = []
            self.update_cards()
            self.regen_button.config(state="disabled")
            self.save_button.config(state="disabled")
            if POSTER_SUPPORT:
                self.preview_button.config(state="disabled")
            return

        self.current_suggestions = self.pick_three_movies()
        self.update_cards()

        # Enable actions
        self.regen_button.config(state="normal")
        self.save_button.config(state="normal")
        if POSTER_SUPPORT:
            self.preview_button.config(state="normal")

    def regenerate_movies(self):
        """Pick 3 new movies from the already-filtered pool."""
        if self.filtered_df is None or self.filtered_df.empty:
            return
        self.current_suggestions = self.pick_three_movies()
        self.update_cards()

    def save_results(self):
        """
        Save the 3 current suggestions to a text file.
        User chooses where to save (Save As dialog).
        """
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
                f.write("IMDB Movie Picker - Suggestions\n")
                f.write("--------------------------------\n\n")
                for i, m in enumerate(self.current_suggestions, start=1):
                    title = m.get("Title", "Unknown title")
                    genre = m.get("Genre", "N/A")
                    rating = m.get("IMDB_Rating", "N/A")
                    runtime = m.get("Runtime", m.get("Runtime_Min", "N/A"))
                    f.write(f"{i}. {title}\n")
                    f.write(f"   Genre: {genre}\n")
                    f.write(f"   Rating: {rating}\n")
                    f.write(f"   Runtime: {runtime}\n\n")

            messagebox.showinfo("Saved", f"Suggestions saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error saving file", f"Could not save file:\n{e}")

    def show_posters(self):
        """Open a small window with poster previews for the 3 suggested movies."""
        if not POSTER_SUPPORT:
            messagebox.showinfo(
                "Poster previews",
                "Pillow or requests not installed, cannot show posters."
            )
            return

        if not self.current_suggestions:
            messagebox.showwarning("No suggestions", "There are no movie suggestions to show.")
            return

        poster_window = tk.Toplevel(self.root)
        poster_window.title("Poster previews")
        poster_window.configure(bg="black")

        for i, movie in enumerate(self.current_suggestions):
            frame = tk.Frame(poster_window, bg="black")
            frame.pack(side="left", padx=10, pady=10)

            title = movie.get("Title", "Unknown title")
            label = tk.Label(
                frame,
                text=title,
                bg="black",
                fg="#f5c518",
                font=("Arial", 10, "bold")
            )
            label.pack(pady=5)

            url = movie.get("Poster_Link", "")
            if not url:
                no_img_label = tk.Label(frame, text="No poster URL", bg="black", fg="white")
                no_img_label.pack()
                continue

            try:
                resp = requests.get(url, timeout=5)
                resp.raise_for_status()
                image_data = resp.content
                img = Image.open(io.BytesIO(image_data))
                img = img.resize((200, 300))
                photo = ImageTk.PhotoImage(img)

                img_label = tk.Label(frame, image=photo, bg="black")
                img_label.image = photo  # keep reference
                img_label.pack()
            except Exception:
                no_img_label = tk.Label(frame, text="Error loading image", bg="black", fg="white")
                no_img_label.pack()

    # ----------------- UI HELPER -----------------

    def update_cards(self):
        """Update the suggestion cards in the main window."""
        # Clear old cards
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        if not self.current_suggestions:
            empty_label = tk.Label(
                self.cards_frame,
                text="No suggestions yet. Load a dataset and click 'Find Movies'.",
                bg="black",
                fg="white",
                font=("Arial", 11)
            )
            empty_label.pack(pady=20)
            return

        for movie in self.current_suggestions:
            card = tk.Frame(self.cards_frame, bg="#1f1f1f", bd=2, relief="groove")
            card.pack(fill="x", pady=5)

            title = movie.get("Title", "Unknown title")
            genre = movie.get("Genre", "N/A")
            rating = movie.get("IMDB_Rating", "N/A")
            runtime = movie.get("Runtime", movie.get("Runtime_Min", "N/A"))

            title_label = tk.Label(
                card,
                text=title,
                bg="#1f1f1f",
                fg="#f5c518",
                font=("Arial", 12, "bold")
            )
            title_label.pack(anchor="w", padx=10, pady=(5, 0))

            info_label = tk.Label(
                card,
                text=f"Genre: {genre}   |   Rating: {rating}   |   Runtime: {runtime}",
                bg="#1f1f1f",
                fg="white",
                font=("Arial", 10)
            )
            info_label.pack(anchor="w", padx=10, pady=(0, 5))


if __name__ == "__main__":
    root = tk.Tk()
    app = MovieRecommenderApp(root)
    root.mainloop()