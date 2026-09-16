import json
from typing import List, Dict, Any, Optional
from groq import Groq
from sqlalchemy.orm import Session

from app.config import settings
from app.services.embedder import generate_embeddings
from app.services.vector_db import vector_db_service
from app.services.redis_memory import redis_memory_service
from app.models.booking import InterviewBooking


class RAGService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self._active_model = None

    def _get_client(self) -> Optional[Groq]:
        if not self.api_key:
            return None
        return Groq(api_key=self.api_key)

    def _resolve_model_name(self, client: Groq) -> str:
        """Dynamically pick the best chat completion model available on your Groq key."""
        if self._active_model:
            return self._active_model
            
        try:
            models_list = client.models.list()
            available_ids = [m.id for m in models_list.data if m.id]
            
            # Prioritized list of active standard chat/text generation models
            preferred_chat_models = [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "llama3-70b-8192",
                "mixtral-8x7b-32768"
            ]
            
            for model in preferred_chat_models:
                if model in available_ids:
                    self._active_model = model
                    return self._active_model

            # Fallback: Filter out classification/guard/whisper models
            valid_chat_models = [
                m for m in available_ids 
                if not any(x in m.lower() for x in ["guard", "whisper", "vision", "embed", "safeguard"])
            ]
            
            if valid_chat_models:
                self._active_model = valid_chat_models[0]
                return self._active_model

        except Exception as e:
            print(f"[Groq Model Auto-Discovery Warning]: {e}")
            
        return "llama-3.3-70b-versatile"

    def search_vector_db(self, query: str, collection_name: str = "documents", top_k: int = 3) -> List[str]:
        try:
            query_vectors = generate_embeddings([query])
            if not query_vectors:
                return []
            
            return vector_db_service.search_similar(
                collection_name=collection_name,
                query_vector=query_vectors[0],
                top_k=top_k
            )
        except Exception as e:
            print(f"[Vector Search Error]: {e}")
            return []

    def check_and_handle_booking(self, user_query: str, db: Session) -> Optional[Dict[str, Any]]:
        client = self._get_client()
        if not client:
            return None

        model_name = self._resolve_model_name(client)

        booking_prompt = f"""
        Analyze the user input to check if they want to book an interview.
        User Input: "{user_query}"

        If they want to book an interview AND provided details (name, email, date, time), extract them into JSON format:
        {{
            "is_booking": true,
            "name": "extracted name",
            "email": "extracted email",
            "date": "extracted date or TBD",
            "time": "extracted time or TBD"
        }}

        If NOT an interview booking request, return:
        {{
            "is_booking": false
        }}
        Return ONLY valid JSON.
        """

        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": booking_prompt}],
                model=model_name,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            
            if data.get("is_booking") and data.get("name") and data.get("email"):
                booking = InterviewBooking(
                    name=data["name"],
                    email=data["email"],
                    date=str(data.get("date", "TBD")),
                    time=str(data.get("time", "TBD"))
                )
                db.add(booking)
                db.commit()
                db.refresh(booking)
                
                return {
                    "status": "success",
                    "booking_id": booking.id,
                    "details": {
                        "name": booking.name,
                        "email": booking.email,
                        "date": booking.date,
                        "time": booking.time
                    }
                }
        except Exception as e:
            print(f"[Booking Extraction Error]: {e}")
            
        return None

    def generate_response(
        self,
        session_id: str,
        user_query: str,
        db: Session,
        collection_name: str = "documents"
    ) -> Dict[str, Any]:
        client = self._get_client()
        if not client:
            return {
                "answer": "GROQ_API_KEY is missing or invalid in your .env file.",
                "type": "error",
                "sources": [],
                "booking_details": None
            }

        try:
            # 1. Check for Interview Booking
            booking_result = self.check_and_handle_booking(user_query, db)
            if booking_result:
                b = booking_result["details"]
                confirmation = f"Your interview has been booked {b['name']} ({b['email']}) on {b['date']} at {b['time']}."
                
                try:
                    redis_memory_service.add_message(session_id, "user", user_query)
                    redis_memory_service.add_message(session_id, "assistant", confirmation)
                except Exception as me:
                    print(f"[Redis Warning]: {me}")

                return {
                    "answer": confirmation,
                    "type": "interview_booking",
                    "sources": [],
                    "booking_details": booking_result["details"]
                }

            # 2. Vector DB Context Search
            context_chunks = self.search_vector_db(user_query, collection_name=collection_name)
            context_str = "\n\n".join(context_chunks) if context_chunks else "No document context found."

            # 3. Memory Retrieval
            history = []
            try:
                history = redis_memory_service.get_history(session_id)
            except Exception as me:
                print(f"[Redis Warning]: {me}")
            
            # 4. Prompt Assembly
            system_prompt = f"You are an AI assistant. Answer the user prompt using the Context and Conversation History provided below.\n\nContext from Documents:\n{context_str}"
            
            messages = [{"role": "system", "content": system_prompt}]
            for item in history:
                messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
            messages.append({"role": "user", "content": user_query})

            # 5. LLM Call
            model_name = self._resolve_model_name(client)
            response = client.chat.completions.create(
                messages=messages,
                model=model_name,
                temperature=0.3
            )
            answer = response.choices[0].message.content

            # 6. Save Memory
            try:
                redis_memory_service.add_message(session_id, "user", user_query)
                redis_memory_service.add_message(session_id, "assistant", answer)
            except Exception as me:
                print(f"[Redis Warning]: {me}")

            return {
                "answer": answer,
                "type": "rag_query",
                "sources": context_chunks,
                "booking_details": None
            }

        except Exception as e:
            return {
                "answer": f"Error executing chat request: {str(e)}",
                "type": "error",
                "sources": [],
                "booking_details": None
            }

rag_service = RAGService()