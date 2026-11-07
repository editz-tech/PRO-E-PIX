"""E-Pix — local passport-photo preparation for Windows.

The app never writes to source files. It preserves each input basename and extension
in a separate output folder; existing output files are skipped, never overwritten.
"""
from __future__ import annotations

import json
import os
import sys
import shutil
import queue
import threading
import time
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

from PIL import Image, ImageOps, ImageTk

APP_TITLE = "E-Pix"
OUTPUT_SIZE = (413, 531)  # 35:45 mm at 300 DPI
SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
WHITE = (255, 255, 255)

os.environ.setdefault("U2NET_HOME", str(Path.home() / ".u2net"))
LOCAL_MODEL = Path(os.environ["U2NET_HOME"]) / "u2net.onnx"
BUNDLED_MODEL = (Path(getattr(sys, "_MEIPASS")) / "models" / "u2net.onnx"
                 if getattr(sys, "frozen", False) else None)

try:
    from rembg import remove as rembg_remove, new_session
except Exception:
    rembg_remove = None
    new_session = None


def settings_path() -> Path:
    base = Path.home() / "AppData" / "Roaming" / "E-Pix"
    base.mkdir(parents=True, exist_ok=True)
    return base / "settings.json"


def load_settings() -> dict:
    try:
        return json.loads(settings_path().read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_settings(data: dict) -> None:
    path = settings_path()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_images(folder: Path) -> list[Path]:
    return sorted(
        (p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED),
        key=lambda p: p.name.casefold(),
    )


def make_passport_image(source: Path, session=None) -> Image.Image:
    """Remove the background, composite on white, center-crop, and resize.

    No face reshaping, skin retouching, clothing recoloring, or pose synthesis is
    performed. The user must review head placement and official photo compliance.
    """
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGBA")

    if rembg_remove is None:
        raise RuntimeError("Background-removal engine is unavailable. Reinstall E-Pix.")

    # rembg runs locally and is configured to require a pre-provisioned model file.
    cutout = rembg_remove(image, session=session).convert("RGBA")
    white = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    white.alpha_composite(cutout)
    flattened = white.convert("RGB")

    # Center crop to 35:45. This is deliberately not a face/pose transformation.
    width, height = flattened.size
    target_ratio = 35 / 45
    if width / height > target_ratio:
        crop_width = max(1, int(height * target_ratio))
        left = (width - crop_width) // 2
        flattened = flattened.crop((left, 0, left + crop_width, height))
    else:
        crop_height = max(1, int(width / target_ratio))
        top = (height - crop_height) // 2
        flattened = flattened.crop((0, top, width, top + crop_height))

    return ImageOps.fit(
        flattened,
        OUTPUT_SIZE,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def save_same_name(image: Image.Image, destination: Path) -> None:
    """Create the output exclusively: never replace an existing file."""
    suffix = destination.suffix.lower()
    with destination.open("xb") as stream:
        if suffix in {".jpg", ".jpeg"}:
            image.save(stream, format="JPEG", quality=95, optimize=True, dpi=(300, 300))
        elif suffix == ".png":
            image.save(stream, format="PNG", optimize=True, dpi=(300, 300))
        elif suffix == ".webp":
            image.save(stream, format="WEBP", quality=95, method=6)
        elif suffix == ".bmp":
            image.save(stream, format="BMP", dpi=(300, 300))
        elif suffix in {".tif", ".tiff"}:
            image.save(stream, format="TIFF", dpi=(300, 300), compression="tiff_deflate")
        else:
            raise ValueError(f"Unsupported output format: {suffix}")


class EPixApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1040x720")
        self.root.minsize(850, 620)
        self.root.configure(bg="#101827")

        self.settings = load_settings()
        self.selected_files: list[Path] = []
        self.output_dir = tk.StringVar(value=self.settings.get("output_dir", ""))
        self.keep_default = tk.BooleanVar(value=bool(self.settings.get("set_default", False)))
        self.status_text = tk.StringVar(value="Choose one photo, multiple photos, or a folder to begin.")
        self.progress_text = tk.StringVar(value="Ready")
        self.preview_ref = None
        self.events: queue.Queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.running = False
        self.failed_files: list[Path] = []

        self._build_ui()
        self.root.after(120, self._poll_events)

    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        style.configure("TCheckbutton", background="#172235", foreground="#e8eef8")
        style.configure("Horizontal.TProgressbar", troughcolor="#26354c", background="#3185f5")

        header = tk.Frame(self.root, bg="#101827")
        header.pack(fill="x", padx=22, pady=(18, 12))
        tk.Label(header, text="E-Pix", font=("Segoe UI", 25, "bold"),
                 fg="#f4f7fb", bg="#101827").pack(anchor="w")
        tk.Label(header, text="Passport & ID Photo Studio  •  35 × 45 mm  •  300 DPI",
                 font=("Segoe UI", 10), fg="#a9bad1", bg="#101827").pack(anchor="w", pady=(2, 0))

        body = tk.Frame(self.root, bg="#101827")
        body.pack(fill="both", expand=True, padx=22, pady=8)
        self.preview = tk.Canvas(body, bg="#e9edf2", highlightthickness=0, width=520, height=520)
        self.preview.pack(side="left", fill="both", expand=True)

        panel = tk.Frame(body, bg="#172235", width=340)
        panel.pack(side="right", fill="y", padx=(16, 0))
        panel.pack_propagate(False)
        tk.Label(panel, text="PHOTO INPUT", bg="#172235", fg="#e8eef8",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=18, pady=(18, 8))

        self._button(panel, "Select Single / Multiple Photos", self.choose_files)
        self._button(panel, "Select Photo Folder", self.choose_folder)
        self.input_label = tk.Label(panel, text="No photos selected", bg="#172235",
                                    fg="#a9bad1", wraplength=290, justify="left")
        self.input_label.pack(anchor="w", padx=18, pady=(4, 12))

        tk.Frame(panel, height=1, bg="#30415a").pack(fill="x", padx=18, pady=8)
        tk.Label(panel, text="OUTPUT FOLDER", bg="#172235", fg="#e8eef8",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=18, pady=(4, 8))
        self._button(panel, "Choose Output Folder", self.choose_output)
        self.output_label = tk.Label(panel, textvariable=self.output_dir, bg="#172235",
                                     fg="#a9bad1", wraplength=290, justify="left")
        self.output_label.pack(anchor="w", padx=18, pady=(2, 4))
        ttk.Checkbutton(panel, text="Set as Default Output Folder",
                        variable=self.keep_default, command=self.persist_settings).pack(
                            anchor="w", padx=16, pady=(4, 12))

        tk.Frame(panel, height=1, bg="#30415a").pack(fill="x", padx=18, pady=8)
        tk.Label(panel, text="PROCESSING", bg="#172235", fg="#e8eef8",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=18, pady=(4, 8))
        self._button(panel, "START", self.start, primary=True)
        self._button(panel, "Cancel", self.cancel)
        self._button(panel, "Retry Failed Photos", self.retry_failed)
        self._button(panel, "Clear", self.clear)

        tk.Label(panel, text="Preserves original filenames and never changes source files. "
                 "Existing output names are skipped to prevent overwriting.",
                 bg="#172235", fg="#a9bad1", wraplength=290, justify="left",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(12, 8))

        footer = tk.Frame(self.root, bg="#101827")
        footer.pack(fill="x", padx=22, pady=(8, 18))
        self.progress = ttk.Progressbar(footer, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(0, 6))
        tk.Label(footer, textvariable=self.progress_text, bg="#101827",
                 fg="#dce6f3", anchor="w").pack(fill="x")
        tk.Label(footer, textvariable=self.status_text, bg="#101827",
                 fg="#8fa4bf", anchor="w").pack(fill="x", pady=(4, 0))
        self._placeholder()

    def _button(self, parent, label, command, primary=False):
        bg = "#2478e8" if primary else "#263750"
        fg = "#ffffff"
        tk.Button(parent, text=label, command=command, bg=bg, fg=fg,
                  activebackground="#398cf5", activeforeground="#ffffff",
                  relief="flat", bd=0, font=("Segoe UI", 10, "bold" if primary else "normal"),
                  cursor="hand2", pady=9).pack(fill="x", padx=18, pady=4)

    def _placeholder(self):
        self.preview.delete("all")
        self.preview.create_text(260, 250, text="Select a portrait photo to preview",
                                 fill="#596579", font=("Segoe UI", 14))

    def choose_files(self):
        paths = filedialog.askopenfilenames(
            title="Select one or more photos",
            filetypes=[("Supported photos", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff")],
        )
        if paths:
            self.selected_files = [Path(p) for p in paths]
            self._update_selection()
            self._show_source_preview(self.selected_files[0])

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Select a folder containing photos")
        if folder:
            self.selected_files = list_images(Path(folder))
            self._update_selection()
            if self.selected_files:
                self._show_source_preview(self.selected_files[0])
            else:
                messagebox.showinfo(APP_TITLE, "No supported image files were found in that folder.")

    def _update_selection(self):
        count = len(self.selected_files)
        self.input_label.config(text=f"{count} photo(s) selected" if count else "No photos selected")
        self.status_text.set(f"{count} photo(s) ready.")

    def _show_source_preview(self, path: Path):
        try:
            with Image.open(path) as opened:
                image = ImageOps.exif_transpose(opened).convert("RGB")
            image.thumbnail((500, 500), Image.Resampling.LANCZOS)
            self.preview_ref = ImageTk.PhotoImage(image)
            self.preview.delete("all")
            self.preview.create_image(260, 260, image=self.preview_ref, anchor="center")
        except Exception as exc:
            self.status_text.set(f"Preview unavailable: {exc}")

    def choose_output(self):
        folder = filedialog.askdirectory(title="Choose a separate output folder")
        if folder:
            self.output_dir.set(folder)
            self.persist_settings()

    def persist_settings(self):
        if self.keep_default.get():
            save_settings({"output_dir": self.output_dir.get(), "set_default": True})
        else:
            save_settings({"output_dir": self.output_dir.get(), "set_default": False})

    def start(self):
        if self.running:
            return
        if not self.selected_files:
            messagebox.showinfo(APP_TITLE, "Select one or more photos, or choose a folder first.")
            return
        if not self.output_dir.get().strip():
            messagebox.showinfo(APP_TITLE, "Choose a separate output folder first.")
            return
        output = Path(self.output_dir.get())
        try:
            output.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Cannot create output folder:\n{exc}")
            return
        if rembg_remove is None:
            messagebox.showerror(APP_TITLE, "The local background-removal engine is not installed.")
            return
        self.persist_settings()
        self.cancel_event.clear()
        self.running = True
        self.progress.configure(value=0, maximum=len(self.selected_files))
        self.progress_text.set(f"0 / {len(self.selected_files)}")
        self.status_text.set("Processing locally. Keep the app open.")
        self.worker = threading.Thread(target=self._process_batch,
                                       args=(list(self.selected_files), output),
                                       daemon=True)
        self.worker.start()

    def _process_batch(self, files: list[Path], output: Path):
        failed: list[Path] = []
        skipped = 0
        started = time.monotonic()
        session = None
        saved = 0
        try:
            if new_session is not None:
                if not LOCAL_MODEL.is_file() and BUNDLED_MODEL and BUNDLED_MODEL.is_file():
                    LOCAL_MODEL.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(BUNDLED_MODEL, LOCAL_MODEL)
                if not LOCAL_MODEL.is_file():
                    raise RuntimeError(
                        "Offline AI model is missing. Reinstall E-Pix or place u2net.onnx in "
                        f"{LOCAL_MODEL}. E-Pix will not download models automatically."
                    )
                session = new_session("u2net", model_path=str(LOCAL_MODEL))
            for index, source in enumerate(files, 1):
                if self.cancel_event.is_set():
                    break
                destination = output / source.name
                try:
                    if destination.exists():
                        skipped += 1
                        self.events.put(("progress", index, len(files), source.name, started))
                        continue
                    result = make_passport_image(source, session=session)
                    # Exclusive create prevents overwriting a file created during processing.
                    if destination.exists():
                        skipped += 1
                    else:
                        try:
                            save_same_name(result, destination)
                            saved += 1
                        except FileExistsError:
                            skipped += 1
                except Exception:
                    failed.append(source)
                    self.events.put(("error", source.name, traceback.format_exc(limit=2)))
                self.events.put(("progress", index, len(files), source.name, started))
        except Exception:
            self.events.put(("fatal", traceback.format_exc(limit=4)))
        finally:
            self.events.put(("complete", saved, len(files), len(failed), skipped,
                             [str(p) for p in failed], self.cancel_event.is_set()))

    def _poll_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "progress":
                    _, done, total, filename, started = event
                    elapsed = max(0.01, time.monotonic() - started)
                    rate = done / elapsed
                    remaining = max(0, int((total - done) / rate)) if rate else 0
                    self.progress.configure(value=done, maximum=total)
                    self.progress_text.set(
                        f"{done} / {total}  •  {filename}  •  estimated remaining: {remaining}s"
                    )
                elif kind == "error":
                    self.status_text.set(f"Failed: {event[1]}")
                elif kind == "fatal":
                    messagebox.showerror(APP_TITLE, event[1])
                elif kind == "complete":
                    _, saved, total, failed, skipped, failed_paths, cancelled = event
                    self.running = False
                    self.failed_files = [Path(p) for p in failed_paths]
                    completed = saved
                    state = "Cancelled" if cancelled else "Finished"
                    self.status_text.set(
                        f"{state}: {completed} saved, {skipped} skipped (already existed), {failed} failed."
                    )
                    self.progress_text.set(self.status_text.get())
                    if failed:
                        messagebox.showwarning(APP_TITLE,
                            f"{completed} saved\n{skipped} skipped to avoid overwriting\n{failed} failed.\n"
                            "Use 'Retry Failed Photos' after checking the output folder.")
                    elif not cancelled:
                        messagebox.showinfo(APP_TITLE,
                            f"Processing complete.\n{completed} photo(s) saved.\n"
                            f"{skipped} existing output file(s) skipped.\n\n"
                            "Review head position, expression, and the official authority's rules.")
        except queue.Empty:
            pass
        self.root.after(120, self._poll_events)

    def cancel(self):
        if self.running:
            self.cancel_event.set()
            self.status_text.set("Cancellation requested…")

    def retry_failed(self):
        if self.running:
            return
        failed = getattr(self, "failed_files", [])
        if not failed:
            messagebox.showinfo(APP_TITLE, "There are no failed photos to retry.")
            return
        self.selected_files = failed
        self._update_selection()
        self.start()

    def clear(self):
        if self.running:
            messagebox.showwarning(APP_TITLE, "Cancel processing before clearing the selection.")
            return
        self.selected_files = []
        self.input_label.config(text="No photos selected")
        self.progress.configure(value=0)
        self.progress_text.set("Ready")
        self.status_text.set("Selection cleared.")
        self._placeholder()


def main():
    root = tk.Tk()
    EPixApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
