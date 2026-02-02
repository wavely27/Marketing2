# AI 营销自动化平台 - 技术方案

> **项目名称**: Marketing2  
> **文档版本**: v1.0  
> **生成日期**: 2026-02-02

---

## 一、项目概述

### 1.1 产品定位

**AI 漫画式短视频生成工具** - 将小说文本自动转换为短视频，实现内容营销自动化。

### 1.2 核心价值

| 指标 | 传统方式 | 本方案 |
|------|----------|--------|
| 单视频生成时间 | 1-2 小时 | < 3 分钟 |
| 单视频成本 | ¥50-100 | ¥0.50 |
| 日产能 | 5-10 条 | 50+ 条 |
| 技能要求 | 专业剪辑师 | 无需专业技能 |

### 1.3 MVP 范围

| 功能 | 状态 |
|------|------|
| 一键视频生成 | MVP |
| 分步视频工作流 (5步) | MVP |
| 章节精彩片段提取 | MVP |
| 小说爬取 (2-3站点) | MVP |
| 实时 SSE 进度推送 | MVP |
| 多用户系统 | 延后 |
| 多风格模板 | 延后 |
| 移动端适配 | 延后 |

---

## 二、技术架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户浏览器                               │
│                    Vue 3 + TypeScript + Vite                    │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP / SSE
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI 服务                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  API 路由    │  │  SSE 推送   │  │  静态文件   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Redis       │     │  PostgreSQL   │     │ Celery Workers│
│  (Broker)     │     │   (JSONB)     │     │  ai / video   │
└───────────────┘     └───────────────┘     └───────────────┘
                                                    │
                              ┌─────────────────────┼─────────────┐
                              ↓                     ↓             ↓
                        ┌──────────┐         ┌──────────┐   ┌──────────┐
                        │通义千问  │         │通义万相  │   │  FFmpeg  │
                        │  (LLM)   │         │ (绘图)   │   │  (视频)  │
                        └──────────┘         └──────────┘   └──────────┘
```

### 2.2 技术栈详情

#### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.4 | 前端框架 |
| TypeScript | ^5.2 | 类型安全 |
| Vite | ^5.0 | 构建工具 |
| Pinia | ^3.0 | 状态管理 |
| TailwindCSS | ^3.4 | 样式框架 |
| Axios | ^1.6 | HTTP 请求 |

#### 后端

| 技术 | 用途 |
|------|------|
| Python 3.10+ | 后端语言 |
| FastAPI | Web 框架 |
| Celery | 异步任务队列 |
| Redis | Broker + 缓存 |
| PostgreSQL | 数据持久化 |
| FFmpeg | 视频处理 |

#### AI 服务 (阿里云)

| 服务 | 模型 | 成本 |
|------|------|------|
| 通义千问 | qwen-turbo/plus/max | 免费额度 |
| 通义万相 | wanx-v1 | ¥0.05/张 |
| Sambert TTS | sambert-xxx | 免费 |

---

## 三、核心流程

### 3.1 一键视频生成

```
用户输入文本
     │
     ↓
┌────────────────────────────────────────────────────┐
│  Celery 任务链 (ai-worker)                          │
├────────────────────────────────────────────────────┤
│  1. LLM 生成分镜脚本 (8-10 个场景)                   │
│  2. 每个分镜生成 3 张 AI 图片                        │
│  3. 每个分镜生成 TTS 配音                           │
└─────────────────────────┬──────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────┐
│  Celery 任务链 (video-worker)                       │
├────────────────────────────────────────────────────┤
│  4. 每个分镜合成视频 (Ken Burns + 字幕)             │
│  5. 拼接所有分镜为最终视频                          │
└─────────────────────────┬──────────────────────────┘
                          ↓
                    返回视频 URL
