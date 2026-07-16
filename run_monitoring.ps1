# run_monitoring.ps1
# Automates the setup of Prometheus and Grafana on Windows using standalone binaries.

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$workspaceRoot = $PSScriptRoot
if (-not $workspaceRoot) {
    $workspaceRoot = Get-Location
}

$monitoringDir = Join-Path $workspaceRoot ".monitoring"
if (-not (Test-Path $monitoringDir)) {
    New-Item -ItemType Directory -Path $monitoringDir | Out-Null
}

$prometheusUrl = "https://github.com/prometheus/prometheus/releases/download/v2.53.1/prometheus-2.53.1.windows-amd64.zip"
$prometheusZip = Join-Path $monitoringDir "prometheus.zip"
$prometheusExtractedDirName = "prometheus-2.53.1.windows-amd64"
$prometheusHome = Join-Path $monitoringDir $prometheusExtractedDirName

$grafanaUrl = "https://dl.grafana.com/oss/release/grafana-10.4.2.windows-amd64.zip"
$grafanaZip = Join-Path $monitoringDir "grafana.zip"
$grafanaExtractedDirName = "grafana-v10.4.2"
$grafanaHome = Join-Path $monitoringDir $grafanaExtractedDirName

# Helper function to download with curl or Invoke-WebRequest
function Download-File {
    param (
        [string]$url,
        [string]$outputPath
    )
    if (Test-Path $outputPath) {
        Write-Host "File already exists: $outputPath"
        return
    }
    Write-Host "Downloading $url to $outputPath..."
    
    # Try using curl.exe first because it is faster and doesn't load whole file in memory
    $curlPath = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($curlPath) {
        Write-Host "Using curl.exe for download..."
        & curl.exe -L -o $outputPath $url
    } else {
        Write-Host "Using Invoke-WebRequest for download..."
        Invoke-WebRequest -Uri $url -OutFile $outputPath
    }
}

# Helper function to stop existing processes
function Stop-ExistingProcesses {
    Write-Host "Stopping any running instances of prometheus or grafana..."
    Get-Process -Name "prometheus" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "grafana-server" -ErrorAction SilentlyContinue | Stop-Process -Force
}

# 1. Stop existing instances
Stop-ExistingProcesses

# 2. Download Prometheus
Download-File -url $prometheusUrl -outputPath $prometheusZip

# 3. Download Grafana
Download-File -url $grafanaUrl -outputPath $grafanaZip

# 4. Extract Prometheus
if (-not (Test-Path $prometheusHome)) {
    Write-Host "Extracting Prometheus zip..."
    Expand-Archive -Path $prometheusZip -DestinationPath $monitoringDir
} else {
    Write-Host "Prometheus is already extracted."
}

# 5. Extract Grafana
if (-not (Test-Path $grafanaHome)) {
    Write-Host "Extracting Grafana zip..."
    Expand-Archive -Path $grafanaZip -DestinationPath $monitoringDir
} else {
    Write-Host "Grafana is already extracted."
}

# 6. Configure Grafana Provisioning
Write-Host "Configuring Grafana autoprovisioning..."
$grafanaProvisioningDatasources = Join-Path $grafanaHome "conf\provisioning\datasources"
$grafanaProvisioningDashboards = Join-Path $grafanaHome "conf\provisioning\dashboards"

if (-not (Test-Path $grafanaProvisioningDatasources)) {
    New-Item -ItemType Directory -Path $grafanaProvisioningDatasources -Force | Out-Null
}
if (-not (Test-Path $grafanaProvisioningDashboards)) {
    New-Item -ItemType Directory -Path $grafanaProvisioningDashboards -Force | Out-Null
}

# Copy Datasource provisioning config
$localDatasourceConf = Join-Path $workspaceRoot "grafana\provisioning\datasources\prometheus.yml"
Copy-Item -Path $localDatasourceConf -Destination $grafanaProvisioningDatasources -Force

# Copy Dashboard provisioning config (Windows-specific version with correct path)
$localDashboardConf = Join-Path $workspaceRoot "grafana\provisioning\dashboards\jobseeker_windows.yml"
Copy-Item -Path $localDashboardConf -Destination (Join-Path $grafanaProvisioningDashboards "jobseeker.yml") -Force

# 7. Start Prometheus
Write-Host "Starting Prometheus in background..."
$prometheusExe = Join-Path $prometheusHome "prometheus.exe"
$prometheusConfig = Join-Path $workspaceRoot "prometheus.yml"
$promProcess = Start-Process -FilePath $prometheusExe -ArgumentList "--config.file=$prometheusConfig" -WorkingDirectory $prometheusHome -WindowStyle Hidden -PassThru

# 8. Start Grafana
Write-Host "Starting Grafana in background..."
$grafanaExe = Join-Path $grafanaHome "bin\grafana-server.exe"
$grafanaWorkingDir = Join-Path $grafanaHome "bin"
$grafanaProcess = Start-Process -FilePath $grafanaExe -WorkingDirectory $grafanaWorkingDir -WindowStyle Hidden -PassThru

# 9. Wait and verify
Write-Host "Waiting for services to initialize..."
Start-Sleep -Seconds 5

$promRunning = Get-Process -Name "prometheus" -ErrorAction SilentlyContinue
$grafanaRunning = Get-Process -Name "grafana-server" -ErrorAction SilentlyContinue

if ($promRunning -and $grafanaRunning) {
    Write-Host "`n==================================================" -ForegroundColor Green
    Write-Host "SUCCESS: Prometheus and Grafana are running!" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "Prometheus URL       : http://localhost:9090"
    Write-Host "Grafana URL          : http://localhost:3000"
    Write-Host "Default Grafana User : admin"
    Write-Host "Default Grafana Pass : admin"
    Write-Host "FastAPI Metrics URL  : http://127.0.0.1:8000/metrics"
    Write-Host "=================================================="
} else {
    Write-Host "`nWARNING: Some services might not have started successfully." -ForegroundColor Yellow
    if (-not $promRunning) { Write-Host "Prometheus is NOT running." -ForegroundColor Red }
    if (-not $grafanaRunning) { Write-Host "Grafana is NOT running." -ForegroundColor Red }
}
