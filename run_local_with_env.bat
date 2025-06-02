@echo off
echo 🧪 Rodando localmente com variáveis de ambiente do .env...

REM Carrega variáveis do .env
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    set "%%a=%%b"
)
set GEMINI_API_KEY=AIzaSyDw-cad3OMvM8sUO6_LqRqLPKOsELhMmy8
docker build -t dermasync-api .

docker run -p 8000:8000 -e GEMINI_API_KEY=%GEMINI_API_KEY%  dermasync-api

echo ✅ App disponível em http://localhost:8000/docs
