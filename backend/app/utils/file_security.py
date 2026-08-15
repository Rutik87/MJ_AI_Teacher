import os
import re
import unicodedata
from pathlib import Path
from fastapi import HTTPException
from app.config import settings

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes filename while preserving Marathi unicode and standard characters.
    Prevents path traversal vulnerabilities.
    """
    # Normalize unicode
    filename = unicodedata.normalize("NFKC", filename)
    # Remove directory separators and null bytes
    filename = os.path.basename(filename)
    filename = re.sub(r'[\x00/\\:*?"<>|]', '_', filename)
    # Strip leading/trailing dots and spaces
    filename = filename.strip('. ')
    if not filename:
        filename = "document.pdf"
    return filename

def validate_pdf_file(filename: str, content_type: str, file_size_bytes: int):
    """
    Validates uploaded file against size and extension policies (.pdf, .txt).
    """
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"अवैध फाईल प्रकार ({ext}). फक्त PDF आणि TXT फाईल्स अनुमत आहेत."
        )
    
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size_bytes > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"फाईल आकार खूप मोठा आहे. कमाल मर्यादा {settings.MAX_UPLOAD_SIZE_MB}MB आहे."
        )

validate_document_file = validate_pdf_file
