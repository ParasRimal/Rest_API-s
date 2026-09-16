from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from app.database import Base

class DocumentMetadata(Base):
    __tablename__ = "document_metadata"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    chunk_count = Column(Integer, nullable=False, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)