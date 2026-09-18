import time
from dotenv import load_dotenv
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

load_dotenv()

pdf_path = Path(__file__).parent.parent / "fastapi_tutorial.pdf"

loader = PyPDFLoader(file_path=str(pdf_path))
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = text_splitter.split_documents(docs)
print(f"Total chunks created: {len(chunks)}")

embedding_model = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2"
)

# 1. Initialize Qdrant Client and VectorStore first
client = QdrantClient(url="http://localhost:6333")

vector_store = QdrantVectorStore(
    client=client,
    collection_name="Rag_Pract",
    embedding=embedding_model,
)

# 2. Manual batching to respect the 100 chunks/minute limit
BATCH_SIZE = 90
total_batches = (len(chunks) - 1) // BATCH_SIZE + 1

for i in range(0, len(chunks), BATCH_SIZE):
    batch = chunks[i:i + BATCH_SIZE]
    batch_num = i // BATCH_SIZE + 1
    print(f"Processing batch {batch_num} of {total_batches} ({len(batch)} chunks)...")
    
    # Add documents to the existing collection
    vector_store.add_documents(batch)
    
    # Pause for 60 seconds if there are more batches to process
    if i + BATCH_SIZE < len(chunks):
        print("Pausing 60 seconds to reset the 100 RPM quota limit...")
        time.sleep(60)

print("Indexing Is Done!")