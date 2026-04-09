import os
import shutil
from pathlib import Path

try:
    from dotenv import load_dotenv

    # โหลด .env จากโฟลเดอร์เดียวกับ main.py (ไม่ผูกกับ cwd ของ uvicorn)
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass
import subprocess
import tempfile
import uuid
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, model_validator

from ai_service import (
    DEFAULT_MODEL,
    MODEL_MAP,
    generate_code_comparison,
    generate_post_submit_analysis,
    generate_pre_submit_hint,
    generate_title_from_text,
)
from db_service import (
    download_question_pdf,
    fetch_question_by_code,
    list_questions_public,
)
from rag_service import rag_service

USE_MOCK_QUESTIONS = os.getenv("USE_MOCK_QUESTIONS", "false").lower() in ("1", "true", "yes")

app = FastAPI(title="Vector Problem AI Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# โหมดทดสอบโดยไม่มี Supabase
MOCK_QUESTIONS_DB = {
    "q1": {
        "code": "q1",
        "id": "q1",
        "title": "Merge Two Sorted Vectors",
        "description": "Given two sorted vectors, merge them into a single sorted vector.",
        "constraints": "1 <= vectors.length <= 10^5\nElements are integers.",
        "difficulty": "Easy",
        "expected_complexity": "O(N)",
        "time_limit": 1000,
        "memory_limit": 256,
        "uri": "",
        "solution": "",
        "starter_code": "def merge_sorted_lists(list1, list2):\n    # Write your code here\n    pass\n",
    },
}

# ซิงก์ PDF → Chroma ตาม updated_at + uri
_rag_sync_state: dict[str, str] = {}


def _ensure_rag_index_for_question(metadata: dict) -> None:
    """ดึง PDF จาก Supabase Storage แล้ว embed แยกตาม question_code (ถ้ามี uri)"""
    if USE_MOCK_QUESTIONS:
        return
    code = metadata.get("code") or metadata.get("id")
    uri = (metadata.get("uri") or "").strip()
    if not code or not uri:
        return
    sync_key = f"{metadata.get('updated_at', '')}|{uri}"
    if _rag_sync_state.get(code) == sync_key:
        return
    pdf_bytes = download_question_pdf(uri)
    rag_service.reindex_question_pdf(str(code), pdf_bytes, source_uri=uri)
    _rag_sync_state[str(code)] = sync_key


def get_question_metadata(question_code: str) -> dict:
    if USE_MOCK_QUESTIONS:
        m = MOCK_QUESTIONS_DB.get(question_code)
        if not m:
            raise HTTPException(status_code=404, detail="Question code not found (mock DB).")
        return dict(m)
    return fetch_question_by_code(question_code)


class HintRequest(BaseModel):
    question_code: Optional[str] = None
    question_id: Optional[str] = None
    student_question: str
    model: Optional[str] = None
    fast_mode: bool = False

    @model_validator(mode="after")
    def _need_code(self):
        if not (self.question_code or self.question_id):
            raise ValueError("question_code is required (หรือใช้ question_id ชั่วคราวเป็น alias)")
        return self

    def resolved_code(self) -> str:
        return (self.question_code or self.question_id or "").strip()


class AnalyzeRequest(BaseModel):
    question_code: Optional[str] = None
    question_id: Optional[str] = None
    student_code: str
    model: Optional[str] = None
    fast_mode: bool = False

    @model_validator(mode="after")
    def _need_code(self):
        if not (self.question_code or self.question_id):
            raise ValueError("question_code is required (หรือใช้ question_id ชั่วคราวเป็น alias)")
        return self

    def resolved_code(self) -> str:
        return (self.question_code or self.question_id or "").strip()


class CompareRequest(BaseModel):
    question_code: Optional[str] = None
    question_id: Optional[str] = None
    old_code: str
    new_code: str
    # คำถาม/โฟกัสจากผู้เรียน (ไม่บังคับ) — ส่งเข้า prompt ร่วมกับโค้ดสองเวอร์ชัน
    student_question: Optional[str] = None
    model: Optional[str] = None
    fast_mode: bool = False

    @model_validator(mode="after")
    def _need_code(self):
        if not (self.question_code or self.question_id):
            raise ValueError("question_code is required (หรือใช้ question_id ชั่วคราวเป็น alias)")
        return self

    def resolved_code(self) -> str:
        return (self.question_code or self.question_id or "").strip()


class RunRequest(BaseModel):
    code: str


@app.post("/ingest")
async def ingest_pdf(
    file: UploadFile = File(...),
    question_code: Optional[str] = Form(None),
):
    """
    อัปโหลด PDF เข้า vector DB (ทดสอบ/แอดมิน)
    ถ้าระบุ question_code จะผูก chunk กับโจทย์นั้น (ให้สอดคล้องกับ /api/hint ฯลฯ)
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    qc = (question_code or "").strip() or "__manual_upload__"
    try:
        result = rag_service.ingest_pdf(temp_file_path, question_code=qc, source_uri=file.filename)
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)

    extracted_text = result.get("text", "") if isinstance(result, dict) else ""
    description_content = (
        extracted_text.strip()
        if extracted_text.strip()
        else f"โจทย์ถูกดึงจาก **{file.filename}** — ใช้ question_code=`{qc}` เวลาเรียก API"
    )

    if USE_MOCK_QUESTIONS:
        new_q_id = f"q_up_{uuid.uuid4().hex[:6]}"
        file_title = (
            generate_title_from_text(extracted_text)
            if extracted_text.strip()
            else file.filename.replace(".pdf", "").replace("_", " ").title()
        )
        MOCK_QUESTIONS_DB[new_q_id] = {
            "code": new_q_id,
            "id": new_q_id,
            "title": f"📑 [Uploaded] {file_title}",
            "description": description_content[:2500]
            + ("...\n\n*(เนื้อหาบางส่วนถูกตัดทอน)*" if len(description_content) > 2500 else ""),
            "constraints": "ตาม PDF",
            "difficulty": "Custom",
            "expected_complexity": "N/A",
            "time_limit": 1000,
            "memory_limit": 256,
            "uri": "",
            "solution": "",
            "starter_code": "def solution():\n    pass\n",
        }
        msg = result.get("message", str(result)) if isinstance(result, dict) else result
        return {"message": "PDF ingested.", "details": msg, "question_code": new_q_id}

    msg = result.get("message", str(result)) if isinstance(result, dict) else result
    return {"message": "PDF ingested.", "details": msg, "question_code": qc}


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>UI not found. Please create index.html</h1>"


@app.get("/api/questions")
async def get_all_questions():
    if USE_MOCK_QUESTIONS:
        return [
            {"code": q.get("code", q.get("id")), "id": q.get("id"), "title": q["title"], "difficulty": q["difficulty"]}
            for q in MOCK_QUESTIONS_DB.values()
        ]
    return list_questions_public()


@app.get("/api/questions/{question_code}")
async def get_question(question_code: str):
    meta = get_question_metadata(question_code)
    out = {k: v for k, v in meta.items() if k not in ("solution",)}
    return out


@app.post("/api/hint")
async def get_hint(request: HintRequest):
    code = request.resolved_code()
    metadata = get_question_metadata(code)
    _ensure_rag_index_for_question(metadata)
    ctx = rag_service.get_context(
        metadata["title"] + " " + metadata["description"] + " " + request.student_question,
        question_code=metadata.get("code") or metadata.get("id"),
    )
    model_name = MODEL_MAP.get(request.model, DEFAULT_MODEL) if request.model else DEFAULT_MODEL
    return StreamingResponse(
        generate_pre_submit_hint(ctx, metadata, request.student_question, model_name, request.fast_mode),
        media_type="text/plain",
    )


@app.post("/api/analyze")
async def analyze_code(request: AnalyzeRequest):
    code = request.resolved_code()
    metadata = get_question_metadata(code)
    _ensure_rag_index_for_question(metadata)
    ctx = rag_service.get_context(
        metadata["title"] + " " + metadata["description"] + "\n" + request.student_code[:2000],
        question_code=metadata.get("code") or metadata.get("id"),
    )
    model_name = MODEL_MAP.get(request.model, DEFAULT_MODEL) if request.model else DEFAULT_MODEL
    return StreamingResponse(
        generate_post_submit_analysis(ctx, metadata, request.student_code, model_name, request.fast_mode),
        media_type="text/plain",
    )


@app.post("/api/compare")
async def compare_code(request: CompareRequest):
    code = request.resolved_code()
    metadata = get_question_metadata(code)
    _ensure_rag_index_for_question(metadata)
    extra_q = (request.student_question or "").strip()
    rag_query = metadata["title"] + " " + metadata["description"]
    if extra_q:
        rag_query += " " + extra_q
    ctx = rag_service.get_context(
        rag_query,
        question_code=metadata.get("code") or metadata.get("id"),
    )
    model_name = MODEL_MAP.get(request.model, DEFAULT_MODEL) if request.model else DEFAULT_MODEL
    return StreamingResponse(
        generate_code_comparison(
            ctx,
            metadata,
            request.old_code,
            request.new_code,
            model_name,
            request.fast_mode,
            student_question=extra_q,
        ),
        media_type="text/plain",
    )


@app.post("/api/run")
async def run_code(request: RunRequest):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(request.code)
        temp_path = f.name

    try:
        result = subprocess.run(
            ["python3", temp_path],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Execution timed out (5s limit)",
            "exit_code": 124,
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
