from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import requests
import logging
import time
import pickle

# Load prompt from file
prompt = open("prompt.txt").read()

# Create a directory for storing chat history if it doesn't exist
HISTORY_DIR = "chat_history"
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

def save_chat_history(history):
    """Save chat history to a file"""
    try:
        with open(os.path.join(HISTORY_DIR, "latest_history.pkl"), "wb") as f:
            pickle.dump(history, f)
        logger.info("Successfully saved chat history")
    except Exception as e:
        logger.error(f"Failed to save chat history: {str(e)}")

def load_chat_history():
    """Load chat history from file"""
    try:
        history_path = os.path.join(HISTORY_DIR, "latest_history.pkl")
        if os.path.exists(history_path):
            with open(history_path, "rb") as f:
                return pickle.load(f)
    except Exception as e:
        logger.error(f"Failed to load chat history: {str(e)}")
    return None

app = FastAPI()

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:8080"],  # Frontend URL
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
# Store the most recent sufficient history
latest_sufficient_history = None

# Competitor search model configurations
competitor_generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

structured_competitor_generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}

# Initialize competitor search models
analysis_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=competitor_generation_config,
)

searchquery_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=competitor_generation_config,
)

competitorfinder_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=structured_competitor_generation_config,
)

@app.get("/")
async def hello_world():
    return {"message": "Hello World"}

