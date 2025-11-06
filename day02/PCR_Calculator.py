#!/usr/bin/env python3
import argparse, sys, os

PER_SAMPLE_TOTAL = 11.0
PRIMER_PER = 0.5
DEFAULT_EXCESS = 10.0

def round_to_half(x: float) -> float:
    return round(x * 2) / 2.0

def per_sample_volumes(mix_x: int):
    if mix_x not in (2, 5):
        raise ValueError("mix_x must be 2 or 5")
    mix_vol = 6.0 * (2.0 / mix_x)       # preserves same final composition as 6 µL of 2X in 11 µL
    ddw_vol = PER_SAMPLE_TOTAL - (mix_vol + 2 * PRIMER_PER)
    if ddw_vol < 0:
        raise ValueError("Computed DDW volume is negative; check inputs.")
    return {
        "DDW (µL)": ddw_vol,
        f"Mix {mix_x}X (µL)": mix_vol,
        "Primer F (µL)": PRIMER_PER,
        "Primer R (µL)": PRIMER_PER,
    }

def compute_totals(n_samples: int, excess_percent: float, mix_x: int):
    per = per_sample_volumes(mix_x)
    factor = 1.0 + (excess_percent / 100.0)
    totals = {k: round_to_half(v * n_samples * factor) for k, v in per.items()}
    total_master_mix = round_to_half(sum(totals.values()))
    return per, totals, total_master_mix

# ---------- Markdown output ----------
def render_markdown(n_samples, excess, mix_x, per, totals, total_master_mix) -> str:
    lines = []
    lines.append(f"# PCR Genotyping Mix Calculator")
    lines.append("")
    lines.append(f"**Samples:** {n_samples}  **Excess:** {excess:.1f}%  **Mix:** {mix_x}X")
    lines.append("")
    lines.append(f"Per-sample total volume: **{PER_SAMPLE_TOTAL:.1f} µL**")
    lines.append("")
    lines.append("## Per-sample recipe")
    lines.append("| Component | Volume (µL) |")
    lines.append("|-----------|-------------:|")
    for k, v in per.items():
        lines.append(f"| {k} | {v:.1f} |")
    lines.append("")
    lines.append("## Totals to prepare (rounded to 0.5 µL)")
    lines.append("| Component | Total (µL) |")
    lines.append("|-----------|------------:|")
    for k in per.keys():
        lines.append(f"| {k} | {totals[k]:.1f} |")
    lines.append("")
    lines.append(f"**Total master mix:** `{total_master_mix:.1f} µL`")
    return "\n".join(lines)

# ---------- CLI helpers ----------
def try_int_positive(x, name="value"):
    try:
        xv = int(x)
        if xv < 1:
            raise ValueError
        return xv
    except Exception:
        print(f"Error: {name} must be a positive integer.", file=sys.stderr); sys.exit(2)

def try_nonneg_float(x, name="value"):
    try:
        xv = float(x)
        if xv < 0:
            raise ValueError
        return xv
    except Exception:
        print(f"Error: {name} must be a non-negative number.", file=sys.stderr); sys.exit(2)

def run_cli(samples: int, excess: float, mix_x: int):
    per, totals, total_master_mix = compute_totals(samples, excess, mix_x)
    print(render_markdown(samples, excess, mix_x, per, totals, total_master_mix))

def interactive_prompt(excess_default: float, mix_default: int):
    raw = input("Enter number of PCR samples: ").strip()
    n = try_int_positive(raw, "samples")
    raw_ex = input(f"Excess % (ENTER for {excess_default}%): ").strip()
    ex = excess_default if raw_ex == "" else try_nonneg_float(raw_ex, "excess")
    raw_mx = input(f"Mix concentration (2 or 5) [ENTER for {mix_default}]: ").strip()
    mx = mix_default if raw_mx == "" else try_int_positive(raw_mx, "mix")
    if mx not in (2, 5):
        print("Error: mix must be 2 or 5.", file=sys.stderr); sys.exit(2)
    run_cli(n, ex, mx)

