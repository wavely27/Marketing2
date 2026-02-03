```
Marketing2/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                          # FastAPI application
│   │   │
│   │   ├── celery_app.py                    # ✅ NEW: Celery configuration
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── endpoints/
│   │   │       ├── __init__.py
│   │   │       └── workflow.py              # Workflow endpoints (to be updated)
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── database.py                  # Database session management
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── task.py                      # Task & Scene models
│   │   │
│   │   ├── services/                        # ✅ NEW: Services layer
│   │   │   └── llm_service.py               # ✅ NEW: LLM/Qwen integration
│   │   │
│   │   └── tasks/                           # ✅ NEW: Celery tasks
│   │       ├── __init__.py                  # ✅ NEW
│   │       └── workflow_tasks.py            # ✅ NEW: Workflow tasks
│   │
│   ├── requirements.txt                     # ✅ UPDATED: Added celery, redis, dashscope
│   ├── start_worker.sh                      # ✅ NEW: Worker startup script
│   └── INTEGRATION_EXAMPLE.py               # ✅ NEW: FastAPI integration guide
│
├── TECHNICAL_DESIGN.md                      # Original design doc
├── PHASE3_IMPLEMENTATION.md                 # ✅ NEW: Implementation guide
└── PHASE3_DELIVERY.md                       # ✅ NEW: Delivery summary

NEW FILES (Phase 3):
  ✅ backend/app/celery_app.py              (80 lines)
  ✅ backend/app/services/llm_service.py    (260 lines)
  ✅ backend/app/tasks/__init__.py          (15 lines)
  ✅ backend/app/tasks/workflow_tasks.py    (240 lines)
  ✅ backend/start_worker.sh                (60 lines)
  ✅ backend/INTEGRATION_EXAMPLE.py         (180 lines)
  ✅ PHASE3_IMPLEMENTATION.md               (Documentation)
  ✅ PHASE3_DELIVERY.md                     (Summary)

UPDATED FILES:
  ✅ backend/requirements.txt               (Added 3 dependencies)

TOTAL DELIVERABLES: 9 files
CORE IMPLEMENTATION: 595 lines of production code
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Vue.js)                    │
│                    [To be connected]                    │
└────────────┬────────────────────────────────────────────┘
             │ HTTP/SSE
             ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Server (app/main.py)               │
│  ┌─────────────────────────────────────────────────┐   │
│  │  POST /api/v1/workflow/create                   │   │
│  │  GET  /api/v1/workflow/{id}                     │   │
│  │  GET  /api/v1/workflow/events/{id}  (SSE)       │   │
│  └─────────────────────────────────────────────────┘   │
└────────┬──────────────────────────────────┬─────────────┘
         │                                  │
         │ DB Access                        │ Task Queue
         ▼                                  ▼
┌────────────────────┐          ┌────────────────────────┐
│    PostgreSQL      │          │    Redis Broker        │
│  ┌──────────────┐  │          │  ┌──────────────────┐  │
│  │   tasks      │  │          │  │ Queue: ai_gen    │  │
│  │   scenes     │  │◄─────────┤  │ Queue: video     │  │
│  └──────────────┘  │          │  │ Pub/Sub: events  │  │
└────────────────────┘          │  └──────────────────┘  │
                                └────────┬───────────────┘
                                         │
                                         ▼
                   ┌─────────────────────────────────────┐
                   │  Celery Workers (start_worker.sh)  │
                   │  ┌───────────────────────────────┐ │
                   │  │ celery_app.py                 │ │
                   │  │  - Config & Queue Routing     │ │
                   │  └───────────────────────────────┘ │
                   │  ┌───────────────────────────────┐ │
                   │  │ workflow_tasks.py             │ │
                   │  │  ┌─────────────────────────┐  │ │
                   │  │  │ generate_script_task    │  │ │
                   │  │  │  1. Get task from DB    │  │ │
                   │  │  │  2. Call LLM service ───┼──┼─┤
                   │  │  │  3. Save scenes to DB   │  │ │ │
                   │  │  │  4. Publish progress    │  │ │ │
                   │  │  └─────────────────────────┘  │ │ │
                   │  │  ┌─────────────────────────┐  │ │ │
                   │  │  │ generate_media_task     │  │ │ │
                   │  │  │  [Stub for Phase 4]     │  │ │ │
                   │  │  └─────────────────────────┘  │ │ │
                   │  │  ┌─────────────────────────┐  │ │ │
                   │  │  │ render_video_task       │  │ │ │
                   │  │  │  [Stub for Phase 5]     │  │ │ │
                   │  │  └─────────────────────────┘  │ │ │
                   │  └───────────────────────────────┘ │ │
                   └─────────────────────────────────────┘ │
                                                            │
                   ┌────────────────────────────────────────┘
                   │
                   ▼
          ┌────────────────────────┐
          │   LLM Service          │
          │  (llm_service.py)      │
          │  ┌──────────────────┐  │
          │  │ extract_roles()  │  │
          │  │ optimize_script()│  │
          │  │ breakdown_scenes│  │
          │  └──────────────────┘  │
          └────────┬───────────────┘
                   │
                   ▼
          ┌────────────────────────┐
          │  DashScope (Qwen API)  │
          │   Alibaba Cloud        │
          └────────────────────────┘
```

