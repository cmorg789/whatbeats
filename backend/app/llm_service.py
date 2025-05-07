import os
import json
import httpx
import logging
import pathlib
import re
import copy
from typing import Dict, Any, Tuple, Optional, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get project root directory (3 levels up from this file)
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.absolute()

# LLM API settings
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_API_URL = os.getenv("LLM_API_URL", "https://openrouter.ai/api/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-3.5-turbo")

# Timeout for API requests (in seconds)
TIMEOUT = 30.0

# Logging configuration
LOGGING_ENABLED = os.getenv("LLM_LOGGING_ENABLED", "true").lower() == "true"
LOG_LEVEL = os.getenv("LLM_LOG_LEVEL", "INFO")
LOG_DIR = os.path.join(PROJECT_ROOT, os.getenv("LLM_LOG_DIR", "logs"))
LOG_FILE = os.getenv("LLM_LOG_FILE", "llm_responses.log")

# Set up logger
logger = logging.getLogger("llm_service")

# Configure logging if enabled
if LOGGING_ENABLED:
    # Create logs directory if it doesn't exist
    log_path = pathlib.Path(LOG_DIR)
    log_path.mkdir(exist_ok=True)
    
    # Set log level
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Create file handler
    file_handler = logging.FileHandler(os.path.join(LOG_DIR, LOG_FILE))
    file_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    logger.info("LLM logging initialized")
else:
    # Set up null handler if logging is disabled
    logger.addHandler(logging.NullHandler())


def sanitize_for_prompt(text: str) -> str:
    """
    Sanitize text before including it in an LLM prompt.
    
    This function removes characters that could interfere with prompt structure
    or enable prompt injection attacks.
    
    Args:
        text: The text to sanitize
        
    Returns:
        Sanitized text safe for inclusion in prompts
    """
    # Normalize input
    text = text.lower().strip()
    
    # Remove characters that could interfere with prompt structure
    sanitized = re.sub(r'["`\'\\]', '', text)
    
    # Remove any potential XML/HTML-like tags that could be used for prompt injection
    sanitized = re.sub(r'<[^>]*>', '', sanitized)
    
    return sanitized

def sanitize_for_logs(data: Any) -> Any:
    """
    Sanitize data before logging to prevent sensitive information exposure.
    
    This function creates a deep copy of the data and removes or redacts sensitive
    information like API keys, authorization headers, and other potentially
    sensitive fields.
    
    Args:
        data: The data to sanitize (any type)
        
    Returns:
        Sanitized copy of the data (same type as input)
    """
    # Return non-dict/list values unchanged
    if not isinstance(data, (dict, list)):
        return data
    
    # Create a deep copy to avoid modifying the original
    sanitized = copy.deepcopy(data)
    
    if isinstance(sanitized, dict):
        # Redact sensitive fields in dictionaries
        for key in sanitized:
            # Redact API keys and authorization headers
            if key.lower() in ('authorization', 'api_key', 'api-key', 'apikey', 'key', 'token', 'secret'):
                if isinstance(sanitized[key], str):
                    # Keep the first few characters and redact the rest
                    if len(sanitized[key]) > 8:
                        sanitized[key] = sanitized[key][:4] + '****' + sanitized[key][-4:]
                    else:
                        sanitized[key] = '********'
            # Recursively sanitize nested structures
            elif isinstance(sanitized[key], (dict, list)):
                sanitized[key] = sanitize_for_logs(sanitized[key])
    
    elif isinstance(sanitized, list):
        # Recursively sanitize list items
        for i, item in enumerate(sanitized):
            sanitized[i] = sanitize_for_logs(item)
    
    return sanitized

