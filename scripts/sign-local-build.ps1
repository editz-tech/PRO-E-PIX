# Signs and verifies a locally built E-Pix executable using the current user's certificate.
# No PFX/private key is stored in the repository or passed to GitHub Actions.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$ExePath = (Join-Path $PSScriptRoot "..\dist\E-Pix.exe"),
    [Parameter(Mandatory=$false)]
    [string]$Thumbprint
)
$ErrorActionPreference = "Stop"
$ExePath = (Resolve-Path -LiteralPath $ExePath).Path
if ([IO.Path]::GetExtension($ExePath) -ne ".exe") { throw "The target must be an .exe file." }

if (-not $Thumbprint) { $Thumbprint = $env:EPIX_SIGNING_CERT_THUMBPRINT }
$certs = Get-ChildItem "Cert:\CurrentUser\My" | Where-Object {
    $_.Subject -eq "CN=E-Pix Personal Code Signing" -and $_.HasPrivateKey -and $_.NotAfter -gt (Get-Date)
}
if ($Thumbprint) {
    $cert = $certs | Where-Object { $_.Thumbprint -eq ($Thumbprint -replace '\s','') } | Select-Object -First 1
} else {
    $cert = $certs | Sort-Object NotAfter -Descending | Select-Object -First 1
}
if (-not $cert) { throw "No matching E-Pix certificate with a private key was found. Run create-local-signing-cert.ps1 first." }

$signtool = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe" -ErrorAction SilentlyContinue |
    Sort-Object { [version]$_.Directory.Parent.Name } -Descending | Select-Object -First 1
if (-not $signtool) { throw "SignTool was not found. Install the Windows 10/11 SDK, then run this script again." }

Write-Host "Signing: $ExePath"
& $signtool.FullName sign /sha1 $cert.Thumbprint /s My /fd SHA256 /v $ExePath
if ($LASTEXITCODE -ne 0) { throw "SignTool failed to sign E-Pix (exit code $LASTEXITCODE)." }

Write-Host "Verifying signature..."
& $signtool.FullName verify /pa /v $ExePath
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Signature verification did not complete as trusted. If you have not installed this exact certificate for this user, run create-local-signing-cert.ps1 -TrustForThisUser. This still cannot override Smart App Control."
    throw "SignTool verification failed (exit code $LASTEXITCODE)."
}
Write-Host "E-Pix signature verified. This is a local self-signed publisher identity, not a public CA signature."
