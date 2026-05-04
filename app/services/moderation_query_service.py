from typing import List

from app.firestore.client import get_firestore_client



class ModerationQueryService:



    def __init__(self):
        raise NotImplementedError("Esta classe foi movida para o domínio e deve ser acessada via caso de uso ListPendingRelatosUseCase. Verifique app/application/relatos/list_pending_relatos_use_case.py para a implementação atualizada.")
        self.db = get_firestore_client()



    def list_pending(self, limit: int = 20) -> List[dict]:
        raise NotImplementedError("Esta função foi movida para o domínio e deve ser acessada via caso de uso ListPendingRelatosUseCase. Verifique app/application/relatos/list_pending_relatos_use_case.py para a implementação atualizada.")
        docs = (

            self.db.collection("relatos")

            .where("moderation_status", "==", "pending")

            .limit(limit)

            .stream()

        )



        result = []

        for doc in docs:

            data = doc.to_dict()

            data["id"] = doc.id

            result.append(data)



        return result

