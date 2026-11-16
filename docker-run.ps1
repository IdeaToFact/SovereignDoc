# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only
<#
.SYNOPSIS
    SovereignDoc Community Edition: Docker Launch Helper Script (Windows PowerShell)
.DESCRIPTION
    Builds, pulls, and launches the air-gapped SovereignDoc All-in-One Workstation container.
.PARAMETER Port
    Host port to expose. Defaults to 8000.
.PARAMETER DataDir
    Host directory for persistent document and vector storage. Defaults to named volume 'sovereigndoc_data'.
.PARAMETER OllamaUrl
    Endpoint for host's Ollama instance. Defaults to 'http://host.docker.internal:11434'.
.PARAMETER Detach
    Run the container in the background (detached mode) and open the browser. Defaults to true.
.PARAMETER NoBrowser
    Do not automatically open the browser when launched.
.PARAMETER BuildOnly
    Build the Docker image from local Dockerfile without starting the container.
.PARAMETER Rebuild
    Force rebuild of the Docker image before running.
.EXAMPLE
    .\docker-run.ps1
.EXAMPLE
    .\docker-run.ps1 -Port 8080 -NoBrowser
.EXAMPLE
    .\docker-run.ps1 -Rebuild
#>

[CmdletBinding()]
param (
    [Parameter(Position = 0)]
    [int]$Port = 8000,

    [string]$DataDir = "",

    [string]$OllamaUrl = "http://host.docker.internal:11434",

    [Alias("d")]
    [switch]$Detach = $true,

    [switch]$NoBrowser,

    [switch]$BuildOnly,

    [switch]$Rebuild
)

$ErrorActionPreference = "Stop"
$ImageName = "airgapaxis/sovereigndoc:1.1.0-community"
$LocalFallbackImage = "airgapaxis/sovereigndoc:latest"

# 1. Verify Docker CLI and Daemon Availability
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker is not installed or not available in PATH." -ForegroundColor Red
    Write-Host "Please install Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

$ErrorActionPreference = "Continue"
$null = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker daemon is not running." -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}
$ErrorActionPreference = "Stop"

# 2. Configure Volume Mount Path
if ($DataDir -and (Test-Path $DataDir)) {
    $DataAbs = (Resolve-Path $DataDir).Path -replace '\\', '/'
    $VolumeMount = "${DataAbs}:/root/.sovereigndoc"
    $StorageDisplay = $DataAbs
} else {
    $VolumeMount = "sovereigndoc_data:/root/.sovereigndoc"
    $StorageDisplay = "Docker Named Volume (sovereigndoc_data)"
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  SovereignDoc Community Edition (v1.1.0-community)" -ForegroundColor Green
Write-Host "  Platform:  AirGap Axis Zero-Telemetry AI Document Workstation" -ForegroundColor DarkGray
Write-Host "  Image:     $ImageName" -ForegroundColor White
Write-Host "  Storage:   $StorageDisplay" -ForegroundColor White
Write-Host "  Workstation: http://localhost:$Port" -ForegroundColor White
Write-Host "  API Docs:    http://localhost:$Port/docs" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# 3. Check Docker Image (Use local if present, try pull, or build)
$imageExists = (docker images -q $ImageName 2>$null) -or (docker images -q $LocalFallbackImage 2>$null)
if ($Rebuild -or -not $imageExists) {
    if (-not $Rebuild) {
        Write-Host "[PULL] Checking Docker Hub for '$ImageName'..." -ForegroundColor DarkGray
        $ErrorActionPreference = "Continue"
        $null = docker pull $ImageName 2>&1
        $pullSuccess = ($LASTEXITCODE -eq 0)
        $ErrorActionPreference = "Stop"
        if ($pullSuccess) {
            $imageExists = $true
        }
    }
    if ($Rebuild -or -not $imageExists) {
        Write-Host "[BUILD] Building Docker image '$ImageName' from local source..." -ForegroundColor Yellow
        docker build -t $ImageName -t $LocalFallbackImage -f Dockerfile .
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to build Docker image." -ForegroundColor Red
            exit $LASTEXITCODE
        }
        Write-Host "[OK] Image '$ImageName' built successfully.`n" -ForegroundColor Green
    }
}

if ($BuildOnly) {
    Write-Host "[OK] Build complete (-BuildOnly specified). Exiting." -ForegroundColor Green
    exit 0
}

# 4. Remove any stale container instance from previous runs
$ErrorActionPreference = "Continue"
$null = docker rm -f sovereigndoc 2>&1
$ErrorActionPreference = "Stop"

# 5. Run the Container
Write-Host "[START] Launching SovereignDoc container..." -ForegroundColor Green

$dockerArgs = @(
    "run",
    "-d",
    "--name", "sovereigndoc",
    "-p", "127.0.0.1:${Port}:8000",
    "-v", $VolumeMount,
    "-e", "OLLAMA_BASE_URL=$OllamaUrl",
    "-e", "SOVEREIGNDOC_OLLAMA_URL=$OllamaUrl",
    "-e", "SOVEREIGNDOC_HOST=0.0.0.0",
    "-e", "SOVEREIGNDOC_PORT=8000",
    "-e", "ANONYMIZED_TELEMETRY=False",
    "-e", "CHROMA_TELEMETRY_IMPL=none",
    "-e", "DO_NOT_TRACK=1",
    "-e", "HF_HUB_DISABLE_TELEMETRY=1",
    "-e", "HF_HUB_OFFLINE=1",
    "--add-host", "host.docker.internal:host-gateway",
    "--restart", "unless-stopped",
    $ImageName
)

$containerId = & docker $dockerArgs

# 6. Wait for Healthy Status API
Write-Host "[WAIT] Probing workstation readiness..." -ForegroundColor DarkGray
$ready = $false
$targetUrl = "http://localhost:$Port"

for ($i = 0; $i -lt 12; $i++) {
    Start-Sleep -Seconds 1
    try {
        $res = curl.exe -s "http://127.0.0.1:${Port}/api/system/health" 2>$null
        if ($res -and $res -match '"app"\s*:\s*"SovereignDoc"') {
            $ready = $true
            break
        }
    } catch {
        # Keep waiting
    }
}

Write-Host ""
Write-Host "[OK] SovereignDoc Workstation is active!" -ForegroundColor Green
Write-Host "   Container:     sovereigndoc ($containerId)" -ForegroundColor DarkGray
Write-Host "   Workstation:   $targetUrl" -ForegroundColor Green
Write-Host "   Swagger Docs:  ${targetUrl}/docs" -ForegroundColor Cyan
Write-Host "   Stop Command:  docker stop sovereigndoc" -ForegroundColor Yellow
Write-Host "   View Logs:     docker logs -f sovereigndoc`n" -ForegroundColor DarkGray

if (-not $NoBrowser) {
    Write-Host "[OPEN] Launching default browser to $targetUrl ..." -ForegroundColor Cyan
    Start-Process $targetUrl
}
