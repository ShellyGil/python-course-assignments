import re
import os
from datetime import datetime
from collections import defaultdict, Counter

# ==========================================
# CONFIGURATION
# ==========================================

# 1. GET THE SCRIPT'S DIRECTORY
# This ensures Python looks in the same folder as the script
script_dir = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(script_dir, 'subjects.txt')

# 2. EXACT DEADLINES (Updated from README)
# Format: 'YYYY-MM-DD HH:MM:SS'
DEADLINES = {
    'Day01': '2025-11-01 22:00:00',
    'Day02': '2025-11-09 22:00:00',
    'Day03': '2025-11-16 22:00:00',
    'Day04': '2025-11-23 22:00:00',
    'Day05': '2025-11-29 22:00:00',
    'Day06': '2025-12-06 22:00:00',
    # Day07 is skipped ("no assignment")
    'Day08': '2025-12-30 22:00:00',
    'Day09': '2026-01-10 22:00:00',
    'Final Project Proposal': '2026-01-11 22:00:00',
    'Final Project': '2026-01-25 22:00:00'
}

# ==========================================
# PARSING LOGIC
# ==========================================

def clean_source_tags(text):
    """Safely removes artifacts."""
    return re.sub(r"\\", "", text)

def parse_subject_details(subject_text):
    """
    Splits the subject line into Assignment Name and Student Name.
    Distinguishes between 'Final Project' and 'Final Project Proposal'.
    """
    # Normalize separators
    normalized = subject_text.replace(" By ", " by ").replace(" - ", " by ").replace("-", " by ")
    
    student = "Unknown"
    
    if " by " in normalized:
        parts = normalized.split(" by ", 1)
        assignment_raw = parts[0].strip()
        student = parts[1].strip()
    else:
        # Fallback regex
        match = re.match(r"(Day\s*\d+|Final\s*Project.*?)\s+(.*)", normalized, re.IGNORECASE)
        if match:
            assignment_raw = match.group(1).strip()
            student = match.group(2).strip()
        else:
            assignment_raw = normalized

    # Normalize Assignment Name
    lower_raw = assignment_raw.lower()
    day_match = re.search(r"Day\s*0?(\d+)", assignment_raw, re.IGNORECASE)
    
    if day_match:
        assignment_norm = f"Day{int(day_match.group(1)):02d}"
    elif "proposal" in lower_raw:
        assignment_norm = "Final Project Proposal"
    elif "final" in lower_raw:
        assignment_norm = "Final Project"
    else:
        assignment_norm = assignment_raw

    return assignment_norm, assignment_raw, student

def parse_file_robust(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"ERROR: File not found at: {filepath}")
        return []

    entries = []
    buffer = ""
    # Regex for timestamp at end of record: YYYY-MM-DDTHH:MM:SSZ
    date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s*$")

    for line in lines:
        cleaned_line = clean_source_tags(line).strip()
        if not cleaned_line:
            continue

        if buffer:
            buffer += " " + cleaned_line
        else:
            buffer = cleaned_line

        date_match = date_pattern.search(buffer)
        if date_match:
            full_entry = buffer
            timestamp_str = date_match.group(1)
            submission_date = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")

            content_without_date = full_entry[:date_match.start()].strip()
            buffer = ""

            # Expecting: ID STATUS SUBJECT
            parts = re.split(r"\s+", content_without_date, maxsplit=2)
            
            if len(parts) >= 3:
                entry_id, status, subject_text = parts[0], parts[1], parts[2]
                assign_norm, assign_raw, student = parse_subject_details(subject_text)
                
                entries.append({
                    'id': entry_id,
                    'status': status,
                    'assignment': assign_norm,
                    'assignment_raw': assign_raw,
                    'student': student,
                    'date': submission_date
                })

    return entries

# ==========================================
# REPORT GENERATION
# ==========================================

def generate_report(data):
    if not data:
        print("No data found.")
        return

    all_students = sorted(list(set(d['student'] for d in data if d['student'] and d['student'] != "Unknown")))
    submissions_by_student = defaultdict(set)
    
    for d in data:
        submissions_by_student[d['student']].add(d['assignment'])

    print(f"Parsed {len(data)} submissions from {len(all_students)} students.\n")

    # --- 1. MISSING ASSIGNMENTS ---
    print("MISSING ASSIGNMENTS")
    print("="*60)
    print(f"{'Student':<30} | {'Missing'}")
    print("-" * 60)
    
    required_assignments = sorted(DEADLINES.keys())
    
    for student in all_students:
        submitted = submissions_by_student[student]
        # Only check against assignments defined in DEADLINES
        missing = [a for a in required_assignments if a not in submitted]
        
        # Optional: Filter out future deadlines if you don't want to see them as missing yet
        # current_time = datetime.now()
        # missing = [a for a in missing if datetime.strptime(DEADLINES[a], '%Y-%m-%d %H:%M:%S') < current_time]
        
        if missing:
            print(f"{student:<30} | {', '.join(missing)}")

    # --- 2. LATE SUBMISSIONS ---
    print("\n\nLATE SUBMISSIONS (Deadline -> Submitted)")
    print("="*80)
    print(f"{'Student':<25} | {'Assignment':<22} | {'Deadline':<10} | {'Submitted':<10} | {'Delay'}")
    print("-" * 80)

    for d in data:
        assign = d['assignment']
        if assign in DEADLINES:
            deadline_str = DEADLINES[assign]
            deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
            
            if d['date'] > deadline_dt:
                delta = d['date'] - deadline_dt
                days = delta.days
                hours = delta.seconds // 3600
                minutes = (delta.seconds // 60) % 60
                
                delay_str = f"{days}d {hours}h {minutes}m"
                
                # Format dates for cleaner output
                sub_str = d['date'].strftime('%m-%d %H:%M')
                dead_str = deadline_dt.strftime('%m-%d %H:%M')
                
                print(f"{d['student']:<25} | {assign:<22} | {dead_str:<10} | {sub_str:<10} | {delay_str}")

if __name__ == "__main__":
    parsed_data = parse_file_robust(FILE_PATH)
    generate_report(parsed_data)