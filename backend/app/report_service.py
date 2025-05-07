from typing import Dict, Optional, Any
from datetime import datetime

from . import database


async def create_report(
    session_id: str,
    item1: str,
    item2: str,
    comparison_id: Optional[str] = None,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new report for a disputed comparison.
    
    This function creates a new report in the database when a user disputes
    a comparison result. It records the session ID, the items being compared,
    and optionally the comparison ID and a reason for the report.
    
    Args:
        session_id: The session ID where the report was made
        item1: The current item in the game
        item2: The user's submission
        comparison_id: Optional ID of the comparison being reported
        reason: Optional reason for the report
        
    Returns:
        Dictionary with report details including the report_id
    """
    # Create a new report in the database
    report = await database.create_report(
        session_id=session_id,
        item1=item1,
        item2=item2,
        comparison_id=comparison_id,
        reason=reason
    )
    
    return {
        "report_id": report["report_id"],
        "status": report["status"],
        "message": "Thank you for your report. Our team will review it soon."
    }


async def get_report(report_id: str) -> Dict[str, Any]:
    """
    Get a report by its ID.
    
    Args:
        report_id: The unique report ID
        
    Returns:
        Dictionary with report details
        
    Raises:
        ValueError: If the report is not found
    """
    report = await database.get_report(report_id)
    if not report:
        raise ValueError(f"Report {report_id} not found")
    
    return report


async def update_report_status(report_id: str, status: str) -> Dict[str, Any]:
    """
    Update the status of a report.
    
    Args:
        report_id: The unique report ID
        status: The new status (e.g., "pending", "reviewed", "approved", "rejected")
        
    Returns:
        Dictionary with updated report details
        
    Raises:
        ValueError: If the report is not found
    """
    updated_report = await database.update_report_status(report_id, status)
    if not updated_report:
        raise ValueError(f"Report {report_id} not found")
    
    return updated_report


async def get_reports(
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
) -> Dict[str, Any]:
    """
    Get reports, optionally filtered by status.
    
    Args:
        status: Optional status to filter by
        limit: Maximum number of reports to return
        skip: Number of reports to skip (for pagination)
        
    Returns:
        Dictionary with list of reports and metadata
    """
    reports = await database.get_reports(status, limit, skip)
    
    return {
        "reports": reports,
        "count": len(reports),
        "limit": limit,
        "skip": skip
    }


async def get_admin_reports(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "created_at",
    sort_direction: str = "desc"
) -> Dict[str, Any]:
    """
    Get reports for admin view with pagination, sorting, and filtering.
    
    Args:
        status: Optional status to filter by
        page: Page number (1-indexed)
        page_size: Number of items per page
        sort_by: Field to sort by (e.g., "created_at", "updated_at", "status")
        sort_direction: Sort direction (asc or desc)
        
    Returns:
        Dictionary with list of reports and metadata
    """
    # Calculate skip value for pagination
    skip = (page - 1) * page_size
    
    # Get reports with filtering
    reports = await database.get_reports(status, page_size, skip)
    
    # Get total count for pagination
    # This is a simplified approach - in a real app, you might want to add a count method
    # to avoid fetching all reports just to count them
    all_reports = await database.get_reports(status)
    total_count = len(all_reports)
    
    # Calculate total pages
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    
    return {
        "reports": reports,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


async def update_comparison(
    item1: str,
    item2: str,
    item1_wins: bool,
    item2_wins: bool,
    description: str,
    emoji: str
) -> Dict[str, Any]:
    """
    Update or create a comparison based on admin corrections.
    
    Args:
        item1: The first item in the comparison
        item2: The second item in the comparison
        item1_wins: Whether the first item beats the second
        item2_wins: Whether the second item beats the first
        description: A brief explanation of the result
        emoji: A relevant emoji for the comparison
        
    Returns:
        Dictionary with updated comparison details
    """
    # Check if the comparison exists
    existing_comparison = await database.get_comparison(item1, item2)
    
    if existing_comparison:
        # Update the existing comparison
        # Note: This function doesn't exist yet in database.py, we'll add it
        updated_comparison = await database.update_comparison(
            item1=item1,
            item2=item2,
            item1_wins=item1_wins,
            item2_wins=item2_wins,
            description=description,
            emoji=emoji
        )
        return updated_comparison
    else:
        # Create a new comparison
        new_comparison = await database.create_comparison(
            item1=item1,
            item2=item2,
            item1_wins=item1_wins,
            item2_wins=item2_wins,
            description=description,
            emoji=emoji
        )
        return new_comparison