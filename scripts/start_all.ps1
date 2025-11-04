$ErrorActionPreference = 'Stop'

# Resolve compose file path relative to this script
$composePath = Join-Path (Split-Path $PSScriptRoot -Parent) 'milvus.docker-compose.yml'

Write-Host "Starting Milvus (docker compose)..."
docker compose -f "$composePath" up -d

# Wait for healthz
Write-Host "Waiting for Milvus health..."
$ok=$false
for ($i=0; $i -lt 60; $i++) {
  try {
    $r = Invoke-WebRequest -Uri http://127.0.0.1:9091/healthz -UseBasicParsing -TimeoutSec 2
    if ($r.StatusCode -eq 200) { $ok=$true; break }
  } catch { Start-Sleep -Seconds 2 }
}
if (-not $ok) { Write-Warning "Milvus health not ready yet, continuing..." }

Write-Host "Running Django migrations and init_milvus..."
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
  .\venv\Scripts\python.exe manage.py migrate --noinput
  .\venv\Scripts\python.exe manage.py init_milvus
  Write-Host "Starting Django server..."
  .\venv\Scripts\python.exe manage.py runserver
} finally {
  Pop-Location
}


