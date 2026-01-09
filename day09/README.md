# Student Submission Analyzer

This Python tool parses a raw submission log (`subjects.txt`) to generate a comprehensive report on student performance. It tracks missing assignments, calculates submission delays based on strict deadlines, and analyzes naming conventions used by students.

## Features

* **Robust Parsing:** Handles multi-line log entries and messy input formats automatically.
* **Missing Assignments:** Identifies exactly which assignments each student has failed to submit.
* **Late Submission Tracking:** compares submission timestamps against strict deadlines (down to the second) and reports the exact delay (Days/Hours/Minutes).
* **Format Popularity:** Analyzes the variations in how students name their subject lines (e.g., "Day01" vs "Day 1").
* **Path Awareness:** Automatically locates the input file in the script's directory, preventing `FileNotFoundError` issues when running from different terminal locations.

## Requirements

* Python 3.6+
* No external dependencies required (uses standard libraries: `re`, `os`, `datetime`, `collections`).

## Setup

1.  **Place Files:** Ensure `analyze_subjects.py` and your data file `subjects.txt` are in the **same folder**.
2.  **Configuration:** The script is pre-configured with the following course deadlines:

    * **Day 1-6, 8, 9:** Specific dates in Nov/Dec 2025 and Jan 2026.
    * **Final Project Proposal:** Jan 11, 2026.
    * **Final Project:** Jan 25, 2026.

    *(Note: You can modify the `DEADLINES` dictionary inside the script to update these dates.)*

## Development History & Prompts

Summary of the user prompts used to build this tool:

Initial Request: The user uploaded a subjects.txt file containing raw submission logs and requested a Python program to generate a report. The requested features included tracking missing assignments, late submissions, distribution of submission times, and subject line format popularity.

Bug Report (Syntax): The user reported a SyntaxError: unterminated string literal in the first version of the code, caused by an issue with regex string escaping.

Bug Report (Pathing): The user reported a FileNotFoundError. Although the file was saved in the correct folder, the script failed because it was being run from the project root rather than the subdirectory. The code was updated to dynamically detect the script's own directory.

Deadline Configuration: The user provided the specific, hard numbers for the deadlines (Dates and Times for Day 1-9 and the Final Project). The code was updated to integrate these exact timestamps into the logic.

Documentation: The user requested this README.md file to document the project and summarize the interaction history.

## Usage

Run the script from your terminal:

```bash
python analyze_subjects.py
