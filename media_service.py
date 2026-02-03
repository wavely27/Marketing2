"""
Media Service - FFmpeg Video Rendering Pipeline

Phase 5: Video assembly with Ken Burns effect, subtitle burning, and BGM mixing.
"""

import os
import subprocess
import tempfile
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import shutil

logger = logging.getLogger(__name__)


@dataclass
class RenderConfig:
    """Configuration for video rendering."""
    output_width: int = 1080
    output_height: int = 1920
    fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    video_bitrate: str = "8M"
    audio_bitrate: str = "192k"
    bgm_volume: float = 0.2  # 20%
    voice_volume: float = 1.0  # 100%


class FFmpegRenderer:
    """
    FFmpeg-based video renderer with Ken Burns effect, subtitle burning, and audio mixing.
    """
    
    def __init__(self, config: Optional[RenderConfig] = None, ffmpeg_path: str = "ffmpeg"):
        self.config = config or RenderConfig()
        self.ffmpeg_path = ffmpeg_path
        self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                check=True
            )
            logger.info(f"FFmpeg available: {self.ffmpeg_path}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("FFmpeg not found. Please install FFmpeg.")
            return False
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio file duration using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "json",
                    audio_path
                ],
                capture_output=True,
                text=True
            )
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except Exception as e:
            logger.warning(f"Could not get audio duration: {e}")
            return 5.0  # Default fallback
    
    def create_srt_file(self, text: str, output_path: str, start_time: float = 0, duration: float = None) -> str:
        """Create an SRT subtitle file from text."""
        if duration is None:
            duration = len(text) / 10  # Estimate: 10 chars per second
        
        end_time = start_time + duration
        
        # SRT format
        srt_content = f"""1
{self._format_srt_time(start_time)} --> {self._format_srt_time(end_time)}
{text}

"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        return output_path
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def render_scene(
        self,
        image_path: str,
        audio_path: str,
        output_path: str,
        subtitle_text: Optional[str] = None,
        bgm_path: Optional[str] = None,
        font_path: Optional[str] = None,
        ken_burns: bool = True
    ) -> Dict[str, Any]:
        """
        Render a single scene video with image + audio + optional subtitle + optional BGM.
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio not found: {audio_path}")
            if bgm_path and not os.path.exists(bgm_path):
                raise FileNotFoundError(f"BGM not found: {bgm_path}")
            
            audio_duration = self._get_audio_duration(audio_path)
            bgm_duration = self._get_audio_duration(bgm_path) if bgm_path else 0
            duration = max(audio_duration, bgm_duration) if bgm_path else audio_duration
            
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            
            cmd = self._build_scene_command(
                image_path=image_path,
                audio_path=audio_path,
                bgm_path=bgm_path,
                subtitle_text=subtitle_text,
                output_path=output_path,
                font_path=font_path,
                duration=duration,
                ken_burns=ken_burns
            )
            
            logger.info(f"Rendering scene: {output_path}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if not os.path.exists(output_path):
                raise RuntimeError("Output file not created")
            
            file_size = os.path.getsize(output_path)
            logger.info(f"Scene rendered: {output_path} ({file_size:,} bytes)")
            
            return {
                "success": True,
                "output_path": output_path,
                "duration": duration,
                "file_size": file_size
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            return {"success": False, "error": e.stderr, "output_path": None}
        except Exception as e:
            logger.error(f"Render error: {str(e)}")
            return {"success": False, "error": str(e), "output_path": None}
    
    def _build_scene_command(
        self,
        image_path: str,
        audio_path: str,
        bgm_path: Optional[str],
        subtitle_text: Optional[str],
        output_path: str,
        font_path: Optional[str],
        duration: float,
        ken_burns: bool
    ) -> List[str]:
        """Build FFmpeg command for scene rendering."""
        
        output_width = self.config.output_width
        output_height = self.config.output_height
        
        cmd = [
            self.ffmpeg_path, "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
        ]
        
        if bgm_path:
            cmd.extend(["-i", bgm_path])
        
        filters = []
        
        if ken_burns:
            zoom_speed = 0.0015
            frames = int(duration * self.config.fps)
            filters.append(
                f"zoompan=z='min(zoom+{zoom_speed},{1.5})':"
                f"d={frames}:s={output_width}x{output_height}:"
                f"fps={self.config.fps}:eval=frame"
            )
        else:
            filters.append(
                f"scale={output_width}:{output_height}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2,"
                f"setsar=1"
            )
        
        if subtitle_text:
            srt_path = output_path.replace('.mp4', '.srt')
            self.create_srt_file(subtitle_text, srt_path, 0, duration)
            
            font_name = "Source Han Sans" if not font_path else None
            force_style = f"Fontname={font_name},FontSize=24,PrimaryColour=&H00FFFFFF,Outline=2"
            
            if font_path:
                filters.append(f"subtitles={srt_path}:force_style='{force_style}':fontsdir={os.path.dirname(font_path)}")
            else:
                filters.append(f"subtitles={srt_path}:force_style='{force_style}'")
        
        cmd.extend(["-vf", ",".join(filters)])
        
        cmd.extend([
            "-t", str(duration),
            "-r", str(self.config.fps),
            "-c:v", self.config.video_codec,
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-b:v", self.config.video_bitrate,
        ])
        
        if bgm_path:
            cmd.extend([
                "-filter_complex", f"[0:a][1:a]amix=inputs=2:duration=first:weights={self.config.voice_volume} {self.config.bgm_volume}[aout]",
                "-map", "[aout]",
                "-c:a", self.config.audio_codec,
                "-b:a", self.config.audio_bitrate,
            ])
        else:
            cmd.extend([
                "-c:a", self.config.audio_codec,
                "-b:a", self.config.audio_bitrate,
            ])
        
        cmd.append(output_path)
        return cmd
    
    def concatenate_videos(self, video_paths: List[str], output_path: str, delete_inputs: bool = False) -> Dict[str, Any]:
        """Concatenate multiple videos into one using FFmpeg concat demuxer."""
        if not video_paths:
            return {"success": False, "error": "No video paths provided"}
        
        if len(video_paths) == 1:
            shutil.copy(video_paths[0], output_path)
            return {"success": True, "output_path": output_path}
        
        try:
            concat_content = "\n".join(f"file '{os.path.abspath(p)}'" for p in video_paths)
            concat_path = output_path.replace('.mp4', '_concat.txt')
            
            with open(concat_path, 'w') as f:
                f.write(concat_content)
            
            cmd = [
                self.ffmpeg_path, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_path,
                "-c", "copy",
                "-movflags", "+faststart",
                output_path
            ]
            
            logger.info(f"Concatenating {len(video_paths)} videos into {output_path}")
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            os.remove(concat_path)
            
            if delete_inputs:
                for p in video_paths:
                    if os.path.exists(p):
                        os.remove(p)
            
            return {
                "success": True,
                "output_path": output_path,
                "video_count": len(video_paths)
            }
            
        except Exception as e:
            logger.error(f"Concatenation error: {str(e)}")
            return {"success": False, "error": str(e)}


# ============================================================================
# FFmpeg Command Wrappers (for reference)
# ============================================================================

def render_basic_synthesis(image_path: str, audio_path: str, output_path: str,
                          output_width: int = 1080, output_height: int = 1920) -> Dict[str, Any]:
    """Basic image + audio synthesis command."""
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
        "-vf", f"scale={output_width}:{output_height}:force_original_aspect_ratio=decrease,pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2,setsar=1",
        "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-shortest", output_path
    ]
    return _execute_ffmpeg(cmd, output_path)


def render_ken_burns(image_path: str, audio_path: str, output_path: str,
                    output_width: int = 1080, output_height: int = 1920,
                    fps: int = 30, zoom_speed: float = 0.0015) -> Dict[str, Any]:
    """Ken Burns effect: slow pan and zoom."""
    try:
        duration_result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", audio_path],
            capture_output=True, text=True
        )
        audio_duration = float(json.loads(duration_result.stdout)["format"]["duration"])
        frames = int(audio_duration * fps)
    except:
        frames = 300
        audio_duration = 10.0
    
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
        "-vf", f"zoompan=z='min(zoom+{zoom_speed},1.5)':d={frames}:s={output_width}x{output_height}:fps={fps}:eval=frame",
        "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", "-shortest", output_path
    ]
    return _execute_ffmpeg(cmd, output_path)


def burn_subtitles(input_path: str, output_path: str, subtitle_path: str,
                   font_name: str = "Source Han Sans", font_size: int = 24) -> Dict[str, Any]:
    """Burn subtitles using subtitles filter."""
    force_style = f"Fontname={font_name},FontSize={font_size},PrimaryColour=&H00FFFFFF,Outline=2"
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", f"subtitles={subtitle_path}:force_style='{force_style}'",
        "-c:a", "copy", output_path
    ]
    return _execute_ffmpeg(cmd, output_path)


def _execute_ffmpeg(cmd: list, output_path: str) -> Dict[str, Any]:
    """Execute FFmpeg command and return result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if os.path.exists(output_path):
            return {"success": True, "output_path": output_path, "file_size": os.path.getsize(output_path)}
        return {"success": False, "error": "Output not created"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}
