import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "whatbeats")

# Initialize MongoDB client
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]

# Collections
comparisons_collection = db["comparisons"]
game_sessions_collection = db["game_sessions"]
high_scores_collection = db["high_scores"]
reports_collection = db["reports"]
count_ranges_collection = db["count_ranges"]

# Create indexes for better query performance
comparisons_collection.create_index([("item1", 1), ("item2", 1)], unique=True)
game_sessions_collection.create_index("session_id", unique=True)
high_scores_collection.create_index([("score", -1)])  # Descending for high scores
reports_collection.create_index("session_id")
reports_collection.create_index("status")
reports_collection.create_index("created_at")
count_ranges_collection.create_index([("range_start", 1)], unique=True)


# Comparison operations
async def get_comparison(item1: str, item2: str) -> Optional[Dict]:
    """
    Get a comparison between two items if it exists.
    
    This function queries the database for an existing comparison between
    two items. It's used to check if we already know whether one item beats
    another before querying the LLM.
    
    Args:
        item1: The first item (usually the current item in the game)
        item2: The second item (usually the user's input)
        
    Returns:
        The comparison document if found, None otherwise
    """
    return comparisons_collection.find_one({"item1": item1, "item2": item2})


async def create_comparison(
    item1: str,
    item2: str,
    item1_wins: bool,
    item2_wins: bool,
    description: str,
    emoji: str
) -> Dict:
    """
    Create a new comparison between two items.
    
    This function stores a new comparison in the database after the LLM
    has determined whether one item beats another. It includes the result,
    a description of why, and a relevant emoji.
    
    Args:
        item1: The first item (usually the current item in the game)
        item2: The second item (usually the user's input)
        item1_wins: Whether the first item beats the second
        item2_wins: Whether the second item beats the first
        description: A brief explanation of the result
        emoji: A relevant emoji for the comparison
        
    Returns:
        The newly created comparison document
    """
    now = datetime.utcnow()
    comparison = {
        "item1": item1,
        "item2": item2,
        "item1_wins": item1_wins,
        "item2_wins": item2_wins,
        "description": description,
        "emoji": emoji,
        "count": 1,
        "created_at": now,
        "updated_at": now
    }
    
    result = comparisons_collection.insert_one(comparison)
    comparison["_id"] = result.inserted_id
    return comparison


