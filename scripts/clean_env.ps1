# Limpeza total do ambiente Python + portas comuns do Firebase Emulator
# Execute no PowerShell (preferencialmente como Administrador)

Write-Host "=== MATANDO PROCESSOS PYTHON ===" -ForegroundColor Yellow

Get-Process python,python3,py -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "=== MATANDO PROCESSOS NODE/FIREBASE/NPM ===" -ForegroundColor Yellow

Get-Process node,npm,npx,firebase -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "=== LIBERANDO PORTAS COMUNS DO FIREBASE EMULATOR ===" -ForegroundColor Yellow

$ports = @(4000,4400,4500,5000,5001,5002,5005,8080,8081,8085,8088,9000,9099,9199)

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        try {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            Write-Host "Porta $port liberada (PID $($conn.OwningProcess))"
        } catch {}
    }
}

Write-Host "=== LIMPEZA CONCLUÍDA ===" -ForegroundColor Green