# 📘 Day 04 – IMDb Movie Picker  
*A Python project demonstrating downloading data from a real website, saving it locally,  
separating business logic from UI, and interacting with the user through a GUI.*

---

## 🎬 Overview  
This project uses the **IMDb public datasets** to create a movie-picking application.  
The program automatically:

1. **Downloads real data** from the IMDb dataset servers  
   https://datasets.imdbws.com/
2. **Extracts, merges and saves** the relevant movie information (title, genre, year, runtime, rating)
3. **Stores the processed data locally** inside:  
   ```
   day04/data/imdb_movies.csv
   ```
4. Provides a **Tkinter GUI** that lets the user:
   - Select a genre  
   - Choose a year range  
   - Set a minimum IMDb rating  
   - Limit movie duration  
   - Generate **three movie recommendations** based on these preferences  

The project demonstrates correct **separation of business logic vs. user interface**:

- `imdb_data.py` → downloading, saving, loading, filtering (no UI code)  
- `imdb_gui.py` → Tkinter interface (no data-processing logic)

---

## 🌐 Data Source  
We use the official IMDb public dataset files:

- `title.basics.tsv.gz`  
- `title.ratings.tsv.gz`  

Downloaded from:  
🔗 https://datasets.imdbws.com/

These contain:
- Titles  
- Genres  
- Release years  
- Runtime  
- IMDb ratings  
- Vote counts  

The program downloads, merges, and saves the processed results as a clean CSV file.

---

## 🧱 Project Structure  

```
day04/
│
├── imdb_data.py            # Business logic: download, save, load, filter
├── imdb_gui.py             # User interface: Tkinter GUI that uses imdb_data.py
├── data/
│      └── imdb_movies.csv  # Saved movie dataset (auto-created)
│
└── README.md               # This file
```

---

## 🧠 Business Logic (imdb_data.py)

`imdb_data.py` contains:

### ✔ Download logic  
Downloads IMDb `.tsv.gz` files using `urllib.request` and a relaxed SSL context  
(to avoid CERTIFICATE_VERIFY_FAILED issues on macOS).

### ✔ Parsing & merging  
Extracts:
- Title  
- Genre(s)  
- Runtime  
- Release year  
- IMDb rating  

### ✔ Saving  
All processed movies are saved locally to:

```
day04/data/imdb_movies.csv
```

### ✔ Loading & filtering  
- Loads the CSV into Python  
- Filters by:
  - genre  
  - year range  
  - minimum rating  
  - duration  

This module does **not** contain any Tkinter or UI code.

---

## 🖥️ User Interface (imdb_gui.py)

The Tkinter interface allows the user to:

- Fetch & save fresh IMDb data  
- Load an existing CSV  
- Select filters via dropdowns, sliders, and text fields  
- Generate 3 matched movie recommendations  
- Regenerate new suggestions  

The UI **does not implement its own filtering or downloading**.  
It only calls:

```python
fetch_and_save_imdb_movies()
load_movies_from_csv()
filter_movies()
```

This ensures separation of concerns.

---

## 🔧 How It Works (Step-by-Step)

1. User runs:
   ```
   python3 imdb_gui.py
   ```
2. User clicks **“Fetch & save from IMDb (online)”**  
   - Downloads IMDb datasets  
   - Parses + merges data  
   - Saves CSV locally  
3. User sets preferences (genre, rating, years, duration)  
4. User clicks **Find Movies**  
   - GUI asks the logic module to filter  
   - 3 movies are suggested  
5. User can click **Regenerate** for new options  

---

## 🔒 No API keys or credentials  
IMDb datasets are completely public.  
No keys, secrets, or emails were required.

---

## 🤝 Interaction With AI

Below is a **clean, summarized list** of the relevant prompts I provided to the AI while developing this project.  
These are the interactions that directly influenced the design, structure, or code.

### **➤ My prompts to the AI (summarized):**

1. *“I want to create a GUI in Visual Studio (Python) to help choose a movie.”*  
2. *“The GUI should ask genre, rating, runtime… and output 3 movies.”*  
3. *“Make the app save results to a text file.”*  
4. *“Include a feature to regenerate 3 new movie suggestions.”*  
5. *“The design is not good — improve it and make the text bigger.”*  
6. *“Fetch data automatically from IMDb instead of using a local CSV.”*  
7. *“I’m getting SSL certificate errors on Mac — fix it.”*  
8. *“Add features: history, posters, YouTube trailer links, year filters.”*  
9. *“Separate business logic from UI to meet assignment requirements.”*  
10. *“Create imdb_data.py and imdb_gui.py with correct separation.”*  
11. *“Generate README.md explaining everything.”*  
12. *“Include my prompts in the README.”*

### **➤ How AI helped me:**
- Designed the project structure  
- Implemented IMDb downloading logic  
- Helped build a clean Tkinter GUI  
- Added filtering & random recommendation logic  
- Handled SSL issues  
- Helped restructure logic/UI separation  
- Wrote documentation  
- Improved maintainability & readability 
