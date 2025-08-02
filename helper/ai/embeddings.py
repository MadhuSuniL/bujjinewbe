from langchain_huggingface.embeddings import HuggingFaceEmbeddings as HF_Embeddings


class HuggingFaceEmbeddings(HF_Embeddings):
    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2", model_kwargs = {'device': 'cpu'}, encode_kwargs = {'normalize_embeddings': False}):
        super().__init__(model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs)
        object.__setattr__(self, 'dimension_size', 768)
