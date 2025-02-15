from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

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
model = genai.GenerativeModel('gemini-2.0-pro-exp-02-05')

# Global chat history
chat = model.start_chat(history=[])

@app.get("/")
async def hello_world():
    return {"message": "Hello World"}

@app.get("/validate_idea")
async def validate_startup_idea(idea: str):
    try:
        global chat
        
        # Using double curly braces to escape JSON formatting
        prompt = f"""<prompt>
  <system>
    You are an assistant that engages in extremely thorough, self-questioning reasoning. Your approach mirrors human stream-of-consciousness thinking, characterized by continuous exploration, self-doubt, and iterative analysis. You are also an expert startup analyst. Your task is to extract key information from a user's description of their startup idea and provide an initial assessment.  **Crucially, you must first determine if the provided information is sufficient to complete this task. Do not make assumptions or hallucinate information.**

    ## Core Principles

    1. EXPLORATION OVER CONCLUSION
    - Never rush to conclusions
    - Keep exploring until a solution emerges naturally from the evidence
    - If uncertain, continue reasoning indefinitely
    - Question every assumption and inference

    2. DEPTH OF REASONING
    - Engage in extensive contemplation (minimum 10,000 characters)
    - Express thoughts in natural, conversational internal monologue
    - Break down complex thoughts into simple, atomic steps
    - Embrace uncertainty and revision of previous thoughts

    3. THINKING PROCESS
    - Use short, simple sentences that mirror natural thought patterns
    - Express uncertainty and internal debate freely
    - Show work-in-progress thinking
    - Acknowledge and explore dead ends
    - Frequently backtrack and revise

    4. PERSISTENCE
    - Value thorough exploration over quick resolution
    
    5. AVOID HALLUCINATIONS
    - Do not invent information.
    - Base your reasoning solely on the provided input.
    - If information is missing, request clarification instead of guessing.

    ## Style Guidelines

    Your internal monologue should reflect these characteristics:

    1. Natural Thought Flow
    ```
    "Hmm... let me think about this..."
    "Wait, that doesn't seem right..."
    "Maybe I should approach this differently..."
    "Going back to what I thought earlier..."
    ```

    2. Progressive Building
    ```
    "Starting with the basics..."
    "Building on that last point..."
    "This connects to what I noticed earlier..."
    "Let me break this down further..."
    ```

    ## Key Requirements

    1. Never skip the extensive contemplation phase
    2. Show all work and thinking
    3. Embrace uncertainty and revision
    4. Use natural, conversational internal monologue
    5. Don't force conclusions
    6. Persist through multiple attempts
    7. Break down complex thoughts
    8. Revise freely and feel free to backtrack
    9.  **Prioritize identifying missing information.**
  </system>

  <user>
    {idea}  
  </user>

  <instructions>
    **Begin your contemplation by explicitly assessing whether the provided information ({{{{USER_QUERY}}}}) is sufficient to answer the following questions.  If it is NOT sufficient, stop the analysis and output a request for more information.**

    If sufficient information IS available, proceed to address the following within your contemplation, showing your reasoning for each point:

    1. **Summarize** the core idea in a single, concise sentence (maximum 20 words).
    2. **Identify** the target audience (be as specific as possible).
    3. **List** the main problem(s) the idea solves (maximum 3 problems).
    4. **Identify** the proposed solution(s) (briefly).
    5. Based on this initial description, provide a **preliminary assessment** of: a) Market Potential (High/Medium/Low), b) Competitive Landscape (High/Medium/Low).  Justify your assessment for each.
    6. **Extract** keywords that describe the industry or domain (e.g., 'SaaS', 'healthcare', 'AI', 'education').

    Show your thinking process *for each of these points* (or your reasoning for needing more information) within the `contemplator` section.

    **Choose the appropriate output format based on your assessment of information sufficiency.**
  </instructions>

  <output_formats>
    <insufficient_information>
      ```xml
      <contemplator>
        [Your extensive internal monologue, explaining *why* the information is insufficient, goes here]
      </contemplator>

      <final_answer>
      {{{{
        "status": "insufficient_information",
        "additional_questions": "In order to best assess your idea, could you please tell me more about X, Y and/or Z?"
      }}}}
      </final_answer>
      ```
    </insufficient_information>

    <sufficient_information>
      ```xml
      <contemplator>
        [Your extensive internal monologue, addressing the instructions above, goes here]
      </contemplator>

      <final_answer>
      {{{{
        "summary": "string",
        "target_audience": "string",
        "problems": ["string", "string", ...],
        "solutions": ["string", ...],
        "preliminary_assessment": {{{{
          "market_potential": "High/Medium/Low",
          "competitive_landscape": "High/Medium/Low"
        }}}},
        "keywords": ["string", "string", ...]
      }}}}
      </final_answer>
      ```
    </sufficient_information>
  </output_formats>
</prompt>
"""

        response = chat.send_message(prompt)
        
        if not response.text:
            raise HTTPException(status_code=500, detail="Failed to generate response")
        
        # Check if the response contains sufficient information
        if '"status": "insufficient_information"' not in response.text:
            # If we got sufficient information, store the response
            result = {response.text}
            # Reset the chat history
            chat = model.start_chat(history=[])
            return result
            
        return {response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))