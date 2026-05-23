import pdfplumber
import io

def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    """
    Extract text and tables from PDF bytes using pdfplumber.
    Accepts raw bytes, handles both text and table-based PDFs.
    Returns a single combined string of all content.
    """
    try:
        text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                for table in page.extract_tables():
                    for row in table:
                        text += " | ".join(
                            [str(c) for c in row if c]
                        ) + "\n"
        return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""