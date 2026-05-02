

from typing import List, Optional

from pydantic import BaseModel


class FeedItem(BaseModel):
    id: str
    titulo: str
    micro_depoimento: Optional[str]
    idade_aprox: Optional[int]
    areas_afetadas: Optional[List[str]]
    foto_antes_url: Optional[str]
    foto_depois_url: Optional[str]
    score_relevancia: float
