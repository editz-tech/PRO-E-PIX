# E-Pix — Portable Passport & ID Photo Studio

E-Pix is being developed as a portable Windows 10/11 x64 desktop application. **There is no installer in this project stage.** When the portable build is ready, extract the ZIP and launch `E-Pix.exe` from the extracted `E-Pix` folder. Keep the accompanying application files and folders together; do not move the EXE out on its own.

## Current features

- Select one photo, select multiple photos, or select a folder of photos.
- Local background removal with a bundled U2Net ONNX model in the portable Windows package.
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

## Portable Windows build

The GitHub Actions workflow `.github/workflows/windows-installer.yml` (workflow display name: **Build E-Pix portable Windows app**) builds a self-contained PyInstaller application folder and packages it as `E-Pix-Portable-Windows.zip`. The ZIP contains `E-Pix.exe`, its runtime files, the bundled local AI model, and this README.

To create a build, open the repository's **Actions** tab, select **Build E-Pix portable Windows app**, and choose **Run workflow**. The ZIP is available as the `E-Pix-Portable-Windows` artifact only after the workflow succeeds and uploads it.

No setup wizard or installer is produced at this stage. Installer creation will be done only when requested later.

## Performance

Processing speed depends on source resolution, CPU, and image complexity. No fixed throughput (including 50 photos per minute) is guaranteed; benchmark with representative photos on the target PC.

## License

See `LICENSE` for the application license. The bundled U2Net model has its own upstream terms; review them before commercial distribution.
