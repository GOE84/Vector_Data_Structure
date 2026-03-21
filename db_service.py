import os
from supabase import create_client, Client
from fastapi import HTTPException

# Supabase coordinates
SUPABASE_URL = "https://xjsnmsajgsohwtddrjwp.supabase.co"
SUPABASE_SERVICE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhqc25tc2FqZ3NvaHd0ZGRyandwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzcyNTc3MCwiZXhwIjoyMDg5MzAxNzcwfQ."
    "J5U6IpLkRmEuQyGLmTqk4xT4LcNeCrTKusupA3B9mwk"
)

# Initialize client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_question_from_db(question_id: str) -> dict:
    """
    Retrieve a question from the Supabase questions table.
    Expects question_id to match either questions.id (if numeric) or questions.code.
    """
    try:
        # Check if question_id is numeric to query by id, otherwise query by code
        if question_id.isdigit():
            response = supabase.table("questions").select("*").eq("id", int(question_id)).execute()
        else:
            response = supabase.table("questions").select("*").eq("code", question_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Question ID not found in database.")
            
        data = response.data[0]
        
        # Difficulty mapping
        difficulty_map = {1: "Easy", 2: "Medium", 3: "Hard"}
        difficulty_level = data.get("difficulty")
        difficulty_str = difficulty_map.get(difficulty_level, str(difficulty_level))
        
        metadata = {
            "id": data.get("code") or str(data.get("id")),
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "constraints": data.get("constraints", ""),
            "difficulty": difficulty_str,
            "expected_complexity": data.get("expected_complexity", ""),
            "time_limit": data.get("time_limit", 1000),
            "memory_limit": data.get("memory_limit", 256)
        }
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
