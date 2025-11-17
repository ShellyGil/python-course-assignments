from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from day04.imdb_client import IMDB_TOP_250_URL, IMDbDownloadError, download_and_store


class IMDbDownloaderGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("IMDb Downloader (Day 04)")
        self.resizable(False, False)

        # Default values
        self.url_var = tk.StringVar(value=IMDB_TOP_250_URL)
        self.html_var = tk.StringVar(value=str(Path("day04/data/imdb_top_250.html")))
        self.parse_var = tk.BooleanVar(value=True)
        self.json_var = tk.StringVar(value=str(Path("day04/data/imdb_top_250.json")))
        self.limit_var = tk.StringVar(value="")
        self.creds_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Idle")

        self._build_layout()

    def _build_layout(self) -> None:
        pad = {"padx": 8, "pady": 4}

        # URL
        tk.Label(self, text="IMDb URL:").grid(row=0, column=0, sticky="e", **pad)
        tk.Entry(self, width=50, textvariable=self.url_var).grid(row=0, column=1, columnspan=2, sticky="w", **pad)

        # HTML output
        tk.Label(self, text="HTML output:").grid(row=1, column=0, sticky="e", **pad)
        tk.Entry(self, width=42, textvariable=self.html_var).grid(row=1, column=1, sticky="w", **pad)
        tk.Button(self, text="Browse", command=self._choose_html).grid(row=1, column=2, sticky="w", **pad)

        # Parse toggle + JSON output
        tk.Checkbutton(self, text="Parse to JSON", variable=self.parse_var, command=self._toggle_parse).grid(
            row=2, column=1, sticky="w", **pad
        )
        tk.Entry(self, width=42, textvariable=self.json_var).grid(row=3, column=1, sticky="w", **pad)
        tk.Button(self, text="Browse", command=self._choose_json).grid(row=3, column=2, sticky="w", **pad)
        tk.Label(self, text="JSON output:").grid(row=3, column=0, sticky="e", **pad)

        # Limit
        tk.Label(self, text="Limit (1-250, optional):").grid(row=4, column=0, sticky="e", **pad)
        tk.Entry(self, width=10, textvariable=self.limit_var).grid(row=4, column=1, sticky="w", **pad)

        # Credentials
        tk.Label(self, text="Credentials JSON:").grid(row=5, column=0, sticky="e", **pad)
        tk.Entry(self, width=42, textvariable=self.creds_var).grid(row=5, column=1, sticky="w", **pad)
        tk.Button(self, text="Browse", command=self._choose_creds).grid(row=5, column=2, sticky="w", **pad)

        # Status + actions
        tk.Label(self, textvariable=self.status_var, fg="blue").grid(row=6, column=0, columnspan=3, sticky="w", **pad)
        self.download_btn = tk.Button(self, text="Download", command=self._start_download, width=20)
        self.download_btn.grid(row=7, column=0, columnspan=3, pady=(4, 10))

        self._toggle_parse()

    def _choose_html(self) -> None:
        chosen = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML files", "*.html"), ("All", "*.*")])
        if chosen:
            self.html_var.set(chosen)

    def _choose_json(self) -> None:
        chosen = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All", "*.*")])
        if chosen:
            self.json_var.set(chosen)

    def _choose_creds(self) -> None:
        chosen = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All", "*.*")])
        if chosen:
            self.creds_var.set(chosen)

    def _toggle_parse(self) -> None:
        state = "normal" if self.parse_var.get() else "disabled"
        for child in self.grid_slaves(row=3, column=1) + self.grid_slaves(row=3, column=2):
            child.configure(state=state)

    def _start_download(self) -> None:
        try:
            html_path = Path(self.html_var.get()).expanduser()
            parsed_path = Path(self.json_var.get()).expanduser() if self.parse_var.get() else None
            credentials_path = Path(self.creds_var.get()).expanduser() if self.creds_var.get().strip() else None
            limit_str = self.limit_var.get().strip()
            limit = int(limit_str) if limit_str else None
            if limit is not None and not (1 <= limit <= 250):
                raise ValueError("Limit must be between 1 and 250.")
        except Exception as exc:  # pragma: no cover - GUI validation
            messagebox.showerror("Invalid input", str(exc))
            return

        self.status_var.set("Downloading...")
        self.download_btn.configure(state="disabled")

        thread = threading.Thread(
            target=self._run_download,
            args=(html_path, parsed_path, credentials_path, limit),
            daemon=True,
        )
        thread.start()

    def _run_download(self, html_path: Path, parsed_path: Path | None, credentials_path: Path | None, limit: int | None) -> None:
        try:
            summary = download_and_store(
                html_path=html_path,
                parsed_path=parsed_path,
                limit=limit,
                credentials_path=credentials_path,
            )
            self.after(
                0,
                lambda: self._on_success(summary),
            )
        except IMDbDownloadError as exc:
            self.after(0, lambda: self._on_error(f"Download failed: {exc}"))
        except Exception as exc:  # pragma: no cover - GUI fallback
            self.after(0, lambda: self._on_error(f"Unexpected error: {exc}"))

    def _on_success(self, summary: dict) -> None:
        self.status_var.set("Done.")
        self.download_btn.configure(state="normal")
        parsed_msg = (
            f"\nParsed {summary['parsed_count']} titles to:\n{summary['parsed_file']}"
            if summary.get("parsed_file")
            else "\nParsing skipped."
        )
        messagebox.showinfo(
            "IMDb Downloader",
            f"HTML saved to:\n{summary['html_file']}{parsed_msg}",
        )

    def _on_error(self, msg: str) -> None:
        self.status_var.set("Error.")
        self.download_btn.configure(state="normal")
        messagebox.showerror("IMDb Downloader", msg)


def main() -> None:
    app = IMDbDownloaderGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
