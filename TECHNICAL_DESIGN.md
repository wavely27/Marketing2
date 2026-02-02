## 1. 系统架构设计 (System Architecture)

### 1.1 总体架构 (Micro-Service Monolith)

虽然是单体仓库 (Monorepo)，但在逻辑上采用微服务分层架构，便于未来拆分。

**部署模式**: 单用户 (Single User Mode) - 无需登录认证系统。

```mermaid
graph TD
    User[用户浏览器] -->|HTTP/SSE| LB[Nginx/Load Balancer]
    LB -->|API Request| API[FastAPI Server]
    LB -->|Static Files| CDN[Nginx Static]
    
    subgraph "Backend Services"
        API -->|CRUD| DB[(PostgreSQL)]
        API -->|Task Push| Redis[(Redis Broker)]
        API -->|Progress Sub| Redis
        
        Worker[Celery Worker Cluster] -->|Task Pop| Redis
        Worker -->|Update Status| DB
        Worker -->|Update Progress| Redis
    end
    
    subgraph "External AI Services (Aliyun)"
        Worker -->|Generate Script| LLM[Qwen-Plus LLM]
        Worker -->|Generate Image| Img[Wanx-v1]
        Worker -->|Generate Audio| TTS[Sambert (Standard Voice)]
    end
    
    subgraph "Media Processing"
        Worker -->|Compose| FFmpeg[FFmpeg Binary]
        FFmpeg -->|Save| Storage[Local FS / OSS]
    end
```

### 1.2 核心组件

1.  **Web Server (FastAPI)**
    *   负责 RESTful API 响应。
    *   负责 SSE (Server-Sent Events) 连接维护，实时推送任务进度。
    *   **不处理**任何耗时超过 500ms 的逻辑。

2.  **Task Queue (Celery)**
    *   **Queue `default`**: 轻量级任务（如数据库清理、简单的状态更新）。
    *   **Queue `ai_generation`**: 调用外部 AI API 的任务（脚本生成、绘图、配音）。需要配置 Rate Limit。
    *   **Queue `video_processing`**: CPU 密集型任务（FFmpeg 渲染）。建议单独部署或分配独立资源。

3.  **Broker & Cache (Redis)**
    *   作为 Celery Broker。
    *   作为 SSE 的 Pub/Sub 通道（Worker -> Redis -> FastAPI -> User）。
    *   缓存高频读取的小说元数据。

4.  **Database (PostgreSQL)**
    *   使用 `JSONB` 存储灵活的分镜数据结构。
    *   利用 PG 的事务特性保证任务状态的一致性。

---

## 2. 数据库设计 (Database Schema)

使用 SQLAlchemy (Async) + Alembic 进行管理。

### 2.1 核心表结构

#### `tasks` (任务主表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| type | VARCHAR | 任务类型 (e.g., `novel_to_video`) |
| status | ENUM | `pending`, `script_gen`, `media_gen`, `video_render`, `success`, `failed` |
| progress | INT | 总体进度 (0-100) |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |
| input_params | JSONB | 用户的原始输入 (小说文本, 风格偏好, 角色设定) |
| output_url | VARCHAR | 最终视频地址 |
| error_msg | TEXT | 失败原因 (如: 敏感内容拦截) |

#### `scenes` (分镜表 - 核心资产)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| task_id | UUID | 外键 -> tasks.id |
| sequence | INT | 排序号 |
| script_text | TEXT | 分镜脚本文字 |
| narration | JSONB | 旁白内容: `{ text: string, emotion: string }` |
| image_prompt | JSONB | AI 绘图提示词: `{ positive: string, negative: string, character: string }` |
| image_urls | TEXT[] | 生成的图片路径（3张） |
| audio_url | VARCHAR | 生成的配音路径 |
| video_url | VARCHAR | 单分镜视频片段路径 |
| duration | FLOAT | 预估/实际时长（秒） |

---

## 3. 接口设计 (API Specification)

遵循 RESTful 规范。

