import fitz  # PyMuPDF
import docx
import csv
import io
import httpx
from bs4 import BeautifulSoup

class TextExtractor:
    @staticmethod
    def extract_pdf(file_path: str) -> str:
        text = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text.append(page.get_text())
        return "\n".join(text)

    @staticmethod
    def extract_docx(file_path: str) -> str:
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

    @staticmethod
    def extract_txt(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    @staticmethod
    def extract_csv(file_path: str) -> str:
        text = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                text.append(", ".join(row))
        return "\n".join(text)

    @staticmethod
    async def extract_url(url: str) -> str:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"User-Agent": "AinaAI-Crawler/1.0"})
            resp.raise_for_status()
            
        soup = BeautifulSoup(resp.text, "html.parser")
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
            
        return soup.get_text(separator="\n", strip=True)
