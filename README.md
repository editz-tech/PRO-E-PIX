# E-Pix Passport Photo Studio

A Windows desktop starter app for preparing passport-style photos.

## Features

- Open a photo and preview it.
- Crop to a 35:45 portrait ratio.
- Export a 413 × 531 pixel JPEG or PNG at 300 DPI.
- Optional white-background removal using `rembg`.
- Select multiple photos or process a folder in bulk.
- Preserve input filenames and skip existing output files rather than overwrite them.

## Requirements

- Windows 10/11
- Python 3.11 for local development
- Pillow
- `rembg[cpu]` (background removal and bulk white-background processing)

## Run on Windows

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## Build a Windows executable

```powershell
pip install pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --name E-Pix --collect-all rembg --collect-all onnxruntime --collect-all pooch --collect-all pymatting app.py
```

The executable will be placed in `dist/E-Pix.exe`.

## Personal-use Windows build (unsigned)

This project is intended for the owner's personal use. The GitHub Actions workflow builds an **unsigned** `E-Pix.exe`; it requires no publisher contract, code-signing certificate, Microsoft Artifact Signing account, or signing secrets.

The executable is available as the GitHub Actions artifact named `E-Pix-Personal-Windows-Unsigned` after a successful workflow run.

### Windows Smart App Control

An unsigned executable may be blocked by Windows 11 Smart App Control. Microsoft does not provide a per-app allow-list or bypass for Smart App Control. Its cloud reputation service may allow some apps, but an unsigned app with no established reputation can be blocked.

Do not install a certificate from an unknown source or disable Windows security just to run an unverified file. Only run a build you have obtained from this repository and trust. If Smart App Control blocks it, keep the protection enabled unless you have independently decided to change that Windows security setting after reviewing Microsoft's current guidance. This repository does not attempt to bypass Windows security.

No publisher identity or digital signature is claimed for this personal-use build.

## Current limitations

- Crop uses the image center; head/eye alignment is not automatically detected.
- The app does not reshape faces or change clothing.
- Output dimensions do not guarantee acceptance by every passport or ID authority.
- The existing white-background-removal method is retained; it may not remove shadows that fall on the person.

## License

MIT (see `LICENSE`).
