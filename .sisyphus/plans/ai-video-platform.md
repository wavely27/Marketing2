# AI 营销自动化平台（小说 → 短视频）工作计划

## TL;DR

> **Quick Summary**: 从零构建 AI 视频生成平台，将小说文本自动转换为短视频。采用 Vue 3 + FastAPI + Celery 架构，集成阿里系 AI 服务，TDD 驱动开发。
> 
> **Deliverables**:
> - 一键视频生成（首页）
> - 分步视频工作流（5步）
> - 章节提取功能
> - 小说爬取功能
> - 实时进度展示（SSE）
> 
> **Estimated Effort**: XL (预计 60-80 小时)
> **Parallel Execution**: YES - 7 Phases
> **Critical Path**: Phase 0 → Phase 1 → Phase 2/3 (并行) → Phase 4 → Phase 5 → Phase 6

---

## Context

### Original Request
从零开发 AI 营销自动化平台，实现小说文本到短视频的自动转换。技术栈已确定，需要制定详细的 Epic → Feature → Task 分解工作计划。

### Interview Summary
**Key Discussions**:
- 测试策略：TDD 驱动，先写测试再实现
- 计划粒度：精细（每个 Task 约 30 分钟 - 1 小时）
- 数据库设计：最小化，JSONB 灵活存储
- Celery Worker：多 Worker 分离（AI + Video）

**Research Findings**:
- 已有 PoC 验证：单视频 < 3 分钟，成本 ¥0.50
- newProject.md 提供完整功能规格（758 行）
- 目录结构和 UI 组件设计已定义

### Metis Review
**Identified Gaps** (addressed):
- 环境依赖验证 → 添加 Phase 0
- API Key 验证 → 添加验证任务
- 任务并发策略 → 单用户限制 1 个并发
- 视频分辨率 → MVP 使用 720p
- SSE 断开重连 → 前端自动重连机制

---

## Work Objectives

### Core Objective
构建一个端到端的 AI 视频生成平台，让用户能够输入小说文本，自动生成漫画风格的短视频。

### Concrete Deliverables
- 后端 FastAPI 服务 (`backend/`)
- Celery Workers（ai-worker + video-worker）
- 前端 Vue 3 应用 (`frontend/`)
- PostgreSQL 数据库 schema
- 完整的 pytest + vitest 测试套件

### Definition of Done
- [ ] 一键视频生成：500字小说 → 完整视频，< 5 分钟
- [ ] 分步工作流：5 个步骤可独立执行和查看
- [ ] 章节提取：上传文件 → 返回 3-5 个精彩片段
- [ ] 小说爬取：支持 2-3 个预设站点
- [ ] 所有核心流程有 E2E 测试覆盖

### Must Have
- 实时进度显示（SSE）
- 任务失败时的清晰错误提示
- AI 服务配额耗尽自动切换模型
- 临时文件自动清理

### Must NOT Have (Guardrails)
- ❌ 多用户认证系统
- ❌ 多风格选择器（仅 anime）
- ❌ 通用爬虫引擎（仅预设站点）
- ❌ 暗色模式、移动端适配
- ❌ 提示词编辑器、A/B 测试
- ❌ 任务队列可视化、优先级管理
- ❌ 配置管理 UI
- ❌ 日志聚合系统

---

## Verification Strategy (MANDATORY)

### Test Decision
- **Infrastructure exists**: NO (需要设置)
- **User wants tests**: TDD (RED-GREEN-REFACTOR)
- **Framework**: 
  - 后端: pytest + pytest-asyncio
  - 前端: vitest + @vue/test-utils

### TDD Workflow

每个 TODO 遵循 RED-GREEN-REFACTOR：

1. **RED**: 先写失败测试
2. **GREEN**: 实现最小代码使测试通过
3. **REFACTOR**: 重构保持测试绿色

### Test Setup Tasks (Phase 0)

后端测试设置：
- 安装: `pip install pytest pytest-asyncio pytest-cov httpx`
- 配置: 创建 `pytest.ini` 和 `conftest.py`
- 验证: `pytest --version`

前端测试设置：
- 安装: `pnpm add -D vitest @vue/test-utils jsdom`
- 配置: 更新 `vite.config.ts` 添加 test 配置
- 验证: `pnpm test`

---

## Execution Strategy

### Parallel Execution Waves

```
Phase 0 (环境验证):
└── Wave 0.1: 环境检查和依赖安装

Phase 1 (后端基础设施):
├── Wave 1.1: 项目脚手架 + 数据库
├── Wave 1.2: Celery + Redis 配置
└── Wave 1.3: API 基础 + SSE

Phase 2 (AI 服务):
├── Wave 2.1: LLM Service
├── Wave 2.2: Image Service + Audio Service (并行)
└── Wave 2.3: 模型切换 + 限流

Phase 3 (视频处理):
├── Wave 3.1: FFmpeg 封装
└── Wave 3.2: Ken Burns + 合并

Phase 4 (前端):
├── Wave 4.1: 项目脚手架 + 路由 + Store
├── Wave 4.2: UI 组件库
├── Wave 4.3: 一键生成 + 分步工作流 (并行)
└── Wave 4.4: 章节提取 + 小说爬取 (并行)

Phase 5 (集成):
└── Wave 5.1: E2E 测试 + 修复
```

### Dependency Matrix

| Phase | Depends On | Blocks | Can Parallelize With |
|-------|------------|--------|---------------------|
| Phase 0 | None | All | None |
| Phase 1 | Phase 0 | Phase 2, 3, 4 | None |
| Phase 2 | Phase 1 | Phase 5 | Phase 3, Phase 4 |
| Phase 3 | Phase 1 | Phase 5 | Phase 2, Phase 4 |
| Phase 4 | Phase 1 | Phase 5 | Phase 2, Phase 3 |
| Phase 5 | Phase 1, 2, 3 | Phase 6 | Phase 4 (后端 API 和前端可并行) |
| Phase 6 | Phase 4, 5 | None | None |

**注意**: 项目文件位于 `Marketing2/Marketing2/` 目录，计划中的相对路径基于该目录。

---

## TODOs

---

## Phase 0: 环境验证和项目初始化

### Epic 0.1: 环境检查

- [ ] 0.1.1. 验证系统依赖

  **What to do**:
  - 检查 Python 版本 (>=3.10)
  - 检查 FFmpeg 安装和版本
  - 检查 Redis 连接
  - 检查 PostgreSQL 连接
  - 检查 Node.js 和 pnpm

  **Must NOT do**:
  - 不要安装未验证的依赖版本

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential (Phase 0 first)
  - **Blocks**: All subsequent tasks
  - **Blocked By**: None

  **References**:
  - `newProject.md:169-199` - 技术栈版本要求

  **Acceptance Criteria**:
  ```bash
  # 验证 Python
  python --version
  # Assert: Python 3.10+

  # 验证 FFmpeg
  ffmpeg -version
  # Assert: 输出包含版本号

  # 验证 Redis
  redis-cli ping
  # Assert: PONG

  # 验证 PostgreSQL
  psql -c "SELECT version();"
  # Assert: 返回版本信息

  # 验证 Node.js
  node --version && pnpm --version
  # Assert: Node 18+, pnpm 存在
  ```

  **Commit**: YES
  - Message: `chore: verify system dependencies`
  - Files: `.sisyphus/evidence/env-check.log`

---

- [ ] 0.1.2. 验证阿里云 API Key

  **What to do**:
  - 创建测试脚本验证 API Key 有效性
  - 测试通义千问 API 连通性
  - 测试通义万相 API 连通性
  - 测试 Sambert TTS API 连通性

  **Must NOT do**:
  - 不要在代码中硬编码 API Key

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 0.1 (with 0.1.1)
  - **Blocks**: Phase 2 tasks
  - **Blocked By**: None

  **References**:
  - `.env` - API Key 配置
  - `newProject.md:192-198` - AI 服务说明

  **Acceptance Criteria**:
  ```bash
  # 创建并运行验证脚本
  python scripts/verify_api_keys.py
  # Assert: 输出 "All API keys verified successfully"
  # Assert: 每个服务返回有效响应
  ```

  **Commit**: YES
  - Message: `chore: add API key verification script`
  - Files: `scripts/verify_api_keys.py`

