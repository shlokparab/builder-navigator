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

# Create a directory for storing audio files if it doesn't exist
AUDIO_DIR = "audio_files"
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

def save_chat_history(history):
    """Save chat history to a file"""
    try:
        logger.info(f"Attempting to save chat history. History type: {type(history)}, Length: {len(history) if history else 0}")
        history_path = os.path.join(HISTORY_DIR, "latest_history.pkl")
        logger.info(f"Saving to path: {history_path}")
        
        # Create directory if it doesn't exist
        if not os.path.exists(HISTORY_DIR):
            logger.info(f"Creating directory: {HISTORY_DIR}")
            os.makedirs(HISTORY_DIR)
        
        with open(history_path, "wb") as f:
            pickle.dump(history, f)
        logger.info(f"Successfully saved chat history to {history_path}")
    except Exception as e:
        logger.error(f"Failed to save chat history: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Current working directory: {os.getcwd()}")
        raise

def load_chat_history():
    """Load chat history from file"""
    try:
        history_path = os.path.join(HISTORY_DIR, "latest_history.pkl")
        logger.info(f"Attempting to load chat history from: {history_path}")
        
        if not os.path.exists(HISTORY_DIR):
            logger.error(f"Chat history directory does not exist: {HISTORY_DIR}")
            return None
            
        if not os.path.exists(history_path):
            logger.error(f"Chat history file does not exist: {history_path}")
            return None
            
        with open(history_path, "rb") as f:
            history = pickle.load(f)
            logger.info(f"Successfully loaded chat history. Type: {type(history)}, Length: {len(history) if history else 0}")
            return history
    except Exception as e:
        logger.error(f"Failed to load chat history: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Current working directory: {os.getcwd()}")
        return None

def save_serp_results(queries, results):
    """Save SERP results to a file"""
    try:
        logger.info(f"Attempting to save SERP results for {len(queries)} queries")
        serp_path = os.path.join(HISTORY_DIR, "latest_serp_results.pkl")
        
        # Create directory if it doesn't exist
        if not os.path.exists(HISTORY_DIR):
            logger.info(f"Creating directory: {HISTORY_DIR}")
            os.makedirs(HISTORY_DIR)
        
        # Save both queries and results to ensure we can validate later
        data = {
            "queries": queries,
            "results": results,
            "timestamp": time.time()
        }
        
        with open(serp_path, "wb") as f:
            pickle.dump(data, f)
        logger.info(f"Successfully saved SERP results to {serp_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save SERP results: {str(e)}")
        return False

