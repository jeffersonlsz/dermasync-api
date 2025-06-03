# app/db/database.py
import chromadb
from sentence_transformers import SentenceTransformer

class DBResourceFactory:
    def __init__(self):
        self._client = None
        self._collection = None
        self._model = None
    
    @property
    def client(self):
        self._initialize_if_needed()
        return self._client
    
    @property
    def collection(self):
        self._initialize_if_needed()
        return self._collection
    
    @property
    def model(self):
        self._initialize_if_needed()
        return self._model
    
    def _initialize_if_needed(self):
        if self._client is None:
            self._client = chromadb.PersistentClient(path="./app/db/dermasync_chroma")
            self._collection = self._client.get_collection(name="segmentos")
            self._model = SentenceTransformer("intfloat/multilingual-e5-base")

# Instância singleton global
db_factory = DBResourceFactory()