def main():
    parser = argparse.ArgumentParser(description="PCR genotyping calculator with Markdown output and GUI preview.")
    parser.add_argument("--samples","-n", type=int, help="Number of PCR samples.")
    parser.add_argument("--excess","-e", type=float, default=DEFAULT_EXCESS, help=f"Excess %% (default {DEFAULT_EXCESS}).")
    parser.add_argument("--mix","-m", type=int, choices=[2,5], default=2, help="Mix concentration (2 or 5). Default 2.")
    parser.add_argument("--no-gui", action="store_true", help="Run in terminal (no GUI). If --samples not given, prompts.")
    parser.add_argument("--save-md", type=str, help="Save Markdown to this file and exit (CLI mode).")
    args = parser.parse_args()

    if args.no_gui or args.save_md:
        if args.samples is not None:
            md = render_markdown(
                args.samples, try_nonneg_float(args.excess,"excess"), args.mix,
                *compute_totals(args.samples, args.excess, args.mix)
            )  # compute_totals returns (per, totals, total_master_mix)
        else:
            # prompt flow
            raw = input("Enter number of PCR samples: ").strip()
            n = try_int_positive(raw, "samples")
            ex = try_nonneg_float(str(args.excess), "excess")
            mx = args.mix
            per, totals, total_master_mix = compute_totals(n, ex, mx)
            md = render_markdown(n, ex, mx, per, totals, total_master_mix)
        if args.save_md:
            with open(args.save_md, "w", encoding="utf-8") as f:
                f.write(md + "\n")
        if not args.save_md:
            print(md)
        return

    # ----- GUI -----
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog
        # Optional pretty Markdown preview via tkhtmlview (if installed)
        html_available = True
        try:
            from tkhtmlview import HTMLLabel  # pip install tkhtmlview
        except Exception:
            html_available = False
    except Exception:
        # Fallback to CLI prompt if GUI can't start
        interactive_prompt(DEFAULT_EXCESS, 2)
        return

    root = tk.Tk()
    root.title("PCR Genotyping Calculator (Markdown)")

    frm = ttk.Frame(root, padding=12)
    frm.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)

    # Inputs
    ttk.Label(frm, text="Samples:").grid(row=0, column=0, sticky="w")
    samples_var = tk.IntVar(value=args.samples if args.samples and args.samples>0 else 8)
    spn = ttk.Spinbox(frm, from_=1, to=999, textvariable=samples_var, width=8)
    spn.grid(row=0, column=1, sticky="w", padx=(8,0))

    ttk.Label(frm, text="Excess (%):").grid(row=0, column=2, sticky="w", padx=(16,0))
    excess_var = tk.DoubleVar(value=max(args.excess, 0.0))
    ex_spn = ttk.Spinbox(frm, from_=0.0, to=100.0, increment=0.5, width=8, textvariable=excess_var)
    ex_spn.grid(row=0, column=3, sticky="w", padx=(8,0))

    ttk.Label(frm, text="Mix:").grid(row=0, column=4, sticky="w", padx=(16,0))
    mix_var = tk.StringVar(value=f"{args.mix}X")
    mix_cmb = ttk.Combobox(frm, textvariable=mix_var, state="readonly", width=6, values=["2X","5X"])
    mix_cmb.grid(row=0, column=5, sticky="w", padx=(8,0))

    # Output area
    # If tkhtmlview is available, show a rendered pane; also keep a hidden text copy for copy/save.
    if html_available:
        html_box = HTMLLabel(frm, html="<p><i>Press Calculate…</i></p>", background="white", width=70)
        html_box.grid(row=2, column=0, columnspan=6, sticky="nsew", pady=(10,0))
    else:
        txt = tk.Text(frm, height=16, width=72, wrap="word")
        txt.grid(row=2, column=0, columnspan=6, sticky="nsew", pady=(10,0))
        txt.insert("1.0", "Markdown preview (plain text). Install `tkhtmlview` for formatted view.\n\n")

    frm.rowconfigure(2, weight=1)
    for c in (0,1,2,3,4,5): frm.columnconfigure(c, weight=0)
    frm.columnconfigure(2, weight=1)  # give some stretch

    # Buttons
    btns = ttk.Frame(frm); btns.grid(row=3, column=0, columnspan=6, sticky="e", pady=(8,0))

    md_cache = {"text": ""}  # store latest markdown

    def compute_and_show():
        try:
            n = int(samples_var.get());  ex = float(excess_var.get())
            if n < 1 or ex < 0: raise ValueError
            mx_label = mix_var.get().strip().upper()
            mx = 2 if mx_label.startswith("2") else 5
        except Exception:
            messagebox.showerror("Invalid input", "Check samples (≥1), excess (≥0), and mix (2X/5X)."); return
        per, totals, total_mm = compute_totals(n, ex, mx)
        md = render_markdown(n, ex, mx, per, totals, total_mm)
        md_cache["text"] = md
        if html_available:
            # Simple Markdown→HTML: replace headings/bold/code & tables minimally
            # (tkhtmlview supports basic HTML; we’ll convert a subset)
            html = md.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            # headings
            html = html.replace("\n## ", "\n<h2>").replace("\n# ", "\n<h1>")
            html = html.replace("\n", "\n")  # keep newlines
            # bold **x**
            import re
            html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html)
            # code `x`
            html = re.sub(r"`(.+?)`", r"<code>\1</code>", html)
            # naive tables: convert markdown tables to <pre> blocks for simplicity
            if "|" in html and "---" in html:
                blocks = []
                for block in html.split("\n\n"):
                    if "|" in block and "---" in block:
                        blocks.append("<pre>"+block+"</pre>")
                    else:
                        blocks.append(block)
                html = "\n\n".join(blocks)
            # wrap
            html = html.replace("<h1>", "<h1>").replace("<h2>", "<h2>")
            html_box.set_html(html)
        else:
            txt.delete("1.0","end"); txt.insert("1.0", md)

    def copy_markdown():
        if not md_cache["text"]:
            messagebox.showinfo("Copy", "Nothing to copy yet. Click Calculate first."); return
        root.clipboard_clear(); root.clipboard_append(md_cache["text"])
        messagebox.showinfo("Copied", "Markdown copied to clipboard.")

    def save_markdown():
        if not md_cache["text"]:
            messagebox.showinfo("Save", "Nothing to save yet. Click Calculate first."); return
        fp = filedialog.asksaveasfilename(defaultextension=".md",
                                          filetypes=[("Markdown files","*.md"),("All files","*.*")],
                                          initialfile="pcr_mix.md")
        if not fp: return
        with open(fp,"w",encoding="utf-8") as f: f.write(md_cache["text"]+"\n")
        messagebox.showinfo("Saved", f"Saved Markdown to:\n{fp}")

    ttk.Button(btns, text="Calculate", command=compute_and_show).grid(row=0, column=0, padx=4)
    ttk.Button(btns, text="Copy Markdown", command=copy_markdown).grid(row=0, column=1, padx=4)
    ttk.Button(btns, text="Save .md", command=save_markdown).grid(row=0, column=2, padx=4)
    ttk.Button(btns, text="Quit", command=root.destroy).grid(row=0, column=3, padx=4)

    compute_and_show()
    root.mainloop()

if __name__ == "__main__":
    main()
