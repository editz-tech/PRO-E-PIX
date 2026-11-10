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

## Microsoft Artifact Signing (formerly Trusted Signing)

The GitHub Actions workflow can sign the Windows executable and verify its Authenticode signature before publishing the artifact. Signing is performed only when all six secrets below are configured. Pull-request builds do not receive signing credentials.

Add these repository secrets under **Settings → Secrets and variables → Actions**:

| Secret | Value |
|---|---|
| `AZURE_TENANT_ID` | Microsoft Entra tenant/directory ID |
| `AZURE_CLIENT_ID` | Application/service-principal client ID |
| `AZURE_CLIENT_SECRET` | Client secret for that application |
| `AZURE_TRUSTED_SIGNING_ENDPOINT` | Artifact Signing endpoint for the account's supported region |
| `AZURE_CODE_SIGNING_NAME` | Artifact Signing account name |
| `AZURE_CERT_PROFILE_NAME` | Verified certificate profile name |

The Entra application must be authorized for the Artifact Signing account and have the **Trusted Signing Certificate Profile Signer** role. Keep credentials in GitHub Actions secrets; never commit them to the repository.

Microsoft's current documentation says Artifact Signing is available to organizations in the United States, Canada, the European Union, and the United Kingdom, while individual developers are currently limited to the United States and Canada. An individual publisher based in the UAE therefore cannot currently rely on Microsoft Artifact Signing eligibility. Check the current rules before purchasing or configuring the service.

For a UAE-based individual publisher, the alternative is to obtain a publicly trusted Authenticode code-signing certificate from a CA that explicitly accepts UAE-based individual applicants. Ask the CA to confirm identity eligibility, supported key storage/signing method, and Windows Authenticode compatibility before paying. The workflow in this repository currently automates Microsoft Artifact Signing only; it does not yet integrate a third-party CA's remote signing service. Do not put a private key or certificate password in source code.

A valid digital signature confirms publisher identity and file integrity. It does not guarantee that Smart App Control or SmartScreen will immediately allow a new app; reputation and Microsoft's security assessment can still affect warnings.

## Current limitations

- Crop uses the image center; head/eye alignment is not automatically detected.
- The app does not reshape faces or change clothing.
- Output dimensions do not guarantee acceptance by every passport or ID authority.
- The existing white-background-removal method is retained; it may not remove shadows that fall on the person.

## License

MIT (see `LICENSE`).
