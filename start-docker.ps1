# start-docker-and-up.ps1
# Testado em Windows 10/11 + Docker Desktop 4.26 até 4.34 (dezembro 2025)

Write-Host "Iniciando o Docker Desktop (sem abrir janela principal)..."
# Força matar qualquer tentativa antiga que tenha ficado zumbi
Get-Process "Docker Desktop" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

Start-Process -FilePath "D:\Program Files\Docker\Docker\Docker Desktop.exe" -ArgumentList "--quit" -WindowStyle Hidden -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# Inicia de novo, em background e tenta não abrir o dashboard
Start-Process -FilePath "D:\Program Files\Docker\Docker\Docker Desktop.exe" -ArgumentList "--no-dashboard" -WindowStyle Hidden

Write-Host "Aguardando o daemon do Docker ficar pronto (pode levar até 2 minutos na primeira vez)..."

$maxRetries = 30    # 30 × 8s = 4 minutos de espera máxima espera
$retryCount = 0
$success = $false

while ($retryCount -lt $maxRetries) {
    # O comando mais confiável é docker context ls ou docker version --format '{{.Server.Version}}'
    $version = docker version --format '{{.Server.Version}}' 2>$null
    if ($LASTEXITCODE -eq 0 -and $version) {
        Write-Host "Docker está pronto! versão $version"
        $success = $true
        break
    }

    $retryCount++
    Write-Host "Docker ainda não está pronto... tentativa $($retryCount)/$maxRetries. Aguardando 8 segundos..."
    Start-Sleep -Seconds 8
}

if (-not $success) {
    Write-Host "O Docker Desktop não iniciou a tempo. Abra manualmente e tente novamente."
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host "`nSubindo os containers com docker compose (plugin moderno)..."
# Primeiro tenta o novo comando (plugin)
docker compose up -d --remove-orphans --build

# Se o comando antigo ainda existir, usa como fallback
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tentando o docker-compose antigo como fallback..."
    docker-compose up -d --remove-orphans --build
}

Write-Host "`nTudo pronto! Os containers estão subindo em background."
Write-Host "Acesse seu projeto e use o docker ps para ver."
Write-Host "Quando quiser parar:   docker compose down"