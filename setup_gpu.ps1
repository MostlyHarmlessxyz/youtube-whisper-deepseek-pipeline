$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

New-Item -ItemType Directory -Force -Path tools, models | Out-Null

if (-not (Get-Command deno -ErrorAction SilentlyContinue)) {
    scoop install deno
}

$zip = "tools\whisper.cpp-windows-vulkan.zip"
$toolDir = "tools\whisper.cpp-vulkan"
if (-not (Test-Path "$toolDir\whisper-cli.exe")) {
    Invoke-WebRequest `
        -Uri "https://github.com/jerryshell/whisper.cpp-windows-vulkan-bin/releases/download/v1.0.0/whisper.cpp-windows-vulkan.zip" `
        -OutFile $zip
    Expand-Archive -LiteralPath $zip -DestinationPath $toolDir -Force
}

$model = "models\ggml-large-v3-turbo-q5_0.bin"
if (-not (Test-Path $model) -or ((Get-Item $model).Length -ne 574041195)) {
    curl.exe -L -C - --retry 10 --retry-delay 3 `
        -o $model `
        "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin"
}

vulkaninfo --summary
.\tools\whisper.cpp-vulkan\whisper-cli.exe -h | Select-String -Pattern "Vulkan|device"

