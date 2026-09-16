import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.metadata import DocumentMetadata
from app.services.text_extractor import extract_text
from app.services.chunker import chunk_text, ChunkingStrategy
from app.services.embedder import generate_embeddings
from app.services.vector_db import vector_db_service

router = APIRouter(prefix="/api/v1", tags=["Ingestion"])

# Directory configuration for persistent upload storage
UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_document(
    file: UploadFile = File(...),
    chunking_strategy: ChunkingStrategy = Form(ChunkingStrategy.RECURSIVE),
    chunk_size: int = Form(500),
    chunk_overlap: int = Form(50),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    doc_id = str(uuid.uuid4())
    saved_file_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"

    try:
        # 1. Save uploaded file explicitly to storage/uploads/
        contents = await file.read()
        with open(saved_file_path, "wb") as f:
            f.write(contents)

        # 2. Extract text from the saved file on disk
        extracted_text = extract_text(saved_file_path, file.filename)
        
        # 3. Chunk text
        chunks = chunk_text(
            text=extracted_text,
            strategy=chunking_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Could not extract any valid text chunks from the document."
            )

        # 4. Generate embeddings & store in Qdrant
        embeddings = generate_embeddings(chunks)
        collection_name = "documents"
        
        vector_db_service.store_embeddings(
            collection_name=collection_name,
            chunks=chunks,
            embeddings=embeddings,
            document_id=doc_id,
            filename=file.filename
        )
        
        # 5. Save database record
        metadata_record = DocumentMetadata(
            id=doc_id,
            filename=file.filename,
            file_path=str(saved_file_path),
            chunk_count=len(chunks)
        )
        db.add(metadata_record)
        db.commit()
        db.refresh(metadata_record)

        return {
            "message": "Document successfully ingested, indexed, and saved to disk.",
            "document_id": doc_id,
            "filename": metadata_record.filename,
            "file_path": str(saved_file_path),
            "chunking_strategy": chunking_strategy.value,
            "num_chunks": metadata_record.chunk_count,
            "vector_collection": collection_name,
            "uploaded_at": metadata_record.uploaded_at
        }

    except Exception as e:
        # Cleanup file if writing/processing failed midway
        if saved_file_path.exists():
            saved_file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")