---

### Epic 0.2: 项目脚手架

- [ ] 0.2.1. 创建后端项目结构

  **What to do**:
  - 创建 `backend/` 目录结构
  - 创建 `requirements.txt` 和 `pyproject.toml`
  - 创建 `.env.example` 模板
  - 初始化 pytest 配置

  **Must NOT do**:
  - 不要添加未使用的依赖
  - 不要创建复杂的配置系统

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 0.2 (with 0.2.2)
  - **Blocks**: Phase 1 backend tasks
  - **Blocked By**: 0.1.1

  **References**:
  - `newProject.md:671-697` - 后端目录结构

  **Acceptance Criteria**:
  ```bash
  # 目录结构验证
  ls backend/app/
  # Assert: 存在 main.py, core/, api/, services/, models/

  # 依赖安装
  cd backend && pip install -e .
  # Assert: 安装成功

  # pytest 验证
  cd backend && pytest --version
  # Assert: pytest 可运行
  ```

  **Commit**: YES
  - Message: `feat(backend): initialize project structure`
  - Files: `backend/`

---

- [ ] 0.2.2. 创建前端项目结构

  **What to do**:
  - 使用 Vite 创建 Vue 3 + TypeScript 项目
  - 配置 TailwindCSS
  - 配置 Pinia
  - 配置 Vue Router
  - 初始化 vitest 配置

  **Must NOT do**:
  - 不要添加复杂的 UI 库
  - 不要配置暗色模式

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 0.2 (with 0.2.1)
  - **Blocks**: Phase 4 frontend tasks
  - **Blocked By**: 0.1.1

  **References**:
  - `newProject.md:639-668` - 前端目录结构
  - `newProject.md:171-180` - 前端技术栈版本

  **Acceptance Criteria**:
  ```bash
  # 依赖安装
  cd frontend && pnpm install
  # Assert: 安装成功

  # 开发服务器
  cd frontend && pnpm dev &
  sleep 5
  curl -s http://localhost:5173 | head -1
  # Assert: 返回 HTML

  # 测试验证
  cd frontend && pnpm test run
  # Assert: vitest 可运行
  ```

  **Commit**: YES
  - Message: `feat(frontend): initialize Vue 3 + Vite project`
  - Files: `frontend/`

---

- [ ] 0.2.3. 创建测试夹具文件

  **What to do**:
  - 创建 `backend/tests/fixtures/` 目录
  - 创建示例小说文本 `sample_novel.txt`（约 2000 字）
  - 创建测试图片 `test_image.png`（1024x1024 纯色图）
  - 创建测试音频 `test_audio.mp3`（5 秒静音或简单音频）
  - 创建 `frontend/tests/fixtures/` 目录

  **Must NOT do**:
  - 不要使用版权素材
  - 不要创建超大文件

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 0.2 (with 0.2.1, 0.2.2)
  - **Blocks**: Phase 2, Phase 3 测试
  - **Blocked By**: 0.1.1

  **References**:
  - 测试所需的模拟数据

  **Acceptance Criteria**:
  ```bash
  # 验证夹具文件存在
  ls backend/tests/fixtures/
  # Assert: 存在 sample_novel.txt, test_image.png, test_audio.mp3

  # 验证小说文件
  wc -c backend/tests/fixtures/sample_novel.txt
  # Assert: 文件大小 > 2000 字节

  # 验证图片文件
  file backend/tests/fixtures/test_image.png
  # Assert: PNG image data

  # 验证音频文件
  file backend/tests/fixtures/test_audio.mp3
  # Assert: Audio file
  ```

  **Commit**: YES
  - Message: `chore: add test fixtures for backend and frontend`
  - Files: `backend/tests/fixtures/`, `frontend/tests/fixtures/`

---

## Phase 1: 后端基础设施

### Epic 1.1: FastAPI 核心

- [ ] 1.1.1. FastAPI 应用入口和配置

  **What to do**:
  - 创建 FastAPI 应用入口 `main.py`
  - 配置 CORS
  - 配置静态文件服务
  - 创建 Pydantic Settings 配置类
  - **TDD**: 先写配置加载测试

  **Must NOT do**:
  - 不要实现认证中间件
  - 不要配置多环境切换

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1.1 (first)
  - **Blocks**: 1.1.2, 1.2.1
  - **Blocked By**: 0.2.1

  **References**:
  - `newProject.md:671-697` - 后端结构
  - `newProject.md:749-752` - 环境变量

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_config.py -v
  # Assert: 配置加载测试通过

  # 应用启动
  cd backend && uvicorn app.main:app --port 8000 &
  sleep 2
  curl -s http://localhost:8000/health
  # Assert: {"status": "healthy"}

  # CORS 验证
  curl -H "Origin: http://localhost:5173" \
       -H "Access-Control-Request-Method: POST" \
       -X OPTIONS http://localhost:8000/api/v1/test
  # Assert: 返回正确的 CORS headers
  ```

  **Commit**: YES
  - Message: `feat(backend): add FastAPI app with config`
  - Files: `backend/app/main.py`, `backend/app/core/config.py`, `backend/tests/test_config.py`

---

- [ ] 1.1.2. 数据库连接和 Schema

  **What to do**:
  - 配置 SQLAlchemy + asyncpg
  - 创建 tasks 表（id, status, type, input_data JSONB, output_data JSONB, created_at, updated_at）
  - 创建数据库迁移脚本
  - **TDD**: 先写数据库连接测试

  **Must NOT do**:
  - 不要创建复杂的关系模型
  - 不要使用 Alembic（MVP 简化）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1.1 (after 1.1.1)
  - **Blocks**: 1.2.3
  - **Blocked By**: 1.1.1

  **References**:
  - Metis 分析 - 最小化数据库设计
  - `newProject.md:418-430` - Scene 数据结构

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_database.py -v
  # Assert: 数据库连接和 CRUD 测试通过

  # 表创建验证
  psql -d marketing -c "\dt"
  # Assert: 存在 tasks 表

  # JSONB 操作验证
  psql -d marketing -c "INSERT INTO tasks (type, input_data) VALUES ('test', '{\"key\": \"value\"}'::jsonb) RETURNING id;"
  # Assert: 返回新插入的 ID
  ```

  **Commit**: YES
  - Message: `feat(backend): add database schema and connection`
  - Files: `backend/app/core/database.py`, `backend/app/models/task.py`, `backend/tests/test_database.py`

---

### Epic 1.2: Celery 任务队列

- [ ] 1.2.1. Celery 配置和 Worker 定义

  **What to do**:
  - 配置 Celery 应用
  - 配置 Redis 作为 broker 和 backend
  - 定义两个 Worker：ai-worker, video-worker
  - 配置任务队列路由
  - **TDD**: 先写 Celery 任务测试

  **Must NOT do**:
  - 不要实现任务优先级系统
  - 不要配置任务超时自动重试（手动控制）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1.2 (first)
  - **Blocks**: 1.2.2, Phase 2, Phase 3
  - **Blocked By**: 1.1.1

  **References**:
  - Metis 分析 - 多 Worker 分离策略
  - `newProject.md:207` - 异步任务队列处理

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_celery.py -v
  # Assert: Celery 配置测试通过

  # Worker 启动验证 (ai-worker)
  cd backend && celery -A app.celery_app worker -Q ai -n ai-worker --loglevel=info &
  sleep 3
  celery -A app.celery_app inspect ping -d celery@ai-worker
  # Assert: 返回 pong

  # Worker 启动验证 (video-worker)
  cd backend && celery -A app.celery_app worker -Q video -n video-worker --loglevel=info &
  sleep 3
  celery -A app.celery_app inspect ping -d celery@video-worker
  # Assert: 返回 pong

  # 队列路由验证
  cd backend && python -c "from app.celery_app import app; print(app.conf.task_routes)"
  # Assert: 输出包含 ai 和 video 队列路由
  ```

  **Commit**: YES
  - Message: `feat(backend): add Celery configuration with dual workers`
  - Files: `backend/app/celery_app.py`, `backend/app/core/celery_config.py`, `backend/tests/test_celery.py`

---

- [ ] 1.2.2. 任务状态管理

  **What to do**:
  - 创建任务状态枚举（pending, running, completed, failed）
  - 创建任务进度更新机制
  - 实现任务结果存储（PostgreSQL + Redis 缓存）
  - **TDD**: 先写状态更新测试

  **Must NOT do**:
  - 不要实现复杂状态机
  - 不要实现任务依赖图

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1.2 (with 1.2.3)
  - **Blocks**: 1.3.2
  - **Blocked By**: 1.2.1

  **References**:
  - `newProject.md:418-430` - Scene 状态结构

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_task_status.py -v
  # Assert: 状态管理测试通过

  # 状态更新验证
  cd backend && python -c "
  from app.services.task_service import TaskService
  ts = TaskService()
  task_id = ts.create_task('test')
  ts.update_progress(task_id, 50, 'Processing...')
  status = ts.get_status(task_id)
  print(status)
  "
  # Assert: 输出包含 progress: 50, message: 'Processing...'
  ```

  **Commit**: YES
  - Message: `feat(backend): add task status management`
  - Files: `backend/app/services/task_service.py`, `backend/tests/test_task_status.py`

