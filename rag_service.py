import os
import tempfile
from typing import Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb

CHROMA_PATH = "./chroma_db"
EMBEDDING_MODEL = os.environ.get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")


class RAGService:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

        self.collection_name = "vector_problems"

        self.db = Chroma(
            client=self.chroma_client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )

    def delete_chunks_for_question(self, question_code: str) -> None:
        """ลบ chunk เก่าของโจทย์นี้ก่อน ingest ใหม่"""
        if not question_code:
            return
        try:
            self.db._collection.delete(where={"question_code": question_code})
        except Exception:
            pass

    def ingest_pdf(self, file_path: str, question_code: Optional[str] = None, source_uri: str = ""):
        """Loads a PDF from disk, chunks it, and adds to ChromaDB."""
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        full_text = "\n\n".join([doc.page_content for doc in documents])
        qc = question_code or "__manual_upload__"
        for doc in documents:
            doc.metadata = doc.metadata or {}
            doc.metadata["question_code"] = qc
            if source_uri:
                doc.metadata["source_uri"] = source_uri

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)

        if chunks:
            self.db.add_documents(chunks)
            print(f"Successfully ingested {len(chunks)} chunks from {file_path} (question_code={qc})")
            return {"message": f"Ingested {len(chunks)} chunks.", "text": full_text}
        return {"message": "No text found in PDF.", "text": full_text}

    def ingest_pdf_bytes(self, pdf_bytes: bytes, question_code: str, source_uri: str = "") -> dict:
        """โหลด PDF จาก bytes (เช่น จาก Supabase Storage) แล้ว embed เข้า Chroma"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            path = tmp.name
        try:
            return self.ingest_pdf(path, question_code=question_code, source_uri=source_uri)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def reindex_question_pdf(self, question_code: str, pdf_bytes: bytes, source_uri: str = "") -> None:
        """ลบเวกเตอร์เดิมของโจทย์ แล้วสร้างใหม่จาก PDF"""
        self.delete_chunks_for_question(question_code)
        self.ingest_pdf_bytes(pdf_bytes, question_code, source_uri=source_uri)

    def get_context(self, query: str, question_code: Optional[str] = None, k: int = 3) -> str:
        """ค้นหา chunk ที่ใกล้เคียง — ถ้ามี question_code จะจำกัดเฉพาะโจทย์นั้น (vector แยกตามโจทย์)"""
        if question_code:
            results = self.db.similarity_search(query, k=k, filter={"question_code": question_code})
        else:
            results = self.db.similarity_search(query, k=k)
        context = "\n\n".join([doc.page_content for doc in results])
        return context


rag_service = RAGService()
