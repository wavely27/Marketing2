"""Workflow API endpoints for video generation"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.models.task import Task, TaskStatus

router = APIRouter(prefix="/api/v1/workflow", tags=["workflow"])


class CreateWorkflowRequest(BaseModel):
    """Request body for creating a new workflow"""
    novel_text: str = Field(..., max_length=5000, description="Novel text to convert to video")
    role_setting: Optional[str] = Field(None, description="Character settings (e.g., '男主:黑发')")
    style: Optional[str] = Field("default", description="Visual style preference")


class CreateWorkflowResponse(BaseModel):
    """Response for workflow creation"""
    task_id: str
    status: str
    message: str


@router.post("/create", response_model=CreateWorkflowResponse)
async def create_workflow(
    request: CreateWorkflowRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new video generation workflow
    
    This endpoint:
    1. Creates a Task record in the database
    2. Stores input parameters
    3. Returns the task_id for tracking
    
    Note: Actual processing (Celery tasks) will be triggered in Phase 3.
    For now, this is a "ping" endpoint to verify frontend-backend connectivity.
    """
    try:
        # Create new task
        task = Task(
            type="novel_to_video",
            status=TaskStatus.PENDING,
            progress=0,
            input_params={
                "novel_text": request.novel_text,
                "role_setting": request.role_setting,
                "style": request.style
            }
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        return CreateWorkflowResponse(
            task_id=str(task.id),
            status=task.status.value,
            message="Workflow created successfully"
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.get("/{task_id}")
async def get_workflow(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get workflow status and details
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task.to_dict()
