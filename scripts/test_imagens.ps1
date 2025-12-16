param(
    [string]$API = "http://localhost:8000",
    [string]$Email = "admin@dermasync.com.br",
    [string]$Password = "admin123",
    [string]$ImageId = "067fc81e"
)

Write-Host "=== Dermasync API Test Script ===" -ForegroundColor Cyan
Write-Host "API: $API" -ForegroundColor Yellow
Write-Host ""

function Call-API {
    param(
        [string]$Method,
        [string]$Url,
        [string]$Token = "",
        [object]$Body = $null
    )

    Write-Host "`n→ $Method $Url" -ForegroundColor Cyan

    $Headers = @{}
    if ($Token -ne "") {
        $Headers["Authorization"] = "Bearer $Token"
        Write-Host "   (Authorization: Bearer <token…>)" -ForegroundColor DarkGray
    }

    try {
        if ($Body) {
            $JsonBody = ($Body | ConvertTo-Json -Depth 5)
            Write-Host "   BODY: $JsonBody" -ForegroundColor DarkGray

            return Invoke-RestMethod -Method $Method -Uri $Url -Headers $Headers `
                -Body $JsonBody -ContentType "application/json"
        }
        else {
            return Invoke-RestMethod -Method $Method -Uri $Url -Headers $Headers
        }
    }
    catch {
        Write-Host "   ❌ ERRO:" -ForegroundColor Red
        # mostrar mensagem de erro inteira (mais útil durante debug)
        if ($_.Exception.Response -and $_.Exception.Response.Content) {
            try {
                $body = $_.Exception.Response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
                Write-Host ($body | ConvertTo-Json -Depth 5) -ForegroundColor Red
            } catch {
                Write-Host $_.Exception.Message -ForegroundColor Red
            }
        } else {
            Write-Host $_.Exception.Message -ForegroundColor Red
        }
        return $null
    }
}

# 1) LOGIN
Write-Host "=== LOGIN ===" -ForegroundColor Green
$LoginBody = @{ email = $Email; password = $Password }
$Login = Call-API -Method "POST" -Url "$API/auth/login" -Body $LoginBody

if (-not $Login) {
    Write-Host "❌ Falha no login, interrompendo." -ForegroundColor Red
    exit 1
}

$Token = $Login.access_token
$Refresh = $Login.refresh_token

Write-Host "`nToken obtido:" -ForegroundColor Yellow
if ($Token.Length -gt 40) { Write-Host $Token.Substring(0,40) "..." -ForegroundColor DarkYellow } else { Write-Host $Token -ForegroundColor DarkYellow }

"Bearer $Token" | Out-File "token.txt" -Encoding ascii
Write-Host "Token salvo em token.txt" -ForegroundColor DarkGreen

# 2) DEBUG CLIENT
Write-Host "`n=== TESTE: /imagens/_debug_client ===" -ForegroundColor Green
$Debug = Call-API -Method "GET" -Url "$API/imagens/_debug_client" -Token $Token
if ($Debug) { $Debug | Format-List }

# 3) LISTAR PÚBLICAS
Write-Host "`n=== TESTE: /imagens/listar-publicas ===" -ForegroundColor Green
$Public = Call-API -Method "GET" -Url "$API/imagens/listar-publicas?include_signed_url=true" -Token $Token
if ($Public) { $Public | Format-List }

# 4) IMAGEM PÚBLICA POR ID (CORREÇÃO: usar ${ImageId} ou $($ImageId) para interpolação segura)
Write-Host "`n=== TESTE: /imagens/public/${ImageId} ===" -ForegroundColor Green
$PublicById = Call-API -Method "GET" -Url "$API/imagens/public/${ImageId}?include_signed_url=true" -Token $Token
if ($PublicById) { $PublicById | Format-List }

# 5) IMAGEM PRIVADA (admin)
Write-Host "`n=== TESTE: /imagens/id/${ImageId} ===" -ForegroundColor Green
$Private = Call-API -Method "GET" -Url "$API/imagens/id/${ImageId}" -Token $Token
if ($Private) { $Private | Format-List }

Write-Host "`n=== FIM DOS TESTES ===" -ForegroundColor Cyan
