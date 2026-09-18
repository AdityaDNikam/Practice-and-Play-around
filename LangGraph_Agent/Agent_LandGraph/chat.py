from dotenv import load_dotenv
from typing_extensions import TypedDict 
from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph,END,START
from langchain.chat_models import init_chat_model

load_dotenv()

llm = init_chat_model(
    model = "gemini-3.5-flash-lite",
    model_provider = "google_genai"
)

class State(TypedDict):
    message: Annotated[list,add_messages]

    
def ChatBot(state : State):
    responce = llm.invoke(state.get("message"))
    return{"message" : [responce]}

graph_builder = StateGraph(State)
graph_builder.add_node("ChatBot", ChatBot)

graph_builder.add_edge(START, "ChatBot")
graph_builder.add_edge("ChatBot", END)

graph = graph_builder.compile()

print(graph.invoke({"message": "Hi I am Aditya Nikam"}))
