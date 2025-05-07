from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
import re


# Report Models
class ReportRequest(BaseModel):
    """Request model for submitting a report."""
    session_id: str = Field(..., description="The unique session ID")
    comparison_id: Optional[str] = Field(None, description="The ID of the comparison being reported")
    item1: str = Field(..., description="The current item in the game", max_length=50)
    item2: str = Field(..., description="The user's submission", max_length=50)
    reason: Optional[str] = Field(None, description="The reason for the report", max_length=500)
    
    @validator('session_id')
    def validate_session_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9]+$', v):
            raise ValueError("Invalid session ID format")
        return v
    
    @validator('item1', 'item2')
    def validate_items(cls, v):
        if not re.match(r'^[a-zA-Z0-9\s.,!?-]+$', v):
            raise ValueError("Item contains invalid characters")
        return v.lower().strip()
    
    @validator('reason')
    def validate_reason(cls, v):
        if v is not None and len(v) > 0:
            # Allow a broader range of characters but still sanitize
            sanitized = re.sub(r'[<>]', '', v)  # Remove potential HTML/script tags
            return sanitized.strip()
        return v


class ReportResponse(BaseModel):
    """Response model for a submitted report."""
    report_id: str = Field(..., description="The unique report ID")
    status: str = Field(..., description="The status of the report")
    message: str = Field(..., description="A message to display to the user")

# Error Models
class ErrorResponse(BaseModel):
    """Base error response model."""
    detail: str = Field(..., description="Error detail message")
    code: str = Field("INTERNAL_ERROR", description="Error code")


class ItemAlreadyUsedError(ErrorResponse):
    """Error response for when an item has already been used in the game."""
    code: str = Field("ITEM_ALREADY_USED", description="Error code for item reuse")


class ValidationErrorResponse(ErrorResponse):
    """Error response for validation errors."""
    code: str = Field("VALIDATION_ERROR", description="Error code for validation errors")
    fields: List[Dict[str, str]] = Field([], description="List of field-specific errors")


class AuthorizationError(ErrorResponse):
    """Error response for authorization errors."""
    code: str = Field("AUTHORIZATION_ERROR", description="Error code for authorization errors")


class RateLimitError(ErrorResponse):
    """Error response for rate limit errors."""
    code: str = Field("RATE_LIMIT_ERROR", description="Error code for rate limit errors")
    retry_after: int = Field(60, description="Seconds to wait before retrying")



# Request Models
class StartGameRequest(BaseModel):
    """Request model for starting a new game."""
    pass  # No parameters needed


class ComparisonRequest(BaseModel):
    """Request model for submitting a comparison."""
    session_id: str = Field(..., description="The unique session ID")
    current_item: str = Field(..., description="The current item in the game", max_length=50)
    user_input: str = Field(..., description="The user's input for what beats the current item", max_length=50)
    
    @validator('user_input')
    def validate_user_input(cls, v):
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9\s.,!?-]+$', v):
            raise ValueError("Input contains invalid characters")
        return v.lower().strip()
    
    @validator('session_id')
    def validate_session_id(cls, v):
        # Ensure session_id is a valid format (alphanumeric)
        if not re.match(r'^[a-zA-Z0-9]+$', v):
            raise ValueError("Invalid session ID format")
        return v


class EndGameRequest(BaseModel):
    """Request model for ending a game."""
    session_id: str = Field(..., description="The unique session ID")


# Response Models
class StartGameResponse(BaseModel):
    """Response model for starting a new game."""
    session_id: str = Field(..., description="The unique session ID")
    current_item: str = Field(..., description="The initial item (rock)")
    message: str = Field(..., description="A message to display to the user")


class CountRangeDescription(BaseModel):
    """Model for count range descriptions."""
    range_start: int = Field(..., description="Start of the count range (inclusive)")
    range_end: Optional[int] = Field(None, description="End of the count range (inclusive, None for open-ended)")
    description: str = Field(..., description="Description for this count range")
    emoji: str = Field(..., description="Emoji for this count range")
    created_at: datetime = Field(..., description="When this range description was created")


class ComparisonResponse(BaseModel):
    """Response model for a comparison result."""
    result: bool = Field(..., description="Whether the user's input beats the current item")
    description: str = Field(..., description="A brief description of why")
    emoji: str = Field(..., description="A relevant emoji")
    next_item: str = Field(..., description="The next item in the game")
    score: int = Field(..., description="The current score")
    game_over: bool = Field(..., description="Whether the game is over")
    count: Optional[int] = Field(None, description="Number of times this comparison has been used")
    count_range_description: Optional[str] = Field(None, description="Description for the count range")
    count_range_emoji: Optional[str] = Field(None, description="Emoji for the count range")
    end_game_data: Optional[Dict[str, Any]] = Field(None, description="End game data if the game is over")


class GameStatusResponse(BaseModel):
    """Response model for game status."""
    session_id: str = Field(..., description="The unique session ID")
    current_item: str = Field(..., description="The current item in the game")
    previous_items: List[str] = Field(default=[], description="The previous items in the game")
    score: int = Field(..., description="The current score")
    is_active: bool = Field(..., description="Whether the game is active")


class EndGameResponse(BaseModel):
    """Response model for ending a game."""
    session_id: str = Field(..., description="The unique session ID")
    final_score: int = Field(..., description="The final score")
    items_chain: List[str] = Field(..., description="The chain of items in the game")
    high_score: bool = Field(False, description="Whether this is a high score")


