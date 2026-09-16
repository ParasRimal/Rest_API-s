from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session ID for Redis history tracking")
    message: str = Field(..., description="User query or input message")

class ChatResponse(BaseModel):
    answer: str
    type: str
    sources: Optional[List[str]] = None
    booking_details: Optional[Dict[str, Any]] = None
