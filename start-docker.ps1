# Inicia o Docker Desktop em segundo plano e sem o painel principal.
Write-Host "Iniciando o Docker Desktop..."
Start-Process -FilePath "D:\Program Files\Docker\Docker\Docker Desktop.exe" -ArgumentList "--no-dashboard"

# Verifica se o Docker está pronto, com um sistema de novas tentativas.
$maxRetries = 10
$retryCount = 0
Write-Host "Aguardando o Docker ficar operacional..."

while ($retryCount -lt $maxRetries) {
    # Tenta executar um comando docker. Se for bem-sucedido, o Docker está pronto.
    docker info > $null 2>&1
    if ($?) {
        Write-Host "Docker está operacional!"
        # Executa o docker-compose para subir os contêineres em modo 'detached' (em segundo plano).
        Write-Host "Executando 'docker-compose up -d'..."
        docker-compose up -d
        Write-Host "Script concluído! Os contêineres devem estar iniciando."
        exit 0 # Sai do script com sucesso
    }

    $retryCount++
    Write-Host "Docker ainda não está pronto. Tentando novamente em 15 segundos... (Tentativa $retryCount de $maxRetries)"
    Start-Sleep -Seconds 15
}

Write-Host "O Docker não iniciou após $maxRetries tentativas. Verifique o Docker Desktop e tente novamente."
exit 1 # Sai do script com um código de erro