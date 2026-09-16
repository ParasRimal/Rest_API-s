from enum import Enum
from typing import List
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter


class ChunkingStrategy(str, Enum):
    FIXED_SIZE = "fixed_size"
    RECURSIVE = "recursive"


def chunk_text(
    text: str, 
    strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[str]:
    """
    Splits input text into chunks using the selected strategy.
    
    Args:
        text (str): The full raw text to be chunked.
        strategy (ChunkingStrategy): "fixed_size" or "recursive".
        chunk_size (int): Max size of each chunk in characters.
        chunk_overlap (int): Overlap between adjacent chunks.
        
    Returns:
        List[str]: A list of text chunks.
    """
    if not text.strip():
        return []

    if strategy == ChunkingStrategy.FIXED_SIZE:
        splitter = CharacterTextSplitter(
            separator=" ",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
    elif strategy == ChunkingStrategy.RECURSIVE:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    else:
        raise ValueError(f"Unsupported chunking strategy: {strategy}")

    chunks = splitter.split_text(text)
    return chunks
