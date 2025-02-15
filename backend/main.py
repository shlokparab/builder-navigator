from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
from dotenv import load_dotenv

app = FastAPI()

# Load environment variables
load_dotenv()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

@app.get("/")
async def read_root():
    return {"message": "Hello World"}

@app.get("/chat/validate_idea")
async def validate_startup_idea(idea: str):
    try:
        prompt = f"""You are an AI startup advisor. Analyze this startup idea:
        
Idea: {idea}

Provide an analysis in the following format:

Analysis:
[Analyze the feasibility and uniqueness of the idea]

Market Potential:
[Evaluate market size, growth potential, and competition]

Challenges:
[Identify key challenges and potential roadblocks]

Recommendations:
[Provide actionable next steps and potential improvements]
"""

        response = model.generate_content(prompt)
        
        if not response.text:
            raise HTTPException(status_code=500, detail="Failed to generate response")
            
        return {"analysis": response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))