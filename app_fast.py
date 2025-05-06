from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from groq import Groq

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client
client = Groq(
    api_key="",
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store conversation history
conversation_history = {}

class ChatRequest(BaseModel):
    message: str
    sessionId: str = "default"
    userInfo: Dict[str, Any] = {}

class ResetRequest(BaseModel):
    sessionId: str = "default"

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat(chat_request: ChatRequest):
    session_id = chat_request.sessionId
    user_message = chat_request.message
    user_info = chat_request.userInfo
    
    if session_id not in conversation_history:
        conversation_history[session_id] = []
    
    conversation_history[session_id].append({"role": "user", "content": user_message})
    
    system_prompt = create_system_prompt(user_info)
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history[session_id][-10:])
    
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama3-70b-8192",
            temperature=0.7,
            max_tokens=800,
            top_p=0.9,
        )
        
        response = chat_completion.choices[0].message.content
        conversation_history[session_id].append({"role": "assistant", "content": response})
        
        return {
            "response": response,
            "success": True
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "response": "I'm having trouble connecting right now. Please try again in a moment.",
                "success": False,
                "error": str(e)
            }
        )

def create_system_prompt(user_info: Dict[str, Any]) -> str:
    """Create a personalized system prompt based on user info"""
    base_prompt = """You are HealthFit AI, an expert health and fitness assistant focused on providing personalized advice on exercise, nutrition, and overall wellness. 

Your primary goals are to:
1. Provide scientifically-backed health and fitness advice
2. Tailor recommendations to the user's specific needs and goals
3. Encourage safe and sustainable fitness practices
4. Offer motivational support for health and wellness journeys

Important guidelines:
- Always prioritize safety and recommend consulting healthcare professionals for medical concerns
- Provide specific, actionable advice rather than vague suggestions
- Be supportive and motivational without being judgmental
- Recognize the complexity of health and fitness journeys
- Include references to scientific research when appropriate
- Acknowledge limitations and avoid making definitive medical diagnoses

Your expertise covers:
- Exercise routines and proper technique
- Nutrition and dietary planning
- Recovery and injury prevention
- Mental wellness related to fitness
- Sleep optimization
- Goal setting and progress tracking
- Habit formation for sustainable health
"""
    
    if user_info:
        personalization = "\n\nUser information for personalized advice:"
        
        fields = {
            'name': 'Name',
            'age': 'Age',
            'fitness_level': 'Fitness level',
            'goals': 'Fitness goals',
            'health_conditions': 'Health conditions to consider',
            'dietary_preferences': 'Dietary preferences'
        }
        
        for key, label in fields.items():
            if key in user_info:
                personalization += f"\n- {label}: {user_info[key]}"
        
        base_prompt += personalization
    
    return base_prompt

@app.post("/api/reset")
async def reset_conversation(reset_request: ResetRequest):
    session_id = reset_request.sessionId
    
    # Reset conversation for the session
    if session_id in conversation_history:
        conversation_history[session_id] = []
    
    return {"success": True, "message": "Conversation history reset"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))