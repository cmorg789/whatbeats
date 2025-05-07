import asyncio
import json
import logging
import sys
from unittest.mock import patch, AsyncMock
from app.llm_service import query_llm, LOGGING_ENABLED

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_llm_service")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Mock response with the problematic "**" prefix
mock_response_with_prefix = {
    "choices": [
        {
            "message": {
                "content": "**\n{\n    \"result\": true,\n    \"description\": \"A hammer can break a rock due to its force and hardness.\",\n    \"emoji\": \"🔨\"\n}"
            }
        }
    ]
}

# Mock response with markdown code block
mock_response_with_markdown = {
    "choices": [
        {
            "message": {
                "content": "```json\n{\n  \"result\": false,\n  \"description\": \"Water does not beat paper in the game.\",\n  \"emoji\": \"❌\"\n}\n```"
            }
        }
    ]
}

# Clean response
mock_clean_response = {
    "choices": [
        {
            "message": {
                "content": "{\n  \"result\": true,\n  \"description\": \"Fire burns paper.\",\n  \"emoji\": \"🔥\"\n}"
            }
        }
    ]
}

async def test_query_llm():
    print("\n=== Testing query_llm with problematic responses ===")
    
    # Test with "**" prefix
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        # Set up the mock response
        mock_response = AsyncMock()
        # Make json() return a coroutine that returns our mock data
        mock_response.json = AsyncMock(return_value=mock_response_with_prefix)
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response
        
        print("\n--- Testing with '**' prefix ---")
        result, description, emoji = await query_llm("rock", "hammer")
        print(f"Result: {result}, Description: '{description}', Emoji: '{emoji}'")
        assert result == True, "Expected result to be True"
        assert "hammer" in description.lower(), "Expected description to mention hammer"
        assert emoji == "🔨", "Expected hammer emoji"
        print("✅ Test passed!")
    
    # Test with markdown code block
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        # Set up the mock response
        mock_response = AsyncMock()
        # Make json() return a coroutine that returns our mock data
        mock_response.json = AsyncMock(return_value=mock_response_with_markdown)
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response
        
        print("\n--- Testing with markdown code block ---")
        result, description, emoji = await query_llm("paper", "water")
        print(f"Result: {result}, Description: '{description}', Emoji: '{emoji}'")
        assert result == False, "Expected result to be False"
        assert "water" in description.lower(), "Expected description to mention water"
        assert emoji == "❌", "Expected X emoji"
        print("✅ Test passed!")
    
    # Test with clean response
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        # Set up the mock response
        mock_response = AsyncMock()
        # Make json() return a coroutine that returns our mock data
        mock_response.json = AsyncMock(return_value=mock_clean_response)
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response
        
        print("\n--- Testing with clean response ---")
        result, description, emoji = await query_llm("paper", "fire")
        print(f"Result: {result}, Description: '{description}', Emoji: '{emoji}'")
        assert result == True, "Expected result to be True"
        assert "fire" in description.lower(), "Expected description to mention fire"
        assert emoji == "🔥", "Expected fire emoji"
        print("✅ Test passed!")

if __name__ == "__main__":
    asyncio.run(test_query_llm())