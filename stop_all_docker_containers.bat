@echo off
echo 🔧 Parando todos os containers Docker em execução...
FOR /F %%i IN ('docker ps -q') DO docker stop %%i
echo ✅ Todos os containers foram parados.
