# Phase 3 Implementation - Asynchronous Task Processing & LLM Integration

## ✅ Completed Components

### 1. **Celery Setup** (`backend/app/celery_app.py`)
- Configured Celery with Redis as broker and backend
- Defined three task queues:
  - `default`: Lightweight tasks
  - `ai_generation`: AI API calls (rate-limited to 10/min for scripts, 20/min for media)
  - `video_processing`: CPU-intensive FFmpeg tasks
- Configured retry policies and task routing

### 2. **LLM Service** (`backend/app/services/llm_service.py`)
- Implemented complete script optimization workflow
- **Features**:
  - Role extraction from novel text
  - Script rewriting for short video format
  - Scene breakdown (1 paragraph → 3 scenes by default)
  - Character consistency enforcement in prompts
- **API Support**:
  - Primary: `dashscope` library (native DashScope SDK)
  - Fallback: `openai` library (OpenAI-compatible mode)
- **Three-step workflow**:
  1. `extract_role_setting()`: Extract character descriptions
  2. `optimize_and_breakdown_script()`: Rewrite + scene breakdown
  3. `script_optimization()`: Complete workflow wrapper

### 3. **Workflow Tasks** (`backend/app/tasks/workflow_tasks.py`)
- **`generate_script_task`**: Main LLM integration task
  - Fetches task from database
  - Calls LLM service for script generation
  - Saves scenes to database
  - Updates task status and progress
  - Publishes real-time events via Redis Pub/Sub
- **`generate_media_task`**: Stub for Phase 4 (image + audio generation)
- **`render_video_task`**: Stub for Phase 5 (video rendering)
- **Progress tracking**: Redis Pub/Sub for SSE streaming
- **Error handling**: Automatic retry for transient API failures

## 📦 Dependencies Required

Add to `backend/requirements.txt`:
```txt
# Async Task Queue
celery==5.3.4
redis==5.0.1

# LLM Integration (install one of the following)
dashscope>=1.14.0  # Recommended: Native Alibaba DashScope SDK
# OR
openai>=1.0.0  # Alternative: OpenAI-compatible client

# For Redis Pub/Sub in tasks
redis[hiredis]==5.0.1
```

## 🚀 Usage

### Start Celery Worker
```bash
# From backend/ directory
cd backend

# Worker for AI tasks (queue: ai_generation)
celery -A app.celery_app worker \
  --loglevel=info \
  --queues=ai_generation \
  --concurrency=4 \
  --max-tasks-per-child=100

# Worker for video tasks (queue: video_processing)
celery -A app.celery_app worker \
  --loglevel=info \
  --queues=video_processing \
  --concurrency=1 \
  --max-tasks-per-child=50
```

### Trigger Workflow Programmatically
```python
from app.tasks import start_workflow

# After creating a task in the database
task_id = "some-uuid-here"
start_workflow(task_id)
```

### Environment Variables
```bash
# Required
export DASHSCOPE_API_KEY="sk-your-dashscope-api-key"

# Optional (defaults shown)
export REDIS_URL="redis://localhost:6379/0"
export DATABASE_URL="postgresql://admin:password@localhost:5432/marketing2"
```

## 🔄 Workflow Flow

```
User Request → FastAPI
    ↓
Create Task (DB) → status=PENDING
    ↓
Queue: start_workflow(task_id)
    ↓
[Celery Worker - ai_generation queue]
    ↓
generate_script_task:
  1. Update status → SCRIPT_GEN
  2. Call LLM service
     - Extract roles
     - Optimize script
     - Break into scenes (1 para → 3 scenes)
  3. Save scenes to DB
  4. Update status → MEDIA_GEN
  5. Publish progress events (Redis Pub/Sub)
    ↓
[TODO: Phase 4] generate_media_task (per scene)
    ↓
[TODO: Phase 5] render_video_task
    ↓
status=SUCCESS
```

## 📊 Database Flow

