from typing import Sequence
from typing import TypedDict
from typing_extensions import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from langchain_core.tools import BaseTool
from langgraph.graph.message import add_messages
from helper.ai.memory import Memory
from helper.ai.vector_dbs import BaseVectorDB


class WorkFlowState(TypedDict):
    _verbose : bool = False
    kids_mode : str = "Casual" # "Scientific", "Story", "Kids", "Auto"
    model : ChatGroq
    memory : Memory
    user_id : str # uuid
    conversation_id : str # uuid
    user_query : str = ""
    tools : list
    messages: Annotated[Sequence[BaseMessage], add_messages] = []
    memory_messages : Annotated[Sequence[BaseMessage], add_messages] = []
    new_messages : Annotated[Sequence[BaseMessage], add_messages] = []

    