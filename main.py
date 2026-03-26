import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
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

# Mock Database for testing since there is no actual database connected yet
MOCK_QUESTIONS_DB = {
    "q1": {
        "id": "q1",
        "title": "Merge Two Sorted Vectors",
        "description": "Given two sorted vectors, merge them into a single sorted vector.",
        "constraints": "1 <= vectors.length <= 10^5\nElements are integers.",
        "difficulty": "Easy",
        "expected_complexity": "O(N)",
        "time_limit": 1000,
        "memory_limit": 256
    },
    "q2": {
        "id": "q2",
        "title": "Find Kth Largest Element",
        "description": "Find the Kth largest element in an unsorted vector.",
        "constraints": "1 <= k <= vector.length <= 10^4",
        "difficulty": "Medium",
        "expected_complexity": "O(N)",
        "time_limit": 2000,
        "memory_limit": 128
    },
    "q3": {
        "id": "q3",
        "title": "Reverse a Vector",
        "description": "Write a function to reverse the elements in a vector in-place.",
        "constraints": "1 <= N <= 10^5",
        "difficulty": "Easy",
        "expected_complexity": "O(N)",
        "time_limit": 1000,
        "memory_limit": 128
    },
    "q4": {
        "id": "q4",
        "title": "Grade Calculation (If-Else)",
        "description": "Given an array of student scores, evaluate and return an array of their corresponding letter grades.",
        "constraints": "0 <= Score <= 100",
        "difficulty": "Easy",
        "expected_complexity": "O(N)",
        "time_limit": 1000,
        "memory_limit": 128
    },
    "q5": {
        "id": "q5",
        "title": "Two Sum",
        "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        "constraints": "2 <= nums.length <= 10^4",
        "difficulty": "Easy",
        "expected_complexity": "O(N)",
        "time_limit": 1000,
        "memory_limit": 128
    },
    "q6": {
        "id": "q6",
        "title": "Maximum Subarray",
        "description": "Given an integer array nums, find the contiguous subarray which has the largest sum and return its sum.",
        "constraints": "1 <= nums.length <= 10^5",
        "difficulty": "Medium",
        "expected_complexity": "O(N)",
        "time_limit": 1000,
        "memory_limit": 128
    },
    "q7": {
        "id": "q7",
        "title": "Palindrome Vector Check",
        "description": "Given an array of characters or integers, determine if it reads the same forwards and backwards.",
        "constraints": "1 <= vector.length <= 10^5",
        "difficulty": "Easy",
        "expected_complexity": "O(N)",
        "time_limit": 1000,
        "memory_limit": 128
    },
    "q8": {
        "id": "q8",
        "title": "Remove Duplicates from Sorted Vector",
        "description": "Given a sorted array of integers, remove the duplicates in-place such that each unique element appears only once.",
        "constraints": "1 <= nums.length <= 3 * 10^4",
        "difficulty": "Easy",
        "expected_complexity": "O(N)",
        "time_limit": 1000,
        "memory_limit": 128
    },
    "q9": {
        "id": "q9",
        "title": "Missing Number",
        "description": "Given an array containing n distinct numbers in the range [0, n], return the only number in the range that is missing from the array.",
        "constraints": "n == nums.length",
        "difficulty": "Easy",
        "expected_complexity": "O(N)",
        "time_limit": 1000,
        "memory_limit": 128
    },
    "q10": {
        "id": "q10",
        "title": "Move Zeroes",
        "description": "Given an integer array nums, move all 0's to the end of it while maintaining the relative order of the non-zero elements.",
        "constraints": "1 <= nums.length <= 10^4",
        "difficulty": "Easy",
        "expected_complexity": "O(N)",
        "time_limit": 1000,
        "memory_limit": 128
    },
    "q11": {
        "id": "q11",
        "title": "Best Time to Buy and Sell Stock",
        "description": "Return the maximum profit you can achieve from a single day to buy and a different day in the future to sell.",
        "constraints": "1 <= prices.length <= 10^5",
        "difficulty": "Easy",
        "expected_complexity": "O(N)",
        "time_limit": 1000,
        "memory_limit": 128
    },
    "q12": {
        "id": "q12",
        "title": "Product of Array Except Self",
        "description": "Return an array answer such that answer[i] is equal to the product of all the elements of nums except nums[i].",
        "constraints": "2 <= nums.length <= 10^5",
        "difficulty": "Medium",
        "expected_complexity": "O(N)",
        "time_limit": 1000,
        "memory_limit": 256
    },
    "q13": {
        "id": "q13",
        "title": "Contains Duplicate",
        "description": "Return true if any value appears at least twice in the array, and return false if every element is distinct.",
        "constraints": "1 <= nums.length <= 10^5",
        "difficulty": "Easy",
        "expected_complexity": "O(N)",
        "time_limit": 1000,
        "memory_limit": 128
    },
    "q14": {
        "id": "q14",
        "title": "Merge Intervals",
        "description": "Given an array of intervals, merge all overlapping intervals, and return an array of non-overlapping intervals.",
        "constraints": "1 <= intervals.length <= 10^4",
        "difficulty": "Medium",
        "expected_complexity": "O(N log N)",
        "time_limit": 2000,
        "memory_limit": 256
    }
}

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

def get_question_metadata(question_id: str):
    """Retrieve question info from DB simulator and raise 404 if not found."""
    metadata = MOCK_QUESTIONS_DB.get(question_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Question ID not found in database.")
    return metadata


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


@app.get("/api/questions")
async def get_all_questions():
    """Return a brief list of all available questions."""
    return [
        {"id": q["id"], "title": q["title"], "difficulty": q["difficulty"]}
        for q in MOCK_QUESTIONS_DB.values()
    ]


@app.get("/api/questions/{question_id}")
async def get_question(question_id: str):
    """Return full details for a specific question."""
    return get_question_metadata(question_id)


@app.post("/api/hint")
async def get_hint(request: HintRequest):
    """
    1. Pre-submit: Get a hint without receiving code.
    """
    metadata = get_question_metadata(request.question_id)
    # Query RAG using title + description to extract context
    context = rag_service.get_context(metadata["title"] + " " + metadata["description"])
    
    return StreamingResponse(
        generate_pre_submit_hint(context, metadata, request.student_question),
        media_type="text/plain"
    )


@app.post("/api/analyze")
async def analyze_code(request: AnalyzeRequest):
    """
    2. Post-submit: Analyze code, checking Big O, logic, and suggesting better code.
    """
    metadata = get_question_metadata(request.question_id)
    context = rag_service.get_context(metadata["title"] + " " + metadata["description"])
    
    return StreamingResponse(
        generate_post_submit_analysis(context, metadata, request.student_code),
        media_type="text/plain"
    )


@app.post("/api/compare")
async def compare_code(request: CompareRequest):
    """
    3. Compare versions: See if the student is heading in the right direction.
    """
    metadata = get_question_metadata(request.question_id)
    context = rag_service.get_context(metadata["title"] + " " + metadata["description"])
    
    return StreamingResponse(
        generate_code_comparison(context, metadata, request.old_code, request.new_code),
        media_type="text/plain"
    )