async def query_llm(current_item: str, user_input: str) -> Tuple[bool, str, str]:
    """
    Query the LLM to determine if user_input beats current_item.
    
    This function sends a request to the LLM API (OpenRouter/OpenAI) with a prompt
    asking if the user's input beats the current item. It uses OpenRouter's structured
    output feature with JSON schema validation to ensure consistent response formatting.
    The function parses the JSON response to extract the result (true/false), a
    description of why, and a relevant emoji.
    
    Args:
        current_item: The current item in the game
        user_input: The user's input for what beats the current item
        
    Returns:
        Tuple of (result: bool, description: str, emoji: str)
        
    Raises:
        ValueError: If the LLM_API_KEY environment variable is not set
        httpx.RequestError: If there's an error communicating with the API
        httpx.HTTPStatusError: If the API returns an error status code
        json.JSONDecodeError: If the response cannot be parsed as JSON despite schema validation
    """
    if not LLM_API_KEY:
        raise ValueError("LLM_API_KEY environment variable is not set")
    
    # Sanitize inputs before including in prompt
    safe_current_item = sanitize_for_prompt(current_item)
    safe_user_input = sanitize_for_prompt(user_input)
    
    # Construct the prompt with clear boundaries using XML-like tags
    prompt = f"""
You are judging a game of "What Beats What" where items compete based on their real-world properties and interactions.

Given the following comparison:
<current_item>{safe_current_item}</current_item>
<user_input>{safe_user_input}</user_input>

Determine if the user's suggestion beats the current item by considering the following, evaluated in the order presented. Rules from higher categories override lower ones:

    ESTABLISHED GAME RELATIONSHIPS - These are definitive and must be respected:
        Rock-Paper-Scissors rules: Paper beats rock, rock beats scissors, scissors beats paper
        Rock-Paper-Scissors-Lizard-Spock extensions: Lizard beats paper and Spock, Spock beats rock and scissors
        Card game hierarchies: Ace beats King, King beats Queen, etc.
        Chess piece values: Queen beats Rook, Rook beats Bishop/Knight, etc.

    PHYSICAL PROPERTIES:
        State of matter: Gas can disperse liquids, liquids can dissolve solids
        Temperature: Hot items melt cold items, extreme cold freezes liquids
        Hardness: Diamond scratches glass, metal dents wood
        Sharpness: Knife cuts rope, scissors cut paper

    CHEMICAL REACTIONS:
        Water dissolves salt/sugar, acid corrodes metal
        Fire burns paper/wood, water extinguishes fire
        Rust degrades iron, bleach removes color

    TEMPORAL/PROCESS RELATIONSHIPS:
        For time-based interactions, the later stage generally beats the earlier stage
        Example: Butterfly beats caterpillar, adult beats child, cooked food beats raw ingredients
        The more evolved or processed form typically wins

    DEFINITIVE JUDGMENT CRITERIA:
        The relationship must be DIRECT and INEVITABLE when the items interact (e.g., a 'Seed' doesn't directly beat 'Barren Land' just because it could grow there with water and time; the interaction isn't immediate or guaranteed upon contact without external factors).
        The winning item must cause a significant, irreversible change or neutralization of the other.
        An item cannot beat an identical item unless a Temporal/Process Relationship applies.
        If the interaction is UNCERTAIN, REVERSIBLE, has NO significant effect, or requires specific unstated circumstances, the challenger LOSES.
        When in doubt, consider what would happen if these items physically encountered each other.
        **LAST RESORT FOR ABSTRACTS: If one or both items are primarily philosophical/abstract AND no other rule above yields a clear winner or loser, you MAY consider if one concept is broadly considered more foundational or encompassing. If still indeterminate, and only in this specific scenario, a playfully creative or humorous interpretation that favors one item decisively (explaining the humorous logic) can be used. If no such interpretation is readily apparent, the challenger loses.**

Your response will be automatically formatted as JSON with the following fields:

    result: A boolean indicating if the user's suggestion beats the current item
    description: A brief explanation (<30 words) of why the result is true or false. Make it creative and slightly goofy. Don't use the word "literally."
    emoji: A single relevant emoji that represents the outcome. Do NOT use the cross mark emoji except on failures (❌)!
"""
    
    # Prepare the API request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }
    
    # Define JSON schema for structured output
    json_schema = {
        "type": "object",
        "properties": {
            "result": {
                "type": "boolean",
                "description": "Whether the user's suggestion beats the current item"
            },
            "description": {
                "type": "string",
                "description": "Brief explanation of why the result is true or false (<30 words)"
            },
            "emoji": {
                "type": "string",
                "description": "Single relevant emoji that represents the outcome"
            }
        },
        "required": ["result", "description", "emoji"],
        "additionalProperties": False
    }
    
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "You are a creative and logical judge for the game 'What Beats What'. You evaluate items based on their real-world properties and how they would naturally interact with each other. Your judgments should be based on realistic physics, chemistry, and natural laws, while still allowing for creative thinking."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 150,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "whatbeats_judgment",
                "strict": True,
                "schema": json_schema
            }
        }
    }
    
    try:
        if LOGGING_ENABLED:
            logger.info(f"Querying LLM for comparison: '{current_item}' vs '{user_input}'")
            # Sanitize the payload before logging
            sanitized_payload = sanitize_for_logs(payload)
            logger.info(f"Request payload: {json.dumps(sanitized_payload, indent=2)}")
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                LLM_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            response_data = response.json()
            content = response_data["choices"][0]["message"]["content"]
            
            if LOGGING_ENABLED:
                logger.info(f"Received LLM response for '{current_item}' vs '{user_input}'")
                # Sanitize the response data before logging
                sanitized_response = sanitize_for_logs(response_data)
                logger.info(f"Raw LLM response: {json.dumps(sanitized_response, indent=2)}")
                logger.info(f"Raw LLM content: {content}")
            
            # Parse the JSON response
            try:
                # Extract and clean JSON from the LLM response
                parsed_content = extract_json_from_llm_response(content, logger if LOGGING_ENABLED else None)
                result = parsed_content.get("result", False)
                description = parsed_content.get("description", "No explanation provided")
                emoji = parsed_content.get("emoji", "❓")
                
                # Validate the response
                if not isinstance(result, bool):
                    result = False
                
                # Remove the 100-character limit truncation to allow full descriptions
                # The LLM is already instructed to keep descriptions brief (<30 words)
                
                if len(emoji) > 2:  # Take only the first emoji if multiple
                    emoji = emoji[0]
                
                if LOGGING_ENABLED:
                    logger.info(f"Parsed LLM response: result={result}, description='{description}', emoji='{emoji}'")
                
                return result, description, emoji
                
            except json.JSONDecodeError:
                # Fallback if the response is not valid JSON
                if LOGGING_ENABLED:
                    logger.error(f"Failed to parse LLM response as JSON: {content}")
                return False, "Could not determine the outcome", "❓"
            except Exception as e:
                # Handle any other exceptions that might occur during parsing
                if LOGGING_ENABLED:
                    logger.error(f"Error parsing LLM response: {str(e)}, content: {content}")
                return False, "Error processing the response", "❓"
    
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        # Log the error
        error_msg = f"Error querying LLM: {str(e)}"
        if LOGGING_ENABLED:
            logger.error(error_msg)
        else:
            print(error_msg)
        return False, "Error communicating with the judgment system", "❌"


