<#
.SYNOPSIS
    MinorityReport - Complete Environment Deployment Script
    
.DESCRIPTION
    This script sets up the complete training environment:
    1. Verifies Python venv with CUDA
    2. Starts Docker and Neo4j
    3. Seeds the database
    4. Trains models with real data
    
.EXAMPLE
    .\deploy_real_environment.ps1
    
.NOTES
    Author: The Oracle Team (feature/gat-model)
    Requires: Docker Desktop, Python 3.11, NVIDIA GPU
#>

param(
    [int]$Citizens = 200,
    [int]$Epochs = 100,
    [switch]$SkipDocker,
    [switch]$SkipSeed,
    [switch]$SkipTraining,
    [switch]$WriteBack
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

# Colors for output
function Write-Header($text) {
    Write-Host "`n$("="*60)" -ForegroundColor Cyan
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host "$("="*60)" -ForegroundColor Cyan
}

function Write-Success($text) {
    Write-Host "[OK] $text" -ForegroundColor Green
}

function Write-Warning($text) {
    Write-Host "[!] $text" -ForegroundColor Yellow
}

function Write-Error($text) {
    Write-Host "[ERROR] $text" -ForegroundColor Red
}

function Write-Info($text) {
    Write-Host "[*] $text" -ForegroundColor White
}

# ============================================================
# STEP 1: Verify Python Environment
# ============================================================
Write-Header "Step 1: Verifying Python Environment"

$VenvPython = ".\venv311\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Python venv not found at $VenvPython"
    Write-Info "Create it with: python -m venv venv311"
    exit 1
}

Write-Success "Python venv found"

# Activate venv
.\venv311\Scripts\Activate.ps1

# Verify CUDA
Write-Info "Checking CUDA availability..."
$cudaCheck = python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')" 2>&1

if ($cudaCheck -match "CUDA: True") {
    Write-Success "CUDA is available"
    $cudaCheck | ForEach-Object { Write-Info $_ }
} else {
    Write-Warning "CUDA not available, will use CPU"
}

# ============================================================
# STEP 2: Start Docker and Neo4j
# ============================================================
if (-not $SkipDocker) {
    Write-Header "Step 2: Starting Docker and Neo4j"
    
    # Check if Docker is running
    $dockerStatus = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker is not running!"
        Write-Info "Please start Docker Desktop and run this script again"
        Write-Info "Or use -SkipDocker flag to skip this step"
        exit 1
    }
    Write-Success "Docker is running"
    
    # Start Neo4j
    Write-Info "Starting Neo4j container..."
    docker-compose up neo4j -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start Neo4j"
        exit 1
    }
    
    Write-Success "Neo4j container started"
    
    # Wait for Neo4j to be ready
    Write-Info "Waiting for Neo4j to initialize (30 seconds)..."
    $maxAttempts = 10
    $attempt = 0
    
    do {
        Start-Sleep -Seconds 3
        $attempt++
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:7474" -TimeoutSec 5 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Success "Neo4j is ready!"
                break
            }
        } catch {
            Write-Info "Waiting... (attempt $attempt/$maxAttempts)"
        }
    } while ($attempt -lt $maxAttempts)
    
    if ($attempt -ge $maxAttempts) {
        Write-Warning "Neo4j may not be fully ready, continuing anyway..."
    }
    
} else {
    Write-Header "Step 2: Skipping Docker (--SkipDocker flag)"
}

# ============================================================
# STEP 3: Seed Database
# ============================================================
if (-not $SkipSeed) {
    Write-Header "Step 3: Seeding Neo4j Database"
    
    Write-Info "Creating $Citizens citizens in the database..."
    python scripts/seed_neo4j.py --citizens $Citizens
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to seed database"
        Write-Info "Make sure Neo4j is running and accessible"
        exit 1
    }
    
    Write-Success "Database seeded successfully"
    
} else {
    Write-Header "Step 3: Skipping Seed (--SkipSeed flag)"
}

# ============================================================
# STEP 4: Train Models
# ============================================================
if (-not $SkipTraining) {
    Write-Header "Step 4: Training Models with Real Data"
    
    # Create models directory
    if (-not (Test-Path "models")) {
        New-Item -ItemType Directory -Path "models" | Out-Null
    }
    
    $trainArgs = "--model both --epochs $Epochs"
    if ($WriteBack) {
        $trainArgs += " --write-back"
    }
    
    Write-Info "Training command: python scripts/train_with_neo4j.py $trainArgs"
    Write-Info "This may take several minutes..."
    
    python scripts/train_with_neo4j.py --model both --epochs $Epochs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Training failed"
        exit 1
    }
    
    Write-Success "Training completed!"
    
    # List saved models
    Write-Info "Saved models:"
    Get-ChildItem -Path "models" -Filter "*.pt" | ForEach-Object {
        Write-Info "  - $($_.Name) ($([math]::Round($_.Length/1KB, 2)) KB)"
    }
    
} else {
    Write-Header "Step 4: Skipping Training (--SkipTraining flag)"
}

# ============================================================
# SUMMARY
# ============================================================
Write-Header "Deployment Complete!"

Write-Host "`nServices:" -ForegroundColor Yellow
Write-Host "  - Neo4j Browser: http://localhost:7474" -ForegroundColor White
Write-Host "  - Neo4j Bolt: bolt://localhost:7687" -ForegroundColor White
Write-Host "  - Username: neo4j" -ForegroundColor White
Write-Host "  - Password: minorityreport" -ForegroundColor White

Write-Host "`nTrained Models:" -ForegroundColor Yellow
if (Test-Path "models/crime_prediction_best.pt") {
    Write-Host "  - models/crime_prediction_best.pt (GraphSAGE - Crime Prediction)" -ForegroundColor Green
}
if (Test-Path "models/escape_route_best.pt") {
    Write-Host "  - models/escape_route_best.pt (OracleNet - Escape Routes)" -ForegroundColor Green
}

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. View data in Neo4j Browser: http://localhost:7474" -ForegroundColor White
Write-Host "  2. Run: MATCH (c:Citizen) RETURN c LIMIT 25" -ForegroundColor White
Write-Host "  3. Export models for backend team" -ForegroundColor White

Write-Host "`nTo stop Neo4j:" -ForegroundColor Yellow
Write-Host "  docker-compose down" -ForegroundColor White

Write-Host "`n" -NoNewline