@app.get("/validate_idea")
async def validate_startup_idea(idea: str):
    try:
        global chat, latest_sufficient_history
        
        logger.info(f"Processing idea validation request")
        
        # Using double curly braces to escape JSON formatting
        response = chat.send_message(prompt + "User Query: " + idea)
        
        if not response.text:
            logger.error("Empty response from model")
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
            if contemplator_end == -1:
                logger.error("Could not find contemplator tags in response")
                raise ValueError("Invalid response format: missing contemplator tags")
            contemplator_content = cleaned_response[contemplator_start:contemplator_end].strip()

            # Extract final answer content
            final_answer_start = cleaned_response.find('<final_answer>') + len('<final_answer>')
            final_answer_end = cleaned_response.find('</final_answer>')
            if final_answer_end == -1:
                logger.error("Could not find final_answer tags in response")
                raise ValueError("Invalid response format: missing final_answer tags")
            final_answer_text = cleaned_response[final_answer_start:final_answer_end].strip()

            # Clean and parse the final answer JSON
            final_answer_text = final_answer_text.replace('{{{{', '{').replace('}}}}', '}')
            
            try:
                # First try direct JSON parsing
                final_answer_json = json.loads(final_answer_text)
            except json.JSONDecodeError:
                logger.warning("Direct JSON parsing failed, attempting to extract JSON content")
                # If direct parsing fails, try to extract status and response using string manipulation
                try:
                    # Extract status
                    status_start = final_answer_text.find('"status":') + len('"status":')
                    if status_start == -1:
                        raise ValueError("Could not find status in response")
                    
                    # Find the next quote after status
                    status_content_start = final_answer_text.find('"', status_start)
                    status_content_end = final_answer_text.find('"', status_content_start + 1)
                    if status_content_start == -1 or status_content_end == -1:
                        # Try without quotes
                        status_end = final_answer_text.find(',', status_start)
                        if status_end == -1:
                            status_end = final_answer_text.find('\n', status_start)
                        if status_end == -1:
                            raise ValueError("Could not find end of status")
                        status = final_answer_text[status_start:status_end].strip()
                    else:
                        status = final_answer_text[status_content_start + 1:status_content_end].strip()
                    
                    # Extract response
                    response_start = final_answer_text.find('"response":') + len('"response":')
                    if response_start == -1:
                        raise ValueError("Could not find response in final answer")
                    
                    # Find the next quote after response
                    response_content_start = final_answer_text.find('"', response_start)
                    if response_content_start == -1:
                        # If no quotes, take everything after "response:" until the end or next field
                        response_content = final_answer_text[response_start:].strip()
                        # Remove trailing XML tags if present
                        if "</final_answer>" in response_content:
                            response_content = response_content[:response_content.find("</final_answer>")].strip()
                    else:
                        # Find matching end quote, handling escaped quotes
                        pos = response_content_start + 1
                        while pos < len(final_answer_text):
                            if final_answer_text[pos] == '"' and final_answer_text[pos-1] != '\\':
                                break
                            pos += 1
                        if pos >= len(final_answer_text):
                            raise ValueError("Could not find end of response content")
                        response_content = final_answer_text[response_content_start + 1:pos]
                    
                    final_answer_json = {
                        "status": status,
                        "response": response_content
                    }
                except Exception as e:
                    logger.error(f"Failed to extract JSON content: {str(e)}")
                    raise ValueError(f"Could not parse response content: {str(e)}")

            # Build result
            result = {
                "status": str(final_answer_json.get("status", "error")),
                "contemplator": contemplator_content,
                "result": final_answer_json.get("response", "No response generated")
            }

            # Store history if we have sufficient information before resetting
            if result["status"] == "sufficient_information":
                logger.info("Sufficient information received, storing chat history")
                latest_sufficient_history = chat.history.copy()
                # Save history to file
                save_chat_history(latest_sufficient_history)
                chat = model.start_chat(history=[])
            return result

        except Exception as parse_error:
            # Detailed error diagnostics
            logger.error(f"Parse error: {str(parse_error)}")
            error_info = {
                "error_type": type(parse_error).__name__,
                "message": str(parse_error),
                "raw_response": response.text
            }
            raise HTTPException(status_code=422, detail=error_info)
            
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market_analysis")
async def market_analysis():
    try:
        global latest_sufficient_history
        
        logger.info("Starting market analysis")
        
        # Try to load history from file if not in memory
        if not latest_sufficient_history:
            latest_sufficient_history = load_chat_history()
        
        # Check if we have stored sufficient history
        if not latest_sufficient_history:
            logger.error("No sufficient history available")
            raise HTTPException(
                status_code=400,
                detail="No sufficient conversation history available for analysis. Please complete the idea validation first."
            )
            
        # Convert history to text format
        try:
            conversation_messages = []
            for msg in latest_sufficient_history:
                # Safely extract message parts
                parts = getattr(msg, 'parts', [])
                if len(parts) >= 2:  # Ensure we have both user and assistant parts
                    user_text = parts[0].text if hasattr(parts[0], 'text') else str(parts[0])
                    assistant_text = parts[1].text if hasattr(parts[1], 'text') else str(parts[1])
                    conversation_messages.append(f"User: {user_text}\nAssistant: {assistant_text}")
                else:
                    # If message format is different, try to extract text safely
                    msg_text = str(msg)
                    conversation_messages.append(msg_text)
            
            conversation_text = "\n".join(conversation_messages)
            logger.info("Successfully processed conversation history")
        except Exception as e:
            logger.error(f"Failed to process conversation history: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to process conversation history: {str(e)}")
        
        # Analyze conversation to understand the business
        try:
            logger.info("Analyzing conversation")
            analysis = analysis_model.generate_content(f"Based on this conversation about a startup idea, analyze the core business concept and value proposition: {conversation_text}")
            if not analysis.text:
                logger.error("Empty analysis response")
                raise ValueError("Failed to analyze conversation")
            logger.info("Successfully generated analysis")
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to analyze conversation: {str(e)}")

        # Generate search queries
        try:
            logger.info("Generating search queries")
            queries = searchquery_model.generate_content(f"Company analysis: {analysis.text}")
            cleaned_queries = eval(queries.text.replace("```python", "").replace("```", "").strip())
            if not cleaned_queries or not isinstance(cleaned_queries, list):
                logger.error("Invalid search queries generated")
                raise ValueError("Failed to generate search queries")
            logger.info(f"Generated {len(cleaned_queries)} search queries")
        except Exception as e:
            logger.error(f"Query generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate search queries: {str(e)}")

        # Search for competitors
        setofresults = []
        try:
            logger.info("Starting competitor search")
            
            # Configure Bright Data API
            bright_data_url = "https://api.brightdata.com/request"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.getenv('BRIGHTDATA_API_KEY')}"
            }
            
            for i, q in enumerate(cleaned_queries):
                logger.info(f"Processing search query {i+1}/{len(cleaned_queries)}")
                
                try:
                    # Prepare the search URL and request body
                    encoded_query = requests.utils.quote(q)
                    search_url = f"https://www.google.com/search?q={encoded_query}"
                    
                    payload = {
                        "zone": "serp_api1",
                        "url": search_url,
                        "format": "raw"
                    }
                    
                    # Make request to Bright Data
                    response = requests.post(bright_data_url, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    # Check if response contains error
                    results = response.json()
                    if "error" in results:
                        logger.error(f"Bright Data API error: {results['error']}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"Search query {i+1} failed: {results['error']}"
                        )
                    
                    # Validate response structure
                    if "organic" not in results:
                        logger.error("Missing organic results in API response")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Invalid response format for query {i+1}"
                        )
                    
                    setofresults.append(results)
                    
                    # Add a small delay between requests to avoid rate limiting
                    time.sleep(1)
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request failed for query {i+1}: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to fetch results for query {i+1}: {str(e)}"
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse response for query {i+1}: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Invalid response format for query {i+1}"
                    )
            
            logger.info("Completed competitor search")
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to search competitors: {str(e)}")

        # Process results
        try:
            logger.info("Processing search results")
            processed_results = []
            for result in setofresults:
                try:
                    # Extract organic search results
                    organic_results = result.get("organic", [])[:20]
                    if not organic_results:
                        logger.warning("No organic results found in response")
                        continue
                        
                    record = []
                    
                    for entry in organic_results:
                        # Validate required fields
                        if not entry.get("title") or not entry.get("link"):
                            logger.warning("Skipping result with missing required fields")
                            continue
                            
                        result_data = {
                            "title": entry.get("title", ""),
                            "link": entry.get("link", ""),
                            "description": entry.get("description", ""),
                            "rank": entry.get("rank", 0),
                            "global_rank": entry.get("global_rank", 0)
                        }
                        
                        # Add image data if available and valid
                        if "image" in entry and entry["image"]:
                            result_data["image"] = entry.get("image", "")
                            result_data["image_alt"] = entry.get("image_alt", "")
                        
                        # Add display link if available
                        if "display_link" in entry and entry["display_link"]:
                            result_data["display_link"] = entry.get("display_link", "")
                            
                        record.append(result_data)
                    
                    # Only add metadata if we have actual results
                    if record:
                        # Add additional context data if available
                        if "general" in result:
                            record.append({
                                "search_metadata": {
                                    "total_results": result["general"].get("results_cnt", 0),
                                    "search_time": result["general"].get("search_time", 0),
                                    "location": result["general"].get("location", ""),
                                    "language": result["general"].get("language", "")
                                }
                            })
                        
                        processed_results.append(record)
                except Exception as e:
                    logger.error(f"Failed to process result: {str(e)}")
                    continue
                    
            if not processed_results:
                raise HTTPException(
                    status_code=500,
                    detail="No valid results could be processed from the search responses"
                )
                
            logger.info(f"Processed {len(processed_results)} result sets")
        except Exception as e:
            logger.error(f"Result processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to process search results: {str(e)}")

        # Find top competitors
        try:
            logger.info("Identifying top competitors")
            competitors = competitorfinder_model.generate_content(
                f"Company Data: {analysis.text}, Probable competitors: {processed_results}"
            )
            if not competitors.text:
                logger.error("Empty competitor analysis response")
                raise ValueError("Failed to identify competitors")
            top_competitors = json.loads(competitors.text)
            logger.info("Successfully identified top competitors")
        except Exception as e:
            logger.error(f"Competitor analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to identify top competitors: {str(e)}")

        # Generate complete analysis
        complete_analysis = f"""
Based on our analysis of your conversation history, we identified the following key aspects:

Business Analysis:
{analysis.text}

Key Search Terms:
{', '.join(cleaned_queries)}

Top Competitors Overview:
{json.dumps(top_competitors, indent=2)}

This analysis provides a comprehensive view of your business's market position and its main competitors.
"""
        logger.info("Market analysis completed successfully")
        return {
            "competitors": top_competitors,
            "analysis": complete_analysis
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in market analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/generate_mvp")
async def generate_mvp():
    try:
        global latest_sufficient_history
        
        logger.info("Starting MVP generation")
        
        # Try to load history from file if not in memory
        if not latest_sufficient_history:
            latest_sufficient_history = load_chat_history()
        
        # Check if we have stored sufficient history
        if not latest_sufficient_history:
            logger.error("No sufficient history available")
            raise HTTPException(
                status_code=400,
                detail="No sufficient conversation history available for MVP generation. Please complete the idea validation first."
            )
            
        # Convert history to text format
        try:
            conversation_messages = []
            for msg in latest_sufficient_history:
                parts = getattr(msg, 'parts', [])
                if len(parts) >= 2:
                    user_text = parts[0].text if hasattr(parts[0], 'text') else str(parts[0])
                    assistant_text = parts[1].text if hasattr(parts[1], 'text') else str(parts[1])
                    conversation_messages.append(f"User: {user_text}\nAssistant: {assistant_text}")
                else:
                    msg_text = str(msg)
                    conversation_messages.append(msg_text)
            
            conversation_text = "\n".join(conversation_messages)
            logger.info("Successfully processed conversation history")
        except Exception as e:
            logger.error(f"Failed to process conversation history: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to process conversation history: {str(e)}")

        # Initialize MVP generation model
        mvp_model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config={
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json"
            }
        )

        # Generate MVP recommendations
        try:
            logger.info("Generating MVP recommendations")
            mvp_prompt = f"""JSON MODE ON.
            Based on this startup idea conversation: {conversation_text}

            Generate a detailed MVP (Minimum Viable Product) recommendation that includes:
            1. Project type classification (SaaS, Hardware, Non-tech, etc.)
            2. For tech projects:
               - Recommended tech stack with justification
               - System architecture in Mermaid diagram format
               - If SaaS: One specific, non-trivial feature implementation example
            3. For non-tech projects:
               - Process flow in Mermaid diagram format
               - Specific, actionable implementation steps
            
            Focus on unique, insightful recommendations rather than common knowledge.
            ENSURE THIS IS A JSON RESPONSE IN THE FORMAT BELOW.
            Format the response as a JSON object with the following structure:
            {{
                "main_response": "Project Type: [Type of project]\\n\
                    Tech Stack: [List of technologies or 'Not applicable']\\n\
                    - Justification: [Reasoning for tech choices]\\n\
                    \\n\
                    Action Steps: [List of steps or 'Not applicable']\\n\
                    \\n\
                    Rationale: [Detailed explanation of recommendations]",
                "mermaid": {{
                    "system_architecture": "[Mermaid diagram or 'Not applicable']",
                    "process_flow": "[Mermaid diagram or 'Not applicable']"
                }},
                "code": "Specific feature example or 'Not applicable'"
            }}
            Note: this is the schema: 
            {{
                "main_response": "string",
                "mermaid": {{
                    "system_architecture": "string",
                    "process_flow": "string"
                }},
                "code": "string"
            }}
            """
            
            mvp_response = mvp_model.generate_content(mvp_prompt)
            if not mvp_response.text:
                logger.error("Empty MVP response")
                raise ValueError("Failed to generate MVP recommendations")
                
            logger.info("Successfully generated MVP response")
            
            # Parse the response as JSON
            try:
                mvp_json = json.loads(mvp_response.text)
                return mvp_json
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse MVP response as JSON: {str(e)}")
                raise ValueError("Invalid JSON response from MVP generation")

        except Exception as e:
            logger.error(f"MVP generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate MVP recommendations: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in MVP generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")