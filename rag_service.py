import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb

CHROMA_PATH = "./chroma_db"
# Assuming standard Ollama embedding model
EMBEDDING_MODEL = "nomic-embed-text" 

class RAGService:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        
        # We will use a default collection for vector problems
        self.collection_name = "vector_problems"
        
        # Initialize Langchain Chroma wrapper
        self.db = Chroma(
            client=self.chroma_client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )

    def ingest_pdf(self, file_path: str):
        """Loads a PDF, chunks it, and adds to ChromaDB."""
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        full_text = "\n\n".join([doc.page_content for doc in documents])
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)
        
        if chunks:
            self.db.add_documents(chunks)
            print(f"Successfully ingested {len(chunks)} chunks from {file_path}")
            return {"message": f"Ingested {len(chunks)} chunks.", "text": full_text}
        return {"message": "No text found in PDF.", "text": full_text}

    def get_context(self, query: str, k: int = 3):
        """Retrieves relevant chunks from ChromaDB for a given query."""
        results = self.db.similarity_search(query, k=k)
        context = "\n\n".join([doc.page_content for doc in results])
        return context

# Singleton instance
rag_service = RAGService()
