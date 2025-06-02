@echo off
set IMAGE_NAME=dermasync-api
set PROJECT_ID=dermasync-llm
set REPO_NAME=llm-services
set REGION=us-central1
set PORT=8000
set GEMINI_API_KEY=AIzaSyDw-cad3OMvM8sUO6_LqRqLPKOsELhMmy8
echo 🔧 Buildando imagem local do Docker...
docker build -t %IMAGE_NAME% .

if %errorlevel% neq 0 (
    echo ❌ Erro ao buildar imagem. Abortando...
    exit /b %errorlevel%
)

echo 🔄 Tagueando imagem para o Artifact Registry...
docker tag %IMAGE_NAME% us-docker.pkg.dev/%PROJECT_ID%/%REPO_NAME%/%IMAGE_NAME%

echo 🔐 Autenticando Docker com Google Cloud...
gcloud auth configure-docker us-docker.pkg.dev

echo 🚀 Fazendo push da imagem para o Artifact Registry...
docker push us-docker.pkg.dev/%PROJECT_ID%/%REPO_NAME%/%IMAGE_NAME%

if %errorlevel% neq 0 (
    echo ❌ Erro ao fazer push da imagem. Verifique permissões.
    exit /b %errorlevel%
)

echo ☁️ Deploy no Cloud Run...
gcloud run deploy %IMAGE_NAME%  --image us-docker.pkg.dev/%PROJECT_ID%/%REPO_NAME%/%IMAGE_NAME%  --platform managed  --region %REGION%  --allow-unauthenticated  --port %PORT%  --set-env-vars GEMINI_API_KEY=%GEMINI_API_KEY%

if %errorlevel% neq 0 (
    echo ❌ Deploy falhou.
    exit /b %errorlevel%
)

echo ✅ Deploy finalizado com sucesso!
