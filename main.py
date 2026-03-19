import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional

from rag_service import rag_service
from ai_service import (
    generate_pre_submit_hint,
    generate_post_submit_analysis,
    generate_code_comparison
)

app = FastAPI(title="Vector Problem AI Tutor API")

class HintRequest(BaseModel):
    student_question: str
    problem_topic: str = "vector data structure"

class AnalyzeRequest(BaseModel):
    student_code: str
    problem_topic: str = "vector data structure"

class CompareRequest(BaseModel):
    old_code: str
    new_code: str
    problem_topic: str = "vector data structure"


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


@app.post("/api/hint")
async def get_hint(request: HintRequest):
    """
    1. Pre-submit: Get a hint without receiving code.
    """
    context = rag_service.get_context(request.problem_topic + " " + request.student_question)
    response = generate_pre_submit_hint(context, request.student_question)
    return {"hint": response}


@app.post("/api/analyze")
async def analyze_code(request: AnalyzeRequest):
    """
    2. Post-submit: Analyze code, checking Big O, logic, and suggesting better code.
    """
    context = rag_service.get_context(request.problem_topic)
    response = generate_post_submit_analysis(context, request.student_code)
    return {"analysis": response}


@app.post("/api/compare")
async def compare_code(request: CompareRequest):
    """
    3. Compare versions: See if the student is heading in the right direction.
    """
    context = rag_service.get_context(request.problem_topic)
    response = generate_code_comparison(context, request.old_code, request.new_code)
    return {"comparison": response}

