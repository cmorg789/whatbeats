from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from typing import List, Dict, Any, Optional
import uvicorn
import os
import math
import time
import traceback
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path as PathLib

from . import models
from . import game_service
from . import database
from . import report_service
from . import count_range_service

# Rate limiting configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "5"))  # requests
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # seconds

# Admin API key configuration
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change-me-in-production")
api_key_header = APIKeyHeader(name="X-API-Key")

# Load environment variables from root directory
root_dir = PathLib(__file__).resolve().parents[2]  # Go up two levels to reach the root directory
env_path = os.path.join(root_dir, '.env')
load_dotenv(dotenv_path=env_path)

# Create FastAPI app
app = FastAPI(
    title="What Beats Rock? API",
    description="API for the 'What Beats Rock?' game",
    version="1.0.0"
)

# Add CORS middleware with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "https://whatbeats.example.com"],  # Restrict to specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Accept", "Authorization", "X-API-Key"],
    expose_headers=["Content-Type", "Content-Length"],  # Only expose necessary headers
)

# Rate limiting middleware
class RateLimitMiddleware:
    """
    Middleware for rate limiting API requests.
    
    This middleware tracks requests by client IP and enforces rate limits
    to prevent abuse of the API, especially for LLM-related endpoints.
    """
    def __init__(self, requests_limit: int, period: int):
        self.requests_limit = requests_limit
        self.period = period
        self.clients = {}
    
    async def __call__(self, request: Request, call_next):
        # Skip rate limiting if disabled
        if not RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Only rate limit LLM-related endpoints
        path = request.url.path
        if not (path.startswith("/api/submit-comparison") or "llm" in path.lower()):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        
        # Check if client has exceeded rate limit
        current_time = time.time()
        if client_ip in self.clients:
            # Clean up old requests
            self.clients[client_ip] = [
                timestamp for timestamp in self.clients[client_ip]
                if current_time - timestamp < self.period
            ]
            
            # Check if client has exceeded rate limit
            if len(self.clients[client_ip]) >= self.requests_limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Rate limit exceeded. Maximum {self.requests_limit} requests per {self.period} seconds."
                    }
                )
        else:
            self.clients[client_ip] = []
        
        # Add current request timestamp
        self.clients[client_ip].append(current_time)
        
        # Process the request
        return await call_next(request)

# Add rate limiting middleware if enabled
if RATE_LIMIT_ENABLED:
    app.middleware("http")(RateLimitMiddleware(RATE_LIMIT_REQUESTS, RATE_LIMIT_PERIOD))

# Global exception handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for all unhandled exceptions.
    
    This handler prevents detailed error information from being exposed to clients,
    which could potentially reveal sensitive information about the application.
    Instead, it returns a generic error message and logs the detailed error for
    debugging purposes.
    
    Args:
        request: The request that caused the exception
        exc: The unhandled exception
        
    Returns:
        A JSON response with a generic error message
    """
    # Log the detailed error for debugging
    error_details = traceback.format_exc()
    print(f"Unhandled exception: {error_details}")
    
    # Return a generic error to the client
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred", "code": "INTERNAL_ERROR"}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Exception handler for request validation errors.
    
    This handler formats validation errors in a consistent way, making it easier
    for clients to understand what went wrong with their request without exposing
    internal details of the validation process.
    
    Args:
        request: The request that caused the validation error
        exc: The validation error
        
    Returns:
        A JSON response with validation error details
    """
    errors = []
    for error in exc.errors():
        # Extract field name and error message
        field_name = error["loc"][-1] if error["loc"] else "unknown"
        message = error["msg"]
        errors.append({"name": field_name, "message": message})
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "code": "VALIDATION_ERROR",
            "fields": errors
        }
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """
    Exception handler for Pydantic validation errors.
    
    This handler formats Pydantic validation errors in a consistent way, similar
    to the RequestValidationError handler.
    
    Args:
        request: The request that caused the validation error
        exc: The validation error
        
    Returns:
        A JSON response with validation error details
    """
    errors = []
    for error in exc.errors():
        # Extract field name and error message
        field_name = error["loc"][-1] if error["loc"] else "unknown"
        message = error["msg"]
        errors.append({"name": field_name, "message": message})
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "code": "VALIDATION_ERROR",
            "fields": errors
        }
    )


# Initialize count range descriptions on startup
@app.on_event("startup")
async def startup_event():
    """Initialize data and services on application startup."""
    # Initialize default count range descriptions
    await count_range_service.initialize_default_ranges()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "ok"}


