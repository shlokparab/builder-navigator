from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

# Load prompt from file
prompt = open("prompt.txt").read()

app = FastAPI()

# Load environment variables
load_dotenv()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*, http://localhost:8080"],  # Frontend URL
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
        response = chat.send_message(prompt + "User Query: " + idea)
        
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