"""E-Pix passport photo studio.

The original single-photo white-background removal method is intentionally preserved.
Batch processing reuses the same rembg operation without altering that method.
"""
from __future__ import annotations

import os
import sys
import logging
from pathlib import Path

# PyInstaller --windowed applications may start with stdout/stderr set to None.
# Some native/AI dependencies (including ONNX Runtime) write diagnostics there.
# Give them a real stream before importing rembg or initializing inference.
_LOG_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "E-Pix" / "logs"
try:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    _LOG_FILE = (_LOG_DIR / "epix.log").open("a", encoding="utf-8", buffering=1)
except OSError:
    _LOG_FILE = open(os.devnull, "w", encoding="utf-8")
if sys.stdout is None:
    sys.stdout = _LOG_FILE
if sys.stderr is None:
    sys.stderr = _LOG_FILE
logging.basicConfig(filename=str(_LOG_DIR / "epix-errors.log") if _LOG_DIR.exists() else os.devnull,
                    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from PIL import Image, ImageTk, ImageOps

APP_TITLE = "E-Pix Passport Photo Studio"
OUTPUT_SIZE = (413, 531)  # 35 × 45 mm at 300 DPI
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

try:
    from rembg import remove as rembg_remove
except Exception:
    rembg_remove = None


class PassportPhotoStudio:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1020x740")
        self.root.minsize(820, 620)
        self.original: Image.Image | None = None
        self.processed: Image.Image | None = None
        self.current_path: Path | None = None
        self.preview_photo = None
        self.batch_paths: list[Path] = []
        self.batch_queue: list[Path] = []
        self.output_dir = Path.home() / "Pictures" / "E-Pix Output"
        self.batch_apply_white = tk.BooleanVar(value=True)

        outer = ttk.Frame(root, padding=16)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=APP_TITLE, font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Passport / ID photo preparation • 35 × 45 mm • 413 × 531 px • 300 DPI",
                  font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 12))

        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        self.preview = tk.Canvas(body, width=420, height=500, background="#eeeeee", highlightthickness=0)
        self.preview.pack(side="left", fill="both", expand=True)
        panel = ttk.Frame(body, padding=(18, 0, 0, 0), width=330)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)

        ttk.Label(panel, text="Single photo", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Button(panel, text="Open photo…", command=self.open_photo).pack(fill="x", pady=(6, 4))
        ttk.Button(panel, text="Remove background", command=self.remove_background).pack(fill="x", pady=4)
        ttk.Button(panel, text="Crop to 35:45", command=self.crop_photo).pack(fill="x", pady=4)
        ttk.Button(panel, text="Reset to original", command=self.reset_photo).pack(fill="x", pady=4)

        ttk.Separator(panel).pack(fill="x", pady=12)
        ttk.Label(panel, text="Bulk photo processing", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Button(panel, text="Select multiple photos…", command=self.select_batch_files).pack(fill="x", pady=(6, 4))
        ttk.Button(panel, text="Select a photo folder…", command=self.select_batch_folder).pack(fill="x", pady=4)
        self.batch_count = tk.StringVar(value="No bulk photos selected")
        ttk.Label(panel, textvariable=self.batch_count, wraplength=300).pack(anchor="w", pady=(3, 5))
        ttk.Checkbutton(panel, text="Apply existing white-background removal to bulk photos",
                        variable=self.batch_apply_white).pack(anchor="w", pady=4)
        self.output_label = tk.StringVar(value=f"Output: {self.output_dir}")
        ttk.Label(panel, textvariable=self.output_label, wraplength=300).pack(anchor="w", pady=(4, 3))
        ttk.Button(panel, text="Choose output folder…", command=self.choose_output_folder).pack(fill="x", pady=4)
        self.start_button = ttk.Button(panel, text="START BULK PROCESSING", command=self.start_batch)
        self.start_button.pack(fill="x", pady=(7, 4))
        self.progress = ttk.Progressbar(panel, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(5, 3))
        self.progress_label = tk.StringVar(value="0 / 0 completed")
        ttk.Label(panel, textvariable=self.progress_label).pack(anchor="w")

        ttk.Separator(panel).pack(fill="x", pady=12)
        ttk.Label(panel, text="Export current photo", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Button(panel, text="Save as JPG…", command=lambda: self.save_photo("JPEG")).pack(fill="x", pady=(6, 4))
        ttk.Button(panel, text="Save as PNG…", command=lambda: self.save_photo("PNG")).pack(fill="x", pady=4)
        ttk.Label(panel, text="The app preserves the person's real face, expression and clothing. It does not reshape faces or turn a side-facing pose into a front-facing pose. Check official photo rules before submission.",
                  wraplength=300, justify="left").pack(anchor="w", pady=(12, 0))

        self.status = tk.StringVar(value="Open a photo or select multiple photos to begin.")
        ttk.Label(outer, textvariable=self.status, relief="sunken", anchor="w", padding=6).pack(fill="x", pady=(12, 0))
        self.draw_placeholder()

    def draw_placeholder(self) -> None:
        self.preview.delete("all")
        self.preview.create_text(210, 235, text="Open a portrait photo to preview it here",
                                 fill="#555555", font=("Segoe UI", 12), width=300, justify="center")

    def open_photo(self) -> None:
        path = filedialog.askopenfilename(title="Choose a photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff"), ("All files", "*.*")])
        if not path:
            return
        try:
            with Image.open(path) as image:
                self.original = ImageOps.exif_transpose(image).convert("RGB")
            self.processed = self.original.copy()
            self.current_path = Path(path)
            self.show_preview()
            self.status.set(f"Loaded: {self.current_path.name} • {self.original.width} × {self.original.height} px")
        except Exception as exc:
            messagebox.showerror("Could not open photo", str(exc))

    def show_preview(self) -> None:
        if self.processed is None:
            self.draw_placeholder()
            return
        self.preview.delete("all")
        image = self.processed.copy()
        image.thumbnail((380, 460), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(image)
        x = (420 - image.width) // 2
        y = (500 - image.height) // 2
        self.preview.create_image(x, y, image=self.preview_photo, anchor="nw")
        self.preview.create_rectangle(x, y, x + image.width, y + image.height, outline="#aaaaaa")

    # PRESERVED: original single-photo white-background-making method.
    def remove_background(self) -> None:
        if self.processed is None:
            messagebox.showinfo("Open a photo first", "Choose a photo before removing its background.")
            return
        if rembg_remove is None:
            if messagebox.askyesno("Optional feature", "Background removal needs the optional 'rembg' package. Try installing it now?\n\nThis may take time and download model files."):
                messagebox.showinfo("Install rembg", "Open a terminal in the project folder and run:\n\npython -m pip install rembg\n\nThen restart the app.")
            return
        try:
            rgba = self.processed.convert("RGBA")
            result = rembg_remove(rgba).convert("RGBA")
            background = Image.new("RGBA", result.size, "white")
            background.alpha_composite(result)
            self.processed = background.convert("RGB")
            self.show_preview()
            self.status.set("Background replaced with white.")
        except Exception as exc:
            logging.exception("Single-photo background removal failed")
            messagebox.showerror("Background removal failed", f"{type(exc).__name__}: {exc}\n\nA diagnostic log was saved in the E-Pix logs folder.")

    def crop_photo(self) -> None:
        if self.processed is None:
            messagebox.showinfo("Open a photo first", "Choose a photo before cropping.")
            return
        try:
            self.processed = ImageOps.fit(self.processed, OUTPUT_SIZE, method=Image.Resampling.LANCZOS,
                                          centering=(0.5, 0.5))
            self.show_preview()
            self.status.set("Prepared 35:45 crop. Check head position before exporting.")
        except Exception as exc:
            messagebox.showerror("Crop failed", str(exc))

    def reset_photo(self) -> None:
        if self.original is None:
            return
        self.processed = self.original.copy()
        self.show_preview()
        self.status.set("Reset to original photo.")

    def choose_output_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choose separate output folder", initialdir=str(self.output_dir))
        if folder:
            self.output_dir = Path(folder)
            self.output_label.set(f"Output: {self.output_dir}")

    def select_batch_files(self) -> None:
        paths = filedialog.askopenfilenames(title="Select multiple photos",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff")])
        if paths:
            self.batch_paths = [Path(p) for p in paths]
            self.batch_count.set(f"{len(self.batch_paths)} photo(s) selected")

    def select_batch_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select folder containing photos")
        if not folder:
            return
        self.batch_paths = sorted(p for p in Path(folder).iterdir()
                                  if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS)
        self.batch_count.set(f"{len(self.batch_paths)} photo(s) found in folder")

    def start_batch(self) -> None:
        if not self.batch_paths:
            messagebox.showinfo("No photos selected", "Select multiple photos or choose a folder first.")
            return
        if self.batch_apply_white.get() and rembg_remove is None:
            messagebox.showerror("Background removal unavailable",
                "The existing rembg background-removal dependency is not available. Install the project requirements, then restart E-Pix.")
            return
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            messagebox.showerror("Output folder error", str(exc))
            return
        self.batch_queue = list(self.batch_paths)
        self.batch_done = 0
        self.batch_ok = 0
        self.batch_skipped = 0
        self.batch_failed: list[str] = []
        self.progress.configure(maximum=len(self.batch_queue), value=0)
        self.progress_label.set(f"0 / {len(self.batch_queue)} completed")
        self.start_button.configure(state="disabled")
        self.status.set("Bulk processing started…")
        self._process_next_batch_item()

    def _process_next_batch_item(self) -> None:
        if not self.batch_queue:
            self.start_button.configure(state="normal")
            summary = (f"Bulk processing finished. Saved: {self.batch_ok}; "
                       f"skipped (name already exists): {self.batch_skipped}; failed: {len(self.batch_failed)}.")
            self.status.set(summary)
            details = summary
            if self.batch_failed:
                details += "\n\nErrors:\n" + "\n".join(self.batch_failed[:20])
            messagebox.showinfo("Bulk processing complete", details)
            return

        source = self.batch_queue.pop(0)
        self.batch_done += 1
        destination = self.output_dir / source.name
        try:
            if destination.exists():
                self.batch_skipped += 1
            else:
                with Image.open(source) as image:
                    working = ImageOps.exif_transpose(image).convert("RGB")
                if self.batch_apply_white.get():
                    rgba = working.convert("RGBA")
                    cutout = rembg_remove(rgba).convert("RGBA")
                    white = Image.new("RGBA", cutout.size, "white")
                    white.alpha_composite(cutout)
                    working = white.convert("RGB")
                output = ImageOps.fit(working, OUTPUT_SIZE, method=Image.Resampling.LANCZOS,
                                      centering=(0.5, 0.5))
                suffix = source.suffix.lower()
                fmt = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP",
                       ".bmp": "BMP", ".tif": "TIFF", ".tiff": "TIFF"}[suffix]
                save_options = {"dpi": (300, 300)}
                if fmt == "JPEG":
                    save_options.update({"quality": 95, "optimize": True})
                output.save(destination, format=fmt, **save_options)
                self.batch_ok += 1
        except Exception as exc:
            logging.exception("Bulk processing failed for %s", source)
            self.batch_failed.append(f"{source.name}: {type(exc).__name__}: {exc}")
        self.progress.configure(value=self.batch_done)
        self.progress_label.set(f"{self.batch_done} / {self.batch_done + len(self.batch_queue)} completed")
        self.status.set(f"Processing {source.name}…")
        self.root.after(10, self._process_next_batch_item)

    def save_photo(self, format_name: str) -> None:
        if self.processed is None:
            messagebox.showinfo("Open a photo first", "Choose a photo before exporting.")
            return
        ext = ".jpg" if format_name == "JPEG" else ".png"
        initial = (self.current_path.stem if self.current_path else "passport_photo") + ext
        path = filedialog.asksaveasfilename(title="Save passport photo", defaultextension=ext,
            initialfile=initial, filetypes=[(f"{format_name} image", f"*{ext}")],
            initialdir=str(self.output_dir))
        if not path:
            return
        destination = Path(path)
        if self.current_path is not None and destination.resolve() == self.current_path.resolve():
            messagebox.showerror("Protecting original photo", "The output path cannot be the original source photo. Choose the separate output folder.")
            return
        if destination.exists():
            messagebox.showwarning("File already exists", "This output already exists. Choose another filename or folder; E-Pix will not overwrite files.")
            return
        try:
            output = ImageOps.fit(self.processed, OUTPUT_SIZE, method=Image.Resampling.LANCZOS,
                                  centering=(0.5, 0.5))
            if format_name == "JPEG":
                output.save(path, format="JPEG", quality=95, dpi=(300, 300), optimize=True)
            else:
                output.save(path, format="PNG", dpi=(300, 300), optimize=True)
            self.status.set(f"Saved: {path} • {OUTPUT_SIZE[0]} × {OUTPUT_SIZE[1]} px")
            messagebox.showinfo("Export complete", f"Saved passport-style photo to:\n{path}\n\nOutput: {OUTPUT_SIZE[0]} × {OUTPUT_SIZE[1]} px at 300 DPI. Please verify official requirements.")
        except Exception as exc:
            messagebox.showerror("Could not save photo", str(exc))


def main() -> None:
    root = tk.Tk()
    PassportPhotoStudio(root)
    root.mainloop()


if __name__ == "__main__":
    main()
