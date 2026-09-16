from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.api import v1_ingestion, v1_chat

# Ensure all SQL tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Document Ingestion & RAG API",
    description="Backend API for Document Ingestion, Conversational RAG, and Interview Booking",
    version="1.0.0"
)

# Enable CORS for cross-origin client requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Router Modules
app.include_router(v1_ingestion.router)
app.include_router(v1_chat.router)


@app.get("/")
def root():
    return {
        "message": "Document Ingestion & RAG API is running.",
        "docs": "/docs"
    }