def extract_json_from_llm_response(content: str, logger=None) -> Dict[str, Any]:
    """
    Extract and clean JSON from various formats of LLM responses.
    
    This function handles different response formats and cleans the content
    to extract valid JSON, including:
    - Direct JSON responses
    - JSON within markdown code blocks
    - JSON with extra non-JSON characters (like "**" at the beginning)
    - JSON with leading/trailing whitespace or newlines
    
    Args:
        content: The raw content from the LLM response
        logger: Optional logger for debugging
        
    Returns:
        Parsed JSON as a dictionary
        
    Raises:
        json.JSONDecodeError: If no valid JSON can be extracted
    """
    if not content or not content.strip():
        if logger:
            logger.warning("Empty content received from LLM")
        raise json.JSONDecodeError("Empty content", "", 0)
    
    # First try: direct parsing (handles clean JSON responses)
    try:
        parsed_content = json.loads(content)
        if logger:
            logger.debug(f"Successfully parsed JSON directly: {parsed_content}")
        return parsed_content
    except json.JSONDecodeError:
        if logger:
            logger.debug(f"Direct JSON parsing failed, trying cleanup methods")
    
    # Second try: clean the content and try again
    # Remove common non-JSON prefixes/suffixes
    cleaned_content = content.strip()
    
    # Handle markdown code blocks
    if "```json" in cleaned_content and "```" in cleaned_content:
        start_idx = cleaned_content.find("```json") + 7
        end_idx = cleaned_content.rfind("```")
        if start_idx < end_idx:
            cleaned_content = cleaned_content[start_idx:end_idx].strip()
            if logger:
                logger.debug(f"Extracted JSON from markdown code block: {cleaned_content}")
    
    # Handle other markdown code blocks without language specification
    elif cleaned_content.startswith("```") and "```" in cleaned_content[3:]:
        start_idx = cleaned_content.find("```") + 3
        end_idx = cleaned_content.rfind("```")
        if start_idx < end_idx:
            cleaned_content = cleaned_content[start_idx:end_idx].strip()
            if logger:
                logger.debug(f"Extracted JSON from generic markdown code block: {cleaned_content}")
    
    # Try to find JSON object pattern in the content
    import re
    json_pattern = r'(\{[\s\S]*\})'
    json_matches = re.search(json_pattern, cleaned_content)
    
    if json_matches:
        potential_json = json_matches.group(1)
        try:
            parsed_content = json.loads(potential_json)
            if logger:
                logger.debug(f"Successfully extracted JSON using regex: {parsed_content}")
            return parsed_content
        except json.JSONDecodeError:
            if logger:
                logger.debug(f"Regex-extracted content is not valid JSON: {potential_json}")
    
    # Last attempt: try to parse the cleaned content directly
    try:
        # Remove any non-JSON characters at the beginning (like "**")
        # Find the first '{' character
        first_brace_idx = cleaned_content.find('{')
        if first_brace_idx > 0:
            if logger:
                logger.debug(f"Removing {first_brace_idx} characters from the beginning: '{cleaned_content[:first_brace_idx]}'")
            cleaned_content = cleaned_content[first_brace_idx:]
        
        parsed_content = json.loads(cleaned_content)
        if logger:
            logger.debug(f"Successfully parsed JSON after cleaning: {parsed_content}")
        return parsed_content
    except json.JSONDecodeError as e:
        if logger:
            logger.error(f"All JSON extraction methods failed: {str(e)}")
        raise
    

