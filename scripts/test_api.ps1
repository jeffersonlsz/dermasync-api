# salvar este bloco como login_get_token.ps1 ou rodar direto no PS
$body = @{
    email = "admin@dermasync.com.br"
    password = "admin123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/auth/login" -Body $body -ContentType "application/json"

if ($response -and $response.access_token) {
    $response.access_token | Out-File -FilePath ".\token.txt" -Encoding ascii
    Write-Host "Token salvo em token.txt"
} else {
    Write-Host "ERRO: resposta não contém token:" 
    $response | ConvertTo-Json -Depth 5
}
