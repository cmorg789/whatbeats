import json
import logging
import sys
from app.llm_service import extract_json_from_llm_response

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_json_extraction")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def test_extraction(test_name, content, expected_result=None):
    print(f"\n=== Testing: {test_name} ===")
    print(f"Input: {repr(content)}")
    
    try:
        result = extract_json_from_llm_response(content, logger)
        print(f"Result: {result}")
        
        if expected_result:
            assert result == expected_result, f"Expected {expected_result}, got {result}"
            print("✅ Test passed!")
        else:
            print("✅ Successfully extracted JSON")
            
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

# Test cases
test_cases = [
    {
        "name": "Clean JSON",
        "content": '{"result": true, "description": "Test description", "emoji": "🔨"}',
        "expected": {"result": True, "description": "Test description", "emoji": "🔨"}
    },
    {
        "name": "JSON with '**' prefix (the issue we're fixing)",
        "content": '**\n{"result": true, "description": "A hammer can break a rock due to its force and hardness.", "emoji": "🔨"}',
        "expected": {"result": True, "description": "A hammer can break a rock due to its force and hardness.", "emoji": "🔨"}
    },
    {
        "name": "JSON in markdown code block",
        "content": '```json\n{"result": false, "description": "Water does not beat paper in the game.", "emoji": "❌"}\n```',
        "expected": {"result": False, "description": "Water does not beat paper in the game.", "emoji": "❌"}
    },
    {
        "name": "JSON with random text before and after",
        "content": 'Here is my response:\n{"result": true, "description": "Fire burns paper.", "emoji": "🔥"}\nHope that helps!',
        "expected": {"result": True, "description": "Fire burns paper.", "emoji": "🔥"}
    },
    {
        "name": "JSON with whitespace and newlines",
        "content": '\n\n  \n{"result": true, "description": "Test", "emoji": "✅"}\n  \n',
        "expected": {"result": True, "description": "Test", "emoji": "✅"}
    }
]

# Run tests
success_count = 0
for test_case in test_cases:
    if test_extraction(test_case["name"], test_case["content"], test_case.get("expected")):
        success_count += 1

print(f"\n=== Summary ===")
print(f"Passed {success_count}/{len(test_cases)} tests")