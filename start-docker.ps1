# Inicia o Docker Desktop em segundo plano e sem o painel principal.
Write-Host "Iniciando o Docker Desktop..."
Start-Process -FilePath "D:\Program Files\Docker\Docker\Docker Desktop.exe" -ArgumentList "--no-dashboard"

# Aguarda 15 segundos para garantir que o serviço do Docker esteja completamente operacional.
Write-Host "Aguardando 15 segundos para a inicialização do Docker..."
Start-Sleep -Seconds 15

# Executa o docker-compose para subir os contêineres em modo 'detached' (em segundo plano).
Write-Host "Executando 'docker-compose up -d'..."
docker-compose up -d

Write-Host "Script concluído! Os contêineres devem estar iniciando."