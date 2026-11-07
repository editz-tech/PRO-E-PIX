# E-Pix — Passport & ID Photo Studio

Windows desktop application for preparing single or batches of passport-style photos.

## Current features

- Select one photo, select multiple photos, or select a folder of photos.
- Local background removal with a bundled U2Net ONNX model in the Windows release.
- Composite the cutout on a white background.
- Center-crop to a 35:45 portrait ratio and export at 413 × 531 pixels with 300 DPI metadata.
- Preserve the exact original filename and extension in a separate output folder.
- Never modify source photos.
- Never overwrite an existing output file: name collisions are skipped and reported.
- Batch progress, estimated remaining time, cancellation, failed-file reporting, and retry.
- Optional "Set as Default Output Folder" preference.

## Photo integrity and compliance

E-Pix does not apply beauty filters, reshape faces, synthesize a pose, or recolor clothing. Background removal and resizing can affect edge pixels, so inspect clothing and hair edges in every output. The current crop is centered; it does not automatically align the eyes or detect whether the face is straight-on, looking at the camera, or neutral. Review those requirements manually before submitting a photo.

The white background is produced by compositing the subject cutout over white. Segmentation can occasionally retain shadows or remove fine hair/clothing edges; the software cannot guarantee rejection-proof results. Inspect the area around the ears, neck, hair, and shoulders.

The 413 × 531 pixel export is a 35:45 approximation at 300 DPI. Authorities may require different framing, dimensions, or other conditions. Confirm the current UAE Emirates ID/passport rules with the relevant authority.

## Run from source on Windows

1. Install Python 3.11 (64-bit).
2. Install dependencies: `python -m pip install -r requirements.txt`.
3. Obtain the official `u2net.onnx` model and place it at `%USERPROFILE%\.u2net\u2net.onnx`.
4. Run `python app.py`.

The source application does not download AI models automatically. The GitHub Actions Windows build downloads the official rembg U2Net model, verifies its MD5 checksum, and bundles it in the installer so image processing runs locally after installation without a model download.

## Build the Windows installer

The GitHub Actions workflow `.github/workflows/windows-installer.yml` builds a Windows 10/11 x64 application folder with PyInstaller, packages it with Inno Setup, and uploads `E-Pix-Setup.exe` as the `E-Pix-Windows-Installer` workflow artifact.

To start a build, open the repository's **Actions** tab, choose **Build E-Pix Windows installer**, and select **Run workflow**. The installer is available only after the workflow succeeds and the artifact is uploaded.

## Performance

Processing speed depends on source resolution, CPU, and image complexity. No fixed throughput (including 50 photos per minute) is guaranteed; benchmark with representative photos on the target PC.

## License

See `LICENSE` for the application license. The bundled U2Net model has its own upstream terms; review them before commercial distribution.