async def determine_comparison(current_item: str, user_input: str) -> Dict[str, Any]:
    """
    Determine if user_input beats current_item and format the response.
    
    This is a wrapper function that normalizes the inputs, calls query_llm,
    and formats the response as a dictionary. The underlying LLM query uses
    structured output with JSON schema validation to ensure consistent formatting.
    
    Args:
        current_item: The current item in the game
        user_input: The user's input for what beats the current item
        
    Returns:
        Dictionary with result, description, and emoji
    """
    # Normalize inputs (lowercase, strip whitespace)
    current_item = current_item.lower().strip()
    user_input = user_input.lower().strip()
    
    # Query the LLM
    result, description, emoji = await query_llm(current_item, user_input)
    
    return {
        "result": result,
        "description": description,
        "emoji": emoji
    }


async def generate_count_range_description(range_start: int, range_end: Optional[int] = None) -> Tuple[str, str]:
    """
    Generate a description and emoji for a count range using the LLM.
    
    This function sends a request to the LLM API to generate a creative description
    and emoji for a specific count range. It's used to create engaging feedback
    for users based on how frequently a comparison has been made.
    
    Args:
        range_start: Start of the count range (inclusive)
        range_end: End of the count range (inclusive, None for open-ended)
        
    Returns:
        Tuple of (description: str, emoji: str)
        
    Raises:
        ValueError: If the LLM_API_KEY environment variable is not set
        httpx.RequestError: If there's an error communicating with the API
        httpx.HTTPStatusError: If the API returns an error status code
        json.JSONDecodeError: If the response cannot be parsed as JSON
    """
    if not LLM_API_KEY:
        raise ValueError("LLM_API_KEY environment variable is not set")
    
    # Construct the range text
    if range_end is None:
        range_text = f"{range_start}+"
    else:
        range_text = f"{range_start}-{range_end}"
    
    # Sanitize the range text (although it's already numeric, this is for consistency)
    safe_range_text = sanitize_for_prompt(range_text)
    
    # Construct the prompt with clear boundaries using XML-like tags
    prompt = f"""
Generate a creative and slightly humorous description and emoji for a comparison that has been used <count_range>{safe_range_text}</count_range> times in a game.

The description should:
1. Be brief (under 20 words)
2. Be engaging and fun
3. Reflect the popularity/frequency of the comparison
4. Not use the word "literally"

The emoji should:
1. Be a single emoji that represents the frequency/popularity
2. Match the tone of the description
3. Be visually distinct from other frequency ranges

Your response will be automatically formatted as JSON with the following fields:
- description: A brief, creative description for this usage frequency
- emoji: A single relevant emoji that represents the frequency
"""
    
    # Prepare the API request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }
    
    # Define JSON schema for structured output
    json_schema = {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "Brief, creative description for this usage frequency (<20 words)"
            },
            "emoji": {
                "type": "string",
                "description": "Single relevant emoji that represents the frequency"
            }
        },
        "required": ["description", "emoji"],
        "additionalProperties": False
    }
    
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "You are a creative writer who generates engaging descriptions and emojis for game statistics."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 100,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "count_range_description",
                "strict": True,
                "schema": json_schema
            }
        }
    }
    
    try:
        if LOGGING_ENABLED:
            logger.info(f"Querying LLM for count range description: '{range_text}'")
            # Sanitize the payload before logging
            sanitized_payload = sanitize_for_logs(payload)
            logger.info(f"Request payload: {json.dumps(sanitized_payload, indent=2)}")
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                LLM_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            response_data = response.json()
            content = response_data["choices"][0]["message"]["content"]
            
            if LOGGING_ENABLED:
                logger.info(f"Received LLM response for count range '{range_text}'")
                # Sanitize the response data before logging
                sanitized_response = sanitize_for_logs(response_data)
                logger.info(f"Raw LLM response: {json.dumps(sanitized_response, indent=2)}")
                logger.info(f"Raw LLM content: {content}")
            
            # Parse the JSON response
            try:
                # Extract and clean JSON from the LLM response
                parsed_content = extract_json_from_llm_response(content, logger if LOGGING_ENABLED else None)
                description = parsed_content.get("description", "This comparison is getting popular!")
                emoji = parsed_content.get("emoji", "🔄")
                
                # Validate the response
                # Remove the 50-character limit truncation to allow full descriptions
                # The LLM is already instructed to keep descriptions brief (<20 words)
                
                if len(emoji) > 2:  # Take only the first emoji if multiple
                    emoji = emoji[0]
                
                if LOGGING_ENABLED:
                    logger.info(f"Parsed LLM response: description='{description}', emoji='{emoji}'")
                
                return description, emoji
                
            except json.JSONDecodeError:
                # Fallback if the response is not valid JSON
                if LOGGING_ENABLED:
                    logger.error(f"Failed to parse LLM response as JSON: {content}")
                return "This comparison is getting popular!", "🔄"
            except Exception as e:
                # Handle any other exceptions that might occur during parsing
                if LOGGING_ENABLED:
                    logger.error(f"Error parsing LLM response: {str(e)}, content: {content}")
                return "This comparison is getting popular!", "🔄"
    
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        # Log the error
        error_msg = f"Error querying LLM for count range: {str(e)}"
        if LOGGING_ENABLED:
            logger.error(error_msg)
        else:
            print(error_msg)
        return "This comparison is getting popular!", "🔄"