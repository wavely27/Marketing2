"""Celery tasks for video generation workflow"""
from celery import Task
from datetime import datetime
from typing import Dict, Optional
import logging
import json

from app.celery_app import celery_app
from app.services.llm_service import get_llm_service
from app.core.database import SessionLocal
from app.models.task import Task as TaskModel, TaskStatus, Scene

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task class with database session management"""
    _db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


def update_task_status(
    db_session,
    task_id: str,
    status: TaskStatus,
    progress: Optional[int] = None,
    error_msg: Optional[str] = None
):
    """Helper function to update task status in database"""
    task = db_session.query(TaskModel).filter(TaskModel.id == task_id).first()
    if task:
        task.status = status
        task.updated_at = datetime.utcnow()
        if progress is not None:
            task.progress = progress
        if error_msg is not None:
            task.error_msg = error_msg
        db_session.commit()
        logger.info(f"Task {task_id} status updated to {status.value}, progress: {progress}%")
    else:
        logger.error(f"Task {task_id} not found in database")


def publish_progress(task_id: str, event_type: str, data: Dict):
    """
    Publish progress event to Redis for SSE streaming
    Uses Redis Pub/Sub pattern
    """
    try:
        import redis
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        
        channel = f"task_progress:{task_id}"
        message = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        r.publish(channel, json.dumps(message))
        logger.debug(f"Published {event_type} event for task {task_id}")
    except Exception as e:
        logger.error(f"Failed to publish progress event: {str(e)}")


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.workflow_tasks.generate_script_task",
    max_retries=3,
    default_retry_delay=60
)
def generate_script_task(self, task_id: str):
    """
    Generate script and scenes from novel text using LLM
    
    This is Phase 1 of the video generation pipeline:
    1. Extract/use role settings
    2. Call LLM to optimize script and break into scenes
    3. Save scenes to database
    4. Update task status to MEDIA_GEN
    
    Args:
        task_id: UUID of the task to process
    """
    logger.info(f"Starting script generation for task {task_id}")
    
    try:
        # Get task from database
        task = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Update status to SCRIPT_GEN
        update_task_status(self.db, task_id, TaskStatus.SCRIPT_GEN, progress=10)
        publish_progress(task_id, "progress", {"status": "script_gen", "progress": 10, "message": "开始生成脚本..."})
        
        # Extract input parameters
        input_params = task.input_params or {}
        novel_text = input_params.get("novel_text")
        user_role_setting = input_params.get("role_setting")
        scenes_per_paragraph = input_params.get("scenes_per_paragraph", 3)
        
        if not novel_text:
            raise ValueError("novel_text not found in input_params")
        
        # Validate novel text length
        if len(novel_text) > 5000:
            raise ValueError(f"novel_text exceeds 5000 character limit (got {len(novel_text)})")
        
        logger.info(f"Processing novel text ({len(novel_text)} chars)")
        
        # Call LLM service
        publish_progress(task_id, "progress", {"progress": 20, "message": "调用LLM优化脚本..."})
        
        llm_service = get_llm_service()
        result = llm_service.script_optimization(
            novel_text=novel_text,
            user_role_setting=user_role_setting,
            scenes_per_paragraph=scenes_per_paragraph
        )
        
        role_setting = result["role_setting"]
        scenes_data = result["scenes"]
        
        logger.info(f"LLM generated {len(scenes_data)} scenes with role setting: {role_setting}")
        
        # Update task with role setting
        input_params["role_setting"] = role_setting
        task.input_params = input_params
        self.db.commit()
        
        publish_progress(task_id, "progress", {"progress": 50, "message": f"脚本生成完成,共{len(scenes_data)}个分镜"})
        
        # Save scenes to database
        for scene_data in scenes_data:
            scene = Scene(
                task_id=task_id,
                sequence=scene_data["sequence"],
                narration=scene_data["narration"],
                image_prompt=scene_data["image_prompt"],
                duration=scene_data.get("duration", 5.0),
                script_text=scene_data.get("script_text", scene_data["narration"])  # Use narration as fallback
            )
            self.db.add(scene)
        
        self.db.commit()
        logger.info(f"Saved {len(scenes_data)} scenes to database")
        
        # Update task status to MEDIA_GEN (ready for next phase)
        update_task_status(self.db, task_id, TaskStatus.MEDIA_GEN, progress=60)
        publish_progress(task_id, "scene_complete", {
            "progress": 60,
            "message": "脚本生成完成,准备生成素材",
            "scene_count": len(scenes_data)
        })
        
        # TODO: Trigger media generation tasks (Phase 2)
        # This would call generate_media_task.delay(task_id) for each scene
        
        return {
            "status": "success",
            "task_id": task_id,
            "scene_count": len(scenes_data),
            "role_setting": role_setting
        }
        
    except Exception as e:
        logger.error(f"Script generation failed for task {task_id}: {str(e)}", exc_info=True)
        
        # Update task status to FAILED
        update_task_status(self.db, task_id, TaskStatus.FAILED, error_msg=str(e))
        publish_progress(task_id, "error", {
            "message": f"脚本生成失败: {str(e)}",
            "error": str(e)
        })
        
        # Retry for transient errors
        if "API" in str(e) or "timeout" in str(e).lower():
            raise self.retry(exc=e)
        else:
            raise


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.workflow_tasks.generate_media_task",
    max_retries=2,
    default_retry_delay=30
)
def generate_media_task(self, scene_id: str):
    """
    Generate media assets (image + audio) for a single scene
    
    This is Phase 2 of the pipeline (to be implemented):
    1. Call Wanx-v1 API for image generation
    2. Call Sambert TTS API for audio generation
    3. Update scene with asset URLs
    
    Args:
        scene_id: UUID of the scene to process
    """
    logger.info(f"Media generation task for scene {scene_id} - TO BE IMPLEMENTED")
    # TODO: Implement in Phase 4 (AI Service Integration)
    pass


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.workflow_tasks.render_video_task",
    max_retries=1
)
def render_video_task(self, task_id: str):
    """
    Render final video from all scene assets using FFmpeg
    
    This is Phase 3 of the pipeline (to be implemented):
    1. Collect all scene assets (images, audio)
    2. Apply Ken Burns effect to images
    3. Add subtitles (hardsub)
    4. Mix BGM with TTS audio
    5. Render final 9:16 video
    
    Args:
        task_id: UUID of the task to process
    """
    logger.info(f"Video rendering task for {task_id} - TO BE IMPLEMENTED")
    # TODO: Implement in Phase 5 (Video Processing)
    pass


# Utility function to trigger the full workflow
def start_workflow(task_id: str):
    """
    Start the complete video generation workflow
    Chains: script generation → media generation → video rendering
    """
    logger.info(f"Starting workflow for task {task_id}")
    
    # Start with script generation
    # The task will automatically trigger subsequent phases
    generate_script_task.apply_async(args=[str(task_id)], queue="ai_generation")
    
    logger.info(f"Workflow queued for task {task_id}")