### 3.1 任务控制
*   `POST /api/v1/workflow/create`: 创建新视频任务
    *   Input: `{ "novel_text": "...", "role_setting": "男主黑发..." }`
    *   Constraint: `novel_text` max 5000 chars.
    *   Output: `{ "task_id": "uuid" }`
*   `GET /api/v1/workflow/{task_id}`: 获取任务详情（包含所有分镜状态）
*   `POST /api/v1/workflow/{task_id}/cancel`: 取消任务

### 3.2 实时流
*   `GET /api/v1/sse/events/{task_id}`
    *   Event Types: `progress`, `log`, `scene_complete`, `error`, `finish`

### 3.3 分镜编辑 (Human-in-the-loop)
*   `PUT /api/v1/scenes/{scene_id}`: 修改分镜内容（如修改提示词、重写旁白）
*   `POST /api/v1/scenes/{scene_id}/regenerate_image`: 重新生成该分镜图片
*   `POST /api/v1/scenes/{scene_id}/regenerate_audio`: 重新生成该分镜配音

---

## 4. 核心业务流程 (Core Business Logic)

### 4.1 核心参数配置
*   **分镜策略**: 1 段文本 (Paragraph) -> 3 个分镜画面 (Scenes)。
*   **视频比例**: 9:16 (竖屏, 1080x1920)。
*   **BGM 策略**: 内置 5 首免版权音乐 (Happy, Sad, Tense, Relaxed, Action)，根据脚本情感标签自动匹配。

### 4.2 一键生成 Pipeline

1.  **脚本优化 & 切分 (Script Optimization)**
    *   Worker 调用 LLM (Qwen)。
    *   **Step 1 (Role Extraction)**: 提取主角特征 (如 "男主:黑发; 女主:红裙") -> 存入 `input_params.role_setting`。
    *   **Step 2 (Script Rewrite)**: 将小说改写为有吸引力的短视频文案。
    *   **Step 3 (Breakdown)**: 按 "1段话 -> 3镜头" 规则切分。输出 JSON List。
    *   *Prompt Key*: "请保持角色一致性，所有画面描述前必须加上: {role_setting}"。

2.  **并行素材生成 (Parallel Asset Generation)**
    *   **Group 任务**: 为每个 Scene 创建子任务。
    *   **绘图**: 调用 Wanx-v1。若 API 返回敏感拦截，标记该 Scene 为 Error，前端提示用户修改 Prompt。
    *   **配音**: 调用 Sambert TTS (标准旁白音色)。不进行情感切换。

3.  **视频合成 (Video Assembly)**
    *   **Ken Burns Effect**: 对 9:16 画布进行推拉运镜。
    *   **字幕**: 硬字幕 (Hardsub)。字体: 思源黑体 Heavy, 白色, 黑色描边, 底部居中。
    *   **混音**: 混入选定的 BGM (音量 20%) + TTS 人声 (音量 100%)。
    *   **输出**: H.264 MP4, 1080x1920, 30fps。

---

## 5. 异常处理与重试策略

*   **敏感内容**: AI 接口报错直接透传，不自动重试，交由用户人工干预。
*   **爬虫策略**: 预置 3 个低防护小说站源 (e.g., 笔趣阁镜像)。若源站 A 失败，自动尝试源站 B。
*   **API 限流**: 使用 `Tenacity` 库实现指数退避重试。

## 6. 前端实现建议 (Frontend)

*   **状态管理**: Pinia Store。
*   **操作流**: 
    1. 输入文本 -> (生成中) -> 2. 脚本/分镜列表页 (可编辑/重绘) -> 3. 最终预览页。
*   **播放器**: 原生 `<video>` 标签即可。

## 7. 部署方案 (Deployment)

*   **Docker Compose**:
    *   `app`: FastAPI
    *   `worker-ai`: Celery (Concurrency: 4)
    *   `worker-video`: Celery (Concurrency: 1)
    *   `redis`: Alpine
    *   `postgres`: Alpine
*   **Volume**: 挂载 `./output` 目录。

---
*Generated by Red (AI Butler) for Marketing2 Project*
