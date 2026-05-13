import urllib.parse

def normalize_storage_path(path: str, bucket_name: str = "") -> str:
    """
    Normaliza um path do Firebase Storage, garantindo que seja apenas o caminho interno.
    Aceita paths completos (https://...) ou já internos.
    """
    if not path:
        return ""
    
    path = str(path).strip()
    
    # Se for uma URL HTTP, precisamos extrair apenas a rota (o caminho interno do objeto)
    if path.startswith("http://") or path.startswith("https://"):
        parsed = urllib.parse.urlparse(path)
        path = parsed.path
        
    # Remove prefixos indesejados da API do GCP/Firebase
    # O path do GCP pode ser /v0/b/{bucket}/o/{path}
    if "/v0/b/" in path:
        parts = path.split("/o/")
        if len(parts) > 1:
            path = urllib.parse.unquote(parts[1])
            # Remove query params
            path = path.split("?")[0]
            
    # Removendo bucket prefix se houver (caso a rota seja /{bucket_name}/...)
    if bucket_name:
        if f"/{bucket_name}/" in path:
            path = path.split(f"/{bucket_name}/")[-1]
        elif path.startswith(f"{bucket_name}/"):
            path = path[len(bucket_name)+1:]

    # Remove barras iniciais
    return path.lstrip("/")