```

### 3.2 分步工作流

| 步骤 | 功能 | 输入 | 输出 |
|------|------|------|------|
| Step 1 | 脚本生成 | 小说文本 | 8-10 个分镜脚本 |
| Step 2 | 音频生成 | 分镜旁白 | 每分镜 1 个 MP3 |
| Step 3 | 图片生成 | 分镜描述 | 每分镜 3 张图片 |
| Step 4 | 视频合成 | 图片+音频 | 每分镜 1 个视频 |
| Step 5 | 合并导出 | 分镜视频 | 最终完整视频 |

---

## 四、数据模型

### 4.1 任务表 (tasks)

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL,          -- workflow, script, audio, image, video
    status VARCHAR(20) NOT NULL,        -- pending, script_gen, media_gen, video_render, success, failed
    progress INTEGER DEFAULT 0,         -- 0-100
    input_data JSONB,                   -- 输入参数
    output_data JSONB,                  -- 输出结果
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 4.2 分镜数据结构 (JSONB)

```typescript
interface Scene {
  scene_id: number
  duration: number              // 秒
  image_prompt: {
    positive: string           // 正向提示词
    negative: string           // 负向提示词
  }
  narration: {
    text: string               // 旁白文本 (100字+)
    emotion: string            // 情感标签
  }
  audio_path?: string
  image_paths?: string[]       // 3张图片
  video_path?: string
}
```

---

## 五、API 设计

### 5.1 工作流 API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/workflow/start` | POST | 启动一键生成任务 |
| `/api/v1/workflow/status/{task_id}` | GET | 获取任务状态 |
| `/api/v1/workflow/stream/{task_id}` | GET (SSE) | 实时进度推送 |

### 5.2 分步工作流 API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/video/script/generate` | POST | 生成分镜脚本 |
| `/api/v1/video/audio/batch` | POST | 批量生成音频 |
| `/api/v1/video/audio/regenerate` | POST | 重新生成单个音频 |
| `/api/v1/video/images/batch` | POST | 批量生成图片 |
| `/api/v1/video/images/regenerate` | POST | 重新生成单个图片 |
| `/api/v1/video/scenes/batch` | POST | 批量生成分镜视频 |
| `/api/v1/video/merge` | POST | 合并最终视频 |

### 5.3 辅助功能 API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/chapter/upload` | POST | 上传小说并提取片段 |
| `/api/v1/novel/crawl` | POST | 启动小说爬取 |
| `/api/v1/novel/status/{task_id}` | GET | 获取爬取状态 |

---

## 六、目录结构

```
Marketing2/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口
│   │   ├── celery_app.py           # Celery 配置
│   │   ├── core/
│   │   │   ├── config.py           # 配置管理
│   │   │   ├── database.py         # 数据库连接
│   │   │   └── retry.py            # 重试装饰器
│   │   ├── api/
│   │   │   ├── router.py           # 路由汇总
│   │   │   └── endpoints/
│   │   │       ├── workflow.py     # 一键工作流
│   │   │       ├── video_workflow.py
│   │   │       ├── chapter_extract.py
│   │   │       ├── novel.py
│   │   │       └── sse.py          # SSE 进度
│   │   ├── services/
│   │   │   ├── llm_service.py      # 通义千问
│   │   │   ├── image_service.py    # 通义万相
│   │   │   ├── audio_service.py    # Sambert TTS
│   │   │   ├── video_service.py    # FFmpeg 封装
│   │   │   ├── novel_service.py    # 小说爬取
│   │   │   ├── task_service.py     # 任务管理
│   │   │   └── file_manager.py     # 文件清理
│   │   ├── tasks/
│   │   │   └── workflow_tasks.py   # Celery 任务
│   │   └── models/
│   │       └── task.py             # SQLAlchemy 模型
│   ├── tests/
│   │   ├── fixtures/               # 测试数据
│   │   └── ...                     # pytest 测试
│   ├── output/                     # 生成文件
│   │   ├── audio/
│   │   ├── images/
│   │   └── video/
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── router/index.ts
│   │   ├── stores/
│   │   │   └── videoWorkflow.ts    # Pinia Store
│   │   ├── api/
│   │   │   ├── client.ts           # Axios 封装
│   │   │   └── workflow.ts
│   │   ├── views/
│   │   │   ├── HomeView.vue        # 一键生成
│   │   │   ├── ChapterExtractView.vue
│   │   │   ├── NovelCrawlerView.vue
│   │   │   └── video/
│   │   │       ├── Step1ScriptView.vue
│   │   │       ├── Step2AudioView.vue
│   │   │       ├── Step3ImagesView.vue
│   │   │       ├── Step4VideosView.vue
│   │   │       └── Step5MergeView.vue
│   │   └── components/ui/
│   │       ├── Card.vue
│   │       ├── Button.vue
│   │       ├── StepIndicator.vue
│   │       └── ProgressBar.vue
│   ├── e2e/                        # Playwright 测试
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── .sisyphus/
│   └── plans/
│       └── ai-video-platform.md    # 详细开发计划
│
├── .env                            # 环境变量
├── PROJECT.md                      # 项目需求文档
├── newProject.md                   # 功能规格文档
└── SOLUTION.md                     # 本技术方案
```

