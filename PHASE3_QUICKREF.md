# Phase 3 Quick Reference Card 📇

## 🎯 What Was Built
**Asynchronous Task Processing & LLM Integration for Marketing2 Video Generation**

## 📦 Files Created (9 total)

### Core Implementation (Required 3)
1. ✅ `backend/app/celery_app.py` - Celery config (Redis broker, 3 queues)
2. ✅ `backend/app/services/llm_service.py` - Qwen/DashScope LLM integration
3. ✅ `backend/app/tasks/workflow_tasks.py` - Workflow tasks (script generation)

### Supporting Files
4. ✅ `backend/app/tasks/__init__.py` - Task package
5. ✅ `backend/requirements.txt` - Updated dependencies
6. ✅ `backend/start_worker.sh` - Worker startup script
7. ✅ `backend/INTEGRATION_EXAMPLE.py` - FastAPI integration guide
8. ✅ `PHASE3_IMPLEMENTATION.md` - Full implementation guide
9. ✅ `PHASE3_DELIVERY.md` - Complete delivery summary
10. ✅ `PHASE3_ARCHITECTURE.md` - Architecture diagrams

## 🚀 Quick Start (5 Steps)

```bash
# 1. Install
cd backend && pip install -r requirements.txt

# 2. Set API key
export DASHSCOPE_API_KEY="sk-your-key-here"

# 3. Start Redis (if needed)
docker run -d -p 6379:6379 redis:alpine

# 4. Start worker
./start_worker.sh ai 4

# 5. Test
curl -X POST http://localhost:8000/api/v1/workflow/create \
  -H "Content-Type: application/json" \
  -d '{"novel_text": "夜幕降临..."}'
```

## 🔑 Key Features

### LLM Service
- **Input**: Novel text (max 5000 chars)
- **Output**: Structured scenes JSON
- **Process**: Extract roles → Optimize script → Break into scenes
- **API**: Qwen-Plus via DashScope

### Celery Tasks
- **Queue**: `ai_generation` (rate: 10/min)
- **Task**: `generate_script_task`
- **Flow**: PENDING → SCRIPT_GEN → MEDIA_GEN
- **Events**: Real-time progress via Redis Pub/Sub

### Configuration
- **Broker**: Redis (localhost:6379/0)
- **Queues**: default, ai_generation, video_processing
- **Retry**: 3 attempts for API errors, fail-fast for content issues

## 📊 Expected Behavior

### Success Path
```
1. User submits novel → Task created (PENDING)
2. Celery picks up → Status: SCRIPT_GEN
3. LLM processes:
   - Extract: "男主:黑发; 女主:红裙"
   - Generate: 6 scenes
4. Save to DB → Status: MEDIA_GEN
5. Progress events → User sees real-time updates
```

### Error Path
```
1. API timeout → Retry (max 3x)
2. Sensitive content → Fail immediately, notify user
3. Invalid JSON → Fail, log response
```

## 🔍 Monitoring

### Worker Logs
```bash
# Watch worker activity
./start_worker.sh ai 4

# Expected output:
[INFO] Starting script generation for task abc-123
[INFO] Extracted role setting: 男主:黑发剑客
[INFO] Generated 6 scenes
```

### Redis Events
```bash
# Monitor progress events
redis-cli PSUBSCRIBE "task_progress:*"

# Expected messages:
{"event": "progress", "data": {"progress": 20, "message": "调用LLM..."}}
{"event": "scene_complete", "data": {"scene_count": 6}}
```

### Database
```sql
-- Check task status
SELECT id, status, progress FROM tasks ORDER BY created_at DESC LIMIT 5;

-- Check scenes
SELECT task_id, sequence, narration FROM scenes WHERE task_id = 'uuid';
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError: dashscope | `pip install dashscope>=1.14.0` |
| DASHSCOPE_API_KEY not set | `export DASHSCOPE_API_KEY="sk-..."` |
| Worker not picking tasks | Check Redis: `redis-cli ping` |
| LLM returns invalid JSON | Lower temperature to 0.3 in code |
| Sensitive content error | User must modify prompt, no retry |

## 📈 Performance

| Metric | Expected Value |
|--------|----------------|
| Script generation | 10-30 seconds |
| LLM API latency | 3-10 seconds |
| Database ops | <100ms |
| Redis Pub/Sub | <10ms |

## 🔗 Integration Points

### FastAPI Endpoint (To Update)
```python
from app.tasks import start_workflow

@router.post("/create")
def create_workflow(request):
    task = create_task_in_db(request)
    start_workflow(str(task.id))  # ← Phase 3 integration
    return {"task_id": task.id}
```

### SSE Streaming (To Implement)
```python
from fastapi.responses import StreamingResponse
import redis.asyncio as aioredis

async def event_stream(task_id):
    r = await aioredis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe(f"task_progress:{task_id}")
    # Stream events...
```

## 📚 Documentation

- **Full Guide**: `PHASE3_IMPLEMENTATION.md`
- **Architecture**: `PHASE3_ARCHITECTURE.md`
- **Delivery**: `PHASE3_DELIVERY.md`
- **Integration**: `backend/INTEGRATION_EXAMPLE.py`

## 🔜 Next Steps

**Phase 4** (AI Services):
- Implement `generate_media_task`
- Wanx-v1 image generation
- Sambert TTS audio

**Phase 5** (Video):
- Implement `render_video_task`
- FFmpeg pipeline
- Final MP4 output

## ✅ Checklist

- [x] Celery configured with Redis
- [x] LLM service implemented (Qwen)
- [x] Script generation task working
- [x] Database updates automated
- [x] Progress events publishing
- [x] Error handling robust
- [x] Documentation complete
- [ ] Integration with FastAPI
- [ ] End-to-end testing
- [ ] Production deployment

---

**Status**: ✅ **PHASE 3 COMPLETE**  
**Builder**: Builder-Bob (Senior Backend Engineer)  
**Date**: 2024  
**Ready For**: Integration & Testing
