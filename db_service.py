import os
import re
from typing import Any, Optional
from urllib.parse import unquote, urlparse

from fastapi import HTTPException
from supabase import Client, create_client

_supabase: Optional[Client] = None
_cached_env_key: Optional[tuple[str, str, str]] = None


def _read_supabase_env() -> tuple[str, str, str]:
    """อ่าน env ทุกครั้งที่สร้าง client (หลัง load_dotenv แล้วจะได้ค่าถูกต้อง)"""
    url = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
    key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY") or "").strip()
    bucket = (os.environ.get("SUPABASE_STORAGE_QUESTIONS_BUCKET") or "question-pdfs").strip()
    return url, key, bucket


def get_supabase() -> Client:
    global _supabase, _cached_env_key
    url, key, _bucket = _read_supabase_env()
    env_key = (url, key)
    if _supabase is not None and _cached_env_key == env_key:
        return _supabase
    if not url or not key:
        raise HTTPException(
            status_code=503,
            detail=(
                "Supabase is not configured. ตั้งค่า SUPABASE_URL และ SUPABASE_SERVICE_ROLE_KEY ในไฟล์ .env "
                "ที่อยู่ข้าง main.py หรือ export เป็น environment variable แล้วรีสตาร์ท uvicorn"
            ),
        )
    _supabase = create_client(url, key)
    _cached_env_key = env_key
    return _supabase


def list_questions_public() -> list[dict[str, Any]]:
    """รายการโจทย์สำหรับ UI (เฉพาะที่ status = true)"""
    sb = get_supabase()
    res = (
        sb.table("questions")
        .select("code,title,difficulty")
        .eq("status", True)
        .order("code")
        .execute()
    )
    rows = res.data or []
    difficulty_map = {1: "Easy", 2: "Medium", 3: "Hard"}
    out = []
    for row in rows:
        d = row.get("difficulty")
        out.append(
            {
                "code": row.get("code"),
                "id": row.get("code"),
                "title": row.get("title") or "",
                "difficulty": difficulty_map.get(d, str(d) if d is not None else "Unknown"),
            }
        )
    return out


def fetch_question_by_code(question_code: str) -> dict[str, Any]:
    """ดึงแถว questions ตาม code (varchar) พร้อม normalize เป็น metadata สำหรับ AI / RAG"""
    if not question_code or not str(question_code).strip():
        raise HTTPException(status_code=400, detail="question_code is required.")
    sb = get_supabase()
    code = str(question_code).strip()
    try:
        res = (
            sb.table("questions")
            .select("*")
            .eq("code", code)
            .eq("status", True)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase query error: {e!s}")

    if not res.data:
        raise HTTPException(status_code=404, detail=f"Question code not found: {code}")

    data = res.data[0]

    difficulty_map = {1: "Easy", 2: "Medium", 3: "Hard"}
    difficulty_level = data.get("difficulty")
    difficulty_str = difficulty_map.get(difficulty_level, str(difficulty_level))

    solution = (data.get("solution") or "").strip()
    if solution:
        starter_code = solution
    else:
        starter_code = (
            "class Solution:\n    def solve(self):\n        # เขียนโค้ดของคุณที่นี่\n        pass\n"
        )

    updated_at = data.get("updated_at")
    updated_at_str = updated_at.isoformat() if hasattr(updated_at, "isoformat") else (str(updated_at) if updated_at else "")

    metadata: dict[str, Any] = {
        "code": data.get("code"),
        "id": data.get("code"),
        "db_id": data.get("id"),
        "title": data.get("title") or "",
        "description": data.get("description") or "",
        "constraints": data.get("constraints") or "",
        "solution": data.get("solution") or "",
        "uri": (data.get("uri") or "").strip(),
        "difficulty": difficulty_str,
        "expected_complexity": data.get("expected_complexity") or "",
        "time_limit": data.get("time_limit") if data.get("time_limit") is not None else 1000,
        "memory_limit": data.get("memory_limit") if data.get("memory_limit") is not None else 256,
        "updated_at": updated_at_str,
        "starter_code": starter_code,
    }
    return metadata


def _parse_supabase_storage_ref(uri_or_path: str) -> tuple[str, str]:
    """
    แปลงค่า questions.uri เป็น (bucket, object_path)
    รองรับทั้งพาธใน bucket เช่น questions/a.pdf และ URL เต็ม
    เช่น …/storage/v1/object/public/question-pdfs/questions/a.pdf
    """
    raw = (uri_or_path or "").strip()
    if not raw:
        return "", ""
    if not raw.lower().startswith(("http://", "https://")):
        return "", unquote(raw.lstrip("/"))

    path = unquote(urlparse(raw).path or "")
    # มาตรฐาน Supabase: /storage/v1/object/public|authenticated|sign/{bucket}/...
    m = re.search(
        r"/storage/v1/object/(?:public|authenticated|sign)/([^/]+)/(.+)$",
        path,
    )
    if m:
        return m.group(1), m.group(2)
    m2 = re.search(r"/object/(?:public|authenticated|sign)/([^/]+)/(.+)$", path)
    if m2:
        return m2.group(1), m2.group(2)
    return "", raw.lstrip("/")


def download_question_pdf(path_in_bucket: str) -> bytes:
    """
    ดาวน์โหลดไฟล์ PDF จาก Supabase Storage
    uri อาจเป็นแค่พาธใน bucket หรือเป็น public URL ทั้งสตริงจาก Supabase
    """
    if not path_in_bucket:
        raise HTTPException(status_code=404, detail="Question has no PDF uri in database.")
    sb = get_supabase()
    _url, _key, default_bucket = _read_supabase_env()
    url_bucket, object_path = _parse_supabase_storage_ref(path_in_bucket)
    bucket = url_bucket or default_bucket
    if not object_path:
        raise HTTPException(status_code=400, detail="Could not parse storage path from questions.uri.")
    try:
        data = sb.storage.from_(bucket).download(object_path)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Storage download failed (bucket={bucket!r}, path={object_path!r}): {e!s}",
        )
    if not data:
        raise HTTPException(status_code=404, detail="Empty file from storage.")
    return data
