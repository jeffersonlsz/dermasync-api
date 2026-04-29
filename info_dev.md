# Informações úteis para dev


## rodar o projeto localmente 

### subir o docker compose do postgres




### subir a API fastAPI localmente

```powershell
# Substitua pelo ID do seu projeto no Google Cloud
$env:GOOGLE_CLOUD_PROJECT="dermasync-3d14a" 

# Substitua pelo nome do seu bucket no Firebase Storage
$env:STORAGE_BUCKET="dermasync-3d14a.appspot.com" 

uvicorn app.main:app --reload --log-level debug


```
usuarios teste
user_test@test.local
Senha123!

admin@dermasync.com.br
admin123

## rodar firestore localmente

firebase emulators:start --only firestore --project dermasync-local