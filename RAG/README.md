docuchat-rag/
├── backend/
│   ├── main.py              # FastAPI RAG backend
│   └── requirements.txt     # Python dependencies
├── frontend/
│   └── src/
│       └── App.jsx          # React upload & chat UI
└── README.md                # Documentation

<!-- Main repository title -->
# DocuChat RAG — Full-Stack Document Intelligence App

<!-- High-level summary of what the application does -->
A Retrieval-Augmented Generation (RAG) web application that lets users upload PDF documents and ask grounded questions with source citations.

<!-- Section header for system architecture -->
## Architecture

<!-- Visual ASCII flow showing how React, FastAPI, OpenAI, and ChromaDB interact -->
[React UI] --(PDF / Query)--> [FastAPI Backend] --(Embeddings)--> [OpenAI API]
                                     |
                              (Vector Search)
                                     v
                                 [ChromaDB]

<!-- Section header highlighting AI engineering skills for interviewers -->
## Key AI Concepts Implemented

<!-- Explains why overlapping chunking prevents lost context at split boundaries -->
- **Overlapping Text Chunking:** Splits documents into 800-character blocks with a 150-character overlap to preserve context across boundaries.
<!-- Explains how text is converted into semantic vectors -->
- **Dense Vector Embeddings:** Uses `text-embedding-3-small` to convert text into semantic vectors.
<!-- Explains how relevant chunks are retrieved -->
- **Cosine Similarity Retrieval:** Queries ChromaDB for the top 3 most relevant document chunks.
<!-- Explains how temperature and prompt constraints stop hallucinations -->
- **Hallucination Guardrails:** Enforces `temperature=0.1` and a strict system prompt so answers rely strictly on uploaded documents.

<!-- Section header for local installation instructions -->
## Setup & Run

<!-- Step 1 instructions for starting the Python backend -->
1. **Backend:**
   ```bash
   # Navigate into the backend directory
   cd backend
   # Install all required Python libraries
   pip install -r requirements.txt
   # Set your OpenAI API key in the terminal session
   export OPENAI_API_KEY="your-key-here"
   # Start the FastAPI server on port 8000 with hot-reload enabled
   uvicorn main:app --reload --port 8000
   ```

<!-- Step 2 instructions for starting the React frontend -->
2. **Frontend:**
   ```bash
   # Navigate into the frontend directory
   cd frontend
   # Install Node packages and launch the React development server
   npm install && npm run dev
   ```
