# Import os to access system environment variables like OPENAI_API_KEY
import os
# Import uuid to generate unique string IDs for each vector entry
import uuid
# Import FastAPI classes for routing, file uploads, and HTTP error responses
from fastapi import FastAPI, UploadFile, File, HTTPException
# Import CORSMiddleware to allow React (port 5173/3000) to call FastAPI (port 8000)
from fastapi.middleware.cors import CORSMiddleware
# Import BaseModel to validate incoming JSON request payloads
from pydantic import BaseModel
# Import PdfReader to read and extract text from PDF streams
from pypdf import PdfReader
# Import chromadb to store vectors locally on disk
import chromadb
# Import OpenAI client to call embedding and LLM models
from openai import OpenAI

# Create the FastAPI application instance
app = FastAPI(title="Full-Stack RAG API")

# Add CORS middleware to permit cross-origin requests from the frontend
app.add_middleware(
    # Specify the CORS middleware class
    CORSMiddleware,
    # Allow requests from any domain during local development
    allow_origins=["*"],
    # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_methods=["*"],
    # Allow all HTTP headers (Content-Type, Authorization, etc.)
    allow_headers=["*"],
)

# Initialize the OpenAI client using the API key from the environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Initialize a persistent ChromaDB client that saves data inside './chroma_db'
chroma_client = chromadb.PersistentClient(path="./chroma_db")
# Create or retrieve a collection (table) named 'company_docs'
collection = chroma_client.get_or_create_collection(name="company_docs")


# Define the expected JSON schema for incoming chat requests
class QueryRequest(BaseModel):
    # Require a string field named 'question'
    question: str


# Define a function to split large text into smaller overlapping chunks
def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    # Initialize an empty list to store the resulting text chunks
    chunks = []
    # Set the starting character index to 0
    start = 0
    # Loop until the start index reaches the end of the text
    while start < len(text):
        # Calculate the ending index for the current chunk
        end = start + chunk_size
        # Slice the string from start to end and append it to chunks
        chunks.append(text[start:end])
        # Advance start by chunk_size minus overlap so sentences aren't cut cleanly
        start += chunk_size - overlap
    # Return the list of overlapping text chunks
    return chunks


# Define a function to convert a text string into a numerical vector embedding
def get_embedding(text: str) -> list[float]:
    # Request a vector embedding from OpenAI's text-embedding-3-small model
    response = client.embeddings.create(
        # Pass the text string to be embedded
        input=text,
        # Specify the embedding model name
        model="text-embedding-3-small"
    )
    # Return the list of floating-point numbers representing the vector
    return response.data[0].embedding


# Define a POST endpoint at '/upload' to ingest and index PDF files
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # Reject any file that does not end with '.pdf'
    if not file.filename.endswith(".pdf"):
        # Raise a 400 Bad Request HTTP exception
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Initialize PdfReader with the uploaded file stream
    reader = PdfReader(file.file)
    # Extract text from every page and join them with newline characters
    full_text = "\n".join([page.extract_text() or "" for page in reader.pages])
    # Split the full document text into overlapping chunks
    chunks = chunk_text(full_text)

    # Check if the PDF had any extractable text
    if not chunks:
        # Raise an error if the PDF is empty or image-based
        raise HTTPException(status_code=400, detail="No readable text found in PDF.")

    # Generate a unique UUID string for each chunk
    ids = [str(uuid.uuid4()) for _ in chunks]
    # Generate a vector embedding for every chunk
    embeddings = [get_embedding(chunk) for chunk in chunks]
    # Create metadata dictionaries storing filename and chunk index for citations
    metadatas = [{"source": file.filename, "chunk_index": i} for i in range(len(chunks))]

    # Save IDs, embeddings, raw text chunks, and metadata into ChromaDB
    collection.add(
        # Unique identifiers for each record
        ids=ids,
        # Numerical vectors for similarity search
        embeddings=embeddings,
        # Original text chunks to be retrieved later
        documents=chunks,
        # Source metadata for displaying citations
        metadatas=metadatas
    )

    # Return a JSON confirmation message with the count of indexed chunks
    return {"message": f"Indexed {len(chunks)} chunks from {file.filename}"}


# Define a POST endpoint at '/chat' to answer questions using stored documents
@app.post("/chat")
async def chat_with_docs(request: QueryRequest):
    # Convert the user's question into a vector embedding
    query_embedding = get_embedding(request.question)

    # Query ChromaDB for the top 3 most semantically similar text chunks
    results = collection.query(
        # Pass the question's embedding inside a list
        query_embeddings=[query_embedding],
        # Request the top 3 closest matches
        n_results=3
    )

    # Safely extract the matched document texts from the nested results list
    retrieved_docs = results["documents"][0] if results["documents"] else []
    # Safely extract the corresponding metadata dictionaries
    sources = results["metadatas"][0] if results["metadatas"] else []

    # If no chunks were found in the database, return an early prompt
    if not retrieved_docs:
        # Inform the user to upload a PDF first
        return {"answer": "No documents indexed yet. Please upload a PDF first.", "sources": []}

    # Combine the retrieved chunks into a single context string separated by dividers
    context_block = "\n\n---\n\n".join(retrieved_docs)
    # Build a strict system prompt instructing the AI to rely only on the context
    system_prompt = (
        "You are a precise technical assistant. Answer the user's question using ONLY "
        "the provided context below. If the answer is not in the context, state that you "
        "do not know. Do not guess or hallucinate.\n\n"
        f"CONTEXT:\n{context_block}"
    )

    # Call OpenAI's Chat Completions API to generate the final answer
    completion = client.chat.completions.create(
        # Use gpt-4o-mini for fast, low-cost reasoning
        model="gpt-4o-mini",
        # Set temperature to 0.1 to keep answers deterministic and factual
        temperature=0.1,
        # Pass the system instructions and user question
        messages=[
            # System message containing the retrieved PDF context
            {"role": "system", "content": system_prompt},
            # User message containing the actual question
            {"role": "user", "content": request.question}
        ]
    )

    # Return the generated answer and source metadata to the React frontend
    return {
        # Extract the assistant's text reply
        "answer": completion.choices[0].message.content,
        # Include the source filenames and chunk numbers
        "sources": sources
    }
