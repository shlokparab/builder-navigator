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
    allow_origins=["*"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

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
        "response": "In order to best assess your idea, could you please tell me more about X, Y and/or Z?"
      }}}}
      </final_answer>
      ```
    </insufficient_information>

    <sufficient_information>
      ```xml
      "status": "sufficient_information",
        "response": "Based on my analysis, here is my evaluation of your startup idea:

Summary: [20 word summary of the core idea]

Target Audience: [Detailed description of specific target users/customers]

Key Problems Addressed:
- [Problem 1]
- [Problem 2]
- [Problem 3]

Proposed Solutions:
[Description of how the idea solves the identified problems]

Market Assessment:
- Market Potential: [High/Medium/Low]
[Justification for market potential rating]

- Competitive Landscape: [High/Medium/Low] 
[Justification for competitive landscape rating]

Industry Keywords: [relevant industry/domain terms]"
      </final_answer>
      ```
    </sufficient_information>
  </output_formats>
</prompt>
"""
        response = chat.send_message(prompt)
        
        if not response.text:
            raise HTTPException(status_code=500, detail="Failed to generate response")

        try:
            # Clean response text by removing code block markers and XML tags
            cleaned_response = response.text.strip()
            
            # Remove XML code block markers if present
            if cleaned_response.startswith('```xml'):
                cleaned_response = cleaned_response[6:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Extract contemplator content
            contemplator_start = cleaned_response.find('<contemplator>') + len('<contemplator>')
            contemplator_end = cleaned_response.find('</contemplator>')
            contemplator_content = cleaned_response[contemplator_start:contemplator_end].strip()

            # Extract final answer content
            final_answer_start = cleaned_response.find('<final_answer>') + len('<final_answer>')
            final_answer_end = cleaned_response.find('</final_answer>')
            final_answer_text = cleaned_response[final_answer_start:final_answer_end].strip()

            # Clean and parse the final answer JSON
            final_answer_text = final_answer_text.replace('{{{{', '{').replace('}}}}', '}')
            
            try:
                # First try direct JSON parsing
                final_answer_json = json.loads(final_answer_text)
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON content
                json_start = final_answer_text.find('{')
                json_end = final_answer_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > 0:
                    final_answer_text = final_answer_text[json_start:json_end]
                    
                    # Handle both cases with more robust parsing
                    if '"status":' in final_answer_text:
                        # Extract status
                        status_start = final_answer_text.find('"status":') + len('"status":')
                        status_end = final_answer_text.find(',', status_start)
                        status = final_answer_text[status_start:status_end].strip().strip('"')
                        
                        # Extract response
                        response_start = final_answer_text.find('"response":') + len('"response":')
                        response_end = final_answer_text.rfind('"', response_start + 1) + 1
                        response_content = final_answer_text[response_start:response_end].strip()
                        
                        # Handle different response formats
                        if response_content.startswith('"') and response_content.endswith('"'):
                            response_content = response_content[1:-1]
                            
                        final_answer_json = {
                            "status": status,
                            "response": response_content
                        }
                    else:
                        raise ValueError("Could not find status in final answer")
                else:
                    raise ValueError("Could not find valid JSON in final answer")

            # Build result
            result = {
                "status": str(final_answer_json.get("status", "error")),
                "contemplator": contemplator_content,
                "result": final_answer_json.get("response", "No response generated")
            }

            # Only reset chat history if we have sufficient information
            if result["status"] == "sufficient_information":
                chat = model.start_chat(history=[])
            return result

        except Exception as parse_error:
            # Detailed error diagnostics
            error_info = {
                "error_type": type(parse_error).__name__,
                "message": str(parse_error),
                "raw_response": response.text[:300] + "..." if len(response.text) > 300 else response.text
            }
            raise HTTPException(status_code=422, detail=error_info)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))