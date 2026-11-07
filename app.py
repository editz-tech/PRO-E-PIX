"""AI Passport Photo Studio — initial desktop starter.

Uses Pillow and Tkinter. Optional background removal uses rembg.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from PIL import Image, ImageTk, ImageOps, ImageDraw

APP_TITLE = "AI Passport Photo Studio"
OUTPUT_SIZE = (413, 531)  # 35:45 mm at approximately 300 DPI

try:
    from rembg import remove as rembg_remove
except Exception:
    rembg_remove = None


class PassportPhotoStudio:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("900x680")
        self.root.minsize(720, 540)
        self.original: Image.Image | None = None
        self.processed: Image.Image | None = None
        self.current_path: Path | None = None
        self.preview_photo = None

        outer = ttk.Frame(root, padding=16)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=APP_TITLE, font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Prepare a passport-style portrait • 35 × 45 mm export", font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 12))

        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        self.preview = tk.Canvas(body, width=420, height=500, background="#eeeeee", highlightthickness=0)
        self.preview.pack(side="left", fill="both", expand=True)
        panel = ttk.Frame(body, padding=(18, 0, 0, 0), width=230)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)

        ttk.Button(panel, text="Open photo…", command=self.open_photo).pack(fill="x", pady=(0, 8))
        ttk.Button(panel, text="Remove background", command=self.remove_background).pack(fill="x", pady=4)
        ttk.Button(panel, text="Crop to 35:45", command=self.crop_photo).pack(fill="x", pady=4)
        ttk.Button(panel, text="Reset to original", command=self.reset_photo).pack(fill="x", pady=4)
        ttk.Separator(panel).pack(fill="x", pady=14)
        ttk.Label(panel, text="Export", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Button(panel, text="Save as JPG…", command=lambda: self.save_photo("JPEG")).pack(fill="x", pady=(8, 4))
        ttk.Button(panel, text="Save as PNG…", command=lambda: self.save_photo("PNG")).pack(fill="x", pady=4)
        ttk.Separator(panel).pack(fill="x", pady=14)
        ttk.Label(panel, text="Notes", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        notes = "• Center crop only; no face alignment yet.\n\n• Background removal requires optional rembg installation and may download a model.\n\n• Check your destination country's official photo rules."
        ttk.Label(panel, text=notes, wraplength=205, justify="left").pack(anchor="w", pady=(6, 0))
        self.status = tk.StringVar(value="Open a photo to begin.")
        ttk.Label(outer, textvariable=self.status, relief="sunken", anchor="w", padding=6).pack(fill="x", pady=(12, 0))
        self.draw_placeholder()

    def draw_placeholder(self) -> None:
        self.preview.delete("all")
        self.preview.create_text(210, 235, text="Open a portrait photo to preview it here", fill="#555555", font=("Segoe UI", 12), width=300, justify="center")

    def open_photo(self) -> None:
        path = filedialog.askopenfilename(title="Choose a photo", filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff"), ("All files", "*.*")])
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
            messagebox.showerror("Background removal failed", str(exc))

    def crop_photo(self) -> None:
        if self.processed is None:
            messagebox.showinfo("Open a photo first", "Choose a photo before cropping.")
            return
        try:
            width, height = self.processed.size
            target_ratio = 35 / 45
            if width / height > target_ratio:
                new_width = int(height * target_ratio)
                left = (width - new_width) // 2
                box = (left, 0, left + new_width, height)
            else:
                new_height = int(width / target_ratio)
                top = (height - new_height) // 2
                box = (0, top, width, top + new_height)
            self.processed = self.processed.crop(box)
            self.show_preview()
            self.status.set("Cropped to 35:45 ratio. Check head position before exporting.")
        except Exception as exc:
            messagebox.showerror("Crop failed", str(exc))

    def reset_photo(self) -> None:
        if self.original is None:
            return
        self.processed = self.original.copy()
        self.show_preview()
        self.status.set("Reset to original photo.")

    def save_photo(self, format_name: str) -> None:
        if self.processed is None:
            messagebox.showinfo("Open a photo first", "Choose a photo before exporting.")
            return
        ext = ".jpg" if format_name == "JPEG" else ".png"
        initial = (self.current_path.stem if self.current_path else "passport_photo") + "_35x45" + ext
        path = filedialog.asksaveasfilename(title="Save passport photo", defaultextension=ext, initialfile=initial, filetypes=[(f"{format_name} image", f"*{ext}")])
        if not path:
            return
        try:
            output = ImageOps.fit(self.processed, OUTPUT_SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
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
