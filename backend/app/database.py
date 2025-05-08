import os
import re
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
from pymongo.collection import Collection
from pymongo.database import Database
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "whatbeats")
MONGODB_CONNECT_TIMEOUT = int(os.getenv("MONGODB_CONNECT_TIMEOUT", "5000"))  # 5 seconds
MONGODB_MAX_RETRIES = int(os.getenv("MONGODB_MAX_RETRIES", "3"))

# Initialize MongoDB client and database as None initially
client = None
db = None
comparisons_collection = None
game_sessions_collection = None
high_scores_collection = None
reports_collection = None
count_ranges_collection = None

def initialize_db_connection(max_retries=MONGODB_MAX_RETRIES):
    """
    Initialize the database connection with retry logic.
    
    Args:
        max_retries: Maximum number of connection attempts
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    global client, db, comparisons_collection, game_sessions_collection
    global high_scores_collection, reports_collection, count_ranges_collection
    
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            logger.info(f"Attempting to connect to MongoDB at {MONGODB_URI} (attempt {retry_count + 1}/{max_retries})")
            
            # Initialize MongoDB client with timeout
            client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=MONGODB_CONNECT_TIMEOUT
            )
            
            # Test the connection
            client.admin.command('ping')
            
            # If we get here, connection is successful
            db = client[MONGODB_DB]
            
            # Initialize collections
            comparisons_collection = db["comparisons"]
            game_sessions_collection = db["game_sessions"]
            high_scores_collection = db["high_scores"]
            reports_collection = db["reports"]
            count_ranges_collection = db["count_ranges"]
            
            # Create indexes for better query performance
            try:
                comparisons_collection.create_index([("item1", 1), ("item2", 1)], unique=True)
                game_sessions_collection.create_index("session_id", unique=True)
                high_scores_collection.create_index([("score", -1)])  # Descending for high scores
                reports_collection.create_index("session_id")
                reports_collection.create_index("status")
                reports_collection.create_index("created_at")
                count_ranges_collection.create_index([("range_start", 1)], unique=True)
            except Exception as e:
                logger.warning(f"Failed to create indexes: {str(e)}")
                # Continue anyway as this is not critical
            
            logger.info("Successfully connected to MongoDB")
            return True, "Connection successful"
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            last_error = str(e)
            retry_count += 1
            
            if retry_count < max_retries:
                # Exponential backoff: 1s, 2s, 4s, etc.
                wait_time = 2 ** (retry_count - 1)
                logger.warning(f"Connection attempt {retry_count} failed: {last_error}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to connect to MongoDB after {max_retries} attempts: {last_error}")
        
        except Exception as e:
            last_error = str(e)
            logger.error(f"Unexpected error connecting to MongoDB: {last_error}")
            break
    
    return False, f"Failed to connect to database: {last_error}"

def check_db_connection():
    """
    Check if the database connection is active.
    
    Returns:
        bool: True if connection is active, False otherwise
    """
    global client
    
    if client is None:
        return False
    
    try:
        # Test the connection with a ping
        client.admin.command('ping')
        return True
    except Exception as e:
        logger.warning(f"Database connection check failed: {str(e)}")
        return False

# Initialize database connection on module import
connection_success, connection_message = initialize_db_connection()
if not connection_success:
    logger.warning(f"Initial database connection failed: {connection_message}")
    logger.warning("Some database operations may fail until connection is established")


# Database sanitization functions
def sanitize_db_input(value: Any) -> Any:
    """
    Sanitize input before using in database operations.
    
    This function removes MongoDB operator characters and other potentially
    dangerous characters from string inputs to prevent NoSQL injection attacks.
    
    Args:
        value: The value to sanitize (any type)
        
    Returns:
        Sanitized value (same type as input)
    """
    if isinstance(value, str):
        # Remove MongoDB operator characters
        sanitized = value.replace('$', '')
        
        # Remove dots which can be used for field traversal
        sanitized = sanitized.replace('.', '')
        
        return sanitized
    elif isinstance(value, dict):
        # Recursively sanitize dictionary values
        return {k: sanitize_db_input(v) for k, v in value.items()}
    elif isinstance(value, list):
        # Recursively sanitize list items
        return [sanitize_db_input(item) for item in value]
    else:
        # Return non-string values unchanged
        return value


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
        
    Raises:
        Exception: If there's a database connection error
    """
    # Check database connection
    if not check_db_connection():
        success, message = initialize_db_connection()
        if not success:
            raise Exception(f"Database connection error: {message}")
    
    try:
        # Sanitize inputs
        safe_item1 = sanitize_db_input(item1)
        safe_item2 = sanitize_db_input(item2)
        
        comparison = comparisons_collection.find_one({"item1": safe_item1, "item2": safe_item2})
        return serialize_document(comparison)
    except Exception as e:
        logger.error(f"Error in get_comparison: {str(e)}")
        raise Exception(f"Database error when retrieving comparison: {str(e)}")


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
        
    Raises:
        Exception: If there's a database connection error
    """
    # Check database connection
    if not check_db_connection():
        success, message = initialize_db_connection()
        if not success:
            raise Exception(f"Database connection error: {message}")
    
    try:
        # Sanitize inputs
        safe_item1 = sanitize_db_input(item1)
        safe_item2 = sanitize_db_input(item2)
        safe_description = sanitize_db_input(description)
        safe_emoji = sanitize_db_input(emoji)
        
        now = datetime.utcnow()
        comparison = {
            "item1": safe_item1,
            "item2": safe_item2,
            "item1_wins": item1_wins,
            "item2_wins": item2_wins,
            "description": safe_description,
            "emoji": safe_emoji,
            "count": 1,
            "created_at": now,
            "updated_at": now
        }
        
        result = comparisons_collection.insert_one(comparison)
        comparison["_id"] = result.inserted_id
        return serialize_document(comparison)
    except OperationFailure as e:
        logger.error(f"Database operation failed in create_comparison: {str(e)}")
        raise Exception(f"Database operation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Error in create_comparison: {str(e)}")
        raise Exception(f"Database error when creating comparison: {str(e)}")


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
    # Sanitize inputs
    safe_item1 = sanitize_db_input(item1)
    safe_item2 = sanitize_db_input(item2)
    
    comparisons_collection.update_one(
        {"item1": safe_item1, "item2": safe_item2},
        {
            "$inc": {"count": 1},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )


# Game session operations
async def create_game_session() -> Dict:
    """
    Create a new game session starting with 'rock'.
    
    Returns:
        The newly created game session document
        
    Raises:
        Exception: If there's a database connection error
    """
    # Check database connection
    if not check_db_connection():
        success, message = initialize_db_connection()
        if not success:
            raise Exception(f"Database connection error: {message}")
    
    try:
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
    except OperationFailure as e:
        logger.error(f"Database operation failed in create_game_session: {str(e)}")
        raise Exception(f"Database operation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Error in create_game_session: {str(e)}")
        raise Exception(f"Database error when creating game session: {str(e)}")


async def get_game_session(session_id: str) -> Optional[Dict]:
    """
    Get a game session by its ID.
    
    Args:
        session_id: The unique session ID
        
    Returns:
        The game session document if found, None otherwise
        
    Raises:
        Exception: If there's a database connection error
    """
    # Check database connection
    if not check_db_connection():
        success, message = initialize_db_connection()
        if not success:
            raise Exception(f"Database connection error: {message}")
    
    try:
        # Sanitize input
        safe_session_id = sanitize_db_input(session_id)
        session = game_sessions_collection.find_one({"session_id": safe_session_id})
        return serialize_document(session)
    except Exception as e:
        logger.error(f"Error in get_game_session: {str(e)}")
        raise Exception(f"Database error when retrieving game session: {str(e)}")


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


async def update_session_owner(session_id: str, owner_ip: str) -> Optional[Dict]:
    """
    Update a game session with the owner's IP address.
    
    This function is used for session validation to prevent unauthorized access.
    
    Args:
        session_id: The unique session ID
        owner_ip: The IP address of the session owner
        
    Returns:
        The updated session document if found, None otherwise
    """
    # Sanitize inputs
    safe_session_id = sanitize_db_input(session_id)
    safe_owner_ip = sanitize_db_input(owner_ip)
    
    result = game_sessions_collection.update_one(
        {"session_id": safe_session_id},
        {
            "$set": {
                "owner_ip": safe_owner_ip,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count:
        return await get_game_session(safe_session_id)
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
    return serialize_document(high_score)


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
    
    # Serialize documents to handle ObjectId fields
    serialized_high_scores = [serialize_document(score) for score in high_scores]
    
    return {
        "high_scores": serialized_high_scores,
        "total_count": total_count
    }


# Helper function for serializing MongoDB documents
def serialize_document(doc: Optional[Dict]) -> Optional[Dict]:
    """
    Convert MongoDB document to a JSON-serializable dictionary.
    
    This function recursively converts ObjectId fields to strings and handles
    nested dictionaries and lists.
    
    Args:
        doc: MongoDB document or None
        
    Returns:
        JSON-serializable dictionary or None
    """
    if doc is None:
        return None
    
    result = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            # Convert ObjectId to string
            result[key] = str(value)
        elif isinstance(value, dict):
            # Recursively serialize nested dictionaries
            result[key] = serialize_document(value)
        elif isinstance(value, list):
            # Recursively serialize items in lists
            result[key] = [
                serialize_document(item) if isinstance(item, dict)
                else str(item) if isinstance(item, ObjectId)
                else item
                for item in value
            ]
        else:
            # Keep other types as is
            result[key] = value
    
    return result


# Statistics operations
async def get_comparison_stats(limit: int = 20) -> List[Dict]:
    """Get statistics about comparisons."""
    try:
        # Convert MongoDB cursor to list and handle BSON serialization
        comparisons = list(comparisons_collection.find().sort("count", -1).limit(limit))
        
        # Serialize documents to handle ObjectId fields
        serialized_comparisons = [serialize_document(comparison) for comparison in comparisons]
        
        return serialized_comparisons
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
    # Sanitize inputs
    safe_session_id = sanitize_db_input(session_id)
    safe_item1 = sanitize_db_input(item1)
    safe_item2 = sanitize_db_input(item2)
    safe_comparison_id = sanitize_db_input(comparison_id) if comparison_id else None
    safe_reason = sanitize_db_input(reason) if reason else None
    
    report_id = str(ObjectId())
    now = datetime.utcnow()
    
    report = {
        "report_id": report_id,
        "session_id": safe_session_id,
        "comparison_id": safe_comparison_id,
        "item1": safe_item1,
        "item2": safe_item2,
        "reason": safe_reason,
        "status": "pending",
        "created_at": now,
        "updated_at": now
    }
    
    result = reports_collection.insert_one(report)
    report["_id"] = result.inserted_id
    return serialize_document(report)


async def get_report(report_id: str) -> Optional[Dict]:
    """
    Get a report by its ID.
    
    Args:
        report_id: The unique report ID
        
    Returns:
        The report document if found, None otherwise
    """
    report = reports_collection.find_one({"report_id": report_id})
    return serialize_document(report)


async def update_report_status(report_id: str, status: str) -> Optional[Dict]:
    """
    Update the status of a report.
    
    When a report is approved:
    - Set item1_wins to False
    - Set item2_wins to True
    
    When a report is rejected:
    - Set item1_wins to True
    - Set item2_wins to False
    
    Args:
        report_id: The unique report ID
        status: The new status (e.g., "pending", "reviewed", "approved", "rejected")
        
    Returns:
        The updated report document if found, None otherwise
    """
    # First, get the report to access its items
    report = await get_report(report_id)
    if not report:
        return None
    
    # Update the report status
    result = reports_collection.update_one(
        {"report_id": report_id},
        {
            "$set": {
                "status": status,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # If the report was approved or rejected, update the corresponding comparison
    if status == "approved" or status == "rejected":
        item1 = report["item1"]
        item2 = report["item2"]
        
        # Set the item1_wins and item2_wins values based on the status
        item1_wins = status == "rejected"  # True if rejected, False if approved
        item2_wins = status == "approved"  # True if approved, False if rejected
        
        # Check if a comparison exists
        existing_comparison = await get_comparison(item1, item2)
        
        if existing_comparison:
            # Update the existing comparison
            await update_comparison(
                item1=item1,
                item2=item2,
                item1_wins=item1_wins,
                item2_wins=item2_wins,
                description=existing_comparison.get("description", ""),
                emoji=existing_comparison.get("emoji", "")
            )
        else:
            # Create a new comparison
            await create_comparison(
                item1=item1,
                item2=item2,
                item1_wins=item1_wins,
                item2_wins=item2_wins,
                description="Updated based on admin review",
                emoji="🔄"
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
    
    reports = list(
        reports_collection.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    
    # Serialize documents to handle ObjectId fields
    return [serialize_document(report) for report in reports]


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
        comparison = await get_comparison(item1, item2)
        return serialize_document(comparison)
    
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
    range_doc = count_ranges_collection.find_one({
        "$and": [
            {"range_start": {"$lte": count}},
            {"$or": [
                {"range_end": {"$gte": count}},
                {"range_end": None}
            ]}
        ]
    })
    return serialize_document(range_doc)


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
    return serialize_document(count_range)


async def get_all_count_ranges() -> List[Dict]:
    """
    Get all count range descriptions.
    
    Returns:
        List of all count range description documents
    """
    ranges = list(count_ranges_collection.find().sort("range_start", 1))
    return [serialize_document(range_doc) for range_doc in ranges]