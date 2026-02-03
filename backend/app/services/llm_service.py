"""LLM Service for script optimization using Qwen (DashScope API)"""
import os
import json
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import dashscope, fall back to openai-compatible client
try:
    import dashscope
    from dashscope import Generation
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    logger.warning("dashscope library not available, will use OpenAI-compatible client")
    try:
        from openai import OpenAI
    except ImportError:
        logger.error("Neither dashscope nor openai library available!")


class LLMService:
    """Service for LLM-based script optimization and scene generation"""
    
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY environment variable not set")
        
        if DASHSCOPE_AVAILABLE:
            dashscope.api_key = self.api_key
            self.model = "qwen-plus"
        else:
            # Use OpenAI-compatible client for DashScope
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            self.model = "qwen-plus"
    
    def _call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Call LLM with message history"""
        try:
            if DASHSCOPE_AVAILABLE:
                response = Generation.call(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    result_format='message'
                )
                
                if response.status_code == 200:
                    return response.output.choices[0].message.content
                else:
                    raise Exception(f"DashScope API error: {response.code} - {response.message}")
            else:
                # Use OpenAI-compatible client
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise
    
    def extract_role_setting(self, novel_text: str) -> str:
        """
        Step 1: Extract character descriptions from novel text
        Returns: e.g., "男主:黑发剑客,白衣; 女主:红裙舞者,长发"
        """
        prompt = f"""请从以下小说文本中提取主要角色的外貌特征描述。
输出格式要求:
- 简洁的角色标签,例如: "男主:黑发剑客,白衣; 女主:红裙舞者,长发"
- 只提取核心外貌特征(发型、服装、体型等)
- 如果没有明确角色,输出"通用角色"

小说文本:
{novel_text[:1000]}

只输出角色设定,不要其他内容:"""
        
        messages = [{"role": "user", "content": prompt}]
        role_setting = self._call_llm(messages, temperature=0.3)
        return role_setting.strip()
    
    def optimize_and_breakdown_script(
        self, 
        novel_text: str, 
        role_setting: str,
        scenes_per_paragraph: int = 3
    ) -> List[Dict]:
        """
        Step 2 & 3: Rewrite novel as engaging short video script and break into scenes
        
        Args:
            novel_text: Original novel text
            role_setting: Character descriptions extracted in step 1
            scenes_per_paragraph: Number of scenes per paragraph (default: 3)
        
        Returns:
            List of scene dictionaries with structure:
            [
                {
                    "sequence": 1,
                    "narration": "旁白文字",
                    "image_prompt": "画面描述(包含角色设定)",
                    "duration": 5.0
                },
                ...
            ]
        """
        prompt = f"""你是一个专业的短视频脚本编剧。请将以下小说文本改写为吸引人的竖屏短视频脚本。

**角色设定**: {role_setting}

**改写要求**:
1. 将文本改写为适合短视频的精炼文案(旁白)
2. 按照"1段文字 → {scenes_per_paragraph}个镜头"的规则切分场景
3. 为每个镜头生成:
   - narration: 旁白文字(简洁有力,适合配音)
   - image_prompt: 画面描述(必须包含角色设定,例如"{role_setting},剑客正在...")
   - duration: 预估时长(3-8秒)
4. 保持角色视觉一致性 - 所有画面描述必须引用角色设定

**输出格式** (JSON):
```json
[
  {{
    "sequence": 1,
    "narration": "夜幕降临,江湖再起风云",
    "image_prompt": "{role_setting},黑发剑客站在山崖边,背对镜头,白衣飘飘",
    "duration": 5.0
  }},
  {{
    "sequence": 2,
    "narration": "一封神秘的挑战书",
    "image_prompt": "{role_setting},特写镜头,黑发剑客手持一封红色信函,表情凝重",
    "duration": 4.0
  }}
]
```

小说原文:
{novel_text}

请只输出JSON数组,不要其他内容:"""
        
        messages = [{"role": "user", "content": prompt}]
        response = self._call_llm(messages, temperature=0.8)
        
        # Extract JSON from response
        try:
            # Try to find JSON array in response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            scenes = json.loads(response)
            
            # Validate structure
            if not isinstance(scenes, list):
                raise ValueError("Response is not a JSON array")
            
            for scene in scenes:
                if not all(key in scene for key in ["sequence", "narration", "image_prompt", "duration"]):
                    raise ValueError(f"Scene missing required fields: {scene}")
            
            return scenes
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {response}")
            raise ValueError(f"LLM returned invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Scene validation failed: {str(e)}")
            raise
    
    def script_optimization(
        self, 
        novel_text: str,
        user_role_setting: Optional[str] = None,
        scenes_per_paragraph: int = 3
    ) -> Dict:
        """
        Complete script optimization workflow
        
        Args:
            novel_text: Original novel text
            user_role_setting: Optional user-provided role setting (overrides extraction)
            scenes_per_paragraph: Number of scenes per paragraph
        
        Returns:
            {
                "role_setting": "角色设定",
                "scenes": [scene1, scene2, ...]
            }
        """
        logger.info("Starting script optimization workflow")
        
        # Step 1: Extract or use provided role setting
        if user_role_setting:
            role_setting = user_role_setting
            logger.info(f"Using user-provided role setting: {role_setting}")
        else:
            logger.info("Extracting role setting from novel text")
            role_setting = self.extract_role_setting(novel_text)
            logger.info(f"Extracted role setting: {role_setting}")
        
        # Step 2 & 3: Optimize script and break down into scenes
        logger.info(f"Generating scenes ({scenes_per_paragraph} per paragraph)")
        scenes = self.optimize_and_breakdown_script(
            novel_text, 
            role_setting,
            scenes_per_paragraph
        )
        logger.info(f"Generated {len(scenes)} scenes")
        
        return {
            "role_setting": role_setting,
            "scenes": scenes
        }


# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get singleton LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
