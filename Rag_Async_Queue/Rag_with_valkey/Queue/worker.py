from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_qdrant import QdrantVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

embedding_model = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2"
)

vector_store = QdrantVectorStore.from_existing_collection(
    url="http://localhost:6333",
    collection_name="Rag_Pract",
    embedding=embedding_model
)


llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0.2)

SYSTEM_PROMPT = """You are a helpful, professional technical assistant. 

Your goal is to answer the user's question directly, clearly, and in a natural human-readable format based strictly on the provided Context.

Rules:
1. **Direct Answer:** Jump straight to answering the question. DO NOT start with robotic boilerplate phrases like "Based on the provided documentation..." or "According to the context...".
2. **Formatting:** Use clean Markdown with bullet points, bold key terms, and code blocks for maximum readability.
3. **Accuracy:** Use ONLY facts present in the Context below. If the context does not contain the answer, simply state: "I don't have enough information in the documentation to answer that."
4. **Citations:** Include page number references (e.g., `[Page 6]`) at the end of key facts.

---
Context:
{context}

---
Question:
{question}
"""

prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
chain = prompt | llm | StrOutputParser()

def process_query(query: str) -> str:
    if not query or not query.strip():
        return "No query provided."

    # 1. Similarity Search to retrieve relevant document chunks
    search_results = vector_store.similarity_search(query=query, k=3)

    # 2. Format variable context with page numbers & source references
    context_blocks = []
    for idx, doc in enumerate(search_results, start=1):
        page_num = doc.metadata.get("page_label") or doc.metadata.get("page", "N/A")
        source = doc.metadata.get("source", "Unknown Document")
        context_blocks.append(
            f"--- Reference {idx} (Page: {page_num}, Source: {source}) ---\n{doc.page_content}"
        )

    context = "\n\n".join(context_blocks)

    # 3. Execute RAG Chain
    response_text = chain.invoke({
        "context": context,
        "question": query
    })

    print(f"\n=== Generated Answer ===\n{response_text}\n{'='*40}\n")
    return response_text

 