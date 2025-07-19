from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, AIMessageChunk

class DynamicCustomResponse:
    def __init__(self, system_message: str, params : dict, llm : ChatGroq = ChatGroq(model='llama-3.3-70b-versatile'), params_trim_length : int = 250):
        self.llm = llm
        self.params = self.trim_params(params, params_trim_length) if params_trim_length else params
        self.system_message = system_message
        self.messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=str(params)),
        ]
        
    
    def trim_params(self, params: dict, params_trim_length : int = 250) -> dict:
        trimmed_params = {}
        for key, value in params.items():
            if isinstance(value, str) and len(value) > params_trim_length:
                trimmed_params[key] = value[:params_trim_length] + "..."
            else:
                trimmed_params[key] = value
        return trimmed_params
        
    
    def invoke(self) -> AIMessage:
        return self.llm.invoke(self.messages)
    
    
    def stream(self) -> list[AIMessageChunk]:
        return self.llm.stream(self.messages)
    