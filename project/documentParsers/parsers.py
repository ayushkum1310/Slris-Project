# document_parsers/parser.py
import os, re, textwrap
from typing import List
import pandas as pd
import docx, pptx
from PyPDF2 import PdfReader

CHUNK_SIZE = 500  # ~500 tokens ≈ 750‑800 characters

class DocumentParser:
    """Unified parser for PDF, DOCX, PPTX, CSV, TXT / MD."""

    def parse(self, filePath: str) -> List[str]:
        ext = os.path.splitext(filePath)[1].lower()
        if ext == ".pdf":
            return self._parsePdf(filePath)
        if ext in {".docx"}:
            return self._parseDocx(filePath)
        if ext in {".pptx"}:
            return self._parsePptx(filePath)
        if ext in {".csv"}:
            return self._parseCsv(filePath)
        return self._parseTxt(filePath)  # default

    # -------- specific parsers --------
    def _parsePdf(self, filePath):
        reader = PdfReader(filePath)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return self._chunk(text)

    def _parseDocx(self, filePath):
        doc = docx.Document(filePath)
        text = "\n".join(p.text for p in doc.paragraphs)
        return self._chunk(text)

    def _parsePptx(self, filePath):
        prs = pptx.Presentation(filePath)
        slides = []
        for slide in prs.slides:
            slideText = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    slideText.append(shape.text)
            slides.append("\n".join(slideText))
        return self._chunk("\n".join(slides))

    def _parseCsv(self, filePath):
        df = pd.read_csv(filePath, dtype=str)
        return self._chunk(df.to_string(index=False))

    def _parseTxt(self, filePath):
        with open(filePath, "r", encoding="utf-8") as f:
            text = f.read()
        return self._chunk(text)

    # -------- helper --------
    def _chunk(self, text: str):
        # remove multiple spaces, limit chunk size
        cleaned = re.sub(r"\s+", " ", text).strip()
        return textwrap.wrap(cleaned, CHUNK_SIZE)



#Code for testing the DocumentParser class
# Uncomment the following lines to test the parser directly


# if __name__ == "__main__":
#     parser = DocumentParser()
#     # Example usage:
#     pdf_chunks = parser.parse(r"D:\Slris\ayushResume.pdf")


#     print(f"PDF chunks: {len(pdf_chunks)}")
#     for i in pdf_chunks:
#         print(i)
#         print("-" * 40)