import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from .ai.providers import generate_object, get_model, parse_response
from .prompt import system_prompt


class FeedbackQuestion(BaseModel):
    questions: List[str]


async def generate_feedback(query: str, num_questions: int = 3) -> List[str]:
    """Generate follow-up questions to clarify research direction"""
    
    prompt = f"Given the following query from the user, ask some follow up questions to clarify the research direction. Return a maximum of {num_questions} questions, but feel free to return less if the original query is clear: <query>{query}</query>"
    
    schema = {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {"type": "string"},
                "description": f"Follow up questions to clarify the research direction, max of {num_questions}"
            }
        },
        "required": ["questions"]
    }
    
    try:
        response = generate_object(system_prompt(), prompt, schema)
        
        # Parse the response
        result = parse_response(response)
        
        questions = result.get("questions", [])
        return questions[:num_questions]
        
    except Exception as e:
        print(f"Error generating feedback: {e}")
        return []
    
    return []
