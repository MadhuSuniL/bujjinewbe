import logging
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode
from helper.ai.memory import Memory
from .schemas import WorkFlowState
from .prompts import SYSTEM_PROMPT
from .tools import wikipedia_search_tool, vector_db_search_tool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

def green_log(message: str):
    green = "\033[92m"  # Bright Green
    reset = "\033[0m"
    logging.info(f"{green}{message}{reset}")


def init_node(state: WorkFlowState):
    _verbose = state['_verbose']
    if _verbose:
        green_log("🚀 Starting workflow")
    user_query = HumanMessage(content=state['user_query'])
    
    return {
        'messages' : [user_query],
        'new_messages' : [user_query],
    }


def load_tools(state : WorkFlowState):
    _verbose = state['_verbose']
    if _verbose:
        green_log("🔧 Loading tools")

    tools = [vector_db_search_tool, wikipedia_search_tool]
    return {
        'tools' : tools
    }
    
    
    
def load_model(state : WorkFlowState):
    _verbose = state['_verbose']

    if _verbose:
        green_log(f"🧠 Loading model")

    tools = state['tools']
    model = state['model']
    model = model.bind_tools(tools)
    
    return {
        'model' : model
    }
    

def load_memory(state: WorkFlowState):
    _verbose = state['_verbose']
    if _verbose:
        green_log(f"🧠 Loading memory")

    conversation_id = state['conversation_id']
    user_id = state['user_id']
    model = state['model']
    kids_mode = state['kids_mode']
    memory : Memory = Memory.get_memory(conversation_id, user_id, 6000)
    system_prompt = SystemMessage(content=SYSTEM_PROMPT.format(kids_mode = 'ON' if kids_mode else 'OFF'))
    
    if _verbose:
        green_log("🧠 Memory loaded")
    memory_messages = memory.messages
    all_memory_messages = [system_prompt, *memory_messages]
    return {
        'memory' : memory,
        'memory_messages' : all_memory_messages
    }
     

def call_model(state: WorkFlowState):
    _verbose = state['_verbose']
    if _verbose:
        green_log("🤖 Calling main model for response generation.")
    
    model = state['model']
    messages = state['messages']
    memory_messages = state['memory_messages']
    messages = [*memory_messages, *messages]
    response : AIMessage = model.invoke(messages)
    return {
        'messages' : [response],
        'new_messages' : [response]
    }
    

def tool_node(state: WorkFlowState) -> dict:
    _verbose = state['_verbose']
    if _verbose:
        green_log("🔧 Calling tool node")

    return ToolNode(tools=state['tools'], handle_tool_errors = True)


def pick_tool_messages(state: WorkFlowState):
    _verbose = state['_verbose']
    if _verbose:
        green_log("🔧 Picking tool messages")

    tool_messages = []
    ai_flag = False
    messages = state['messages']
    for message in reversed(messages):
        if isinstance(message, ToolMessage):
            tool_messages.append(message)
        else:
            ai_flag = True
            break
        
    return {
        'new_messages' : tool_messages
    }


def save_messages_to_memory(state: WorkFlowState):
    _verbose = state['_verbose']
    if _verbose:
        green_log("💾 Saving messages to memory.")
    
    memory = state['memory']
    new_messages = state['new_messages']
    
    for message in new_messages:
        memory.add_message(message)    
    
    return {
        'new_messages' : []
    }
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
# def tool_node_2(state: WorkFlowState) -> dict:
    # _verbose = state['_verbose']
    # if _verbose:
    #     green_log("🔧 Calling tool node")
    
    # last_message : AIMessage = state['messages'][-1]
    # tools = state['tools']

    # tools_by_name = {tool.name: tool for tool in tools}
    # tool_messages = []

    # for tool_call in last_message.tool_calls:
    #     tool = tools_by_name.get(tool_call["name"])
    #     if not tool:
    #         continue

    #     retries = 2
    #     for attempt in range(1, retries + 1):
    #         try:
    #             observation = tool.invoke(input={**tool_call["args"], "state" : state}, verbose=False)  
    #             tool_messages.append(ToolMessage(
    #                 content=observation,
    #                 name=tool.name,
    #                 tool_call_id=tool_call["id"],
    #             ))
    #             break  

    #         except Exception as e:
    #             if attempt == retries:
    #                 error_message = f"Error: Tool invocation failed after {retries}/2 attempts. Error: {str(e)}"
    #                 tool_messages.append(ToolMessage(
    #                     content=error_message,
    #                     name=tool.name,
    #                     tool_call_id=tool_call["id"],
    #                 ))
    
    # return {
    #     "messages": tool_messages,
    #     "new_messages" : tool_messages
    # }