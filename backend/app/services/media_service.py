"""Media Generation Service for AI-powered image and audio generation

Implements:
- WanxImageGenerator: Aliyun Wanx-v1 image generation API
- SambertTTS: Aliyun Sambert text-to-speech API
"""
import os
import json
import base64
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

# API endpoints (Aliyun WANX & Sambert)
WANX_API_URL = "https://wanx.baidubce.com/v1/wanx/v1/text2image"
SAMBERT_API_URL = "https://nlp.cn-beijing.aliyuncs.com/api"


@dataclass
class ImageResult:
    """Result from image generation"""
    success: bool
    image_url: Optional[str] = None
    local_path: Optional[str] = None
    error: Optional[str] = None
    request_id: Optional[str] = None


@dataclass
class AudioResult:
    """Result from TTS generation"""
    success: bool
    audio_url: Optional[str] = None
    local_path: Optional[str] = None
    error: Optional[str] = None
    duration: Optional[float] = None


class WanxImageGenerator:
    """Aliyun Wanx-v1 Image Generation Service
    
    Generates images based on text prompts for video scenes.
    """
    
    def __init__(self):
        self.api_key = os.getenv("WANX_API_KEY")
        self.api_secret = os.getenv("WANX_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("WANX_API_KEY and WANX_API_SECRET environment variables must be set")
        
        self.output_dir = os.getenv("IMAGE_OUTPUT_DIR", "/home/admin/.openclaw/workspace/Marketing2/output/images")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Default generation parameters
        self.default_params = {
            "size": "720:1280",  # 9:16 aspect ratio for vertical video
            "steps": 20,
            "cfg_scale": 7.0,
            "negative_prompt": "low quality, blurry, bad anatomy, watermark, text",
        }
    
    def _get_access_token(self) -> str:
        """Get access token for API authentication (mock implementation)
        
        In production, this should use the actual Aliyun authentication flow.
        For now, returns the API key directly for Bearer token auth.
        """
        # Aliyun Wanx-v1 typically uses Bearer token authentication
        return self.api_key
    
    def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        size: Optional[str] = None,
        steps: Optional[int] = None,
    ) -> ImageResult:
        """
        Generate an image from a text prompt
        
        Args:
            prompt: Text description of the image to generate
            negative_prompt: Elements to avoid in the image
            size: Image dimensions (default: 720x1280 for 9:16)
            steps: Number of diffusion steps (default: 20)
        
        Returns:
            ImageResult with success status and image URL/path
        """
        try:
            # Prepare request payload
            payload = {
                "prompt": prompt,
                "size": size or self.default_params["size"],
                "steps": steps or self.default_params["steps"],
                "cfg_scale": self.default_params["cfg_scale"],
            }
            
            if negative_prompt:
                payload["negative_prompt"] = negative_prompt
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_access_token()}",
            }
            
            logger.info(f"Calling Wanx-v1 API with prompt: {prompt[:100]}...")
            
            # Make API request
            response = requests.post(
                WANX_API_URL,
                json=payload,
                headers=headers,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_response(result)
            else:
                error_msg = f"Wanx-v1 API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return ImageResult(success=False, error=error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "Wanx-v1 API request timed out"
            logger.error(error_msg)
            return ImageResult(success=False, error=error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Wanx-v1 API request failed: {str(e)}"
            logger.error(error_msg)
            return ImageResult(success=False, error=error_msg)
        except Exception as e:
            error_msg = f"Unexpected error in image generation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ImageResult(success=False, error=error_msg)
    
    def _parse_response(self, response: Dict) -> ImageResult:
        """Parse API response and extract image URL"""
        try:
            # Handle different response formats based on actual API
            if "data" in response:
                data = response["data"]
                if isinstance(data, list) and len(data) > 0:
                    image_url = data[0].get("url") or data[0].get("image_url")
                    request_id = response.get("request_id")
                    return ImageResult(
                        success=True,
                        image_url=image_url,
                        request_id=request_id
                    )
            
            # Alternative response format
            if "images" in response:
                image_url = response["images"][0].get("url")
                return ImageResult(success=True, image_url=image_url)
            
            # Direct URL in response
            if "url" in response:
                return ImageResult(success=True, image_url=response["url"])
            
            logger.error(f"Unexpected Wanx-v1 response format: {response}")
            return ImageResult(
                success=False,
                error="Unexpected response format from Wanx-v1 API"
            )
            
        except Exception as e:
            error_msg = f"Failed to parse Wanx-v1 response: {str(e)}"
            logger.error(error_msg)
            return ImageResult(success=False, error=error_msg)
    
    def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        retry_delay: int = 5,
        **kwargs
    ) -> ImageResult:
        """
        Generate image with automatic retry on failure
        
        Args:
            prompt: Text description for image
            max_retries: Maximum retry attempts
            retry_delay: Seconds between retries
            **kwargs: Additional arguments for generate()
        
        Returns:
            ImageResult with success status
        """
        for attempt in range(max_retries):
            result = self.generate(prompt, **kwargs)
            
            if result.success:
                logger.info(f"Image generated successfully on attempt {attempt + 1}")
                return result
            
            # Check if error is retryable
            if result.error:
                if "timeout" in result.error.lower() or "rate" in result.error.lower():
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
            
            # Non-retryable error
            return result
        
        return ImageResult(
            success=False,
            error=f"Image generation failed after {max_retries} attempts"
        )


class SambertTTS:
    """Aliyun Sambert Text-to-Speech Service
    
    Generates natural-sounding audio from text for video narration.
    Uses standard voice settings for consistent quality.
    """
    
    def __init__(self):
        self.api_key = os.getenv("SAMBERT_API_KEY")
        self.api_secret = os.getenv("SAMBERT_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("SAMBERT_API_KEY and SAMBERT_API_SECRET environment variables must be set")
        
        self.output_dir = os.getenv("AUDIO_OUTPUT_DIR", "/home/admin/.openclaw/workspace/Marketing2/output/audio")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Default voice parameters
        self.default_params = {
            "voice": "siyue",  # Standard narration voice
            "speed": 1.0,      # Normal speed
            "pitch": 0,        # Normal pitch
            "volume": 80,      # 80% volume
            "sample_rate": 24000,
        }
    
    def _get_access_token(self) -> str:
        """Get access token for API authentication
        
        In production, this should use the actual Aliyun authentication flow.
        """
        return self.api_key
    
    def generate(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        pitch: Optional[int] = None,
        volume: Optional[int] = None,
    ) -> AudioResult:
        """
        Generate audio from text using Sambert TTS
        
        Args:
            text: Text to convert to speech
            voice: Voice type (default: siyue for narration)
            speed: Speech speed (0.5-2.0, default: 1.0)
            pitch: Voice pitch adjustment (-500 to 500, default: 0)
            volume: Volume level (0-100, default: 80)
        
        Returns:
            AudioResult with success status and audio URL/path
        """
        try:
            # Prepare request payload
            payload = {
                "text": text,
                "voice": voice or self.default_params["voice"],
                "speed": speed or self.default_params["speed"],
                "pitch": pitch or self.default_params["pitch"],
                "volume": volume or self.default_params["volume"],
                "sample_rate": self.default_params["sample_rate"],
            }
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_access_token()}",
            }
            
            logger.info(f"Calling Sambert TTS API: {text[:50]}...")
            
            # Make API request
            response = requests.post(
                SAMBERT_API_URL,
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                return self._parse_response(response)
            else:
                error_msg = f"Sambert API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return AudioResult(success=False, error=error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "Sambert API request timed out"
            logger.error(error_msg)
            return AudioResult(success=False, error=error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Sambert API request failed: {str(e)}"
            logger.error(error_msg)
            return AudioResult(success=False, error=error_msg)
        except Exception as e:
            error_msg = f"Unexpected error in TTS: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return AudioResult(success=False, error=error_msg)
    
    def _parse_response(self, response: requests.Response) -> AudioResult:
        """Parse API response and extract audio"""
        try:
            result = response.json()
            
            # Check for API-level errors
            if "error_code" in result or "err_msg" in result:
                error_msg = result.get("error_msg") or result.get("err_msg")
                return AudioResult(success=False, error=error_msg)
            
            # Handle binary audio response
            if response.headers.get("Content-Type", "").startswith("audio/"):
                # Generate unique filename
                timestamp = int(time.time())
                filename = f"narration_{timestamp}.wav"
                filepath = os.path.join(self.output_dir, filename)
                
                # Save audio file
                with open(filepath, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Audio saved to: {filepath}")
                return AudioResult(
                    success=True,
                    local_path=filepath,
                    duration=self._estimate_duration_from_text(
                        response.headers.get("X-Audio-Duration", "")
                    )
                )
            
            # Handle JSON response with audio URL
            if "data" in result:
                audio_url = result["data"].get("audio_url") or result["data"].get("url")
                return AudioResult(
                    success=True,
                    audio_url=audio_url
                )
            
            # Direct audio URL
            if "audio_url" in result:
                return AudioResult(success=True, audio_url=result["audio_url"])
            
            logger.error(f"Unexpected Sambert response format: {result}")
            return AudioResult(
                success=False,
                error="Unexpected response format from Sambert API"
            )
            
        except Exception as e:
            error_msg = f"Failed to parse Sambert response: {str(e)}"
            logger.error(error_msg)
            return AudioResult(success=False, error=error_msg)
    
    def _estimate_duration_from_text(self, duration_header: str) -> Optional[float]:
        """Estimate audio duration from response header or text length"""
        try:
            if duration_header:
                return float(duration_header)
        except (ValueError, TypeError):
            pass
        return None
    
    def generate_with_retry(
        self,
        text: str,
        max_retries: int = 3,
        retry_delay: int = 3,
        **kwargs
    ) -> AudioResult:
        """
        Generate audio with automatic retry on failure
        
        Args:
            text: Text to convert to speech
            max_retries: Maximum retry attempts
            retry_delay: Seconds between retries
            **kwargs: Additional arguments for generate()
        
        Returns:
            AudioResult with success status
        """
        for attempt in range(max_retries):
            result = self.generate(text, **kwargs)
            
            if result.success:
                logger.info(f"Audio generated successfully on attempt {attempt + 1}")
                return result
            
            # Check if error is retryable
            if result.error:
                if "timeout" in result.error.lower() or "rate" in result.error.lower():
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
            
            return result
        
        return AudioResult(
            success=False,
            error=f"Audio generation failed after {max_retries} attempts"
        )


# Singleton instances
_wanx_generator = None
_sambert_tts = None

def get_wanx_generator() -> WanxImageGenerator:
    """Get singleton WanxImageGenerator instance"""
    global _wanx_generator
    if _wanx_generator is None:
        _wanx_generator = WanxImageGenerator()
    return _wanx_generator


def get_sambert_tts() -> SambertTTS:
    """Get singleton SambertTTS instance"""
    global _sambert_tts
    if _sambert_tts is None:
        _sambert_tts = SambertTTS()
    return _sambert_tts
