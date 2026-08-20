# Force-recreate TLE_SWEVO_PDFs_only.zip in D:\新论文\
$ErrorActionPreference = 'Stop'

$SUB = 'D:\新论文\论文\_submission'
$OUT = 'D:\新论文\TLE_SWEVO_PDFs_only.zip'

# Delete existing
if (Test-Path $OUT) {
    Remove-Item $OUT -Force
    Write-Host "Deleted old: $OUT"
}

# Recreate
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::Open($OUT, 'Create')

$files = @(
    'main_submission.pdf',
    'cover_letter.pdf',
    'supplementary_material.pdf',
    'EM_UPLOAD_GUIDE.md',
    'ai_audit.txt'
)

foreach ($f in $files) {
    $src = Join-Path $SUB $f
    if (Test-Path $src) {
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $zip, $src, $f, 'Optimal') | Out-Null
        Write-Host "Added: $f"
    } else {
        Write-Host "MISSING: $f"
    }
}
$zip.Dispose()

$f = Get-Item $OUT
"--- Result ---"
"Path: $($f.FullName)"
"Size: $($f.Length) bytes ($([math]::Round($f.Length/1MB, 3)) MB)"
"LastWriteTime: $($f.LastWriteTime)"
