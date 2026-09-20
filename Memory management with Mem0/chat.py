from dotenv import load_dotenv
import os
from mem0 import Memory
from openai import OpenAI
import json


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = OpenAI(
    api_key= GEMINI_API_KEY,
    base_url=  "https://generativelanguage.googleapis.com/v1beta/openai/"
)


config = {
    "version": "v1.1",
    "embedder": {
        "provider": "gemini",
        "config": {"api_key": GEMINI_API_KEY, "model": "gemini-embedding-2"}
    },
    "llm":{
        "provider": "gemini",
        "config": {"api_key": GEMINI_API_KEY, "model": "gemini-3.5-flash-lite"}
    },
    "vector_store":{
        "provider":"qdrant",
        "config" : {
            "host" : "localhost",
            "port" : 6333,
            "collection_name": "mem0_gemini",
            "embedding_model_dims": 768
        }
    }
}

m = Memory.from_config(config)


while True:

    user_query = input("-> ")

    search_memory = m.search(query=user_query, filters={"user_id": "Aditya"})

    memory = [f"ID : {mem.get('id')},\n Memory: {mem.get('memory')}" for mem in search_memory.get("results", [])]

    SYSTEM_PROMPT = f"The context related to user is {json.dumps(memory)}"
    
    responce = client.chat.completions.create(
        model= "gemini-3.5-flash-lite",
        messages= [{
            "role" : "user",
            "content": user_query
        },
        {
            "role" : "system",
            "content" : SYSTEM_PROMPT
        }
        ]
    )

    responce= responce.choices[0].message.content

    m.add(
        user_id = "Aditya",
        messages =[
            {"role" : "user", "content": user_query},
            {"role" : "AI", "content": responce}
        ]
    )

    print("AI", responce)

