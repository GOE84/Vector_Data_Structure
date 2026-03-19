import ollama

MODEL_NAME = "gemma3:12b"

def generate_pre_submit_hint(context: str, student_question: str):
    """
    Generates hints without providing direct code.
    """
    prompt = f"""
    You are an AI tutor helping a student with a vector data structure problem.
    
    <ProblemContext>
    {context}
    </ProblemContext>
    
    The student is asking for help or a hint:
    "{student_question}"
    
    INSTRUCTIONS:
    - Provide a helpful hint or explain the logic (e.g., algorithmic approach, Big O complexity).
    - DO NOT write actual code for the student. Provide algorithmic steps or pseudocode only if highly necessary, but prefer conceptual explanations.
    - Be encouraging.
    """
    
    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'user', 'content': prompt}
    ])
    return response['message']['content']


def generate_post_submit_analysis(context: str, student_code: str):
    """
    Analyzes submitted code and suggests improvements with code.
    """
    prompt = f"""
    You are an AI code reviewer analyzing a student's solution to a vector data structure problem.
    
    <ProblemContext>
    {context}
    </ProblemContext>
    
    <StudentCode>
    {student_code}
    </StudentCode>
    
    INSTRUCTIONS:
    - Analyze the code. Is it conceptually correct? Is it efficient in terms of time and space complexity (Big O)?
    - Provide constructive feedback.
    - If there is a more optimal or cleaner way to write it, show the improved code and explain why it's better.
    """
    
    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'user', 'content': prompt}
    ])
    return response['message']['content']


def generate_code_comparison(context: str, old_code: str, new_code: str):
    """
    Compares two versions of student code.
    """
    prompt = f"""
    You are an AI code tutor. The student is iterating on their solution for a vector data structure problem.
    
    <ProblemContext>
    {context}
    </ProblemContext>
    
    <OldCodeVersion>
    {old_code}
    </OldCodeVersion>
    
    <NewCodeVersion>
    {new_code}
    </NewCodeVersion>
    
    INSTRUCTIONS:
    - Compare the two versions. Did the student improve the solution in the new version?
    - Are they heading in the right direction? Or did they introduce new bugs or make it less efficient?
    - Point out specific improvements or regressions.
    - Be encouraging and indicate clearly whether the change is positive or negative.
    """
    
    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'user', 'content': prompt}
    ])
    return response['message']['content']

