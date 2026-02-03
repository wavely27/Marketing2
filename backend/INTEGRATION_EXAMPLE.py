"""
Example integration: Connecting Phase 3 tasks with FastAPI endpoints

This demonstrates how to integrate the Celery tasks with your existing
FastAPI workflow endpoints.
"""

# In your app/api/endpoints/workflow.py, modify the create endpoint:

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from uuid import uuid4

from app.core.database import get_db
from app.models.task import Task, TaskStatus
from app.tasks import start_workflow  # Import from Phase 3

router = APIRouter()


class CreateWorkflowRequest(BaseModel):
    """Request model for workflow creation"""
    novel_text: str = Field(..., max_length=5000, description="Novel text (max 5000 chars)")
    role_setting: str | None = Field(None, description="Optional character setting")
    scenes_per_paragraph: int = Field(3, ge=1, le=5, description="Scenes per paragraph")


class CreateWorkflowResponse(BaseModel):
    """Response model for workflow creation"""
    task_id: str
    status: str
    message: str


@router.post("/create", response_model=CreateWorkflowResponse)
def create_workflow(
    request: CreateWorkflowRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new video generation workflow
    
    This endpoint:
    1. Creates a task record in the database
    2. Queues the async workflow (Celery)
    3. Returns task_id for progress tracking
    """
    try:
        # Create task record
        task = Task(
            id=uuid4(),
            type="novel_to_video",
            status=TaskStatus.PENDING,
            progress=0,
            input_params={
                "novel_text": request.novel_text,
                "role_setting": request.role_setting,
                "scenes_per_paragraph": request.scenes_per_paragraph
            }
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Queue async workflow (Phase 3)
        start_workflow(str(task.id))
        
        return CreateWorkflowResponse(
            task_id=str(task.id),
            status="queued",
            message="视频生成任务已创建，正在处理中..."
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


# SSE endpoint for real-time progress
from fastapi.responses import StreamingResponse
import asyncio
import redis.asyncio as aioredis
import json
import os


async def event_stream(task_id: str):
    """
    Server-Sent Events stream for task progress
    Subscribes to Redis Pub/Sub channel
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = await aioredis.from_url(redis_url)
    pubsub = redis_client.pubsub()
    
    channel = f"task_progress:{task_id}"
    await pubsub.subscribe(channel)
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"].decode("utf-8")
                yield f"data: {data}\n\n"
                
                # Check for terminal events
                event_data = json.loads(data)
                if event_data.get("event") in ["finish", "error"]:
                    break
                    
    finally:
        await pubsub.unsubscribe(channel)
        await redis_client.close()


@router.get("/events/{task_id}")
async def stream_progress(task_id: str):
    """
    SSE endpoint for real-time task progress
    
    Usage (JavaScript):
    ```javascript
    const eventSource = new EventSource(`/api/v1/workflow/events/${taskId}`);
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data.event, data.data);
    };
    ```
    """
    return StreamingResponse(
        event_stream(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# Get task details
from app.models.task import Task as TaskModel


@router.get("/{task_id}")
def get_task_details(task_id: str, db: Session = Depends(get_db)):
    """Get complete task details including all scenes"""
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task.to_dict()


# Cancel task
@router.post("/{task_id}/cancel")
def cancel_task(task_id: str, db: Session = Depends(get_db)):
    """Cancel a running task"""
    from app.celery_app import celery_app
    
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status in [TaskStatus.SUCCESS, TaskStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Task already completed")
    
    # Revoke Celery task
    celery_app.control.revoke(task_id, terminate=True)
    
    # Update database
    task.status = TaskStatus.FAILED
    task.error_msg = "Cancelled by user"
    db.commit()
    
    return {"message": "Task cancelled"}
