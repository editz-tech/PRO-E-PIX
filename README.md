# AI Passport Photo Studio

A Windows desktop starter app for preparing passport-style photos.

## Features

- Open a photo and preview it.
- Crop to a 35:45 portrait ratio.
- Export a 413 × 531 pixel JPEG or PNG at 300 DPI.
- Optional background removal using `rembg` (install separately; model download may be required).

> Important: This is a starter utility, not a guarantee of compliance with every country's passport-photo rules. Check the destination authority's requirements. The crop is centered and does not automatically detect head position.

## Requirements

- Python 3.10 or newer recommended
- Pillow
- Optional: `rembg` for background removal

## Run on Windows

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

To enable background removal, install the optional dependency:

```powershell
pip install rembg
```

Depending on the environment, `rembg` may need additional runtime/model downloads.

## Build a Windows executable

```powershell
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name AI-Passport-Photo-Studio app.py
```

The executable will be placed in `dist/`.

## Current limitations

- Background removal is optional and may not be installed.
- Crop uses the image center; head/eye alignment is not automatically detected.
- Output dimensions are a useful print size, not a promise that all agencies accept the photo.

## License

MIT (see `LICENSE`).
