# MinorityReport - OracleNet Environment Setup
# Configura Python 3.11 con CUDA support

param([switch]$Force)

$ErrorActionPreference = "Stop"

Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "  MinorityReport - OracleNet Setup" -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan

# 1. Buscar Python 3.11
Write-Host "`n[1/7] Buscando Python 3.11..." -ForegroundColor Yellow
$python311 = $null
try {
    $pyVer = py -3.11 --version 2>&1 | Out-String
    if ($pyVer -match "3\.11") {
        $python311 = "py"
        $pyArgs = @("-3.11")
        Write-Host "  Encontrado via py launcher" -ForegroundColor Green
    }
}
catch {}

if (-not $python311) {
    Write-Host "  ERROR: Python 3.11 no encontrado" -ForegroundColor Red
    Write-Host "  Descarga desde: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# 2. Crear venv
Write-Host "`n[2/7] Creando entorno virtual..." -ForegroundColor Yellow
$venvPath = "venv311"
if ((Test-Path $venvPath) -and $Force) {
    Remove-Item -Recurse -Force $venvPath
}
if (-not (Test-Path $venvPath)) {
    & $python311 $pyArgs -m venv $venvPath
    Write-Host "  Creado: $venvPath" -ForegroundColor Green
}

# 3. Usar python del venv
$venvPy = ".\venv311\Scripts\python.exe"
Write-Host "`n[3/7] Usando: $venvPy" -ForegroundColor Yellow

# 4. Actualizar pip
Write-Host "`n[4/7] Actualizando pip..." -ForegroundColor Yellow
& $venvPy -m pip install --upgrade pip -q

# 5. PyTorch CUDA
Write-Host "`n[5/7] Instalando PyTorch con CUDA..." -ForegroundColor Yellow
Write-Host "  (Puede tardar varios minutos)" -ForegroundColor DarkGray
$torchIdx = "https://download.pytorch.org/whl/cu118"
& $venvPy -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==0.2.0 --index-url $torchIdx
Write-Host "  PyTorch instalado" -ForegroundColor Green

# 6. PyTorch Geometric
Write-Host "`n[6/7] Instalando PyTorch Geometric..." -ForegroundColor Yellow
& $venvPy -m pip install torch-geometric -q
$pygWhl = "https://data.pyg.org/whl/torch-2.0.1+cu118.html"
& $venvPy -m pip install torch-scatter torch-sparse -f $pygWhl
Write-Host "  PyG instalado" -ForegroundColor Green

# 7. Dependencias
Write-Host "`n[7/7] Instalando dependencias..." -ForegroundColor Yellow
$pkgs = "neo4j networkx numpy pandas matplotlib seaborn tqdm scipy scikit-learn"
& $venvPy -m pip install $pkgs.Split() -q
Write-Host "  Dependencias instaladas" -ForegroundColor Green

# Verificacion
Write-Host "`n" -NoNewline
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "  Verificacion" -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan

$checkCode = 'import torch; print("PyTorch:", torch.__version__); print("CUDA:", torch.cuda.is_available()); print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU only")'
& $venvPy -c $checkCode

Write-Host "`n" -NoNewline
Write-Host ("=" * 80) -ForegroundColor Green
Write-Host "  Completado!" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Green
Write-Host "`nProximos pasos:" -ForegroundColor Yellow
Write-Host "  1. .\venv311\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "  2. python oracle_net.py" -ForegroundColor Cyan
Write-Host "  3. python train_oracle.py`n" -ForegroundColor Cyan
