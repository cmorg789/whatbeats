import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the LLM service
from app.llm_service import query_llm

async def test_llm_logging():
    """Test the LLM logging functionality."""
    print("Testing LLM logging functionality...")
    
    # Make a test query to the LLM
    try:
        # Import the necessary modules to access the raw response
        import httpx
        import os
        from app.llm_service import LLM_API_KEY, LLM_API_URL, LLM_MODEL, TIMEOUT
        
        # Construct the prompt
        prompt = f"""
You are judging a game of "What Beats What".
Given the following comparison:
- Current item: rock
- User's suggestion: paper

Determine if the user's suggestion beats the current item.
Respond in the following JSON format:
{{
  "result": true/false,
  "description": "Brief explanation (<30 words)",
  "emoji": "Single relevant emoji"
}}
"""
        
        # Prepare the API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}"
        }
        
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that judges a game of 'What Beats What'."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 150
        }
        
        # Make the request directly
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                LLM_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            response_data = response.json()
            content = response_data["choices"][0]["message"]["content"]
            
            print(f"Raw LLM response content: {content}")
            
            # Now call the query_llm function
            result, description, emoji = await query_llm("rock", "paper")
            print(f"LLM Response: result={result}, description='{description}', emoji='{emoji}'")
            print("Check the logs directory for the log file.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_llm_logging())