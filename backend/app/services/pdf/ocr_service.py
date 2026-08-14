import io
from PIL import Image
from app.utils.logger import logger

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

class OCRService:
    def __init__(self):
        self.is_available = HAS_PYTESSERACT
        if self.is_available:
            try:
                # Test pytesseract installation
                pytesseract.get_tesseract_version()
                self.has_tesseract_binary = True
            except Exception as e:
                logger.warning(f"Tesseract binary not found in PATH: {e}. OCR fallback enabled.")
                self.has_tesseract_binary = False
        else:
            self.has_tesseract_binary = False

    def extract_text_from_image(self, image_bytes: bytes, lang: str = "mar+eng") -> str:
        """
        Extracts Marathi/English text from image bytes using Tesseract OCR.
        """
        if not self.has_tesseract_binary:
            return ""

        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Try Marathi first, fallback to standard if marathi lang pack is missing
            try:
                text = pytesseract.image_to_string(image, lang=lang)
            except Exception:
                text = pytesseract.image_to_string(image, lang="eng")
            return text.strip()
        except Exception as e:
            logger.error(f"OCR Extraction failed: {e}")
            return ""

ocr_service = OCRService()
