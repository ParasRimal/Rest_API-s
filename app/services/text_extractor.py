import io
from pathlib import Path
from typing import Any
from fastapi import HTTPException
from pypdf import PdfReader


def extract_text(file_input: Any, filename: str = "") -> str:
    """
    Extracts plain text from a PDF or TXT file path, UploadFile object, or raw bytes.
    """
    contents: bytes = b""

    # 1. Handle FastAPI UploadFile object
    if hasattr(file_input, "file") and hasattr(file_input, "filename"):
        if not filename:
            filename = file_input.filename or ""
        file_input.file.seek(0)
        contents = file_input.file.read()

    # 2. Handle File Path (Path or str)
    elif isinstance(file_input, (Path, str)):
        path = Path(file_input)
        if not filename:
            filename = path.name
        with open(path, "rb") as f:
            contents = f.read()

    # 3. Handle raw bytes
    elif isinstance(file_input, bytes):
        contents = file_input
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file input type: {type(file_input).__name__}"
        )

    filename_lower = filename.lower()

    # Extract TXT
    if filename_lower.endswith(".txt"):
        try:
            return contents.decode("utf-8")
        except UnicodeDecodeError:
            return contents.decode("latin-1")

    # Extract PDF
    elif filename_lower.endswith(".pdf"):
        try:
            pdf_stream = io.BytesIO(contents)
            reader = PdfReader(pdf_stream)
            extracted_text = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text.append(text)

            full_text = "\n".join(extracted_text).strip()

            if not full_text:
                raise HTTPException(
                    status_code=400,
                    detail="PDF contains no extractable text (it might be scanned or image-based)."
                )

            return full_text

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process PDF file: {str(e)}"
            )

    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a .pdf or .txt file."
        )