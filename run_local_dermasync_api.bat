@echo off
set IMAGE_NAME=dermasync-api
set LOCAL_PORT=8000
set CONTAINER_PORT=8000

echo 🔄 Parando containers anteriores (se houver)...
docker stop %IMAGE_NAME%
docker rm %IMAGE_NAME%

echo ▶️ Rodando container local na porta %LOCAL_PORT%...
docker run -d --name %IMAGE_NAME% -p %LOCAL_PORT%:%CONTAINER_PORT% %IMAGE_NAME%

if %errorlevel% neq 0 (
    echo ❌ Erro ao rodar o container.
    exit /b %errorlevel%
)

echo 🌐 Acesse o serviço localmente em http://localhost:%LOCAL_PORT%/docs
