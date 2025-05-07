from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import uvicorn
import os
import math
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path as PathLib

from . import models
from . import game_service
from . import database
from . import report_service
from . import count_range_service

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

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers to the browser
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
async def submit_comparison(request: models.ComparisonRequest):
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
        else:
            # Other ValueError exceptions (like session not found)
            raise HTTPException(status_code=404, detail=error_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/game-status/{session_id}", response_model=models.GameStatusResponse)
async def get_game_status(session_id: str):
    """Get current game status."""
    try:
        result = await game_service.get_game_status(session_id)
        
        return models.GameStatusResponse(
            session_id=result["session_id"],
            current_item=result["current_item"],
            previous_items=result["previous_items"],
            score=result["score"],
            is_active=result["is_active"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
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


# Admin Endpoints
@app.get("/api/admin/reports", response_model=models.AdminReportsResponse)
async def get_admin_reports(
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
async def update_comparison(request: models.UpdateComparisonRequest):
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
    request: models.UpdateReportStatusRequest = Body(...)
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