---

- [ ] 1.2.3. 临时文件管理

  **What to do**:
  - 创建输出目录结构（audio/, images/, video/）
  - 实现任务完成后的文件清理
  - 实现 24 小时过期清理定时任务
  - **TDD**: 先写文件清理测试

  **Must NOT do**:
  - 不要实现 OSS 上传
  - 不要实现复杂的存储策略

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1.2 (with 1.2.2)
  - **Blocks**: Phase 3
  - **Blocked By**: 1.1.2, 1.2.1

  **References**:
  - `newProject.md:696-700` - 输出目录结构
  - Metis 分析 - 临时文件 24 小时清理

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_file_manager.py -v
  # Assert: 文件管理测试通过

  # 目录创建验证
  ls backend/output/
  # Assert: 存在 audio/, images/, video/

  # 清理任务验证
  cd backend && python -c "
  from app.services.file_manager import FileManager
  fm = FileManager()
  fm.cleanup_expired(hours=24)
  "
  # Assert: 无错误输出
  ```

  **Commit**: YES
  - Message: `feat(backend): add file management and cleanup`
  - Files: `backend/app/services/file_manager.py`, `backend/tests/test_file_manager.py`

---

### Epic 1.3: API 基础

- [ ] 1.3.1. API 路由结构

  **What to do**:
  - 创建 API 路由汇总 (`api/router.py`)
  - 创建各模块路由占位符
  - 定义通用响应模型
  - **TDD**: 先写路由注册测试

  **Must NOT do**:
  - 不要实现具体业务逻辑
  - 不要添加认证中间件

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1.3 (with 1.3.2)
  - **Blocks**: Phase 2 API endpoints
  - **Blocked By**: 1.1.1

  **References**:
  - `newProject.md:509-538` - API 端点汇总

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_routes.py -v
  # Assert: 路由注册测试通过

  # 路由列表验证
  cd backend && python -c "
  from app.main import app
  for route in app.routes:
      if hasattr(route, 'path'):
          print(route.path)
  " | grep /api/v1
  # Assert: 输出包含主要 API 路径

  # OpenAPI 验证
  curl -s http://localhost:8000/openapi.json | jq '.paths | keys'
  # Assert: 返回 API 路径列表
  ```

  **Commit**: YES
  - Message: `feat(backend): add API router structure`
  - Files: `backend/app/api/router.py`, `backend/app/api/endpoints/`, `backend/tests/test_routes.py`

---

