import sys
import os
from datetime import datetime, timezone
from uuid import uuid4

# Adiciona o diretÃ³rio raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.firestore.client import get_firestore_client


def seed_relato_publico():
    db = get_firestore_client()

    relato_id = uuid4().hex
    now = datetime.now(timezone.utc).isoformat()

    doc = {
        "id": relato_id,
        "created_at": now,

        # âš ï¸ Campos internos mÃ­nimos
        "public_visibility": {
            "status": "PUBLIC",
            "reason": "seed_manual_teste",
            "updated_at": now
        },

        # âš ï¸ ÃšNICA fonte usada pela galeria pÃºblica
        "public_excerpt": {
            "text": "ApÃ³s alguns meses de cuidados consistentes, a pele apresentou melhora visÃ­vel.",
            "age_range": "30-39",
            "duration": "3 meses",
            "tags": ["hidrataÃ§Ã£o", "rotina", "coceira"],
            "image_previews": {
                "before": "https://placehold.co/400x300?text=Antes",
                "after": "https://placehold.co/400x300?text=Depois"
            }
        },

        # Campos extras (nÃ£o usados pelo preview, mas realistas)
        "conteudo_original": "Relato completo fictÃ­cio usado apenas para testes.",
        "status": "processed"
    }

    db.collection("relatos").document(relato_id).set(doc)

    print(f"âœ… Relato pÃºblico de teste criado com ID: {relato_id}")


if __name__ == "__main__":
    seed_relato_publico()
