from typing import Dict, List, Optional, Tuple, Any
import asyncio
import re
from datetime import datetime

from . import database
from . import llm_service
from . import count_range_service

# Known relationships dictionary for validation
# Format: {item1: {item2: True/False}} where True means item2 beats item1
KNOWN_RELATIONSHIPS = {
    # Rock-Paper-Scissors relationships
    "rock": {"paper": True, "scissors": False, "lizard": False, "spock": True},
    "paper": {"rock": False, "scissors": True, "lizard": True, "spock": False},
    "scissors": {"rock": True, "paper": False, "lizard": False, "spock": True},
    
    # Rock-Paper-Scissors-Lizard-Spock extensions
    "lizard": {"rock": True, "paper": False, "scissors": True, "spock": False},
    "spock": {"rock": False, "paper": True, "scissors": False, "lizard": True},
    
    # Common physical relationships
    "fire": {"water": True, "paper": False, "wood": False, "ice": False},
    "water": {"fire": False, "paper": False, "electricity": True},
    "ice": {"fire": True, "water": False},
    
    # Card game hierarchies
    "ace": {"king": False, "queen": False, "jack": False},
    "king": {"ace": True, "queen": False, "jack": False},
    "queen": {"king": True, "jack": False, "ace": True},
    "jack": {"queen": True, "king": True, "ace": True},
    
    # Temporal relationships
    "butterfly": {"caterpillar": False},
    "caterpillar": {"butterfly": True},
    "adult": {"child": False},
    "child": {"adult": True}
}

def validate_against_known_relationships(item1: str, item2: str) -> Optional[bool]:
    """
    Validate a comparison against known relationships.
    
    Args:
        item1: The first item (current item)
        item2: The second item (user input)
        
    Returns:
        Optional[bool]: True if item2 beats item1, False if item1 beats item2,
                       None if the relationship is not in the known relationships
    """
    # Normalize inputs
    item1 = item1.lower().strip()
    item2 = item2.lower().strip()
    
    # Check if the relationship is in the known relationships
    if item1 in KNOWN_RELATIONSHIPS and item2 in KNOWN_RELATIONSHIPS[item1]:
        return KNOWN_RELATIONSHIPS[item1][item2]
    
    # Check the reverse relationship
    if item2 in KNOWN_RELATIONSHIPS and item1 in KNOWN_RELATIONSHIPS[item2]:
        return not KNOWN_RELATIONSHIPS[item2][item1]
    
    # Relationship not found
    return None

def validate_user_input(user_input: str) -> Tuple[bool, str]:
    """
    Validate user input to prevent prompt injection and ensure data quality.
    
    Args:
        user_input: The user's input to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: str)
        If is_valid is False, error_message contains the reason
    """
    # Check for empty input
    if not user_input or not user_input.strip():
        return False, "Input cannot be empty"
    
    # Limit length
    if len(user_input) > 50:
        return False, "Input too long (max 50 characters)"
    
    # Allow only alphanumeric characters, spaces, and basic punctuation
    if not re.match(r'^[a-zA-Z0-9\s.,!?-]+$', user_input):
        return False, "Input contains invalid characters"
    
    return True, ""


async def start_game() -> Dict[str, Any]:
    """
    Start a new game session with 'rock' as the initial item.
    
    This function creates a new game session in the database and initializes
    it with 'rock' as the starting item. Each game session has a unique ID.
    
    Returns:
        Dictionary with session_id, current_item, and message
    """
    # Create a new game session in the database
    session = await database.create_game_session()
    
    return {
        "session_id": session["session_id"],
        "current_item": "rock",
        "message": "What beats rock? 🪨"
    }


