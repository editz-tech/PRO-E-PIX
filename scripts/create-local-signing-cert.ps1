# Creates a personal-use E-Pix Authenticode certificate for the current Windows user.
# The private key stays non-exportable in Cert:\CurrentUser\My. Only the public .cer is exported.
[CmdletBinding()]
param(
    [switch]$TrustForThisUser
)
$ErrorActionPreference = "Stop"
$subject = "CN=E-Pix Personal Code Signing"
$store = "Cert:\CurrentUser\My"
$dir = Join-Path $env:LOCALAPPDATA "E-Pix\signing"
$publicCert = Join-Path $dir "E-Pix-Personal-CodeSigning.cer"

if (-not $env:LOCALAPPDATA) { throw "LOCALAPPDATA is unavailable. Run this script in your normal Windows user session." }
New-Item -ItemType Directory -Path $dir -Force | Out-Null

$existing = Get-ChildItem $store | Where-Object {
    $_.Subject -eq $subject -and $_.HasPrivateKey -and $_.NotAfter -gt (Get-Date)
} | Sort-Object NotAfter -Descending | Select-Object -First 1

if ($existing) {
    $cert = $existing
    Write-Host "Reusing existing valid E-Pix signing certificate."
} else {
    $cert = New-SelfSignedCertificate `
        -Subject $subject `
        -Type CodeSigningCert `
        -CertStoreLocation $store `
        -KeyAlgorithm RSA `
        -KeyLength 3072 `
        -HashAlgorithm SHA256 `
        -KeyExportPolicy NonExportable `
        -NotAfter (Get-Date).AddYears(3)
    Write-Host "Created a new 3-year RSA code-signing certificate."
}

Export-Certificate -Cert $cert -FilePath $publicCert -Force | Out-Null
Write-Host ""
Write-Host "Certificate thumbprint: $($cert.Thumbprint)"
Write-Host "Public certificate: $publicCert"
Write-Host "Private key: remains in CurrentUser\My and is marked non-exportable."

if ($TrustForThisUser) {
    # Trust only this exact self-signed certificate for this Windows user.
    # This does NOT make it a Microsoft-trusted CA or satisfy Smart App Control.
    Import-Certificate -FilePath $publicCert -CertStoreLocation "Cert:\CurrentUser\Root" | Out-Null
    Import-Certificate -FilePath $publicCert -CertStoreLocation "Cert:\CurrentUser\TrustedPublisher" | Out-Null
    Write-Warning "This trusts this certificate for this Windows user only. Smart App Control may still block the app."
} else {
    Write-Host "Optional local trust: rerun with -TrustForThisUser if you want Windows Authenticode trust for this exact certificate."
}
