"""Task and Scene Database Models"""
from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TaskStatus(str, PyEnum):
    """Task status enumeration"""
    PENDING = "pending"
    SCRIPT_GEN = "script_gen"
    MEDIA_GEN = "media_gen"
    VIDEO_RENDER = "video_render"
    SUCCESS = "success"
    FAILED = "failed"


class Task(Base):
    """Main task table for video generation workflow"""
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(String(50), nullable=False, default="novel_to_video")
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    input_params = Column(JSON)  # Store novel_text, role_setting, etc.
    output_url = Column(String(500))
    error_msg = Column(Text)

    # Relationship to scenes
    scenes = relationship("Scene", back_populates="task", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            "id": str(self.id),
            "type": self.type,
            "status": self.status.value,
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "input_params": self.input_params,
            "output_url": self.output_url,
            "error_msg": self.error_msg,
            "scenes": [scene.to_dict() for scene in self.scenes] if self.scenes else []
        }


class Scene(Base):
    """Scene table - individual video segments"""
    __tablename__ = "scenes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    sequence = Column(Integer, nullable=False)
    script_text = Column(Text)
    narration = Column(Text)
    image_prompt = Column(Text)
    image_url = Column(String(500))
    audio_url = Column(String(500))
    video_url = Column(String(500))
    duration = Column(Float, default=0.0)

    # Relationship to parent task
    task = relationship("Task", back_populates="scenes")

    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "sequence": self.sequence,
            "script_text": self.script_text,
            "narration": self.narration,
            "image_prompt": self.image_prompt,
            "image_url": self.image_url,
            "audio_url": self.audio_url,
            "video_url": self.video_url,
            "duration": self.duration
        }