async def process_comparison(session_id: str, current_item: str, user_input: str) -> Dict[str, Any]:
    """
    Process a user's comparison input and determine if it beats the current item.
    
    This function is the core of the game logic. It checks if the user's input beats
    the current item by either looking up an existing comparison in the database or
    querying the LLM for a new comparison. It then updates the game state accordingly.
    
    Args:
        session_id: The unique session ID
        current_item: The current item in the game
        user_input: The user's input for what beats the current item
        
    Returns:
        Dictionary with comparison result and updated game state
    
    Raises:
        ValueError: If the game session is not found or is no longer active
        ValueError: If the user tries to use an item that has already been used in this game
        ValueError: If the user input fails validation
    """
    # Get the game session
    session = await database.get_game_session(session_id)
    if not session:
        raise ValueError(f"Game session {session_id} not found")
    
    if not session["is_active"]:
        raise ValueError(f"Game session {session_id} is no longer active")
    
    # Normalize inputs
    current_item = current_item.lower().strip()
    user_input = user_input.lower().strip()
    
    # Validate user input
    is_valid, error_message = validate_user_input(user_input)
    if not is_valid:
        raise ValueError(f"INPUT_VALIDATION_ERROR: {error_message}")
    
    # Check if the user is trying to reuse the current item
    if user_input == current_item:
        raise ValueError("ITEM_ALREADY_USED: You can't use the current item again")
    
    # Check if the user is trying to reuse an item from previous rounds
    if user_input in session["previous_items"]:
        raise ValueError("ITEM_ALREADY_USED: This item has already been used in this game")
    
    # Check if this comparison already exists in the database
    existing_comparison = await database.get_comparison(current_item, user_input)
    
    # Check against known relationships first
    known_result = validate_against_known_relationships(current_item, user_input)
    
    if existing_comparison:
        # Get the stored result
        stored_result = existing_comparison["item2_wins"]  # user_input is item2
        
        # If we have a known relationship that contradicts the stored result,
        # update the stored comparison with the correct result
        if known_result is not None and known_result != stored_result:
            # Log the correction
            print(f"Correcting stored relationship: {current_item} vs {user_input}. "
                  f"Stored: {stored_result}, Known correct: {known_result}")
            
            # Override the incorrect stored judgment with the known correct one
            await database.update_comparison(
                item1=current_item,
                item2=user_input,
                item1_wins=not known_result,  # If user_input wins, current_item loses
                item2_wins=known_result,      # If user_input wins, it's true
                description=existing_comparison["description"],  # Keep the original description
                emoji=existing_comparison["emoji"]               # Keep the original emoji
            )
            # Use the known correct result
            result = known_result
            description = existing_comparison["description"]
            emoji = existing_comparison["emoji"]
        else:
            # Use the stored result
            result = stored_result
            description = existing_comparison["description"]
            emoji = existing_comparison["emoji"]
        
        # Increment the count for this comparison
        await database.increment_comparison_count(current_item, user_input)
        
        # Get the updated count (it was just incremented)
        count = existing_comparison["count"] + 1
        
        # Get count range description and emoji
        count_range_description, count_range_emoji = await count_range_service.get_count_range_description(count)
    else:
        # This is a new comparison
        
        # If we have a known relationship, use it instead of querying the LLM
        if known_result is not None:
            result = known_result
            # Generate a description and emoji for the known relationship
            if result:
                description = f"{user_input} triumphantly overcomes {current_item} in this classic matchup!"
                emoji = "🏆"
            else:
                description = f"{user_input} fails to beat {current_item} in this well-known interaction."
                emoji = "❌"
        else:
            # Query the LLM for unknown relationships
            comparison_result = await llm_service.determine_comparison(current_item, user_input)
            
            result = comparison_result["result"]
            description = comparison_result["description"]
            emoji = comparison_result["emoji"]
        
        # This is a new comparison, so count is 1
        count = 1
        
        # Get count range description and emoji for first-time comparisons
        count_range_description, count_range_emoji = await count_range_service.get_count_range_description(count)
        
        # Store the new comparison in the database
        await database.create_comparison(
            item1=current_item,
            item2=user_input,
            item1_wins=not result,  # If user_input wins, current_item loses
            item2_wins=result,      # If user_input wins, it's true
            description=description,
            emoji=emoji
        )
    
    # Update the game state based on the result
    game_over = not result  # Game is over if the user's input doesn't beat the current item
    
    # Get the previous items and score from the session
    previous_items = session["previous_items"].copy()
    score = session["score"]
    
    if result:
        # User's input beats the current item, continue the game
        previous_items.append(current_item)
        score += 1
        next_item = user_input
    else:
        # User's input doesn't beat the current item, game over
        next_item = current_item
    
    # Update the game session in the database
    await database.update_game_session(
        session_id=session_id,
        current_item=next_item,
        previous_items=previous_items,
        score=score,
        is_active=not game_over
    )
    
    # Initialize end game data as None
    end_game_data = None
    
    # If the game is over, process end game logic immediately
    if game_over:
        # Construct the items chain
        items_chain = previous_items + [current_item]
        
        # Check if this is a high score (score >= 3)
        is_high_score = score >= 3
        
        # If it's a high score, save it
        if is_high_score:
            await database.save_high_score(
                session_id=session_id,
                score=score,
                items_chain=items_chain
            )
        
        # Create end game data to include in the response
        end_game_data = {
            "session_id": session_id,
            "final_score": score,
            "items_chain": items_chain,
            "high_score": is_high_score
        }
    
    response_data = {
        "result": result,
        "description": description,
        "emoji": emoji,
        "next_item": next_item,
        "score": score,
        "game_over": game_over,
        "count": count,
        "count_range_description": count_range_description,
        "count_range_emoji": count_range_emoji
    }
    
    # If the game is over, include end game data in the response
    if end_game_data:
        response_data["end_game_data"] = end_game_data
    
    return response_data