# Game Flow Endpoints
@app.post("/api/start-game", response_model=models.StartGameResponse)
async def start_game():
    """Initialize a new game session starting with 'rock'."""
    try:
        result = await game_service.start_game()
        return models.StartGameResponse(
            session_id=result["session_id"],
            current_item=result["current_item"],
            message=result["message"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/submit-comparison", response_model=models.ComparisonResponse)
async def submit_comparison(request: models.ComparisonRequest, client_request: Request):
    """Process user input and determine if it beats the current item."""
    try:
        result = await game_service.process_comparison(
            session_id=request.session_id,
            current_item=request.current_item,
            user_input=request.user_input
        )
        
        # Create response with all fields from the result
        response_data = {
            "result": result["result"],
            "description": result["description"],
            "emoji": result["emoji"],
            "next_item": result["next_item"],
            "score": result["score"],
            "game_over": result["game_over"],
            "count": result["count"],
            "count_range_description": result["count_range_description"],
            "count_range_emoji": result["count_range_emoji"]
        }
        
        # Include end_game_data if present in the result
        if "end_game_data" in result:
            response_data["end_game_data"] = result["end_game_data"]
        
        return models.ComparisonResponse(**response_data)
    except ValueError as e:
        error_message = str(e)
        if error_message.startswith("ITEM_ALREADY_USED:"):
            # Return a specific error for item reuse
            error_detail = error_message.split(":", 1)[1].strip()
            error_response = models.ItemAlreadyUsedError(detail=error_detail)
            return JSONResponse(
                status_code=422,
                content=error_response.dict()
            )
        elif error_message.startswith("INPUT_VALIDATION_ERROR:"):
            # Return a specific error for input validation
            error_detail = error_message.split(":", 1)[1].strip()
            return JSONResponse(
                status_code=422,
                content={"detail": error_detail, "code": "INPUT_VALIDATION_ERROR"}
            )
        else:
            # Other ValueError exceptions (like session not found)
            raise HTTPException(status_code=404, detail=error_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/game-status/{session_id}", response_model=models.GameStatusResponse)
async def get_game_status(session_id: str, request: Request):
    """Get current game status."""
    try:
        # Get client IP for session validation
        client_ip = request.client.host
        
        # Validate session ownership
        if not await game_service.validate_session_ownership(session_id, client_ip):
            raise HTTPException(status_code=403, detail="Unauthorized access to session")
        
        result = await game_service.get_game_status(session_id, client_ip)
        
        return models.GameStatusResponse(
            session_id=result["session_id"],
            current_item=result["current_item"],
            previous_items=result["previous_items"],
            score=result["score"],
            is_active=result["is_active"]
        )
    except ValueError as e:
        error_message = str(e)
        if "Unauthorized" in error_message:
            raise HTTPException(status_code=403, detail=error_message)
        else:
            raise HTTPException(status_code=404, detail=error_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/end-game", response_model=models.EndGameResponse)
async def end_game(request: models.EndGameRequest):
    """End the current game session."""
    try:
        result = await game_service.end_game(request.session_id)
        
        return models.EndGameResponse(
            session_id=result["session_id"],
            final_score=result["final_score"],
            items_chain=result["items_chain"],
            high_score=result["high_score"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Statistics Endpoints
@app.get("/api/stats/comparisons", response_model=models.ComparisonStatsResponse)
async def get_comparison_stats(limit: int = Query(20, ge=1, le=100)):
    """Get statistics about comparisons."""
    try:
        comparisons = await game_service.get_comparison_stats(limit)
        # Return a properly formatted response
        return models.ComparisonStatsResponse(comparisons=comparisons)
    except Exception as e:
        # Log the error
        print(f"Error in get_comparison_stats: {str(e)}")
        # Return a more detailed error message
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve comparison stats: {str(e)}"
        )


@app.get("/api/stats/high-scores", response_model=models.HighScoresResponse)
async def get_high_scores(limit: int = Query(10, ge=1, le=100)):
    """Get top scores (legacy endpoint)."""
    try:
        result = await game_service.get_high_scores(limit=limit)
        total_count = result["total_count"]
        high_scores = result["high_scores"]
        
        return models.HighScoresResponse(
            high_scores=high_scores,
            total_count=total_count,
            page=1,
            page_size=limit,
            total_pages=math.ceil(total_count / limit)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scoreboard", response_model=models.HighScoresResponse)
async def get_scoreboard(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("score", description="Field to sort by (score, created_at)"),
    sort_direction: str = Query("desc", description="Sort direction (asc, desc)"),
    min_score: Optional[int] = Query(None, ge=0, description="Minimum score filter"),
    max_score: Optional[int] = Query(None, ge=0, description="Maximum score filter"),
    date_from: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="End date filter (ISO format)")
):
    """
    Get paginated, sorted, and filtered high scores for the scoreboard.
    
    This endpoint provides comprehensive functionality for the scoreboard UI:
    - Pagination with page and page_size parameters
    - Sorting by different criteria (score, date)
    - Filtering by score range and date range
    """
    try:
        # Validate parameters
        filter_params = models.HighScoresFilterRequest(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_direction=sort_direction,
            min_score=min_score,
            max_score=max_score,
            date_from=date_from,
            date_to=date_to
        )
        
        # Calculate skip value for pagination
        skip = (filter_params.page - 1) * filter_params.page_size
        
        # Get high scores with filters
        result = await game_service.get_high_scores(
            limit=filter_params.page_size,
            skip=skip,
            sort_by=filter_params.sort_by,
            sort_direction=filter_params.sort_direction,
            min_score=filter_params.min_score,
            max_score=filter_params.max_score,
            date_from=filter_params.date_from,
            date_to=filter_params.date_to
        )
        
        total_count = result["total_count"]
        high_scores = result["high_scores"]
        total_pages = math.ceil(total_count / filter_params.page_size)
        
        return models.HighScoresResponse(
            high_scores=high_scores,
            total_count=total_count,
            page=filter_params.page,
            page_size=filter_params.page_size,
            total_pages=total_pages
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scoreboard/stats")
async def get_scoreboard_stats():
    """
    Get statistics about the scoreboard.
    
    Returns summary statistics like:
    - Total number of high scores
    - Highest score ever achieved
    - Average score
    - Most recent high score date
    """
    try:
        # Get all high scores (limited to 1000 for performance)
        result = await game_service.get_high_scores(limit=1000)
        high_scores = result["high_scores"]
        total_count = result["total_count"]
        
        # Calculate statistics
        stats = {
            "total_count": total_count,
            "highest_score": 0,
            "average_score": 0,
            "most_recent_date": None
        }
        
        if high_scores:
            # Find highest score
            stats["highest_score"] = max(hs["score"] for hs in high_scores)
            
            # Calculate average score
            stats["average_score"] = sum(hs["score"] for hs in high_scores) / len(high_scores)
            
            # Find most recent date
            stats["most_recent_date"] = max(hs["created_at"] for hs in high_scores)
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Report Endpoints
@app.post("/api/report-comparison", response_model=models.ReportResponse)
async def report_comparison(request: models.ReportRequest):
    """Submit a report for a disputed comparison."""
    try:
        result = await report_service.create_report(
            session_id=request.session_id,
            item1=request.item1,
            item2=request.item2,
            comparison_id=request.comparison_id,
            reason=request.reason
        )
        
        return models.ReportResponse(
            report_id=result["report_id"],
            status=result["status"],
            message=result["message"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/{report_id}")
async def get_report(report_id: str):
    """Get a specific report by ID."""
    try:
        report = await report_service.get_report(report_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports")
async def get_reports(
    status: Optional[str] = Query(None, description="Filter reports by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of reports to return"),
    skip: int = Query(0, ge=0, description="Number of reports to skip")
):
    """Get reports, optionally filtered by status."""
    try:
        result = await report_service.get_reports(status, limit, skip)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Admin API key validation
def get_api_key(api_key: str = Security(api_key_header)):
    """
    Validate the API key for admin endpoints.
    
    Args:
        api_key: The API key from the X-API-Key header
        
    Returns:
        The API key if valid
        
    Raises:
        HTTPException: If the API key is invalid
    """
    if api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    return api_key

# Admin Endpoints
@app.get("/api/admin/reports", response_model=models.AdminReportsResponse)
async def get_admin_reports(
    api_key: str = Depends(get_api_key),
    status: Optional[str] = Query(None, description="Filter reports by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_direction: str = Query("desc", description="Sort direction (asc, desc)")
):
    """Get reports for admin view with pagination, sorting, and filtering."""
    try:
        # Validate parameters
        filter_params = models.AdminReportsFilterRequest(
            page=page,
            page_size=page_size,
            status=status,
            sort_by=sort_by,
            sort_direction=sort_direction
        )
        
        result = await report_service.get_admin_reports(
            status=filter_params.status,
            page=filter_params.page,
            page_size=filter_params.page_size,
            sort_by=filter_params.sort_by,
            sort_direction=filter_params.sort_direction
        )
        
        return models.AdminReportsResponse(
            reports=result["reports"],
            total_count=result["total_count"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/admin/comparisons", response_model=Dict[str, Any])
async def update_comparison(
    request: models.UpdateComparisonRequest,
    api_key: str = Depends(get_api_key)
):
    """Update a comparison based on admin corrections."""
    try:
        result = await report_service.update_comparison(
            item1=request.item1,
            item2=request.item2,
            item1_wins=request.item1_wins,
            item2_wins=request.item2_wins,
            description=request.description,
            emoji=request.emoji
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/admin/reports/{report_id}/status", response_model=Dict[str, Any])
async def update_report_status(
    report_id: str = Path(..., description="The unique report ID"),
    request: models.UpdateReportStatusRequest = Body(...),
    api_key: str = Depends(get_api_key)
):
    """Update the status of a report."""
    try:
        result = await report_service.update_report_status(report_id, request.status)
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run the application if executed directly
if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 8000))
    
    # Run the FastAPI application with Uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)