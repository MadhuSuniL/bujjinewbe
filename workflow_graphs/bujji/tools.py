from typing import Annotated
from langchain_core.tools import tool
from langchain_community.utilities import WikipediaAPIWrapper
from helper.classes import WikipediaQueryRunWithVectorDBStore
from helper.ai.vector_dbs import ChromaVectorDB
from helper.ai.embeddings import HuggingFaceEmbeddings

# Initialize API wrapper and tools
api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=8142)
wiki = WikipediaQueryRunWithVectorDBStore(api_wrapper=api_wrapper)
vector_db = ChromaVectorDB(embeddings=HuggingFaceEmbeddings())

@tool
def wikipedia_search_tool(
    query: Annotated[
        str, 
        "A concise, specific natural language question or topic to search on Wikipedia (e.g., 'What is black hole?', 'History of AI')."
    ]
) -> str:
    """
    🔍 Wikipedia Search Tool
    
    Uses Wikipedia to retrieve factual, structured summaries about a topic, event, person, or concept. 
    This tool fetches the top relevant result and automatically stores it in the internal vector database 
    for faster access in future queries.

    ✅ Ideal For:
    - General knowledge questions
    - Well-known public topics
    - Definitions, overviews, and history

    ⚙️ Behavior:
    - Searches Wikipedia using the given query.
    - Returns a structured summary (text).
    - Automatically stores the result into the internal vector DB.

    ❌ Not suitable for private or domain-specific content not available on Wikipedia.
    """
    response = wiki.invoke(input=query)
    return response

@tool
def vector_db_search_tool(
    query: Annotated[
        str, 
        "A natural language question targeting existing indexed content (e.g., resume info, private documents)."
    ],
    k: Annotated[
        int, 
        "Number of most relevant chunks to return from vector DB (range: 1–10)."
    ]
) -> str:
    """
    📚 Vector DB Search Tool

    Searches a pre-indexed private knowledge base using semantic similarity. 
    Ideal for retrieving content from resumes, documents, or datasets already embedded in the system.

    ✅ Ideal For:
    - Resume analysis
    - Domain-specific documents
    - Internal notes or indexed facts

    ⚙️ Behavior:
    - Performs similarity search using the provided query.
    - Returns up to `k` most relevant content chunks (already embedded).
    
    ❗ Do not include file names or parsing instructions — content is already pre-processed.
    ❌ Not suitable for general world knowledge or public information (use Wikipedia tool instead).
    """
    return vector_db.query(query, k)