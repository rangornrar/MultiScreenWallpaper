# Construit le paquet MSIX de WallCraft Pro pour le Microsoft Store.
#
#   cd python
#   $env:WALLCRAFT_ONEDIR = "1"; pyinstaller --noconfirm WallCraft.spec
#   .\msix\build_msix.ps1 -Version 2026.11.13
#
# Le paquet produit n'est pas signé : le Microsoft Store le signe lui-même à la publication.
# Pour l'installer sur un PC sans passer par le Store, il faut le signer (-SignWithTestCert).
param(
    [Parameter(Mandatory = $true)][string]$Version,          # 2026.11.13 -> 2026.11.13.0
    [string]$IdentityName = "WallCraftPro.Dev",               # Partner Center : Package/Identity/Name
    [string]$Publisher = "CN=WallCraftDev",                   # Partner Center : Package/Identity/Publisher
    [string]$PublisherDisplayName = "rangornrar",             # Partner Center : Package/Properties/PublisherDisplayName
    [string]$Dist = "dist/WallCraft",
    [string]$OutDir = "dist",
    [switch]$SignWithTestCert
)
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot

# Version MSIX : quatre nombres, le dernier à 0 (exigence du Store).
$parts = $Version.Split(".")
while ($parts.Count -lt 3) { $parts += "0" }
$msixVersion = ($parts[0..2] -join ".") + ".0"

# Outils du Windows SDK (présents sur les runners windows-latest).
$sdkBin = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin\10.*" -Directory |
    Where-Object { Test-Path "$($_.FullName)\x64\makeappx.exe" } |
    Sort-Object { [version]$_.Name } -Descending | Select-Object -First 1
if (-not $sdkBin) { throw "Windows SDK introuvable (makeappx.exe)." }
$makeappx = "$($sdkBin.FullName)\x64\makeappx.exe"
$makepri = "$($sdkBin.FullName)\x64\makepri.exe"
$signtool = "$($sdkBin.FullName)\x64\signtool.exe"

$layout = Join-Path $OutDir "msix-layout"
if (Test-Path $layout) { Remove-Item $layout -Recurse -Force }
New-Item -ItemType Directory $layout | Out-Null
Copy-Item "$Dist\*" $layout -Recurse
Copy-Item "$here\Assets" "$layout\Assets" -Recurse

$manifest = Get-Content "$here\AppxManifest.xml" -Raw -Encoding UTF8
$manifest = $manifest.Replace('$IDENTITY_NAME$', $IdentityName).Replace('$PUBLISHER$', $Publisher)
$manifest = $manifest.Replace('$PUBLISHER_DISPLAY_NAME$', $PublisherDisplayName).Replace('$VERSION$', $msixVersion)
[IO.File]::WriteAllText("$layout\AppxManifest.xml", $manifest, (New-Object Text.UTF8Encoding $false))

# resources.pri : seulement pour les icônes (tailles et échelles), pas pour les fichiers de Python.
$pri = Join-Path $OutDir "msix-pri"
if (Test-Path $pri) { Remove-Item $pri -Recurse -Force }
New-Item -ItemType Directory $pri | Out-Null
Copy-Item "$here\Assets" "$pri\Assets" -Recurse
Copy-Item "$layout\AppxManifest.xml" $pri
& $makepri createconfig /cf "$pri\priconfig.xml" /dq en-US /pv 10.0.0 /o
if ($LASTEXITCODE) { throw "makepri createconfig a échoué." }
& $makepri new /pr $pri /cf "$pri\priconfig.xml" /mn "$pri\AppxManifest.xml" /of "$layout\resources.pri" /o
if ($LASTEXITCODE) { throw "makepri new a échoué." }

$msix = Join-Path $OutDir "WallCraft-Pro-v$Version-Store.msix"
& $makeappx pack /d $layout /p $msix /o
if ($LASTEXITCODE) { throw "makeappx pack a échoué." }

if ($SignWithTestCert) {
    # Certificat de test au nom de l'éditeur du manifeste, pour installer le paquet hors Store.
    $cert = New-SelfSignedCertificate -Type Custom -Subject $Publisher -KeyUsage DigitalSignature `
        -FriendlyName "WallCraft MSIX test" -CertStoreLocation "Cert:\CurrentUser\My" `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
    & $signtool sign /fd SHA256 /sha1 $cert.Thumbprint /s My $msix
    if ($LASTEXITCODE) { throw "signtool a échoué." }
    $cer = Join-Path $OutDir "WallCraft-test.cer"
    Export-Certificate -Cert $cert -FilePath $cer | Out-Null
    Write-Host "Certificat de test : $cer"
}

Write-Host "Paquet : $msix (version $msixVersion)"
if ($env:GITHUB_OUTPUT) { "msix=$msix" | Out-File -Append -Encoding utf8 $env:GITHUB_OUTPUT }
