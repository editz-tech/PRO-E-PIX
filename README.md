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

## Free local self-signing (personal PC only)

The GitHub Actions build remains unsigned. For personal use, you can sign the downloaded `E-Pix.exe` on your own Windows PC with a free self-signed certificate:

1. Download and extract the `E-Pix-Personal-Windows-Unsigned` artifact from a successful Actions run.
2. On your Windows PC, install the Windows 10/11 SDK if SignTool is not already installed.
3. Open PowerShell in the repository folder and run:

   ```powershell
   .\scripts\create-local-signing-cert.ps1
   ```

   This creates an RSA-3072/SHA-256 code-signing certificate in your **Current User** certificate store. Its private key is marked non-exportable and is not written to the repository. Only the public certificate is exported under `%LOCALAPPDATA%\E-Pix\signing\`.
4. Optional: if you want Windows Authenticode to trust this exact certificate for your Windows user, run:

   ```powershell
   .\scripts\create-local-signing-cert.ps1 -TrustForThisUser
   ```

   This adds only the public certificate to your current-user Root and TrustedPublisher stores. Do not install certificates received from other people.
5. Copy the downloaded `E-Pix.exe` into the repository's `dist` folder (or pass its full path), then sign and verify it:

   ```powershell
   .\scripts\sign-local-build.ps1 -ExePath "C:\path\to\E-Pix.exe"
   ```

   The script signs with SHA-256 and verifies the signature. Re-sign every new build after downloading it.

**Important:** This self-signed identity is trusted only on your own configured Windows user account. It is not issued by a public certificate authority, does not establish a publicly verified publisher identity, and does not make E-Pix trusted on another PC. It **does not satisfy Smart App Control's trusted-CA requirement** and cannot bypass Smart App Control. Keep Smart App Control enabled; do not weaken Windows security to run the app. If Smart App Control blocks E-Pix, a local self-signed certificate will not solve that block.

Never upload the private key, export a PFX, commit certificate files containing private keys, or add signing secrets to GitHub Actions. The hosted build intentionally remains unsigned; signing happens only on your own PC.

## Current limitations

- Crop uses the image center; head/eye alignment is not automatically detected.
- The app does not reshape faces or change clothing.
- Output dimensions do not guarantee acceptance by every passport or ID authority.
- The existing white-background-removal method is retained; it may not remove shadows that fall on the person.

## License

MIT (see `LICENSE`).
