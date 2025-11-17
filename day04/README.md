# Day 04 – IMDb Downloader

This program downloads data from the [IMDb Top 250](https://www.imdb.com/chart/top) page, saves the raw HTML locally, and can also parse the titles (rank/title/year/url) into a JSON file. The UI is available both as a GUI (`day04.gui`) and a Typer CLI that call the business logic in `imdb_client.py`.

## Setup
- Install dependencies: `python3 -m pip install -r ../requirements.txt`
- (Optional) Copy `credentials.example.json` to `credentials.json` and fill in `user_agent`/`email` if you want to pass contact info with requests. The credentials file is git-ignored.

## GUI Usage
- Launch GUI: `python -m day04.gui`
- Choose where to save the HTML/JSON, toggle parsing, set an optional limit (1-250), and optionally point to a credentials JSON.

## CLI Usage
- CLI help: `python -m day04.cli --help`
- Download and parse (default paths under `day04/data`): `python -m day04.cli download`
- Skip parsing: `python -m day04.cli download --no-parse`
- Limit parsed titles: `python -m day04.cli download --limit 20`

## Prompts given to Codex
- “Remove the __pycache__ folder(s) from my day03 folder in my python course assignment repository and make sure it won't be added again by mistake.”
- “In the day04 folder write a program that will download some data from IMDb web site and save it locally in a file or in multiple files. Separate the "business logic" and the UI (User Interface), the way the program interacts with the user. Pick whatever UI method you like. If I need to provide my email addres or if I need to use some API secrets, makes sure thos are saved in a separate file and make my code read these values from that file. Make sure the file does not get added to git by adding its name to .gitignore.”
- “fix the problem on this script”
- “create a readme.md file in the day04 folder. in the day04/README.md explain in a few words what the program does. Include links where necessary. Also include any interaction I had with the codex (prompts)”