class ComparisonStatsResponse(BaseModel):
    """Response model for comparison statistics."""
    comparisons: List[Dict[str, Any]] = Field(..., description="List of comparison statistics")
    
    class Config:
        """Pydantic model configuration."""
        # Allow arbitrary types for better compatibility with MongoDB documents
        arbitrary_types_allowed = True
        # Configure JSON serialization to handle MongoDB ObjectId and other non-standard types
        json_encoders = {
            # Add custom encoders if needed
        }


class HighScoreEntry(BaseModel):
    """Model for a high score entry."""
    session_id: str = Field(..., description="The unique session ID")
    score: int = Field(..., description="The score")
    items_chain: List[str] = Field(..., description="The chain of items in the game")
    created_at: datetime = Field(..., description="When the high score was created")


class HighScoresResponse(BaseModel):
    """Response model for high scores."""
    high_scores: List[HighScoreEntry] = Field(..., description="List of high scores")
    total_count: int = Field(..., description="Total number of high scores matching the query")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


class HighScoresFilterRequest(BaseModel):
    """Request model for filtering high scores."""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page")
    sort_by: str = Field("score", description="Field to sort by")
    sort_direction: str = Field("desc", description="Sort direction (asc or desc)")
    min_score: Optional[int] = Field(None, ge=0, description="Minimum score filter")
    max_score: Optional[int] = Field(None, ge=0, description="Maximum score filter")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = ['score', 'created_at']
        if v not in allowed_fields:
            raise ValueError(f"sort_by must be one of {allowed_fields}")
        return v
    
    @validator('sort_direction')
    def validate_sort_direction(cls, v):
        allowed_directions = ['asc', 'desc']
        if v.lower() not in allowed_directions:
            raise ValueError(f"sort_direction must be one of {allowed_directions}")
        return v.lower()
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and 'date_from' in values and values['date_from'] and v < values['date_from']:
            raise ValueError("date_to must be greater than or equal to date_from")
        return v
    
    @validator('max_score')
    def validate_score_range(cls, v, values):
        if v and 'min_score' in values and values['min_score'] and v < values['min_score']:
            raise ValueError("max_score must be greater than or equal to min_score")
        return v


# LLM Models
class LLMRequest(BaseModel):
    """Request model for LLM API."""
    current_item: str = Field(..., description="The current item in the game", max_length=50)
    user_input: str = Field(..., description="The user's input for what beats the current item", max_length=50)
    
    @validator('current_item', 'user_input')
    def validate_inputs(cls, v):
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9\s.,!?-]+$', v):
            raise ValueError("Input contains invalid characters")
        return v.lower().strip()


class LLMResponse(BaseModel):
    """Response model for LLM API."""
    result: bool = Field(..., description="Whether the user's input beats the current item")
    description: str = Field(..., description="A brief description of why")
    emoji: str = Field(..., description="A relevant emoji")


class CountRangeLLMRequest(BaseModel):
    """Request model for count range LLM API."""
    range_start: int = Field(..., description="Start of the count range")
    range_end: Optional[int] = Field(None, description="End of the count range (None for open-ended)")


class CountRangeLLMResponse(BaseModel):
    """Response model for count range LLM API."""
    description: str = Field(..., description="Description for this count range")
    emoji: str = Field(..., description="Emoji for this count range")


class Report(BaseModel):
    """Model for a report entry."""
    report_id: str = Field(..., description="The unique report ID")
    session_id: str = Field(..., description="The unique session ID")
    comparison_id: Optional[str] = Field(None, description="The ID of the comparison being reported")
    item1: str = Field(..., description="The current item in the game")
    item2: str = Field(..., description="The user's submission")
    reason: Optional[str] = Field(None, description="The reason for the report")
    status: str = Field("pending", description="The status of the report")
    created_at: datetime = Field(..., description="When the report was created")
    updated_at: datetime = Field(..., description="When the report was last updated")


# Admin Models
class AdminReportsFilterRequest(BaseModel):
    """Request model for filtering admin reports."""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page")
    status: Optional[str] = Field(None, description="Filter by status")
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_direction: str = Field("desc", description="Sort direction (asc or desc)")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = ['created_at', 'updated_at', 'status']
        if v not in allowed_fields:
            raise ValueError(f"sort_by must be one of {allowed_fields}")
        return v
    
    @validator('sort_direction')
    def validate_sort_direction(cls, v):
        allowed_directions = ['asc', 'desc']
        if v.lower() not in allowed_directions:
            raise ValueError(f"sort_direction must be one of {allowed_directions}")
        return v.lower()


class AdminReportsResponse(BaseModel):
    """Response model for admin reports."""
    reports: List[Report] = Field(..., description="List of reports")
    total_count: int = Field(..., description="Total number of reports matching the query")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


class UpdateComparisonRequest(BaseModel):
    """Request model for updating a comparison."""
    item1: str = Field(..., description="The first item in the comparison")
    item2: str = Field(..., description="The second item in the comparison")
    item1_wins: bool = Field(..., description="Whether the first item beats the second")
    item2_wins: bool = Field(..., description="Whether the second item beats the first")
    description: str = Field(..., description="A brief explanation of the result")
    emoji: str = Field(..., description="A relevant emoji for the comparison")


class UpdateReportStatusRequest(BaseModel):
    """Request model for updating a report status."""
    status: str = Field(..., description="The new status for the report")
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['pending', 'reviewed', 'approved', 'rejected']
        if v not in allowed_statuses:
            raise ValueError(f"status must be one of {allowed_statuses}")
        return v