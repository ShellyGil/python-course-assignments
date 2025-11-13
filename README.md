# PCR Calculator Assignments

## Requirements
- Python 3.10 or newer
- `pip` for dependency installation

## Installation
1. (Optional) create and activate a virtual environment.
2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the Typer-powered CLI from the repository root. Example:
```bash
python day03/PCR_Calculator.py 24 --excess 12 --mix 5
```
The command prints the per-sample recipe and total volumes using the shared `pcr_logic` module.

## Tests
The business logic is covered via the standard library's `unittest` module (`tests/test_pcr_logic.py`).
```bash
python -m unittest discover tests
```

## AI Usage
This project was assisted by ChatGPT (Codex) using the following prompts provided by the course:

1. “Regarding the PCR_Calculator on the day03 folder: Move the ‘business logic’ (the computation) to a separate file and make the main program use it. It is enough to have one way to use it GUI/command line/STDIN.”
2. “Add some tests, especially to check the ‘business logic’. Make sure you can run the tests. Look at the tests and make sure they test the code properly.
   Replace code with some 3rd-party.
   Add a README.md explaining how to install dependencies, if there are any. Also explain how I used AI”
