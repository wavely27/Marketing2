"""
Workflow Tasks - Video Rendering Pipeline

Phase 5: FFmpeg video rendering workflow integration.
"""

import logging
import asyncio
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

import redis

from media_service import FFmpegRenderer, RenderConfig

logger = logging.getLogger(__name__)


class RedisPublisher:
    """Redis publisher for workflow progress updates."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self._client = None
    
    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            try:
                self._client = redis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=True)
            except Exception as e:
                logger.warning(f"Could not connect to Redis: {e}")
                return None
        return self._client
    
    def publish_progress(self, task_id: str, status: str, progress: int, details: Dict = None):
        """Publish task progress to Redis."""
        message = {
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        channel = f"workflow:tasks:{task_id}:progress"
        try:
            if self.client:
                self.client.publish(channel, message)
                logger.debug(f"Published: {channel} -> {status} ({progress}%)")
        except Exception as e:
            logger.warning(f"Failed to publish progress: {e}")
    
    def set_task_data(self, task_id: str, status: str, data: Dict = None):
        """Set task data in Redis hash."""
        key = f"task:{task_id}"
        try:
            if self.client:
                self.client.hset(key, mapping={
                    "status": status,
                    "data": str(data or {}),
                    "updated_at": datetime.utcnow().isoformat()
                })
                logger.debug(f"Set task data: {key} = {status}")
        except Exception as e:
            logger.warning(f"Failed to set task data: {e}")


# Global publisher
redis_publisher: Optional[RedisPublisher] = None


def get_redis_publisher() -> Optional[RedisPublisher]:
    """Get or create Redis publisher."""
    global redis_publisher
    if redis_publisher is None:
        try:
            redis_publisher = RedisPublisher(host="localhost", port=6379)
        except Exception as e:
            logger.warning(f"Could not create Redis publisher: {e}")
            return None
    return redis_publisher


async def render_video_task(
    task_id: str,
    scenes: List[Dict],
    bgm_path: Optional[str] = None,
    font_path: Optional[str] = None,
    output_dir: str = "/tmp/renders",
    config: Optional[RenderConfig] = None
) -> Dict[str, Any]:
    """
    Celery task for rendering video from multiple scenes.
    
    Workflow:
    1. Iterate through all scenes
    2. For each scene: render image + audio + subtitle → MP4
    3. Concatenate all scene videos into final output
    4. Update status: MEDIA_GEN → VIDEO_RENDER → SUCCESS
    
    Args:
        task_id: Unique task identifier
        scenes: List of scene dicts with image_url, audio_url, narration, etc.
        bgm_path: Path to background music (optional)
        font_path: Path to font file for subtitles
        output_dir: Directory for output files
        config: Optional RenderConfig
    
    Returns:
        Dict with success status and output details
    """
    publisher = get_redis_publisher()
    
    # Initial status
    if publisher:
        publisher.set_task_data(task_id, "video_render", {"stage": "starting", "progress": 0})
        publisher.publish_progress(task_id, "video_render", 0, {"stage": "starting", "message": "开始视频渲染"})
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        renderer = FFmpegRenderer(config=config or RenderConfig())
        
        scene_videos = []
        total_scenes = len(scenes)
        
        for i, scene in enumerate(scenes):
            scene_num = i + 1
            progress = 10 + (50 * scene_num // total_scenes)  # 10-60% for scene rendering
            
            if publisher:
                publisher.publish_progress(task_id, "video_render", progress, {
                    "stage": "rendering_scene",
                    "scene": scene_num,
                    "total": total_scenes,
                    "message": f"正在渲染第{scene_num}个分镜"
                })
            
            # Build scene paths
            scene_output = os.path.join(output_dir, f"{task_id}_scene_{scene_num}.mp4")
            
            # Get local paths (could be URLs that need downloading)
            image_path = scene.get("image_url") or scene.get("image_path")
            audio_path = scene.get("audio_url") or scene.get("audio_path")
            subtitle_text = scene.get("narration") or scene.get("subtitle_text")
            
            if not image_path or not audio_path:
                logger.warning(f"Scene {scene_num} missing assets, skipping")
                continue
            
            # Render scene
            result = renderer.render_scene(
                image_path=image_path,
                audio_path=audio_path,
                output_path=scene_output,
                subtitle_text=subtitle_text,
                bgm_path=bgm_path,
                font_path=font_path,
                ken_burns=True
            )
            
            if result["success"]:
                scene_videos.append(scene_output)
                logger.info(f"Scene {scene_num} rendered: {scene_output}")
            else:
                logger.error(f"Scene {scene_num} failed: {result.get('error')}")
        
        if not scene_videos:
            raise RuntimeError("No scenes rendered successfully")
        
        # Concatenate scenes
        if publisher:
            publisher.publish_progress(task_id, "video_render", 70, {
                "stage": "concatenating",
                "message": "正在合成最终视频"
            })
        
        final_output = os.path.join(output_dir, f"{task_id}_final.mp4")
        
        concat_result = renderer.concatenate_videos(scene_videos, final_output, delete_inputs=True)
        
        if not concat_result["success"]:
            raise RuntimeError(f"Concatenation failed: {concat_result.get('error')}")
        
        # Success
        if publisher:
            publisher.publish_progress(task_id, "success", 100, {
                "stage": "completed",
                "message": "视频渲染完成",
                "output_path": final_output,
                "scene_count": len(scene_videos),
                "total_duration": sum(renderer._get_audio_duration(v) for v in scene_videos)
            })
            publisher.set_task_data(task_id, "success", {
                "output_path": final_output,
                "scene_count": len(scene_videos)
            })
        
        logger.info(f"Video render complete: {final_output}")
        
        return {
            "success": True,
            "task_id": task_id,
            "output_path": final_output,
            "scene_count": len(scene_videos),
            "status": "success"
        }
    
    except Exception as e:
        logger.exception(f"Video render failed: {e}")
        
        if publisher:
            publisher.publish_progress(task_id, "failed", 0, {
                "stage": "failed",
                "message": f"渲染失败: {str(e)}",
                "error": str(e)
            })
            publisher.set_task_data(task_id, "failed", {"error": str(e)})
        
        return {"success": False, "task_id": task_id, "error": str(e), "status": "failed"}


def update_task_status(task_id: str, from_status: str, to_status: str, details: Dict = None) -> bool:
    """Update task status from one state to another."""
    publisher = get_redis_publisher()
    if not publisher:
        return False
    
    try:
        key = f"task:{task_id}"
        current_status = publisher.client.hget(key, "status") if publisher.client else None
        
        if current_status and current_status != from_status:
            logger.warning(f"Status mismatch for {task_id}: expected {from_status}, got {current_status}")
            return False
        
        publisher.set_task_data(task_id, to_status, details)
        publisher.publish_progress(task_id, to_status, 0, {
            "stage": "status_change",
            "message": f"Status: {from_status} → {to_status}"
        })
        return True
    except Exception as e:
        logger.error(f"Failed to update task status: {e}")
        return False


# Celery task wrapper
try:
    from celery import Celery
    
    celery_app = Celery("marketing2_tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/1")
    
    @celery_app.task(bind=True, name="marketing2.render_video", max_retries=3, default_retry_delay=60)
    def celery_render_video(self, **kwargs) -> Dict[str, Any]:
        """Celery-wrapped render_video_task with retry."""
        task_id = kwargs.get("task_id", self.request.id)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(render_video_task(**kwargs))
        finally:
            loop.close()
    
except ImportError:
    logger.info("Celery not available - using synchronous execution")
