import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from rag_service import rag_service
from ai_service import (
    generate_pre_submit_hint,
    generate_post_submit_analysis,
    generate_code_comparison
)

app = FastAPI(title="Vector Problem AI Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HintRequest(BaseModel):
    question_id: str
    student_question: str

class AnalyzeRequest(BaseModel):
    question_id: str
    student_code: str

class CompareRequest(BaseModel):
    question_id: str
    old_code: str
    new_code: str

from db_service import get_question_from_db

def get_question_metadata(question_id: str):
    """Retrieve question info from actual PostgreSQL Database (Supabase) and raise 404 if not found."""
    return get_question_from_db(question_id)

@app.post("/ingest")
async def ingest_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF containing the vector problem description.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # Save uploaded file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Process and ingest
        result = rag_service.ingest_pdf(temp_file_path)
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    # Cleanup
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
        
    return {"message": "PDF successfully ingested into Vector DB.", "details": result}


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serves the Chatbot UI."""
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>UI not found. Please create index.html</h1>"


@app.post("/api/hint")
async def get_hint(request: HintRequest):
    """
    1. Pre-submit: Get a hint without receiving code.
    """
    metadata = get_question_metadata(request.question_id)
    # Query RAG using title + description to extract context
    context = rag_service.get_context(metadata["title"] + " " + metadata["description"])
    
    response = generate_pre_submit_hint(context, metadata, request.student_question)
    return {"hint": response}


@app.post("/api/analyze")
async def analyze_code(request: AnalyzeRequest):
    """
    2. Post-submit: Analyze code, checking Big O, logic, and suggesting better code.
    """
    metadata = get_question_metadata(request.question_id)
    context = rag_service.get_context(metadata["title"] + " " + metadata["description"])
    
    response = generate_post_submit_analysis(context, metadata, request.student_code)
    return {"analysis": response}


@app.post("/api/compare")
async def compare_code(request: CompareRequest):
    """
    3. Compare versions: See if the student is heading in the right direction.
    """
    metadata = get_question_metadata(request.question_id)
    context = rag_service.get_context(metadata["title"] + " " + metadata["description"])
    
    response = generate_code_comparison(context, metadata, request.old_code, request.new_code)
    return {"comparison": response}
