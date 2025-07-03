# here we will expose endpoints related to video sources

from fastapi import APIRouter

from ..pipeline.data_reader import ler_jsonl_videos

router = APIRouter()


# buscar todos os videos da base
@router.post("/buscar-videos")
def buscar_todos_videos():
    print("chamando busca de videos")
    catalogo = ler_jsonl_videos()
    return catalogo