**Before task execution**:
```
Task: {
  id: "uuid",
  status: "pending",
  input_params: {
    "novel_text": "...",
    "role_setting": null  // Optional user input
  }
}
Scenes: []
```

**After `generate_script_task`**:
```
Task: {
  id: "uuid",
  status: "media_gen",
  progress: 60,
  input_params: {
    "novel_text": "...",
    "role_setting": "男主:黑发剑客,白衣; 女主:红裙舞者,长发"  // LLM extracted
  }
}

Scenes: [
  {
    sequence: 1,
    narration: "夜幕降临,江湖再起风云",
    image_prompt: "男主:黑发剑客,白衣,站在山崖边,背对镜头",
    duration: 5.0
  },
  {
    sequence: 2,
    narration: "一封神秘的挑战书",
    image_prompt: "男主:黑发剑客,白衣,特写镜头,手持红色信函",
    duration: 4.0
  },
  ...
]
```

## 🎯 Real-time Progress Events (Redis Pub/Sub)

Channel: `task_progress:{task_id}`

**Event Types**:
```json
// Progress update
{
  "event": "progress",
  "timestamp": "2024-01-01T12:00:00",
  "data": {
    "status": "script_gen",
    "progress": 20,
    "message": "调用LLM优化脚本..."
  }
}

// Scene completion
{
  "event": "scene_complete",
  "timestamp": "2024-01-01T12:01:00",
  "data": {
    "progress": 60,
    "message": "脚本生成完成,准备生成素材",
    "scene_count": 6
  }
}

// Error
{
  "event": "error",
  "timestamp": "2024-01-01T12:02:00",
  "data": {
    "message": "脚本生成失败: API rate limit exceeded",
    "error": "..."
  }
}
```

## 🧪 Testing

### Test LLM Service Standalone
```python
from app.services.llm_service import get_llm_service

llm = get_llm_service()
result = llm.script_optimization(
    novel_text="夜幕降临，江湖再起风云。一封神秘的挑战书送到了剑客李云手中...",
    scenes_per_paragraph=3
)

print(f"Role Setting: {result['role_setting']}")
print(f"Scenes: {len(result['scenes'])}")
for scene in result['scenes']:
    print(f"  [{scene['sequence']}] {scene['narration']}")
```

### Test Celery Task
```python
from app.tasks import generate_script_task
from app.models.task import Task, TaskStatus
from app.core.database import SessionLocal

# Create test task
db = SessionLocal()
task = Task(
    type="novel_to_video",
    status=TaskStatus.PENDING,
    input_params={
        "novel_text": "夜幕降临，江湖再起风云。一封神秘的挑战书送到了剑客李云手中..."
    }
)
db.add(task)
db.commit()

# Queue task
result = generate_script_task.delay(str(task.id))
print(f"Task queued: {result.id}")
```

## ⚠️ Error Handling

### Sensitive Content Blocking
If DashScope API returns sensitive content error, the task:
1. Sets task status to `FAILED`
2. Stores error message in `task.error_msg`
3. Does NOT retry (user must modify prompt)

### Transient API Failures
For network/timeout errors:
1. Automatically retries up to 3 times
2. 60-second delay between retries
3. Exponential backoff via Celery

### Invalid JSON from LLM
If LLM returns malformed JSON:
1. Task fails immediately (no retry)
2. Error logged with full LLM response
3. User can regenerate with different prompt

## 🔜 Next Steps (Future Phases)

**Phase 4 - AI Service Integration**:
- Implement `generate_media_task`
- Integrate Wanx-v1 for image generation
- Integrate Sambert for TTS audio

**Phase 5 - Video Processing**:
- Implement `render_video_task`
- FFmpeg pipeline (Ken Burns, subtitles, BGM mixing)
- Final 9:16 MP4 output

---

**Implementation Status**: ✅ Phase 3 Complete
**Next**: Integrate with FastAPI endpoints + implement Phase 4
