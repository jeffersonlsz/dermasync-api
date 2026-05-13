<#
.SYNOPSIS
  Inicia o ambiente de desenvolvimento local (Firebase Emulators + Uvicorn).
.DESCRIPTION
  Este script limpa as portas necessárias, inicia os emuladores do Firebase em uma nova janela
  e, em seguida, inicia o servidor Uvicorn na janela atual.
#>

$ErrorActionPreference = "Stop"

# Garante que o script está rodando na raiz do projeto
$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = Split-Path $scriptPath
$projectRoot = Split-Path $scriptDir
Set-Location $projectRoot

Write-Host "=== PREPARANDO AMBIENTE DE DESENVOLVIMENTO ===" -ForegroundColor Cyan

# Define as portas que precisamos liberar
# 8000: Uvicorn
# 4000: Emulator UI
# 4400: Emulator Hub
# 8080: Firestore
# 9099: Auth
# 9199: Storage
$portsToClear = @(8000, 4000, 4400, 8080, 9099, 9199)

Write-Host "=== LIBERANDO PORTAS ===" -ForegroundColor Yellow
foreach ($port in $portsToClear) {
    # Busca por conexões TCP ativas na porta
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            try {
                $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "Matando processo $($process.ProcessName) (PID $($process.Id)) na porta $port..."
                    Stop-Process -Id $process.Id -Force -ErrorAction Stop
                    Write-Host "Porta $port liberada com sucesso." -ForegroundColor Green
                }
            } catch {
                Write-Warning "Não foi possível liberar a porta $port. Pode ser necessário rodar como Administrador."
            }
        }
    }
}

Write-Host "`n=== INICIANDO FIREBASE EMULATORS ===" -ForegroundColor Yellow
# Inicia o emulador em uma nova janela para não bloquear o Uvicorn e manter os logs separados
$firebaseCmd = "firebase emulators:start --only firestore,storage,auth --project demo-dermasync --import=./emulator-data --export-on-exit"
try {
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$projectRoot'; $firebaseCmd`"" -WindowStyle Normal
    Write-Host "Firebase Emulators iniciados em uma nova janela." -ForegroundColor Green
} catch {
    Write-Error "Falha ao iniciar os emuladores do Firebase: $_"
    exit
}

Write-Host "`n=== AGUARDANDO EMULADORES (5s) ===" -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "`n=== INICIANDO UVICORN ===" -ForegroundColor Yellow
# Executa o Uvicorn na janela atual
try {
    uvicorn app.main:app  --log-level debug


} catch {
    Write-Error "Falha ao iniciar o Uvicorn: $_"
}


