# Modular Document Ingestion & Conversational RAG API

A high-performance, production-ready backend API service built with **FastAPI**, **Qdrant**, **Redis**, **SQLAlchemy**, and **Groq LLM**. This system provides robust end-to-end document processing, text chunking, dense vector embeddings, persistent vector search indexing, sliding-window session memory, and automated interview booking extraction.

---

## 🌟 Key Features

- **Document Ingestion API (`POST /api/v1/ingest`)**:
  - Supports `.pdf` and `.txt` file uploads.
  - Disk-backed raw file persistence in `storage/uploads/` with UUID conflict prevention.
  - Selectable text chunking strategies (`recursive` or `character`).
  - Dense 384-dimensional vector embedding generation using `SentenceTransformer` (`all-MiniLM-L6-v2`).
  - Local disk vector indexing via **Qdrant**.
  - Relational document metadata tracking in **SQLite**.

- **Conversational RAG API (`POST /api/v1/chat`)**:
  - Custom Retrieval-Augmented Generation (RAG) implementation (built without heavy chain abstractions).
  - Powered by fast **Groq LLM** (`llama-3.3-70b-versatile`).
  - **Redis** sliding-window session history management (retains multi-turn context per `session_id`).
  - Integrated zero-shot LLM **Intent Detection** for automated interview booking (`name`, `email`, `date`, `time`).
  - Relational interview booking persistence in **SQLite**.

---

## 🏗 System Architecture & Directory Structure

```text
Palm_Mind_Technology/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1_ingestion.py      # Route: Document upload, chunking, and indexing
│   │   └── v1_chat.py           # Route: Conversational RAG & interview booking
│   ├── models/
│   │   ├── __init__.py
│   │   ├── metadata.py          # SQLAlchemy model for DocumentMetadata
│   │   └── booking.py           # SQLAlchemy model for InterviewBooking
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── chat.py              # Pydantic request/response validation schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── text_extractor.py    # Multi-format text extraction (pypdf / TXT)
│   │   ├── chunker.py           # Recursive & Character text splitting service
│   │   ├── embedder.py          # SentenceTransformer vector embedding service
│   │   ├── vector_db.py         # Persistent local Qdrant vector store service
│   │   ├── redis_memory.py      # Session-bound Redis chat history manager
│   │   └── llm_rag.py           # Custom RAG engine & LLM booking intent extractor
│   ├── config.py                # Pydantic settings & environment configuration
│   ├── database.py              # SQLAlchemy engine & session factory setup
│   └── main.py                  # FastAPI application entry point
├── storage/
│   ├── uploads/                 # Persistent storage for raw uploaded files
│   └── qdrant_storage/          # Disk-backed Qdrant vector database collection
├── .env                         # Environment variables & secret API keys
├── .gitignore                   # Version control exclusion rules
├── metadata.db                  # SQLite database for operational metadata
└── requirements.txt             # Python project dependencies
```

---

## 🛠 Tech Stack & Tools

| Component | Tool / Library | Purpose |
| :--- | :--- | :--- |
| **Framework** | FastAPI + Uvicorn | Async web framework & high-concurrency server |
| **Database ORM** | SQLAlchemy + SQLite | Relational metadata and interview booking storage |
| **Vector Database** | Qdrant Client (Disk-Backed) | Local persistent vector index with Cosine similarity |
| **LLM Inference** | Groq API (`llama-3.3-70b-versatile`) | Rapid context synthesis and intent extraction |
| **Embeddings** | `SentenceTransformer` (`all-MiniLM-L6-v2`) | Generates dense 384-dimensional vector embeddings |
| **Session Memory** | Redis | Multi-turn conversation sliding window memory |
| **Document Parsing** | `pypdf` (`PdfReader`) | Memory-safe text extraction from PDF pages |

---

## ⚙️ Environment Configuration (`.env`)

Create a `.env` file in the project root folder:

```env
# Server & Database Settings
DATABASE_URL=sqlite:///./metadata.db
HOST=0.0.0.0
PORT=8000

# Groq LLM API Key
GROQ_API_KEY=your_groq_api_key_here

# Embedding Model
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

# Redis Cache Service
REDIS_HOST=localhost
REDIS_PORT=6379

# Qdrant Vector Service
QDRANT_URL=http://localhost:6333
```

---

## 🚀 Local Setup & Installation

### 1. Clone Repository & Activate Environment

```bash
git clone https://github.com/YOUR_USERNAME/Document_Ingestion_API.git
cd Document_Ingestion_API

# Activate virtual environment
source venv/bin/activate  # Or 'source api/bin/activate' depending on your setup
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Required Services

Make sure your local Redis server is running:

```bash
redis-server
```

### 4. Launch Application Server

```bash
uvicorn app.main:app --reload
```

The application starts at `http://127.0.0.1:8000`. Database tables in `metadata.db` will automatically initialize upon startup.

---

## 📖 API Documentation & Usage

Access interactive OpenAPI documentation at **`http://127.0.0.1:8000/docs`**.

### 1. Document Ingestion (`POST /api/v1/ingest`)

**cURL Request:**
```bash
curl -X 'POST'   'http://127.0.0.1:8000/api/v1/ingest'   -H 'accept: application/json'   -H 'Content-Type: multipart/form-data'   -F 'file=@sample_contract.pdf;type=application/pdf'   -F 'chunking_strategy=recursive'   -F 'chunk_size=500'   -F 'chunk_overlap=50'
```

**Response (`201 Created`):**
```json
{
  "message": "Document successfully ingested, indexed, and saved to disk.",
  "document_id": "a8f9b8c2-3e21-4f81-98ab-123456789abc",
  "filename": "sample_contract.pdf",
  "file_path": "storage/uploads/a8f9b8c2-3e21-4f81-98ab-123456789abc_sample_contract.pdf",
  "chunking_strategy": "recursive",
  "num_chunks": 18,
  "vector_collection": "documents",
  "uploaded_at": "2026-09-17T10:15:20.123456"
}
```

---

### 2. Conversational RAG (`POST /api/v1/chat`)

#### Scenario A: Contextual Document Query
**Request Payload:**
```json
{
  "session_id": "user_session_101",
  "message": "What is the project delivery timeline specified in the contract?"
}
```

**Response (`200 OK`):**
```json
{
  "answer": "According to the contract, final project delivery is scheduled for Q4 2026.",
  "type": "rag_query",
  "sources": [
    "Final project delivery is scheduled for Q4 2026 subject to compliance verification."
  ],
  "booking_details": null
}
```

#### Scenario B: Automated Interview Booking
**Request Payload:**
```json
{
  "session_id": "user_session_101",
  "message": "I want to schedule an interview. Name: John Doe, email: john@example.com, tomorrow at 3 PM."
}
```

**Response (`200 OK`):**
```json
{
  "answer": "Your interview has been booked John Doe (john@example.com) on tomorrow at 3 PM.",
  "type": "interview_booking",
  "sources": [],
  "booking_details": {
    "name": "John Doe",
    "email": "john@example.com",
    "date": "tomorrow",
    "time": "3 PM"
  }
}
```

---

## 📊 Database Inspection

To inspect relational database tables (`document_metadata` and `interview_bookings`) interactively:

```bash
pip install datasette
datasette metadata.db
```

Open `http://127.0.0.1:8001` in your browser to browse, search, or export database entries.