async def increment_comparison_count(item1: str, item2: str) -> None:
    """
    Increment the count for an existing comparison.
    
    This function updates the count field for an existing comparison
    and sets the updated_at timestamp to the current time. It's used
    to track how often certain comparisons are made.
    
    Args:
        item1: The first item in the comparison
        item2: The second item in the comparison
    """
    comparisons_collection.update_one(
        {"item1": item1, "item2": item2},
        {
            "$inc": {"count": 1},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )


# Game session operations
async def create_game_session() -> Dict:
    """Create a new game session starting with 'rock'."""
    session_id = str(ObjectId())
    now = datetime.utcnow()
    
    session = {
        "session_id": session_id,
        "current_item": "rock",
        "previous_items": [],
        "score": 0,
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    result = game_sessions_collection.insert_one(session)
    session["_id"] = result.inserted_id
    return session


async def get_game_session(session_id: str) -> Optional[Dict]:
    """Get a game session by its ID."""
    return game_sessions_collection.find_one({"session_id": session_id})


async def update_game_session(
    session_id: str, 
    current_item: str, 
    previous_items: List[str], 
    score: int, 
    is_active: bool = True
) -> Optional[Dict]:
    """Update a game session with new state."""
    result = game_sessions_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "current_item": current_item,
                "previous_items": previous_items,
                "score": score,
                "is_active": is_active,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count:
        return await get_game_session(session_id)
    return None


async def end_game_session(session_id: str) -> Optional[Dict]:
    """End a game session by setting is_active to False."""
    result = game_sessions_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count:
        return await get_game_session(session_id)
    return None


# High score operations
async def save_high_score(session_id: str, score: int, items_chain: List[str]) -> Dict:
    """Save a high score entry."""
    high_score = {
        "session_id": session_id,
        "score": score,
        "items_chain": items_chain,
        "created_at": datetime.utcnow()
    }
    
    result = high_scores_collection.insert_one(high_score)
    high_score["_id"] = result.inserted_id
    return high_score


async def get_high_scores(
    limit: int = 10,
    skip: int = 0,
    sort_by: str = "score",
    sort_direction: int = -1,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get high scores with pagination, sorting, and filtering.
    
    Args:
        limit: Maximum number of high scores to return
        skip: Number of high scores to skip (for pagination)
        sort_by: Field to sort by (e.g., "score", "created_at")
        sort_direction: Sort direction (1 for ascending, -1 for descending)
        filters: Optional dictionary of filters to apply
        
    Returns:
        Dictionary with high scores and total count
    """
    # Build the query
    query = {}
    if filters:
        # Apply any filters provided
        if "min_score" in filters and filters["min_score"] is not None:
            query["score"] = {"$gte": filters["min_score"]}
        if "max_score" in filters and filters["max_score"] is not None:
            query.setdefault("score", {}).update({"$lte": filters["max_score"]})
        if "date_from" in filters and filters["date_from"] is not None:
            query["created_at"] = {"$gte": filters["date_from"]}
        if "date_to" in filters and filters["date_to"] is not None:
            query.setdefault("created_at", {}).update({"$lte": filters["date_to"]})
    
    # Get total count for pagination
    total_count = high_scores_collection.count_documents(query)
    
    # Get the high scores with sorting and pagination
    high_scores = list(
        high_scores_collection.find(query)
        .sort(sort_by, sort_direction)
        .skip(skip)
        .limit(limit)
    )
    
    return {
        "high_scores": high_scores,
        "total_count": total_count
    }


# Statistics operations
async def get_comparison_stats(limit: int = 20) -> List[Dict]:
    """Get statistics about comparisons."""
    try:
        # Convert MongoDB cursor to list and handle BSON serialization
        comparisons = list(comparisons_collection.find().sort("count", -1).limit(limit))
        
        # Convert ObjectId to string for proper JSON serialization
        for comparison in comparisons:
            if "_id" in comparison:
                comparison["_id"] = str(comparison["_id"])
        
        return comparisons
    except Exception as e:
        # Log the error and re-raise with more context
        print(f"Error retrieving comparison stats: {str(e)}")
        raise Exception(f"Database error when retrieving comparison stats: {str(e)}")


# Report operations
async def create_report(
    session_id: str,
    item1: str,
    item2: str,
    comparison_id: Optional[str] = None,
    reason: Optional[str] = None
) -> Dict:
    """
    Create a new report for a disputed comparison.
    
    Args:
        session_id: The session ID where the report was made
        item1: The current item in the game
        item2: The user's submission
        comparison_id: Optional ID of the comparison being reported
        reason: Optional reason for the report
        
    Returns:
        The newly created report document
    """
    report_id = str(ObjectId())
    now = datetime.utcnow()
    
    report = {
        "report_id": report_id,
        "session_id": session_id,
        "comparison_id": comparison_id,
        "item1": item1,
        "item2": item2,
        "reason": reason,
        "status": "pending",
        "created_at": now,
        "updated_at": now
    }
    
    result = reports_collection.insert_one(report)
    report["_id"] = result.inserted_id
    return report


async def get_report(report_id: str) -> Optional[Dict]:
    """
    Get a report by its ID.
    
    Args:
        report_id: The unique report ID
        
    Returns:
        The report document if found, None otherwise
    """
    return reports_collection.find_one({"report_id": report_id})


async def update_report_status(report_id: str, status: str) -> Optional[Dict]:
    """
    Update the status of a report.
    
    Args:
        report_id: The unique report ID
        status: The new status (e.g., "pending", "reviewed", "approved", "rejected")
        
    Returns:
        The updated report document if found, None otherwise
    """
    result = reports_collection.update_one(
        {"report_id": report_id},
        {
            "$set": {
                "status": status,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count:
        return await get_report(report_id)
    return None


async def get_reports(
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
) -> List[Dict]:
    """
    Get reports, optionally filtered by status.
    
    Args:
        status: Optional status to filter by
        limit: Maximum number of reports to return
        skip: Number of reports to skip (for pagination)
        
    Returns:
        List of report documents
    """
    query = {}
    if status:
        query["status"] = status
    
    return list(
        reports_collection.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )


async def update_comparison(
    item1: str,
    item2: str,
    item1_wins: bool,
    item2_wins: bool,
    description: str,
    emoji: str
) -> Dict:
    """
    Update an existing comparison between two items.
    
    This function updates a comparison in the database based on admin corrections.
    It includes the updated result, description, and emoji.
    
    Args:
        item1: The first item in the comparison
        item2: The second item in the comparison
        item1_wins: Whether the first item beats the second
        item2_wins: Whether the second item beats the first
        description: A brief explanation of the result
        emoji: A relevant emoji for the comparison
        
    Returns:
        The updated comparison document
    """
    now = datetime.utcnow()
    
    # Update the comparison
    result = comparisons_collection.update_one(
        {"item1": item1, "item2": item2},
        {
            "$set": {
                "item1_wins": item1_wins,
                "item2_wins": item2_wins,
                "description": description,
                "emoji": emoji,
                "updated_at": now
            }
        }
    )
    
    if result.modified_count:
        # Return the updated document
        return await get_comparison(item1, item2)
    
    # If no document was modified, return None
    return None


# Count Range operations
async def get_count_range_description(count: int) -> Optional[Dict]:
    """
    Get a count range description for a specific count.
    
    This function finds the appropriate count range description for a given count.
    It looks for a range where range_start <= count <= range_end (or range_end is None).
    
    Args:
        count: The count to find a range description for
        
    Returns:
        The count range description document if found, None otherwise
    """
    # Find a range where range_start <= count <= range_end (or range_end is None)
    return count_ranges_collection.find_one({
        "$and": [
            {"range_start": {"$lte": count}},
            {"$or": [
                {"range_end": {"$gte": count}},
                {"range_end": None}
            ]}
        ]
    })


async def create_count_range_description(
    range_start: int,
    range_end: Optional[int],
    description: str,
    emoji: str
) -> Dict:
    """
    Create a new count range description.
    
    This function stores a new count range description in the database.
    
    Args:
        range_start: Start of the count range (inclusive)
        range_end: End of the count range (inclusive, None for open-ended)
        description: Description for this count range
        emoji: Emoji for this count range
        
    Returns:
        The newly created count range description document
    """
    now = datetime.utcnow()
    count_range = {
        "range_start": range_start,
        "range_end": range_end,
        "description": description,
        "emoji": emoji,
        "created_at": now
    }
    
    result = count_ranges_collection.insert_one(count_range)
    count_range["_id"] = result.inserted_id
    return count_range


async def get_all_count_ranges() -> List[Dict]:
    """
    Get all count range descriptions.
    
    Returns:
        List of all count range description documents
    """
    return list(count_ranges_collection.find().sort("range_start", 1))