## Component Responsibilities

### ✅ celery_app.py
- Celery instance creation
- Redis broker/backend configuration
- Queue routing (default, ai_generation, video_processing)
- Rate limiting (10/min scripts, 20/min media)
- Task serialization settings

### ✅ services/llm_service.py
- LLM API abstraction layer
- Qwen/DashScope integration
- Three-step workflow:
  1. Role extraction
  2. Script optimization
  3. Scene breakdown
- JSON parsing & validation
- Error handling

### ✅ tasks/workflow_tasks.py
- Celery task definitions
- Database operations (Task & Scene CRUD)
- LLM service integration
- Progress tracking (Redis Pub/Sub)
- Error handling & retry logic
- Status transitions (PENDING → SCRIPT_GEN → MEDIA_GEN)

## Workflow Execution Example

```python
# 1. User submits novel text
POST /api/v1/workflow/create
{
  "novel_text": "夜幕降临，江湖再起风云...",
  "scenes_per_paragraph": 3
}

# 2. FastAPI creates task in DB
Task {
  id: "uuid-123",
  status: "pending",
  input_params: { "novel_text": "...", ... }
}

# 3. Queue Celery task
start_workflow("uuid-123")
  → generate_script_task.delay("uuid-123")

# 4. Celery worker picks up task
[Worker] Starting generate_script_task for uuid-123

# 5. Update status & call LLM
Task.status = "script_gen"
Publish event: {"progress": 20, "message": "调用LLM优化脚本..."}

llm_service.script_optimization(novel_text)
  → extract_role_setting()
      → DashScope API: "男主:黑发剑客; 女主:红裙"
  → optimize_and_breakdown_script()
      → DashScope API: [scene1, scene2, ...]

# 6. Save scenes to DB
for scene in scenes:
  Scene.create(task_id, sequence, narration, image_prompt, ...)

# 7. Update task status
Task.status = "media_gen"
Task.progress = 60
Publish event: {"progress": 60, "scene_count": 6}

# 8. User receives SSE events
EventSource /api/v1/workflow/events/uuid-123
  → data: {"event": "progress", "data": {"progress": 20, ...}}
  → data: {"event": "progress", "data": {"progress": 50, ...}}
  → data: {"event": "scene_complete", "data": {"scene_count": 6}}
```

## Testing Commands

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Set environment
export DASHSCOPE_API_KEY="sk-your-key"
export REDIS_URL="redis://localhost:6379/0"

# 3. Start worker
cd backend
./start_worker.sh ai 4

# 4. Test LLM service (Python REPL)
python
>>> from app.services.llm_service import get_llm_service
>>> llm = get_llm_service()
>>> result = llm.script_optimization("夜幕降临...")
>>> print(result)

# 5. Test Celery task
>>> from app.tasks import start_workflow
>>> start_workflow("task-id-here")

# 6. Monitor Redis events
redis-cli PSUBSCRIBE "task_progress:*"
```

---

**Phase 3 Implementation**: ✅ **COMPLETE**
**Ready for**: Integration Testing & Phase 4 Development
