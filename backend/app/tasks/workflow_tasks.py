"""Celery tasks for video generation workflow"""
from celery import Task
from datetime import datetime
from typing import Dict, Optional
import logging
import json
import os

from app.celery_app import celery_app
from app.services.llm_service import get_llm_service
from app.services.media_service import get_wanx_generator, get_sambert_tts
from app.services.ffmpeg_service import FFmpegRenderer, RenderConfig, get_ffmpeg_renderer
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
        
        # Trigger media generation tasks for each scene (Phase 2)
        scenes = self.db.query(Scene).filter(Scene.task_id == task_id).all()
        for scene in scenes:
            generate_media_task.apply_async(
                args=[str(scene.id)],
                queue="ai_generation"
            )
        logger.info(f"Queued {len(scenes)} media generation tasks")
        
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
    
    This is Phase 2 of the pipeline:
    1. Call Wanx-v1 API for image generation
    2. Call Sambert TTS API for audio generation
    3. Update scene with asset URLs
    
    Args:
        scene_id: UUID of the scene to process
    """
    logger.info(f"Starting media generation for scene {scene_id}")
    
    try:
        # Get scene from database
        scene = self.db.query(Scene).filter(Scene.id == scene_id).first()
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        # Get task for progress updates
        task = self.db.query(TaskModel).filter(TaskModel.id == scene.task_id).first()
        
        # Initialize media service
        wanx_generator = get_wanx_generator()
        sambert_tts = get_sambert_tts()
        
        # Update task progress
        publish_progress(scene.task_id, "progress", {
            "scene_id": scene_id,
            "status": "media_gen",
            "progress": 65,
            "message": f"开始为第{scene.sequence}个分镜生成素材"
        })
        
        # Generate image from prompt
        logger.info(f"Generating image for scene {scene_id} with prompt: {scene.image_prompt[:100]}...")
        
        publish_progress(scene.task_id, "progress", {
            "scene_id": scene_id,
            "progress": 68,
            "message": f"调用Wanx-v1生成图片..."
        })
        
        image_result = wanx_generator.generate_with_retry(
            prompt=scene.image_prompt,
            max_retries=2,
            retry_delay=10
        )
        
        if image_result.success:
            scene.image_url = image_result.image_url or image_result.local_path
            logger.info(f"Image generated successfully: {scene.image_url}")
        else:
            logger.error(f"Image generation failed: {image_result.error}")
            # Don't fail the entire task for image errors - user can retry
            scene.image_url = None
        
        # Generate audio from narration
        logger.info(f"Generating audio for scene {scene_id} with text: {scene.narration[:50]}...")
        
        publish_progress(scene.task_id, "progress", {
            "scene_id": scene_id,
            "progress": 85,
            "message": f"调用Sambert TTS生成配音..."
        })
        
        audio_result = sambert_tts.generate_with_retry(
            text=scene.narration,
            max_retries=2,
            retry_delay=5
        )
        
        if audio_result.success:
            scene.audio_url = audio_result.audio_url or audio_result.local_path
            if audio_result.duration:
                scene.duration = audio_result.duration
            logger.info(f"Audio generated successfully: {scene.audio_url}")
        else:
            logger.error(f"Audio generation failed: {audio_result.error}")
            # Don't fail the entire task for audio errors
            scene.audio_url = None
        
        # Commit changes
        self.db.commit()
        
        # Update task progress
        new_progress = 80  # Partial progress for this scene
        publish_progress(scene.task_id, "scene_complete", {
            "scene_id": scene_id,
            "sequence": scene.sequence,
            "progress": new_progress,
            "message": f"第{scene.sequence}个分镜素材生成完成",
            "image_url": scene.image_url,
            "audio_url": scene.audio_url
        })
        
        # Check if all scenes in task have media generated
        remaining_scenes = self.db.query(Scene).filter(
            Scene.task_id == scene.task_id,
            Scene.image_url.is_(None) | Scene.audio_url.is_(None)
        ).count()
        
        if remaining_scenes == 0:
            # All scenes have media, update task status to VIDEO_RENDER
            update_task_status(self.db, scene.task_id, TaskStatus.VIDEO_RENDER, progress=90)
            publish_progress(scene.task_id, "progress", {
                "progress": 90,
                "message": "所有分镜素材生成完成,准备渲染视频"
            })
        
        return {
            "status": "success",
            "scene_id": scene_id,
            "image_url": scene.image_url,
            "audio_url": scene.audio_url,
            "image_success": image_result.success,
            "audio_success": audio_result.success
        }
        
    except Exception as e:
        logger.error(f"Media generation failed for scene {scene_id}: {str(e)}", exc_info=True)
        
        # Publish error but don't mark task as failed (partial success is okay)
        publish_progress(scene.task_id, "error", {
            "scene_id": scene_id,
            "message": f"分镜{scene.sequence}素材生成部分失败: {str(e)}",
            "error": str(e)
        })
        
        # For transient errors, retry
        if "API" in str(e) or "timeout" in str(e).lower() or "connection" in str(e).lower():
            raise self.retry(exc=e)
        
        # For other errors, return partial result
        return {
            "status": "partial",
            "scene_id": scene_id,
            "error": str(e)
        }


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.workflow_tasks.render_video_task",
    max_retries=1
)
def render_video_task(self, task_id: str):
    """
    Render final video from all scene assets using FFmpeg
    
    Phase 5: Video assembly with Ken Burns effect, subtitle burning, and BGM mixing.
    
    Workflow:
    1. Collect all scene assets (images, audio)
    2. Render each scene with Ken Burns effect
    3. Add subtitles (hardsub with Source Han Sans)
    4. Mix BGM with TTS audio (BGM 20%, Voice 100%)
    5. Concatenate all scenes into final video
    6. Update task status: MEDIA_GEN → VIDEO_RENDER → SUCCESS
    
    Args:
        task_id: UUID of the task to process
    """
    from sqlalchemy.orm import Session
    from app.models.task import Task as TaskModel, TaskStatus, Scene
    
    logger.info(f"Starting video rendering for task {task_id}")
    
    db: Session = self.db
    
    try:
        # Get task from database
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Update status to VIDEO_RENDER
        update_task_status(db, task_id, TaskStatus.VIDEO_RENDER, progress=10)
        publish_progress(task_id, "progress", {
            "status": "video_render",
            "progress": 10,
            "message": "开始视频渲染"
        })
        
        # Get all scenes for this task (ordered by sequence)
        scenes = db.query(Scene).filter(Scene.task_id == task_id).order_by(Scene.sequence).all()
        
        if not scenes:
            raise ValueError(f"No scenes found for task {task_id}")
        
        logger.info(f"Found {len(scenes)} scenes for task {task_id}")
        
        # Initialize FFmpeg renderer
        config = RenderConfig(
            output_width=1080,
            output_height=1920,
            fps=30,
            bgm_volume=0.2,  # 20%
            voice_volume=1.0  # 100%
        )
        renderer = get_ffmpeg_renderer(config=config)
        
        # Output directory
        output_dir = os.getenv("RENDER_OUTPUT_DIR", "/tmp/renders")
        os.makedirs(output_dir, exist_ok=True)
        
        # Get optional BGM path
        bgm_path = os.getenv("BGM_PATH")
        font_path = os.getenv("FONT_PATH", "/usr/share/fonts/truetype/source-han-sans/SourceHanSansSC-Regular.otf")
        
        # Render each scene
        scene_videos = []
        total_scenes = len(scenes)
        
        for i, scene in enumerate(scenes):
            scene_num = i + 1
            progress = 10 + (50 * scene_num // total_scenes)  # 10-60%
            
            logger.info(f"Rendering scene {scene_num}/{total_scenes}")
            
            publish_progress(task_id, "progress", {
                "scene_id": str(scene.id),
                "scene_sequence": scene.sequence,
                "progress": progress,
                "message": f"正在渲染第{scene_num}个分镜"
            })
            
            # Skip scenes without required assets
            if not scene.image_url:
                logger.warning(f"Scene {scene_num} missing image, skipping")
                continue
            if not scene.audio_url:
                logger.warning(f"Scene {scene_num} missing audio, skipping")
                continue
            
            # Build output path for this scene
            scene_output = os.path.join(output_dir, f"{task_id}_scene_{scene_num}.mp4")
            
            # Render scene with Ken Burns, subtitles, and BGM mixing
            result = renderer.render_scene(
                image_path=scene.image_url,
                audio_path=scene.audio_url,
                output_path=scene_output,
                subtitle_text=scene.narration,  # Use narration as subtitle
                bgm_path=bgm_path,
                font_path=font_path if os.path.exists(font_path) else None,
                ken_burns=True  # Apply Ken Burns effect
            )
            
            if result["success"]:
                scene_videos.append(scene_output)
                # Update scene with video URL
                scene.video_url = scene_output
                logger.info(f"Scene {scene_num} rendered: {scene_output}")
            else:
                logger.error(f"Scene {scene_num} failed: {result.get('error')}")
        
        if not scene_videos:
            raise RuntimeError("No scenes rendered successfully")
        
        # Commit scene updates
        db.commit()
        
        # Concatenate all scene videos
        publish_progress(task_id, "progress", {
            "progress": 65,
            "message": "正在合成最终视频"
        })
        
        final_output = os.path.join(output_dir, f"{task_id}_final.mp4")
        
        concat_result = renderer.concatenate_videos(
            video_paths=scene_videos,
            output_path=final_output,
            delete_inputs=True  # Clean up scene videos
        )
        
        if not concat_result["success"]:
            raise RuntimeError(f"Concatenation failed: {concat_result.get('error')}")
        
        # Update task status to SUCCESS
        update_task_status(db, task_id, TaskStatus.SUCCESS, progress=100, error_msg=None)
        
        # Update task with final output URL
        task.output_url = final_output
        db.commit()
        
        # Publish completion
        publish_progress(task_id, "completed", {
            "progress": 100,
            "message": "视频渲染完成",
            "output_url": final_output,
            "scene_count": len(scene_videos),
            "video_count": concat_result.get("video_count", len(scene_videos))
        })
        
        logger.info(f"Video rendering complete for task {task_id}: {final_output}")
        
        return {
            "status": "success",
            "task_id": task_id,
            "output_url": final_output,
            "scene_count": len(scene_videos),
            "video_count": concat_result.get("video_count", len(scene_videos))
        }
        
    except Exception as e:
        logger.error(f"Video rendering failed for task {task_id}: {str(e)}", exc_info=True)
        
        # Update task status to FAILED
        update_task_status(db, task_id, TaskStatus.FAILED, error_msg=str(e))
        publish_progress(task_id, "error", {
            "message": f"视频渲染失败: {str(e)}",
            "error": str(e)
        })
        
        # Don't retry for rendering errors
        raise


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
