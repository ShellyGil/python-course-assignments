import tkinter as tk
from tkinter import filedialog, messagebox
import string

def browse_file():
    """Opens a file dialog for the user to select a text file."""
    filename = filedialog.askopenfilename(
        title="Select a Text File",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
    )
    if filename:
        file_path_var.set(filename)
        status_label.config(text="File loaded successfully", fg="green")

def count_word():
    """Reads the file and counts occurrences of the specified word."""
    file_path = file_path_var.get()
    target_word = word_entry.get().strip()

    if not file_path:
        messagebox.showwarning("Warning", "Please select a text file first.")
        return

    if not target_word:
        messagebox.showwarning("Warning", "Please enter a word to search for.")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Normalize content and target word to lowercase for case-insensitive matching
            # Remove punctuation to ensure accurate word matching (e.g., "word." matches "word")
            translator = str.maketrans('', '', string.punctuation)
            content_clean = content.translate(translator).lower()
            target_clean = target_word.translate(translator).lower()
            
            # Split into list to avoid partial matches (e.g. counting "cat" inside "catapult")
            words = content_clean.split()
            count = words.count(target_clean)

            result_label.config(text=f"The word '{target_word}' appears {count} times.", fg="blue")
            status_label.config(text="Count complete.", fg="black")

    except FileNotFoundError:
        messagebox.showerror("Error", "The selected file was not found.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

# --- GUI Setup ---
root = tk.Tk()
root.title("Word Occurrence Counter")
root.geometry("450x300")
root.resizable(False, False)

# Store file path
file_path_var = tk.StringVar()

# 1. Section: Select File
frame_file = tk.Frame(root, pady=10)
frame_file.pack(fill="x", padx=20)

btn_browse = tk.Button(frame_file, text="1. Select Text File", command=browse_file, width=20)
btn_browse.pack(anchor="w")

lbl_file_display = tk.Label(frame_file, textvariable=file_path_var, fg="gray", wraplength=400, justify="left")
lbl_file_display.pack(anchor="w", pady=5)

# 2. Section: Enter Word
frame_word = tk.Frame(root, pady=10)
frame_word.pack(fill="x", padx=20)

lbl_instruction = tk.Label(frame_word, text="2. Enter word to count:")
lbl_instruction.pack(anchor="w")

word_entry = tk.Entry(frame_word, font=("Arial", 12))
word_entry.pack(fill="x", pady=5)

# 3. Section: Count Button & Result
frame_action = tk.Frame(root, pady=20)
frame_action.pack(fill="x", padx=20)

btn_count = tk.Button(frame_action, text="Count Occurrences", command=count_word, bg="#dddddd", font=("Arial", 10, "bold"))
btn_count.pack(fill="x")

result_label = tk.Label(root, text="", font=("Arial", 14, "bold"), pady=10)
result_label.pack()

status_label = tk.Label(root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_label.pack(side=tk.BOTTOM, fill=tk.X)

# Start the application
root.mainloop()