- [ ] 1.3.2. SSE 进度推送

  **What to do**:
  - 实现 SSE 端点 (`/api/v1/workflow/stream/{task_id}`)
  - 从 Redis 订阅任务进度更新
  - 实现连接心跳
  - **TDD**: 先写 SSE 连接测试

  **Must NOT do**:
  - 不要实现 WebSocket（用 SSE）
  - 不要实现复杂的重连逻辑（前端处理）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1.3 (with 1.3.1)
  - **Blocks**: Phase 4 实时进度
  - **Blocked By**: 1.2.2

  **References**:
  - `newProject.md:207` - 异步任务队列处理
  - Metis 分析 - SSE 断开重连机制

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_sse.py -v
  # Assert: SSE 测试通过

  # SSE 连接验证
  # 先创建测试任务
  TASK_ID=$(curl -s -X POST http://localhost:8000/api/v1/test/task | jq -r '.task_id')
  
  # 连接 SSE
  timeout 5 curl -N http://localhost:8000/api/v1/workflow/stream/$TASK_ID 2>/dev/null | head -5
  # Assert: 输出包含 data: {"progress": ...}
  ```

  **Commit**: YES
  - Message: `feat(backend): add SSE progress streaming`
  - Files: `backend/app/api/endpoints/sse.py`, `backend/tests/test_sse.py`

---

## Phase 2: AI 服务集成

### Epic 2.1: LLM 服务

- [ ] 2.1.1. 通义千问基础集成

  **What to do**:
  - 创建 LLMService 类
  - 实现 DashScope SDK 调用封装
  - 实现 JSON 响应解析（带容错）
  - **TDD**: 先写 LLM 调用测试（使用 mock）

  **Must NOT do**:
  - 不要实现流式响应（MVP 不需要）
  - 不要实现提示词管理系统

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2.1 (first)
  - **Blocks**: 2.1.2, 2.1.3
  - **Blocked By**: 1.2.1

  **References**:
  - `newProject.md:546-563` - LLM 服务架构
  - `newProject.md:556-560` - JSON 解析增强

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行 (mock)
  cd backend && pytest tests/test_llm_service.py -v
  # Assert: LLM 服务测试通过（包括 mock 测试）

  # 实际 API 调用验证
  cd backend && python -c "
  from app.services.llm_service import LLMService
  llm = LLMService()
  result = llm.generate_script('测试文本', max_scenes=3)
  print(len(result['scenes']))
  "
  # Assert: 输出 3（生成 3 个分镜）
  ```

  **Commit**: YES
  - Message: `feat(backend): add LLM service with DashScope SDK`
  - Files: `backend/app/services/llm_service.py`, `backend/tests/test_llm_service.py`

---

- [ ] 2.1.2. 分镜脚本生成

  **What to do**:
  - 实现脚本生成提示词
  - 解析返回的分镜数据结构
  - 验证分镜数量（5-15 个）
  - **TDD**: 先写分镜解析测试

  **Must NOT do**:
  - 不要实现提示词 A/B 测试
  - 不要实现多语言提示词

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2.1 (with 2.1.3)
  - **Blocks**: 2.3.1
  - **Blocked By**: 2.1.1

  **References**:
  - `newProject.md:270-288` - 分镜脚本要求
  - `newProject.md:277-285` - 分镜数据结构

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_script_generation.py -v
  # Assert: 分镜生成测试通过

  # 分镜结构验证
  cd backend && python -c "
  from app.services.llm_service import LLMService
  llm = LLMService()
  result = llm.generate_script('一个关于冒险的故事...')
  scene = result['scenes'][0]
  assert 'scene_id' in scene
  assert 'duration' in scene
  assert 'image_prompt' in scene
  assert 'narration' in scene
  print('结构验证通过')
  "
  # Assert: 输出 "结构验证通过"
  ```

  **Commit**: YES
  - Message: `feat(backend): add script generation with scene parsing`
  - Files: `backend/app/services/llm_service.py` (更新), `backend/tests/test_script_generation.py`

---

- [ ] 2.1.3. 章节提取功能

  **What to do**:
  - 实现长文本精彩片段提取
  - 返回 3-5 个 500-800 字片段
  - 生成片段标题和情感标签
  - **TDD**: 先写章节提取测试

  **Must NOT do**:
  - 不要实现复杂的文本分析
  - 不要保存提取历史

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2.1 (with 2.1.2)
  - **Blocks**: Phase 4 章节提取页面
  - **Blocked By**: 2.1.1

  **References**:
  - `newProject.md:229-262` - 章节提取功能
  - `newProject.md:251-261` - Highlight 数据结构

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_chapter_extract.py -v
  # Assert: 章节提取测试通过

  # 提取结果验证
  cd backend && python -c "
  from app.services.llm_service import LLMService
  llm = LLMService()
  with open('tests/fixtures/sample_novel.txt', 'r') as f:
      text = f.read()
  result = llm.extract_highlights(text)
  print(f'提取到 {len(result[\"highlights\"])} 个片段')
  for h in result['highlights']:
      print(f'  - {h[\"title\"]}: {len(h[\"script\"])} 字')
  "
  # Assert: 输出 3-5 个片段，每个 500-800 字
  ```

  **Commit**: YES
  - Message: `feat(backend): add chapter highlight extraction`
  - Files: `backend/app/services/llm_service.py` (更新), `backend/tests/test_chapter_extract.py`, `backend/tests/fixtures/sample_novel.txt`

---

### Epic 2.2: 图片服务

- [ ] 2.2.1. 通义万相集成

  **What to do**:
  - 创建 ImageService 类
  - 实现图片生成 API 调用
  - 配置 anime 风格固定参数
  - 实现图片下载和保存
  - **TDD**: 先写图片服务测试（mock）

  **Must NOT do**:
  - 不要实现多风格选择
  - 不要实现图片编辑功能

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2.2 (with 2.2.2)
  - **Blocks**: 2.3.1
  - **Blocked By**: 1.2.1

  **References**:
  - `newProject.md:564-570` - 图片服务架构
  - `newProject.md:322-334` - 图片生成参数

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行 (mock)
  cd backend && pytest tests/test_image_service.py -v
  # Assert: 图片服务测试通过

  # 实际生成验证
  cd backend && python -c "
  from app.services.image_service import ImageService
  img = ImageService()
  path = img.generate('a cute anime girl, digital art', 'test_image')
  print(f'生成图片: {path}')
  "
  # Assert: 输出图片路径，文件存在于 output/images/

  # 图片格式验证
  file backend/output/images/test_image_*.png
  # Assert: PNG image data
  ```

  **Commit**: YES
  - Message: `feat(backend): add image service with Wanx integration`
  - Files: `backend/app/services/image_service.py`, `backend/tests/test_image_service.py`

---

- [ ] 2.2.2. 音频服务（Sambert TTS）

  **What to do**:
  - 创建 AudioService 类
  - 实现 Sambert TTS API 调用
  - 配置音频参数（48000Hz, mp3）
  - 实现音频文件保存
  - **TDD**: 先写音频服务测试（mock）

  **Must NOT do**:
  - 不要实现多音色选择
  - 不要实现音频编辑

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2.2 (with 2.2.1)
  - **Blocks**: 2.3.1
  - **Blocked By**: 1.2.1

  **References**:
  - `newProject.md:573-580` - 音频服务架构
  - `newProject.md:291-309` - 音频生成参数

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行 (mock)
  cd backend && pytest tests/test_audio_service.py -v
  # Assert: 音频服务测试通过

  # 实际生成验证
  cd backend && python -c "
  from app.services.audio_service import AudioService
  audio = AudioService()
  path = audio.generate('这是一段测试文本', 'test_audio')
  print(f'生成音频: {path}')
  "
  # Assert: 输出音频路径

  # 音频格式验证
  file backend/output/audio/test_audio.mp3
  # Assert: Audio file with ID3
  ```

  **Commit**: YES
  - Message: `feat(backend): add audio service with Sambert TTS`
  - Files: `backend/app/services/audio_service.py`, `backend/tests/test_audio_service.py`

---

### Epic 2.3: AI 服务增强

- [ ] 2.3.1. 模型自动切换

  **What to do**:
  - 实现配额检测逻辑
  - 实现模型切换顺序（turbo → plus → max）
  - 记录模型使用统计
  - **TDD**: 先写模型切换测试

  **Must NOT do**:
  - 不要实现配额预警
  - 不要实现用户选择模型

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2.3 (with 2.3.2)
  - **Blocks**: Phase 5
  - **Blocked By**: 2.1.1, 2.2.1, 2.2.2

  **References**:
  - `newProject.md:550-555` - 模型优先级
  - Metis 分析 - 配额耗尽自动切换

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_model_switch.py -v
  # Assert: 模型切换测试通过

  # 模拟切换验证
  cd backend && python -c "
  from app.services.llm_service import LLMService
  llm = LLMService()
  # 模拟 turbo 配额耗尽
  llm._simulate_quota_exhausted('qwen-turbo')
  result = llm.generate_script('测试')
  print(f'使用模型: {result[\"model_used\"]}')
  "
  # Assert: 输出使用 qwen-plus 或 qwen-max
  ```

  **Commit**: YES
  - Message: `feat(backend): add automatic model switching`
  - Files: `backend/app/services/llm_service.py` (更新), `backend/tests/test_model_switch.py`

---

- [ ] 2.3.2. 限流和重试

  **What to do**:
  - 实现指数退避重试装饰器
  - 配置最大重试次数（3 次）
  - 配置超时时间（30 秒）
  - 记录重试日志
  - **TDD**: 先写重试逻辑测试

  **Must NOT do**:
  - 不要实现全局限流器
  - 不要实现配额预估

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2.3 (with 2.3.1)
  - **Blocks**: Phase 5
  - **Blocked By**: 2.2.1, 2.2.2

  **References**:
  - Metis 分析 - 指数退避重试策略
  - Metis 分析 - 30 秒超时

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_retry.py -v
  # Assert: 重试逻辑测试通过

  # 重试行为验证
  cd backend && python -c "
  from app.core.retry import with_retry
  import time

  call_count = 0
  @with_retry(max_retries=3, base_delay=0.1)
  def flaky_function():
      global call_count
      call_count += 1
      if call_count < 3:
          raise Exception('Temporary error')
      return 'success'

  result = flaky_function()
  print(f'调用次数: {call_count}, 结果: {result}')
  "
  # Assert: 调用次数: 3, 结果: success
  ```

  **Commit**: YES
  - Message: `feat(backend): add exponential backoff retry decorator`
  - Files: `backend/app/core/retry.py`, `backend/tests/test_retry.py`

---

## Phase 3: 视频处理服务

### Epic 3.1: FFmpeg 封装

- [ ] 3.1.1. 视频服务基础

  **What to do**:
  - 创建 VideoService 类
  - 封装 FFmpeg 调用
  - 实现视频参数配置（720p, 24fps）
  - 实现错误处理和日志
  - **TDD**: 先写视频服务测试

  **Must NOT do**:
  - 不要实现多分辨率选择
  - 不要实现视频编辑功能

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3.1 (first)
  - **Blocks**: 3.1.2, 3.2.1
  - **Blocked By**: 1.2.3

  **References**:
  - `newProject.md:583-598` - 视频服务架构
  - `newProject.md:206-207` - FFmpeg 核心动效引擎

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_video_service.py -v
  # Assert: 视频服务测试通过

  # FFmpeg 可用性验证
  cd backend && python -c "
  from app.services.video_service import VideoService
  vs = VideoService()
  print(f'FFmpeg 版本: {vs.get_ffmpeg_version()}')
  "
  # Assert: 输出 FFmpeg 版本号

  # 基础合成验证
  cd backend && python -c "
  from app.services.video_service import VideoService
  vs = VideoService()
  vs.create_test_video('output/video/test.mp4')
  "
  file backend/output/video/test.mp4
  # Assert: MPEG v4 system
  ```

  **Commit**: YES
  - Message: `feat(backend): add video service with FFmpeg wrapper`
  - Files: `backend/app/services/video_service.py`, `backend/tests/test_video_service.py`

---

- [ ] 3.1.2. Ken Burns 动效

  **What to do**:
  - 实现 3 种动效类型（zoom in, zoom out, pan）
  - 实现图片到视频转换
  - 配置动效参数
  - **TDD**: 先写 Ken Burns 测试

  **Must NOT do**:
  - 不要实现自定义动效参数
  - 不要实现动效预览

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3.1 (with 3.1.3)
  - **Blocks**: 3.2.1
  - **Blocked By**: 3.1.1

  **References**:
  - `newProject.md:346-353` - Ken Burns 效果类型
  - `newProject.md:358-366` - 视频合成实现

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_ken_burns.py -v
  # Assert: Ken Burns 测试通过

  # 动效生成验证
  cd backend && python -c "
  from app.services.video_service import VideoService
  vs = VideoService()
  # 使用测试图片
  vs.apply_ken_burns(
      'tests/fixtures/test_image.png',
      'output/video/ken_burns_test.mp4',
      duration=5,
      effect_type=0  # zoom in
  )
  "
  ffprobe -v error -show_entries format=duration backend/output/video/ken_burns_test.mp4
  # Assert: duration=5.0
  ```

  **Commit**: YES
  - Message: `feat(backend): add Ken Burns effect implementation`
  - Files: `backend/app/services/video_service.py` (更新), `backend/tests/test_ken_burns.py`, `backend/tests/fixtures/test_image.png`

---

- [ ] 3.1.3. 字幕生成

  **What to do**:
  - 实现字幕渲染（使用 FFmpeg drawtext）
  - 配置中文字体
  - 实现自动换行（每行 25 字）
  - **TDD**: 先写字幕测试

  **Must NOT do**:
  - 不要实现字幕样式编辑
  - 不要实现时间轴编辑

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3.1 (with 3.1.2)
  - **Blocks**: 3.2.1
  - **Blocked By**: 3.1.1

  **References**:
  - `newProject.md:354-356` - 字幕特性
  - `newProject.md:592-597` - 字幕自动换行

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_subtitle.py -v
  # Assert: 字幕测试通过

  # 字幕渲染验证
  cd backend && python -c "
  from app.services.video_service import VideoService
  vs = VideoService()
  vs.add_subtitle(
      'output/video/ken_burns_test.mp4',
      '这是一段很长的测试文本，需要自动换行处理',
      'output/video/subtitle_test.mp4'
  )
  "
  # 目视确认字幕存在
  ffprobe -v error -show_streams backend/output/video/subtitle_test.mp4
  # Assert: 输出包含 video stream
  ```

  **Commit**: YES
  - Message: `feat(backend): add subtitle rendering with auto line-wrap`
  - Files: `backend/app/services/video_service.py` (更新), `backend/tests/test_subtitle.py`

---

### Epic 3.2: 分镜合成

- [ ] 3.2.1. 单分镜视频合成

  **What to do**:
  - 实现图片 + 音频 + 字幕合成
  - 支持多图轮播（3 张图）
  - 以音频时长为准调整视频
  - **TDD**: 先写单分镜合成测试

  **Must NOT do**:
  - 不要实现转场效果（MVP 后）
  - 不要实现背景音乐

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3.2 (first)
  - **Blocks**: 3.2.2
  - **Blocked By**: 3.1.2, 3.1.3

  **References**:
  - `newProject.md:336-366` - 视频生成步骤
  - `newProject.md:358-366` - 单场景视频合成

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_scene_synthesis.py -v
  # Assert: 单分镜合成测试通过

  # 合成验证
  cd backend && python -c "
  from app.services.video_service import VideoService
  vs = VideoService()
  vs.create_scene_video(
      image_paths=['tests/fixtures/test_image.png'] * 3,
      audio_path='tests/fixtures/test_audio.mp3',
      text='这是测试旁白文本',
      output_path='output/video/scene_test.mp4'
  )
  "
  ffprobe -v error -show_entries format=duration,format_name backend/output/video/scene_test.mp4
  # Assert: format_name=mov,mp4..., duration > 0
  ```

  **Commit**: YES
  - Message: `feat(backend): add scene video synthesis`
  - Files: `backend/app/services/video_service.py` (更新), `backend/tests/test_scene_synthesis.py`, `backend/tests/fixtures/test_audio.mp3`

---

- [ ] 3.2.2. 视频拼接

  **What to do**:
  - 实现多视频拼接
  - 保持分镜顺序
  - 输出最终视频文件
  - **TDD**: 先写视频拼接测试

  **Must NOT do**:
  - 不要实现片头片尾
  - 不要实现水印

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3.2 (after 3.2.1)
  - **Blocks**: Phase 5
  - **Blocked By**: 3.2.1

  **References**:
  - `newProject.md:368-385` - 合并导出功能
  - `newProject.md:379-384` - 视频拼接实现

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/test_video_concat.py -v
  # Assert: 视频拼接测试通过

  # 拼接验证
  cd backend && python -c "
  from app.services.video_service import VideoService
  vs = VideoService()
  vs.concat_videos(
      ['output/video/scene_test.mp4', 'output/video/scene_test.mp4'],
      'output/video/final_test.mp4'
  )
  "
  ffprobe -v error -show_entries format=duration backend/output/video/final_test.mp4
  # Assert: duration 约为单个视频的 2 倍
  ```

  **Commit**: YES
  - Message: `feat(backend): add video concatenation`
  - Files: `backend/app/services/video_service.py` (更新), `backend/tests/test_video_concat.py`

---

## Phase 4: 前端实现

### Epic 4.1: 前端基础

- [ ] 4.1.1. 路由配置

  **What to do**:
  - 配置 Vue Router
  - 定义所有页面路由
  - 实现导航守卫（步骤完成检查）
  - **TDD**: 先写路由测试

  **Must NOT do**:
  - 不要实现认证路由守卫
  - 不要实现路由动画

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4.1 (first)
  - **Blocks**: 4.1.2, 4.2.1
  - **Blocked By**: 0.2.2

  **References**:
  - `newProject.md:645-648` - 路由配置文件
  - `newProject.md:204-225` - 首页路由说明

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd frontend && pnpm test run src/router/__tests__/
  # Assert: 路由测试通过

  # 路由定义验证
  cd frontend && pnpm build
  cat dist/assets/*.js | grep -o '"/video/step[0-9]' | sort | uniq
  # Assert: 输出 /video/step1 到 /video/step5
  ```

  **Agent-Executable Verification (Playwright)**:
  ```
  1. Navigate to: http://localhost:5173/
  2. Assert: URL is "/"
  3. Click: link containing "分步工作流"
  4. Assert: URL contains "/video/step1"
  5. Screenshot: .sisyphus/evidence/task-4.1.1-routes.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add Vue Router configuration`
  - Files: `frontend/src/router/index.ts`, `frontend/src/router/__tests__/router.test.ts`

---

- [ ] 4.1.2. Pinia Store 设计

  **What to do**:
  - 创建 videoWorkflow store
  - 实现分镜数据管理
  - 实现 localStorage 持久化
  - **TDD**: 先写 Store 测试

  **Must NOT do**:
  - 不要实现服务端状态同步
  - 不要实现撤销/重做

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4.1 (with 4.1.3)
  - **Blocks**: 4.3.1, 4.3.2
  - **Blocked By**: 4.1.1

  **References**:
  - `newProject.md:413-453` - videoWorkflow Store 设计
  - `newProject.md:418-430` - Scene 接口定义

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd frontend && pnpm test run src/stores/__tests__/
  # Assert: Store 测试通过

  # 持久化验证
  cd frontend && pnpm test run --filter "localStorage"
  # Assert: 持久化测试通过
  ```

  **Commit**: YES
  - Message: `feat(frontend): add Pinia videoWorkflow store`
  - Files: `frontend/src/stores/videoWorkflow.ts`, `frontend/src/stores/__tests__/videoWorkflow.test.ts`

---

- [ ] 4.1.3. API 请求封装

  **What to do**:
  - 创建 axios instance
  - 配置 baseURL 和超时
  - 实现请求/响应拦截器
  - 创建类型安全的 API 函数
  - **TDD**: 先写 API 函数测试（mock）

  **Must NOT do**:
  - 不要实现 token 刷新
  - 不要实现请求缓存

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4.1 (with 4.1.2)
  - **Blocks**: 4.3.1, 4.3.2
  - **Blocked By**: 4.1.1

  **References**:
  - `newProject.md:509-538` - API 端点列表
  - Metis 分析 - API 请求封装

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行 (mock)
  cd frontend && pnpm test run src/api/__tests__/
  # Assert: API 测试通过

  # 类型检查
  cd frontend && pnpm type-check
  # Assert: 无 TypeScript 错误
  ```

  **Commit**: YES
  - Message: `feat(frontend): add axios API client with type safety`
  - Files: `frontend/src/api/client.ts`, `frontend/src/api/workflow.ts`, `frontend/src/api/__tests__/api.test.ts`

---

### Epic 4.2: UI 组件库

- [ ] 4.2.1. 基础组件（Card, Button）

  **What to do**:
  - 实现 Card 组件
  - 实现 Button 组件（4 种变体）
  - 配置 TailwindCSS 主题色
  - **TDD**: 先写组件测试

  **Must NOT do**:
  - 不要实现暗色模式
  - 不要使用第三方 UI 库

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4.2 (first)
  - **Blocks**: 4.2.2, 4.3.1
  - **Blocked By**: 4.1.1

  **References**:
  - `newProject.md:459-480` - Card 和 Button 组件规格
  - `newProject.md:617-626` - 配色方案

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd frontend && pnpm test run src/components/ui/__tests__/
  # Assert: 组件测试通过
  ```

  **Agent-Executable Verification (Playwright)**:
  ```
  1. Navigate to: http://localhost:5173/dev/components
  2. Assert: element ".card" is visible
  3. Assert: element "button.btn-primary" is visible
  4. Click: button containing "Loading"
  5. Assert: button shows loading spinner
  6. Screenshot: .sisyphus/evidence/task-4.2.1-components.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add Card and Button components`
  - Files: `frontend/src/components/ui/Card.vue`, `frontend/src/components/ui/Button.vue`, `frontend/src/components/ui/__tests__/`

---

- [ ] 4.2.2. 进度组件（StepIndicator, ProgressBar）

  **What to do**:
  - 实现 5 步指示器
  - 实现进度条组件
  - 实现日志面板组件
  - **TDD**: 先写组件测试

  **Must NOT do**:
  - 不要实现可编辑步骤
  - 不要实现动画效果

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4.2 (after 4.2.1)
  - **Blocks**: 4.3.1, 4.3.2
  - **Blocked By**: 4.2.1

  **References**:
  - `newProject.md:485-503` - StepIndicator 和 ProgressBar 规格

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd frontend && pnpm test run src/components/ui/__tests__/StepIndicator.test.ts
  cd frontend && pnpm test run src/components/ui/__tests__/ProgressBar.test.ts
  # Assert: 测试通过
  ```

  **Agent-Executable Verification (Playwright)**:
  ```
  1. Navigate to: http://localhost:5173/dev/components
  2. Assert: element ".step-indicator" shows 5 steps
  3. Assert: step 1 has "completed" class
  4. Assert: step 2 has "active" class
  5. Assert: ".progress-bar" shows "50%"
  6. Screenshot: .sisyphus/evidence/task-4.2.2-progress.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add StepIndicator and ProgressBar components`
  - Files: `frontend/src/components/ui/StepIndicator.vue`, `frontend/src/components/ui/ProgressBar.vue`, `frontend/src/components/ui/LogPanel.vue`

---

### Epic 4.3: 核心页面

- [ ] 4.3.1. 首页 - 一键视频生成

  **What to do**:
  - 实现文本输入区域
  - 实现一键生成按钮
  - 实现 SSE 进度订阅
  - 实现实时日志面板
  - 实现视频预览和下载
  - **TDD**: 先写页面测试

  **Must NOT do**:
  - 不要实现历史记录管理（MVP 后）
  - 不要实现 API 消耗统计 UI

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4.3 (with 4.3.2)
  - **Blocks**: Phase 5
  - **Blocked By**: 4.1.2, 4.1.3, 4.2.2

  **References**:
  - `newProject.md:204-227` - 首页功能描述
  - `newProject.md:210-215` - 核心流程
  - `newProject.md:217-222` - UI 特性

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd frontend && pnpm test run src/views/__tests__/HomeView.test.ts
  # Assert: 首页测试通过
  ```

  **Agent-Executable Verification (Playwright)**:
  ```
  1. Navigate to: http://localhost:5173/
  2. Fill: textarea with "这是一段测试小说文本..."
  3. Click: button containing "一键生成"
  4. Wait for: element ".log-panel" to be visible
  5. Wait for: progress bar to show > 0%
  6. Assert: loading indicator is visible
  7. Screenshot: .sisyphus/evidence/task-4.3.1-home-generating.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add HomeView with one-click generation`
  - Files: `frontend/src/views/HomeView.vue`, `frontend/src/views/__tests__/HomeView.test.ts`

---

- [ ] 4.3.2. 分步工作流 - Step 1 脚本生成

  **What to do**:
  - 实现文本输入
  - 实现脚本生成调用
  - 展示分镜列表
  - 支持编辑分镜内容
  - **TDD**: 先写页面测试

  **Must NOT do**:
  - 不要实现分镜拖拽排序
  - 不要实现分镜删除/添加

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4.3 (with 4.3.1, 4.3.3)
  - **Blocks**: 4.3.4
  - **Blocked By**: 4.1.2, 4.1.3, 4.2.2

  **References**:
  - `newProject.md:266-288` - Step 1 功能描述
  - `newProject.md:277-285` - 分镜数据结构

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd frontend && pnpm test run src/views/video/__tests__/Step1ScriptView.test.ts
  # Assert: 测试通过
  ```

  **Agent-Executable Verification (Playwright)**:
  ```
  1. Navigate to: http://localhost:5173/video/step1-script
  2. Fill: textarea with "一个冒险故事..."
  3. Click: button containing "生成分镜"
  4. Wait for: element ".scene-card" count >= 8
  5. Assert: each scene card has "scene_id", "narration", "image_prompt"
  6. Screenshot: .sisyphus/evidence/task-4.3.2-step1.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add Step1 script generation view`
  - Files: `frontend/src/views/video/Step1ScriptView.vue`, `frontend/src/views/video/__tests__/Step1ScriptView.test.ts`

---

- [ ] 4.3.3. 分步工作流 - Step 2 音频生成

  **What to do**:
  - 展示分镜列表（从 Store 读取）
  - 实现批量音频生成
  - 实现单个重新生成
  - 音频预览播放
  - **TDD**: 先写页面测试

  **Must NOT do**:
  - 不要实现音色选择
  - 不要实现音频下载

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4.3 (with 4.3.2)
  - **Blocks**: 4.3.4
  - **Blocked By**: 4.1.2, 4.1.3, 4.2.2

  **References**:
  - `newProject.md:291-309` - Step 2 功能描述

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd frontend && pnpm test run src/views/video/__tests__/Step2AudioView.test.ts
  # Assert: 测试通过
  ```

  **Agent-Executable Verification (Playwright)**:
  ```
  1. Navigate to: http://localhost:5173/video/step2-audio
  2. Assert: scene list is visible
  3. Click: button containing "批量生成"
  4. Wait for: each scene card has audio player
  5. Click: first audio play button
  6. Assert: audio is playing (or has played)
  7. Screenshot: .sisyphus/evidence/task-4.3.3-step2.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add Step2 audio generation view`
  - Files: `frontend/src/views/video/Step2AudioView.vue`, `frontend/src/views/video/__tests__/Step2AudioView.test.ts`

---

- [ ] 4.3.4. 分步工作流 - Step 3 图片生成

  **What to do**:
  - 展示分镜列表
  - 实现批量图片生成（每分镜 3 张）
  - 实现单个重新生成
  - 图片预览
  - **TDD**: 先写页面测试

  **Must NOT do**:
  - 不要实现图片选择/删除
  - 不要实现 prompt 编辑

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4.3 (after 4.3.2, 4.3.3)
  - **Blocks**: 4.3.5
  - **Blocked By**: 4.3.2, 4.3.3

  **References**:
  - `newProject.md:311-334` - Step 3 功能描述

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd frontend && pnpm test run src/views/video/__tests__/Step3ImagesView.test.ts
  # Assert: 测试通过
  ```

  **Agent-Executable Verification (Playwright)**:
  ```
  1. Navigate to: http://localhost:5173/video/step3-images
  2. Click: button containing "批量生成"
  3. Wait for: each scene has 3 images
  4. Assert: images are visible and loaded
  5. Screenshot: .sisyphus/evidence/task-4.3.4-step3.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add Step3 image generation view`
  - Files: `frontend/src/views/video/Step3ImagesView.vue`, `frontend/src/views/video/__tests__/Step3ImagesView.test.ts`

---

- [ ] 4.3.5. 分步工作流 - Step 4 视频生成

  **What to do**:
  - 展示分镜列表
  - 实现批量视频合成
  - 实现单个重新生成
  - 视频预览播放
  - **TDD**: 先写页面测试

  **Must NOT do**:
  - 不要实现视频下载
  - 不要实现 Ken Burns 参数调整

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4.3 (after 4.3.4)
  - **Blocks**: 4.3.6
  - **Blocked By**: 4.3.4

  **References**:
  - `newProject.md:336-366` - Step 4 功能描述

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd frontend && pnpm test run src/views/video/__tests__/Step4VideosView.test.ts
  # Assert: 测试通过
  ```

  **Agent-Executable Verification (Playwright)**:
  ```
  1. Navigate to: http://localhost:5173/video/step4-videos
  2. Click: button containing "批量生成"
  3. Wait for: each scene has video player
  4. Click: first video play button
  5. Assert: video is playing
  6. Screenshot: .sisyphus/evidence/task-4.3.5-step4.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add Step4 video generation view`
  - Files: `frontend/src/views/video/Step4VideosView.vue`, `frontend/src/views/video/__tests__/Step4VideosView.test.ts`

---

- [ ] 4.3.6. 分步工作流 - Step 5 合并导出

  **What to do**:
  - 展示所有分镜视频预览
  - 实现一键合并
  - 实现最终视频预览
  - 实现视频下载
  - **TDD**: 先写页面测试

  **Must NOT do**:
  - 不要实现分镜排序
  - 不要实现重新开始流程

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4.3 (after 4.3.5)
  - **Blocks**: Phase 5
  - **Blocked By**: 4.3.5

  **References**:
  - `newProject.md:368-385` - Step 5 功能描述

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd frontend && pnpm test run src/views/video/__tests__/Step5MergeView.test.ts
  # Assert: 测试通过
  ```

  **Agent-Executable Verification (Playwright)**:
  ```
  1. Navigate to: http://localhost:5173/video/step5-merge
  2. Assert: all scene videos are listed
  3. Click: button containing "合并导出"
  4. Wait for: final video player is visible
  5. Assert: download button is enabled
  6. Screenshot: .sisyphus/evidence/task-4.3.6-step5.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add Step5 merge and export view`
  - Files: `frontend/src/views/video/Step5MergeView.vue`, `frontend/src/views/video/__tests__/Step5MergeView.test.ts`

---

### Epic 4.4: 辅助功能页面

- [ ] 4.4.1. 章节提取页面

  **What to do**:
  - 实现文件上传（拖拽 + 点击）
  - 调用章节提取 API
  - 展示精彩片段列表
  - 支持复制片段到剪贴板
  - **TDD**: 先写页面测试

  **Must NOT do**:
  - 不要实现提取历史
  - 不要实现多文件上传

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4.4 (with 4.4.2)
  - **Blocks**: Phase 5
  - **Blocked By**: 4.2.1

  **References**:
  - `newProject.md:229-262` - 章节提取功能描述

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd frontend && pnpm test run src/views/__tests__/ChapterExtractView.test.ts
  # Assert: 测试通过
  ```

  **Agent-Executable Verification (Playwright)**:
  ```
  1. Navigate to: http://localhost:5173/chapter-extract
  2. Upload: tests/fixtures/sample_novel.txt
  3. Wait for: highlights list is visible
  4. Assert: 3-5 highlight cards are shown
  5. Click: first "复制" button
  6. Assert: toast shows "已复制"
  7. Screenshot: .sisyphus/evidence/task-4.4.1-chapter.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add chapter extraction view`
  - Files: `frontend/src/views/ChapterExtractView.vue`, `frontend/src/views/__tests__/ChapterExtractView.test.ts`

---

- [ ] 4.4.2. 小说爬取页面

  **What to do**:
  - 实现站点选择下拉框
  - 实现小说名/URL 输入
  - 调用爬取 API
  - 展示爬取进度和结果
  - **TDD**: 先写页面测试

  **Must NOT do**:
  - 不要实现自定义站点
  - 不要实现章节选择

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4.4 (with 4.4.1)
  - **Blocks**: Phase 5
  - **Blocked By**: 4.2.1

  **References**:
  - `newProject.md:387-409` - 小说爬取功能描述

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd frontend && pnpm test run src/views/__tests__/NovelCrawlerView.test.ts
  # Assert: 测试通过
  ```

  **Agent-Executable Verification (Playwright)**:
  ```
  1. Navigate to: http://localhost:5173/novel-crawler
  2. Select: dropdown option "站点A"
  3. Fill: input with "测试小说名"
  4. Click: button containing "开始爬取"
  5. Wait for: progress indicator
  6. Assert: chapter list is visible (or error message)
  7. Screenshot: .sisyphus/evidence/task-4.4.2-crawler.png
  ```

  **Commit**: YES
  - Message: `feat(frontend): add novel crawler view`
  - Files: `frontend/src/views/NovelCrawlerView.vue`, `frontend/src/views/__tests__/NovelCrawlerView.test.ts`

---

## Phase 5: 后端 API 端点实现

### Epic 5.1: 工作流 API

- [ ] 5.1.1. 一键工作流端点

  **What to do**:
  - 实现 POST `/api/v1/workflow/start`
  - 实现 GET `/api/v1/workflow/status/{task_id}`
  - 创建 Celery 任务链
  - **TDD**: 先写 API 测试

  **Must NOT do**:
  - 不要实现任务取消
  - 不要实现任务优先级

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5.1 (with 5.1.2)
  - **Blocks**: Phase 6
  - **Blocked By**: Phase 2, Phase 3

  **References**:
  - `newProject.md:509-516` - 工作流 API
  - `newProject.md:210-215` - 核心流程

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/api/test_workflow.py -v
  # Assert: API 测试通过

  # 端到端验证
  TASK_ID=$(curl -s -X POST http://localhost:8000/api/v1/workflow/start \
    -H "Content-Type: application/json" \
    -d '{"text": "测试小说文本..."}' | jq -r '.task_id')
  
  # 等待完成
  for i in {1..60}; do
    STATUS=$(curl -s http://localhost:8000/api/v1/workflow/status/$TASK_ID | jq -r '.status')
    if [ "$STATUS" = "completed" ]; then break; fi
    sleep 5
  done
  
  curl -s http://localhost:8000/api/v1/workflow/status/$TASK_ID | jq '.video_url'
  # Assert: 返回有效的视频 URL
  ```

  **Commit**: YES
  - Message: `feat(backend): add one-click workflow API`
  - Files: `backend/app/api/endpoints/workflow.py`, `backend/app/tasks/workflow_tasks.py`, `backend/tests/api/test_workflow.py`

---

- [ ] 5.1.2. 分步工作流端点

  **What to do**:
  - 实现脚本生成 API
  - 实现音频批量/单独生成 API
  - 实现图片批量/单独生成 API
  - 实现视频批量/单独生成 API
  - 实现合并 API
  - **TDD**: 先写 API 测试

  **Must NOT do**:
  - 不要实现步骤跳过
  - 不要实现回退

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5.1 (with 5.1.1)
  - **Blocks**: Phase 6
  - **Blocked By**: Phase 2, Phase 3

  **References**:
  - `newProject.md:517-524` - 分步工作流 API

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/api/test_video_workflow.py -v
  # Assert: API 测试通过

  # 分步验证
  # Step 1: 脚本生成
  curl -s -X POST http://localhost:8000/api/v1/video/script/generate \
    -H "Content-Type: application/json" \
    -d '{"text": "测试文本"}' | jq '.scenes | length'
  # Assert: 返回 8-10

  # Step 2: 音频生成
  curl -s -X POST http://localhost:8000/api/v1/video/audio/batch \
    -H "Content-Type: application/json" \
    -d '{"scenes": [...]}' | jq '.results | length'
  # Assert: 返回与输入相同数量
  ```

  **Commit**: YES
  - Message: `feat(backend): add step-by-step workflow APIs`
  - Files: `backend/app/api/endpoints/video_workflow.py`, `backend/tests/api/test_video_workflow.py`

---

- [ ] 5.1.3. 章节提取端点

  **What to do**:
  - 实现 POST `/api/v1/chapter/upload`
  - 处理文件上传
  - 调用 LLM 提取精彩片段
  - **TDD**: 先写 API 测试

  **Must NOT do**:
  - 不要实现文件持久化
  - 不要实现分段功能

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5.1 (with 5.1.4)
  - **Blocks**: Phase 6
  - **Blocked By**: 2.1.3

  **References**:
  - `newProject.md:525-530` - 章节处理 API

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/api/test_chapter.py -v
  # Assert: API 测试通过

  # 上传验证
  curl -s -X POST http://localhost:8000/api/v1/chapter/upload \
    -F "file=@tests/fixtures/sample_novel.txt" | jq '.highlights | length'
  # Assert: 返回 3-5
  ```

  **Commit**: YES
  - Message: `feat(backend): add chapter extraction API`
  - Files: `backend/app/api/endpoints/chapter_extract.py`, `backend/tests/api/test_chapter.py`

---

- [ ] 5.1.4. 小说爬取端点

  **What to do**:
  - 实现 POST `/api/v1/novel/crawl`
  - 实现 GET `/api/v1/novel/status/{task_id}`
  - 创建爬取 Celery 任务
  - 支持 2-3 个预设站点
  - **TDD**: 先写 API 测试

  **Must NOT do**:
  - 不要实现通用爬虫
  - 不要实现站点自动发现

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5.1 (with 5.1.3)
  - **Blocks**: Phase 6
  - **Blocked By**: 1.2.1

  **References**:
  - `newProject.md:532-538` - 小说爬取 API
  - `newProject.md:600-606` - 小说服务架构

  **Acceptance Criteria**:
  ```bash
  # TDD: 测试先行
  cd backend && pytest tests/api/test_novel.py -v
  # Assert: API 测试通过

  # 爬取验证（使用 mock 或预设站点）
  TASK_ID=$(curl -s -X POST http://localhost:8000/api/v1/novel/crawl \
    -H "Content-Type: application/json" \
    -d '{"site": "test", "keyword": "测试小说"}' | jq -r '.task_id')

  sleep 10
  curl -s http://localhost:8000/api/v1/novel/status/$TASK_ID | jq '.chapters | length'
  # Assert: 返回 > 0
  ```

  **Commit**: YES
  - Message: `feat(backend): add novel crawler API`
  - Files: `backend/app/api/endpoints/novel.py`, `backend/app/services/novel_service.py`, `backend/tests/api/test_novel.py`

---

## Phase 6: 集成和验收

### Epic 6.1: E2E 测试

- [ ] 6.1.1. 核心流程 E2E 测试

  **What to do**:
  - 配置 Playwright
  - 编写一键生成流程测试
  - 编写分步工作流测试
  - **TDD**: E2E 测试本身

  **Must NOT do**:
  - 不要测试边缘情况
  - 不要实现截图对比

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`playwright`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 6.1 (sequential)
  - **Blocks**: 6.1.2
  - **Blocked By**: Phase 4, Phase 5

  **References**:
  - Metis 分析 - 使用 Playwright 验证 UI 交互

  **Acceptance Criteria**:
  ```bash
  # 安装 Playwright
  cd frontend && pnpm exec playwright install chromium

  # 运行 E2E 测试
  cd frontend && pnpm exec playwright test e2e/
  # Assert: 所有测试通过

  # 测试报告
  cd frontend && pnpm exec playwright show-report
  # Assert: 可查看测试报告
  ```

  **Commit**: YES
  - Message: `test(e2e): add Playwright E2E tests for core flows`
  - Files: `frontend/e2e/`, `frontend/playwright.config.ts`

---

- [ ] 6.1.2. 修复和完善

  **What to do**:
  - 修复 E2E 测试发现的问题
  - 完善错误处理
  - 优化加载性能
  - 更新文档

  **Must NOT do**:
  - 不要添加新功能
  - 不要重构架构

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 6.1 (last)
  - **Blocks**: None
  - **Blocked By**: 6.1.1

  **References**:
  - E2E 测试结果
  - Metis 分析 - 边缘情况处理

  **Acceptance Criteria**:
  ```bash
  # 所有测试通过
  cd backend && pytest -v
  cd frontend && pnpm test run
  cd frontend && pnpm exec playwright test
  # Assert: 全部通过

  # 类型检查
  cd frontend && pnpm type-check
  # Assert: 无错误

  # 构建验证
  cd frontend && pnpm build
  # Assert: 构建成功
  ```

  **Commit**: YES
  - Message: `fix: address issues found in E2E testing`
  - Files: 根据实际修复内容

---

## Commit Strategy

| Phase | Message Pattern | Verification |
|-------|----------------|--------------|
| Phase 0 | `chore: ...` | 环境验证脚本 |
| Phase 1 | `feat(backend): ...` | pytest |
| Phase 2 | `feat(backend): ...` | pytest + API 调用 |
| Phase 3 | `feat(backend): ...` | pytest + ffprobe |
| Phase 4 | `feat(frontend): ...` | vitest + Playwright |
| Phase 5 | `feat(backend): ...` | pytest + curl |
| Phase 6 | `test(e2e): ...` / `fix: ...` | Playwright 全量 |

---

## Success Criteria

### Verification Commands

```bash
# 后端测试
cd backend && pytest -v --cov=app
# Expected: 覆盖率 > 80%

# 前端测试
cd frontend && pnpm test run --coverage
# Expected: 覆盖率 > 70%

# E2E 测试
cd frontend && pnpm exec playwright test
# Expected: 全部通过

# 类型检查
cd frontend && pnpm type-check
# Expected: 无错误

# 一键生成验证
curl -X POST http://localhost:8000/api/v1/workflow/start -d '{"text": "..."}' | jq
# Expected: 返回 task_id，最终生成视频
```

### Final Checklist

- [ ] 一键视频生成：500字 → 完整视频
- [ ] 分步工作流：5 步可独立执行
- [ ] 章节提取：上传 → 3-5 个片段
- [ ] 小说爬取：2-3 个站点可用
- [ ] SSE 进度：实时更新无断开
- [ ] 错误处理：清晰的错误提示
- [ ] AI 服务：配额耗尽自动切换
- [ ] 临时文件：24 小时自动清理

---

## Risk Management

### High Risk Items

| Risk | Mitigation |
|------|------------|
| AI 服务配额耗尽 | 模型切换机制 + 配额监控日志 |
| FFmpeg 处理超时 | 独立 Worker + 超时设置 |
| SSE 连接不稳定 | 前端自动重连 + 心跳机制 |
| 大文件上传 | 前端大小限制 + 后端校验 |

### Rollback Plan

每个 Phase 完成后创建 Git tag：
- `v0.0.1-phase0`: 环境验证完成
- `v0.0.2-phase1`: 后端基础设施完成
- `v0.0.3-phase2`: AI 服务集成完成
- `v0.0.4-phase3`: 视频处理完成
- `v0.0.5-phase4`: 前端完成
- `v0.1.0`: MVP 完成
