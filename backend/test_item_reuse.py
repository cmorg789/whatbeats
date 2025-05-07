import asyncio
import pytest
from app import game_service
from app import database

# Test data
TEST_SESSION_ID = "test_session_id"
INITIAL_ITEM = "rock"
FIRST_USER_INPUT = "paper"
REUSED_INPUT = "paper"  # Trying to reuse the same item


async def setup_test_session():
    """Set up a test game session with one successful comparison."""
    # Create a mock session directly in the database
    session = {
        "session_id": TEST_SESSION_ID,
        "current_item": FIRST_USER_INPUT,  # After first comparison, paper becomes current
        "previous_items": [INITIAL_ITEM],  # Rock is now in previous items
        "score": 1,
        "is_active": True
    }
    
    # Insert directly into database - not awaiting as it's not an async function
    database.game_sessions_collection.insert_one(session)
    
    return session


async def cleanup_test_session():
    """Clean up the test session after tests."""
    # Not awaiting as it's not an async function
    database.game_sessions_collection.delete_one({"session_id": TEST_SESSION_ID})


@pytest.mark.asyncio
async def test_prevent_reusing_current_item():
    """Test that users cannot reuse the current item."""
    try:
        # Set up test session
        await setup_test_session()
        
        # Try to reuse the current item (paper)
        with pytest.raises(ValueError) as excinfo:
            await game_service.process_comparison(
                session_id=TEST_SESSION_ID,
                current_item=FIRST_USER_INPUT,
                user_input=FIRST_USER_INPUT  # Reusing paper
            )
        
        # Check that the correct error message is raised
        assert "ITEM_ALREADY_USED" in str(excinfo.value)
        assert "current item" in str(excinfo.value).lower()
    finally:
        # Clean up
        await cleanup_test_session()


@pytest.mark.asyncio
async def test_prevent_reusing_previous_item():
    """Test that users cannot reuse an item from previous rounds."""
    try:
        # Set up test session
        await setup_test_session()
        
        # Try to reuse a previous item (rock)
        with pytest.raises(ValueError) as excinfo:
            await game_service.process_comparison(
                session_id=TEST_SESSION_ID,
                current_item=FIRST_USER_INPUT,
                user_input=INITIAL_ITEM  # Reusing rock
            )
        
        # Check that the correct error message is raised
        assert "ITEM_ALREADY_USED" in str(excinfo.value)
        assert "already been used" in str(excinfo.value).lower()
    finally:
        # Clean up
        await cleanup_test_session()


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_prevent_reusing_current_item())
    asyncio.run(test_prevent_reusing_previous_item())
    print("All tests passed!")