async def validate_session_ownership(session_id: str, request_ip: str) -> bool:
    """
    Validate that the request is coming from the session owner.
    
    Args:
        session_id: The unique session ID
        request_ip: The IP address of the requester
        
    Returns:
        Boolean indicating if the requester is the session owner
    """
    session = await database.get_game_session(session_id)
    if not session:
        return False
    
    # Add IP tracking to sessions
    if "owner_ip" not in session:
        # First access, set the owner
        await database.update_session_owner(session_id, request_ip)
        return True
    
    # Check if the request is from the same IP
    return session["owner_ip"] == request_ip

async def get_game_status(session_id: str, request_ip: str = None) -> Dict[str, Any]:
    """
    Get the current status of a game session.
    
    Args:
        session_id: The unique session ID
        request_ip: The IP address of the requester (optional)
        
    Returns:
        Dictionary with game session details
        
    Raises:
        ValueError: If the session is not found or the requester is not authorized
    """
    session = await database.get_game_session(session_id)
    if not session:
        raise ValueError(f"Game session {session_id} not found")
    
    # If request_ip is provided, validate ownership
    if request_ip and "owner_ip" in session:
        if session["owner_ip"] != request_ip:
            raise ValueError("Unauthorized access to session")
    
    return {
        "session_id": session["session_id"],
        "current_item": session["current_item"],
        "previous_items": session["previous_items"],
        "score": session["score"],
        "is_active": session["is_active"]
    }


async def end_game(session_id: str) -> Dict[str, Any]:
    """
    End a game session and return the final results.
    
    Args:
        session_id: The unique session ID
        
    Returns:
        Dictionary with final game results
    """
    session = await database.get_game_session(session_id)
    if not session:
        raise ValueError(f"Game session {session_id} not found")
    
    # End the game session
    updated_session = await database.end_game_session(session_id)
    
    # Construct the items chain
    items_chain = session["previous_items"] + [session["current_item"]]
    
    # Check if this is a high score (score >= 3)
    is_high_score = session["score"] >= 3
    
    # If it's a high score and the session was active, save it
    if is_high_score and session["is_active"]:
        await database.save_high_score(
            session_id=session_id,
            score=session["score"],
            items_chain=items_chain
        )
    
    return {
        "session_id": session_id,
        "final_score": session["score"],
        "items_chain": items_chain,
        "high_score": is_high_score
    }


async def get_comparison_stats(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get statistics about comparisons.
    
    Args:
        limit: Maximum number of comparisons to return
        
    Returns:
        List of comparison statistics
        
    Raises:
        Exception: If there's an error retrieving the comparison stats
    """
    try:
        return await database.get_comparison_stats(limit)
    except Exception as e:
        # Log the error and re-raise with more context
        print(f"Error in game_service.get_comparison_stats: {str(e)}")
        raise Exception(f"Failed to retrieve comparison statistics: {str(e)}")


async def get_high_scores(
    limit: int = 10,
    skip: int = 0,
    sort_by: str = "score",
    sort_direction: str = "desc",
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get high scores with pagination, sorting, and filtering.
    
    Args:
        limit: Maximum number of high scores to return
        skip: Number of high scores to skip (for pagination)
        sort_by: Field to sort by (e.g., "score", "created_at")
        sort_direction: Sort direction ("asc" for ascending, "desc" for descending)
        min_score: Optional minimum score filter
        max_score: Optional maximum score filter
        date_from: Optional start date filter
        date_to: Optional end date filter
        
    Returns:
        Dictionary with high scores and total count
    """
    # Convert sort direction string to integer
    sort_dir_int = -1 if sort_direction.lower() == "desc" else 1
    
    # Build filters dictionary
    filters = {
        "min_score": min_score,
        "max_score": max_score,
        "date_from": date_from,
        "date_to": date_to
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    return await database.get_high_scores(
        limit=limit,
        skip=skip,
        sort_by=sort_by,
        sort_direction=sort_dir_int,
        filters=filters if filters else None
    )