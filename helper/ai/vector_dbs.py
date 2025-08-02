from uuid import uuid4
from abc import ABC, abstractmethod
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

class BaseVectorDB(ABC):
    @abstractmethod
    def add_documents(self, documents: list[Document]) -> None:
        ...
    
    @abstractmethod
    def query(self, query: str, k: int = 5) -> str:
        ...
        
    @abstractmethod
    def delete_index(self):
        ...
    
    @abstractmethod
    def delete_vectors(self):
        ...


class ChromaVectorDB(BaseVectorDB):
    def __init__(self, collection_name: str = 'global', embeddings : Embeddings = None):
        self.store : Chroma = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory="./vector_db",
        )
        
            
    def add_documents(self, documents : list[Document]) -> None:
        uuids = [str(uuid4()) for _ in range(len(documents))]
        return self.store.add_documents(documents=documents, ids=uuids)
        
        
    def query(self, query: str, k: int = 5) -> list[Document]:
        results = self.store.similarity_search(query, k=k)
        response = ["Chunk " + str(id+1) + '\n' + result.page_content for id, result in enumerate(results)]
        return "\n\n".join(response)
    
    
    def delete_index(self):
        self.client.delete_index(index_name=self.index_name)
        
    
    def delete_vectors(self, ids : list = []) -> None:
        self.store.delete(ids=ids)