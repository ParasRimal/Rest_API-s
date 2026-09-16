from pydantic import BaseModel, Field
from typing import Optional

class IngestionResponse(BaseModel):
    status: str = Field(..., example="success")
    message: str = Field(..., example="Document ingested and vectorized successfully.")
    document_id: str = Field(..., example="b1234567-89ab-cdef-0123-456789abcdef")
    filename: str = Field(..., example="sample_document.pdf")
    total_chunks: int = Field(..., example=12)
    storage_path: Optional[str] = Field(None, example="storage/uploads/b1234567..._sample.pdf")