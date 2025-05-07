from typing import Dict, Optional, Tuple, List
from datetime import datetime

from . import database
from . import llm_service


async def get_count_range_description(count: int) -> Tuple[Optional[str], Optional[str]]:
    """
    Get a description and emoji for a specific count.
    
    This function checks if there's an existing description for the count range
    that includes the given count. If not, it generates a new one using the LLM.
    
    Args:
        count: The count to get a description for
        
    Returns:
        Tuple of (description: Optional[str], emoji: Optional[str])
    """
    # Check if there's an existing description for this count range
    count_range = await database.get_count_range_description(count)
    
    if count_range:
        return count_range["description"], count_range["emoji"]
    
    # No existing description, determine the range and generate a new one
    range_start, range_end = determine_count_range(count)
    
    # Generate a description and emoji using the LLM
    description, emoji = await llm_service.generate_count_range_description(range_start, range_end)
    
    # Store the new description
    await database.create_count_range_description(
        range_start=range_start,
        range_end=range_end,
        description=description,
        emoji=emoji
    )
    
    return description, emoji


def determine_count_range(count: int) -> Tuple[int, Optional[int]]:
    """
    Determine the appropriate range for a count.
    
    This function implements the count range logic according to the requirements:
    - 1
    - 2-5
    - 5-10
    - Every 10 afterward (10-19, 20-29, etc.)
    
    Args:
        count: The count to determine a range for
        
    Returns:
        Tuple of (range_start: int, range_end: Optional[int])
    """
    if count == 1:
        return 1, 1
    elif count <= 5:
        return 2, 5
    elif count <= 10:
        return 6, 10
    else:
        # For counts > 10, use ranges of 10 (10-19, 20-29, etc.)
        range_start = (count // 10) * 10
        range_end = range_start + 9
        return range_start, range_end


async def initialize_default_ranges() -> None:
    """
    Initialize default count range descriptions.
    
    This function checks if there are any existing count range descriptions.
    If not, it creates default ones for the first few ranges.
    """
    # Check if there are any existing count ranges
    existing_ranges = await database.get_all_count_ranges()
    
    if not existing_ranges:
        # Create default ranges
        default_ranges = [
            (1, 1, "First time seeing this comparison!", "🆕"),
            (2, 5, "This comparison is gaining popularity!", "📈"),
            (6, 10, "A frequent matchup in the game!", "🔄"),
            (10, 19, "This comparison is becoming a classic!", "⭐"),
            (20, 29, "A very popular comparison!", "🔥")
        ]
        
        for range_start, range_end, description, emoji in default_ranges:
            await database.create_count_range_description(
                range_start=range_start,
                range_end=range_end,
                description=description,
                emoji=emoji
            )