---

## 七、关键技术决策

### 7.1 为什么选择 Celery + Redis

| 需求 | Celery 解决方案 |
|------|----------------|
| FFmpeg CPU 密集型 | 独立 Worker 进程，不阻塞 FastAPI |
| 任务持久化 | Redis 作为 Broker，重启不丢失 |
| 任务监控 | Flower 开箱即用 |
| 双队列 | ai-worker / video-worker 分离 |

### 7.2 为什么选择 SSE 而非 WebSocket

| 对比项 | SSE | WebSocket |
|--------|-----|-----------|
| 场景 | 单向推送 (任务进度) | 双向通信 |
| 复杂度 | 低 (FastAPI 原生支持) | 高 (心跳管理) |
| 重连 | 浏览器自动重连 | 需要手动实现 |
| **结论** | **本项目选择** | 不需要 |

### 7.3 AI 服务配额策略

```python
MODEL_PRIORITY = [
    "qwen-turbo",       # 主力模型
    "qwen-plus",        # 备用
    "qwen-max",         # 最终备用
]

# 配额耗尽时自动切换下一个模型
# 超时 30 秒 + 指数退避重试 (最多 3 次)
```

---

## 八、开发计划概览

### 8.1 阶段划分

| Phase | 内容 | 预估工时 |
|-------|------|----------|
| Phase 0 | 环境验证 + 项目脚手架 | 4h |
| Phase 1 | 后端基础设施 | 12h |
| Phase 2 | AI 服务集成 | 10h |
| Phase 3 | 视频处理服务 | 8h |
| Phase 4 | 前端实现 | 20h |
| Phase 5 | API 端点实现 | 8h |
| Phase 6 | 集成验收 | 4h |
| **总计** | | **60-80h** |

### 8.2 并行执行策略

```
Phase 0 ────┬──── Phase 1 ────┬──── Phase 2 ────┐
            │                 ├──── Phase 3 ────┤
            │                 └──── Phase 4 ────┼──── Phase 5 ──── Phase 6
            └─────────────────────────────────────┘
                    可并行执行
```

### 8.3 详细计划

详见 `.sisyphus/plans/ai-video-platform.md`，包含 42 个任务的：
- 验收标准 (可执行命令)
- 依赖关系
- 推荐 Agent 配置
- Commit 规范

---

## 九、风险与缓解

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| AI 配额耗尽 | 高 | 模型自动切换 + 配额监控 |
| FFmpeg 超时 | 高 | 独立 Worker + 超时设置 |
| SSE 断开 | 中 | 前端自动重连 + 心跳 |
| 临时文件堆积 | 中 | 24 小时自动清理 |
| 限流触发 | 中 | 指数退避重试 |

---

## 十、成本估算

### 单视频成本 (15 秒)

| 资源 | 用量 | 单价 | 成本 |
|------|------|------|------|
| 通义千问 | ~2000 tokens | 免费额度 | ¥0 |
| 通义万相 | 10 张图片 | ¥0.05/张 | ¥0.50 |
| Sambert TTS | ~1000 字符 | 免费 | ¥0 |
| **单视频总计** | | | **¥0.50** |

### 月度成本 (1000 条产能)

| 项目 | 成本 |
|------|------|
| AI 图片 | ¥500 |
| 服务器 | ¥200-500 |
| **月度总计** | **¥700-1000** |

---

## 十一、验收标准

### MVP 完成标准

- [ ] 一键视频生成：500 字输入 → 完整视频 < 5 分钟
- [ ] 分步工作流：5 个步骤可独立执行
- [ ] 章节提取：上传文件 → 返回 3-5 个片段
- [ ] 小说爬取：2-3 个站点可用
- [ ] SSE 进度：实时更新无断开
- [ ] 错误处理：清晰的错误提示
- [ ] 测试覆盖：后端 80%+，前端 70%+

### 验收命令

```bash
# 后端测试
cd backend && pytest -v --cov=app

# 前端测试
cd frontend && pnpm test run --coverage

# E2E 测试
cd frontend && pnpm exec playwright test

# 一键生成验证
curl -X POST http://localhost:8000/api/v1/workflow/start \
  -H "Content-Type: application/json" \
  -d '{"text": "测试小说文本..."}' | jq
```

---

*文档生成: 2026-02-02*  
*详细开发计划: `.sisyphus/plans/ai-video-platform.md`*