def load_serp_results(current_queries):
    """Load SERP results if they exist"""
    try:
        serp_path = os.path.join(HISTORY_DIR, "latest_serp_results.pkl")
        
        if not os.path.exists(serp_path):
            logger.info("No cached SERP results found")
            return None
            
        with open(serp_path, "rb") as f:
            data = pickle.load(f)
            
        # Validate data structure
        if not isinstance(data, dict) or "queries" not in data or "results" not in data:
            logger.error("Invalid SERP results data structure")
            return None
            
        # Always return cached results if they exist
        logger.info("Using cached SERP results")
        return data["results"]
            
    except Exception as e:
        logger.error(f"Failed to load SERP results: {str(e)}")
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
                logger.info(f"Current chat history type: {type(chat.history)}, Length: {len(chat.history) if chat.history else 0}")
                latest_sufficient_history = chat.history.copy()
                logger.info(f"Copied history type: {type(latest_sufficient_history)}, Length: {len(latest_sufficient_history) if latest_sufficient_history else 0}")
                # Save history to file
                save_chat_history(latest_sufficient_history)
                chat = model.start_chat(history=[])

            # Log current chat history state
            logger.info("Current chat history state at end of validation:")
            logger.info(f"Chat history type: {type(chat.history)}")
            logger.info(f"Chat history length: {len(chat.history) if chat.history else 0}")
            if chat.history:
                for i, msg in enumerate(chat.history):
                    logger.info(f"Message {i + 1}:")
                    logger.info(f"  Parts: {len(msg.parts) if hasattr(msg, 'parts') else 'No parts'}")
                    if hasattr(msg, 'parts'):
                        for j, part in enumerate(msg.parts):
                            logger.info(f"    Part {j + 1}: {str(part)[:100]}...")

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
            analysis = analysis_model.generate_content(f"Based on this conversation about a startup idea, analyze the core business concept and value proposition: {conversation_text}.")
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
            queries = searchquery_model.generate_content(f"""
Based on this startup idea conversation and business analysis, generate EXACTLY 3 specific search queries that would help find direct competitors.
Format the response as a valid Python list of strings. For example: ["query 1", "query 2", "query 3"]

Conversation History:
{conversation_text}

Business Analysis:
{analysis.text}

Requirements:
1. Generate EXACTLY 3 queries, no more, no less
2. Each query should be specific and targeted to find direct competitors
3. Include the company's core business model/product type in each query
4. Format as a Python list of strings
5. DO NOT include generic terms like "best" or "top" alone
6. Each query should be 3-6 words long and highly specific
""")
            # Clean and parse the response
            query_text = queries.text.strip()
            logger.info(f"Raw query response: {query_text}")
            
            # Remove any code block markers
            query_text = query_text.replace("```python", "").replace("```", "").strip()
            logger.info(f"Cleaned query text: {query_text}")
            
            try:
                # First try direct eval of the list
                cleaned_queries = eval(query_text)
                logger.info(f"Successfully evaluated query text as list: {cleaned_queries}")
            except Exception as eval_error:
                logger.warning(f"Failed to eval query text: {str(eval_error)}")
                # If that fails, try to parse it manually
                query_text = query_text.replace("[", "").replace("]", "")
                cleaned_queries = [q.strip().strip('"\'') for q in query_text.split(",") if q.strip()]
                logger.info(f"Manually parsed queries: {cleaned_queries}")
            
            # Ensure exactly 3 queries
            if not cleaned_queries or not isinstance(cleaned_queries, list):
                logger.error("Invalid search queries generated")
                raise ValueError("Failed to generate valid search queries")
            
            # Take only first 3 queries if more were generated
            if len(cleaned_queries) > 3:
                logger.warning(f"More than 3 queries generated ({len(cleaned_queries)}), truncating to first 3")
                cleaned_queries = cleaned_queries[:3]
            
            # If less than 3 queries, add generic ones based on analysis
            if len(cleaned_queries) < 3:
                logger.warning(f"Less than 3 queries generated ({len(cleaned_queries)}), adding generic queries")
                while len(cleaned_queries) < 3:
                    generic_query = f"competitors {analysis.text[:50]}"
                    cleaned_queries.append(generic_query)
                    logger.info(f"Added generic query: {generic_query}")
            
            # Ensure all queries are strings and non-empty
            cleaned_queries = [str(q) for q in cleaned_queries if q]
            
            logger.info(f"Final search queries ({len(cleaned_queries)}):")
            for i, query in enumerate(cleaned_queries, 1):
                logger.info(f"Query {i}: {query}")
                
        except Exception as e:
            logger.error(f"Query generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate search queries: {str(e)}")

        # Search for competitors
        setofresults = []
        try:
            logger.info("Starting competitor search")
            
            for i, q in enumerate(cleaned_queries):
                logger.info(f"Executing search query {i+1}/{len(cleaned_queries)}: '{q}'")
                
                try:
                    params = {
                        "api_key": os.getenv("SERPAPI_KEY"),
                        "engine": "google",
                        "q": q,
                        "google_domain": "google.com",
                        "gl": "us",
                        "hl": "en",
                    }
                    logger.info(f"SERP API request parameters for query {i+1}: {params}")
                    
                    # Make request to SERPAPI
                    response = requests.get("https://serpapi.com/search", params=params)
                    response.raise_for_status()
                    
                    results = response.json()
                    logger.info(f"SERP API response received for query {i+1}")
                    
                    # Extract organic results
                    if "organic_results" in results:
                        organic = results["organic_results"][:20]  # Get top 20 results
                        logger.info(f"Found {len(organic)} organic results for query {i+1}")
                        
                        record = []
                        for j, entry in enumerate(organic, 1):
                            if entry.get("title") and entry.get("link"):
                                record.append({
                                    "title": entry["title"],
                                    "link": entry["link"],
                                    "snippet": entry.get("snippet", "")
                                })
                                logger.debug(f"Query {i+1}, Result {j}: {entry['title']}")
                                
                        if record:
                            setofresults.append(record)
                            logger.info(f"Successfully processed query {i+1} with {len(record)} valid results")
                        else:
                            logger.warning(f"No valid results found for query {i+1}")
                    else:
                        logger.warning(f"No organic results found for query {i+1}")
                    
                    # Add a small delay between requests
                    logger.info(f"Adding delay after query {i+1}")
                    time.sleep(1)
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request failed for query {i+1}: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error processing query {i+1}: {str(e)}")
                    continue
                
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to search competitors: {str(e)}")

        # Check if we got any valid results
        if not setofresults:
            raise HTTPException(
                status_code=500,
                detail="Failed to get any valid search results. Please try again."
            )
        
        # Flatten results for competitor analysis
        processed_results = []
        for result_set in setofresults:
            processed_results.extend(result_set)
        
        logger.info(f"Completed competitor search with {len(processed_results)} total results")

        # Find top competitors
        logger.info("Identifying top competitors")
        competitors = competitorfinder_model.generate_content(f"""
Based on the following business analysis and search results, identify the top 3-5 DIRECT competitors. 
Focus on companies that directly compete in the same space, not generic listings or articles.

Business Analysis:
{analysis.text}

Search Results:
{processed_results}

Requirements:
1. Return a JSON object with this exact structure:
{{
    "competitors": [
        {{
            "name": "Competitor Name",
            "description": "2-3 sentence description of how they compete",
            "differentiators": "Key ways they differ from the proposed business",
            "url": "Main company URL"
        }}
    ]
}}

2. Only include actual companies that are direct competitors
3. Skip any listicle sites, review sites, or general articles
4. For each competitor, verify they have a real web presence
5. Focus on companies with similar business models and target markets
6. DO NOT INCLUDE FLAVOUR TEXT. Do not say stuff like "The model has correctly identified the competitors" or anything like that. Do NOT mention the key search terms. Simply provide the core competitors. 
Now use these core competitors to give the startup strategic advice on company building and growth. 
Advise them on what they can do to set themselves apart from the competitors.
NOTE: PRETEND THE MODEL'S RESULTS WERE YOUR OWN RESULTS. YOU ARE TALKING TO THE FOUNDER OF THE STARTUP. YOU ARE SPEAKING FOR ALL DATA YOU HAVE
""")
        if not competitors.text:
            logger.error("Empty competitor analysis response")
            raise ValueError("Failed to identify competitors")
        top_competitors = json.loads(competitors.text)
        logger.info("Successfully identified top competitors")

        # Generate complete analysis
        complete_analysis = f"""
Market Assessment:
- Market Potential: {analysis.text}
- Competitive Landscape: High. Numerous players exist in this space. Differentiation through unique features and comprehensive solutions is crucial.

Direct Competitors:

1. {top_competitors.get('competitors', [])[0]['name']}
   {top_competitors.get('competitors', [])[0]['description']}
   Key Differentiators: {top_competitors.get('competitors', [])[0]['differentiators']}

2. {top_competitors.get('competitors', [])[1]['name']}
   {top_competitors.get('competitors', [])[1]['description']}
   Key Differentiators: {top_competitors.get('competitors', [])[1]['differentiators']}

3. {top_competitors.get('competitors', [])[2]['name']}
   {top_competitors.get('competitors', [])[2]['description']}
   Key Differentiators: {top_competitors.get('competitors', [])[2]['differentiators']}
"""
        logger.info("Market analysis completed successfully")
        return {
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
        logger.info(f"Initial latest_sufficient_history state: {type(latest_sufficient_history) if latest_sufficient_history else 'None'}")
        
        # Try to load history from file if not in memory
        if not latest_sufficient_history:
            logger.info("No history in memory, attempting to load from file")
            latest_sufficient_history = load_chat_history()
            logger.info(f"Loaded history state: {type(latest_sufficient_history) if latest_sufficient_history else 'None'}")
        
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

            For Mermaid diagrams, follow these strict rules:
1. Node Naming:
   - Use simple, consistent IDs (like A, B, C or user1, api2, db3)
   - Reference the same ID throughout the diagram
   - No spaces or special characters in IDs

2. Node Labels:
   - Place text descriptions in square brackets at the end of nodes: A[User Interface]
   - Never put brackets in the middle of text
   - Keep descriptions concise

3. Diagram Structure:
   - Always start with "graph LR" or "graph TD"
   - Use consistent indentation
   - Group related components using subgraph
   - End each subgraph properly

4. Styling:
   - Use white backgrounds
   - Use simple color codes (#fff, #f9f, etc.)
   - Keep styling consistent for similar components
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

@app.get("/validate_audio")
async def validate_audio_idea(audio_url: str):
    try:
        logger.info(f"Processing audio validation request for URL: {audio_url}")
        
        # Create a unique filename for the audio
        audio_filename = f"audio_{int(time.time())}.wav"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        
        # Download the audio file from Supabase
        try:
            response = requests.get(audio_url)
            response.raise_for_status()
            
            with open(audio_path, "wb") as f:
                f.write(response.content)
            logger.info(f"Successfully downloaded audio to {audio_path}")
        except Exception as e:
            logger.error(f"Failed to download audio: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to download audio: {str(e)}")
        
        try:
            # Upload the audio file to Gemini
            audio_file = genai.upload_file(audio_path, mime_type="audio/wav")
            logger.info(f"Successfully uploaded audio to Gemini")
            
            # First, get a transcription using a one-off request
            transcription_model = genai.GenerativeModel('gemini-2.0-flash')
            transcription_response = transcription_model.generate_content([
                "Please provide a precise, word-for-word transcription of this audio. Include only the transcription, no commentary or analysis.",
                audio_file
            ])
            
            if not transcription_response.text:
                logger.error("Empty transcription response")
                raise HTTPException(status_code=500, detail="Failed to transcribe audio")
                
            logger.info("Successfully transcribed audio")
            
            # Use the global chat instance with the transcription
            global chat, latest_sufficient_history
            
            # Send the transcription as if it were text input
            response = chat.send_message(prompt + "\nUser Query: " + transcription_response.text)
            
            if not response.text:
                logger.error("Empty response from model")
                raise HTTPException(status_code=500, detail="Failed to generate response")
            
            # Process the response similar to text validation
            try:
                # Clean response text
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
                    final_answer_json = json.loads(final_answer_text)
                except json.JSONDecodeError:
                    logger.warning("Direct JSON parsing failed, attempting to extract JSON content")
                    try:
                        # Extract status and response using string manipulation
                        status_start = final_answer_text.find('"status":') + len('"status":')
                        status_content_start = final_answer_text.find('"', status_start)
                        status_content_end = final_answer_text.find('"', status_content_start + 1)
                        if status_content_start == -1 or status_content_end == -1:
                            status_end = final_answer_text.find(',', status_start)
                            if status_end == -1:
                                status_end = final_answer_text.find('\n', status_start)
                            if status_end == -1:
                                raise ValueError("Could not find end of status")
                            status = final_answer_text[status_start:status_end].strip()
                        else:
                            status = final_answer_text[status_content_start + 1:status_content_end].strip()
                        
                        response_start = final_answer_text.find('"response":') + len('"response":')
                        response_content_start = final_answer_text.find('"', response_start)
                        if response_content_start == -1:
                            response_content = final_answer_text[response_start:].strip()
                            if "</final_answer>" in response_content:
                                response_content = response_content[:response_content.find("</final_answer>")].strip()
                        else:
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

                # Store history if we have sufficient information
                if result["status"] == "sufficient_information":
                    logger.info("Sufficient information received, storing chat history")
                    latest_sufficient_history = chat.history.copy()
                    save_chat_history(latest_sufficient_history)
                    chat = model.start_chat(history=[])
                
                return result

            except Exception as parse_error:
                logger.error(f"Parse error: {str(parse_error)}")
                error_info = {
                    "error_type": type(parse_error).__name__,
                    "message": str(parse_error),
                    "raw_response": response.text
                }
                raise HTTPException(status_code=422, detail=error_info)
                
        except Exception as e:
            logger.error(f"Gemini processing error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to process audio with Gemini: {str(e)}")
        finally:
            # Clean up audio file
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                    logger.info(f"Cleaned up audio file: {audio_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up audio file: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))