from typing import List
from sentence_transformers import SentenceTransformer
from app.config import settings

# Load model lazily / once in module scope
_model = None

def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    return _model

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Converts a list of text strings into a list of vector embeddings.
    """
    if not texts:
        return []
    
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.tolist()
