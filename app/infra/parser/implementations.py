from io import BytesIO
from pypdf import PdfReader

from app.domain.interfaces import PDFParserInterface

#✅#
class V1_PDFParser(PDFParserInterface):
    """
    Extracts plain text from all pages
    """
    def parse_pdf(self, file_content: bytes) -> str:
        """
        Args:
            file_content: Raw PDF bytes.

        Returns:
            Extracted text as a single string.
        """
        if not file_content:
            return ""
        
        #check if file is a PDF by looking at the first few bytes (PDF files start with %PDF-)
        if not file_content.startswith(b'%PDF-'):
            raise ValueError("Invalid file type. Only PDFs are allowed.")

        pdf_stream = BytesIO(file_content)
        reader = PdfReader(pdf_stream)

        text_chunks: list[str] = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)

        return "\n".join(text_chunks)