import re
from typing import List
from app.core.config import settings
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class TextChunker:
    @staticmethod
    def split_text(text: str, chunk_size: int = settings.CHUNK_SIZE, overlap: int = settings.CHUNK_OVERLAP) -> List[str]:
        if not text.strip():
            return []

        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if overlap < 0:
            raise ValueError("overlap cannot be negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        # 1. Semantic Splitting based on Markdown Headers
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        
        try:
            md_docs = markdown_splitter.split_text(text)
        except Exception:
            md_docs = [Document(page_content=text, metadata={})]

        if not md_docs:
            md_docs = [Document(page_content=text, metadata={})]

        # 2. Token-Based Chunking
        # We explicitly exclude comma (,) to prevent breaking sentences and tables.
        try:
            token_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                separators=["\n\n", "\n", ".", "?", "!", " "]
            )
        except ImportError:
            # Fallback to character chunking if tiktoken is missing
            token_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                separators=["\n\n", "\n", ".", "?", "!", " "]
            )

        final_chunks = []
        for doc in md_docs:
            # Split the section into token-sized chunks
            sub_chunks = token_splitter.split_text(doc.page_content)
            
            # Reconstruct parent context
            header_str = ""
            if doc.metadata:
                header_parts = [f"{k}: {v}" for k, v in doc.metadata.items()]
                if header_parts:
                    header_str = f"[{' | '.join(header_parts)}]\n"

            for sub in sub_chunks:
                clean_chunk = sub.strip()
                if clean_chunk:
                    final_chunks.append(f"{header_str}{clean_chunk}")

        return final_chunks
