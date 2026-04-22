param(
    [string]$UrlFile = "url.txt",
    [string]$OutputDir = "videos"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$urls = Get-Content -LiteralPath $UrlFile |
    ForEach-Object { $_.Trim() } |
    Where-Object { $_ -and -not $_.StartsWith("#") }

foreach ($url in $urls) {
    Write-Host "Downloading best video: $url"
    .\.venv\Scripts\python.exe -m yt_dlp `
        --js-runtimes deno `
        --remote-components ejs:github `
        --continue `
        --retries 20 `
        --fragment-retries 20 `
        --socket-timeout 30 `
        --merge-output-format mp4 `
        -f "bv*+ba/b" `
        -o "$OutputDir\%(title).160B [%(id)s].%(ext)s" `
        $url
}
