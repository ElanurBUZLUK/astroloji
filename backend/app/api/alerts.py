"""
Alert and notification endpoints
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from app.services import AlertService

router = APIRouter()

class AlertCreateRequest(BaseModel):
    """Alert creation request model"""
    alert_type: str = Field(..., description="Type of alert: system, chart, interpretation, etc.")
    severity: str = Field("info", description="Alert severity: info, warning, error, critical")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional alert metadata")
    user_id: Optional[str] = Field(None, description="User ID for user-specific alerts")

class AlertResponse(BaseModel):
    """Alert response model"""
    id: str
    alert_type: str
    severity: str
    title: str
    message: str
    metadata: Optional[Dict[str, Any]]
    is_read: bool
    is_resolved: bool
    created_at: str
    resolved_at: Optional[str]

@router.post("/", response_model=Dict[str, Any])
async def create_alert(alert_data: AlertCreateRequest):
    """Create new alert"""
    try:
        alert_id = AlertService.create_alert(
            alert_type=alert_data.alert_type,
            severity=alert_data.severity,
            title=alert_data.title,
            message=alert_data.message,
            metadata=alert_data.metadata,
            user_id=alert_data.user_id
        )

        if alert_id:
            return {
                "alert_id": alert_id,
                "status": "created",
                "message": "Alert created successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create alert"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating alert: {str(e)}"
        )

@router.get("/", response_model=List[AlertResponse])
async def get_alerts(user_id: Optional[str] = None, include_resolved: bool = False):
    """Get user alerts"""
    try:
        alerts = AlertService.get_alerts(user_id=user_id, include_resolved=include_resolved)
        return alerts

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving alerts: {str(e)}"
        )

@router.put("/{alert_id}/read")
async def mark_alert_as_read(alert_id: str):
    """Mark alert as read"""
    try:
        success = AlertService.mark_as_read(alert_id)
        if success:
            return {"status": "success", "message": "Alert marked as read"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with ID {alert_id} not found"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking alert as read: {str(e)}"
        )

@router.put("/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert"""
    try:
        success = AlertService.resolve_alert(alert_id)
        if success:
            return {"status": "success", "message": "Alert resolved"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with ID {alert_id} not found"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resolving alert: {str(e)}"
        )

@router.get("/stats")
async def get_alert_stats(user_id: Optional[str] = None):
    """Get alert statistics"""
    try:
        all_alerts = AlertService.get_alerts(user_id=user_id, include_resolved=True)
        active_alerts = AlertService.get_alerts(user_id=user_id, include_resolved=False)

        # Count by severity
        severity_counts = {}
        for alert in all_alerts:
            severity = alert["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Count unread alerts
        unread_count = sum(1 for alert in active_alerts if not alert["is_read"])

        return {
            "total_alerts": len(all_alerts),
            "active_alerts": len(active_alerts),
            "unread_alerts": unread_count,
            "severity_breakdown": severity_counts,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting alert stats: {str(e)}"
        )