from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document



class Splitter:
    
    @staticmethod    
    def split_and_get_documents(content : str) -> list[Document]:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        return splitter.create_documents([content])

    def get_document(content : str) -> list[Document]:
        return Document(page_content=content)
   