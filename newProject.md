# Marketing 项目功能与设计总结

> 本文档用于重构项目时的功能参考，总结了当前项目的所有功能模块、技术架构和设计思路。

---

## 一、项目概述

**项目名称**: AI 营销工具集 (Marketing)

**核心定位**: 互联网营销自动化平台，专注于小说推文和短视频推文场景的营销能力建设。

**MVP 目标**: 实现从内容生产到收入确认的完整闭环，通过自动化提升营销效率。

**核心场景**:
- 小说推文营销
- 短视频推文营销

---

## 项目意图与商业背景

### 1. 商业目标

**核心目标**: 通过 AI 技术将小说内容自动转化为短视频推广素材，实现低成本、高效率的内容营销闭环。

**商业模式**:
- **CPS 分成**: 用户通过短视频引流至小说平台阅读，按付费转化分成
- **CPA 推广**: 按用户注册/下载 APP 获得推广佣金
- **播放分成**: 短视频平台的播放量分成收益
- **带货佣金**: 结合小说周边商品的带货转化

**收入公式**: 
```
收入 = 视频数量 × 播放量 × 完播率 × 点击率 × 转化率 × 客单价
```

### 2. 用户场景与痛点

**目标用户**: 小说推广从业者、MCN 机构、个人自媒体创作者

**传统痛点**:
| 痛点 | 传统方式 | 本项目解决方案 |
|------|----------|----------------|
| 内容生产慢 | 手动剪辑 1-2 小时/条 | AI 自动生成 < 3 分钟/条 |
| 成本高 | 需要专业剪辑师、配音演员 | 纯 AI 生成，成本 ¥0.50/条 |
| 素材依赖 | 需要购买/寻找配图素材 | AI 实时生成漫画图片 |
| 规模受限 | 人力瓶颈，日产 5-10 条 | 自动化可达日产 100+ 条 |
| 质量不稳定 | 依赖个人技能 | AI 模板化输出，质量可控 |

### 3. 产品愿景

**阶段一 (MVP - 当前)**:
- 实现"小说文本 → 短视频"的端到端自动化
- 自动化率: 90%（仅保留人工质量审核）
- 目标: 验证技术可行性和市场需求

**阶段二 (规模化)**:
- 批量生产能力 (日产 100+ 条)
- 多风格模板（国风、现代、玄幻）
- 数据驱动的内容优化

**阶段三 (智能化)**:
- AI 自动选择爆点
- 发布后数据反馈闭环
- 自动优化生成策略

### 4. 核心价值主张

**对用户的价值**:
1. **降本增效**: 从手工制作到 AI 自动化，成本降低 90%，效率提升 20 倍
2. **门槛降低**: 无需专业剪辑技能，上传文本即可生成视频
3. **规模化生产**: 突破人力瓶颈，实现批量内容生产
4. **快速迭代**: 支持多版本生成，A/B 测试优化内容

**技术差异化**:
- 全阿里系 AI 服务，国内访问稳定无需翻墙
- 漫画式视频风格，避免真人素材版权问题
- Ken Burns 动效让静态图片"动"起来，提升观感
- 自动模型切换，配额耗尽无感切换备用模型

### 5. 完整工作链路 (0 → 收入确认)

```
┌─────────────────────────────────────────────────────────────────┐
│                        内容准备阶段                              │
├─────────────────────────────────────────────────────────────────┤
│  [素材获取] → [内容筛选] → [爆点提取]                            │
│      ↓            ↓            ↓                                │
│   爬取小说     热门题材     AI 分析                              │
│   API 对接     数据分析     情感曲线                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        内容生产阶段 (本项目核心)                  │
├─────────────────────────────────────────────────────────────────┤
│  [脚本生成] → [图片生成] → [配音生成] → [视频合成] → [质量审核]  │
│      ↓            ↓            ↓            ↓            ↓      │
│   LLM 创作    AI 绘图     TTS 语音    FFmpeg      人工审核      │
│   分镜脚本    漫画风格    情感控制    动效转场    最终确认       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        分发投放阶段                              │
├─────────────────────────────────────────────────────────────────┤
│  [账号管理] → [智能发布] → [标签优化]                            │
│      ↓            ↓            ↓                                │
│   多平台账号   最佳时间     热门标签                             │
│   权重维护     批量发布     SEO 布局                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        流量运营阶段                              │
├─────────────────────────────────────────────────────────────────┤
│  [数据监控] → [互动管理] → [流量优化]                            │
│      ↓            ↓            ↓                                │
│   实时监控     评论维护     投放调整                             │
│   完播分析     私信引流     AB 测试                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        转化变现阶段                              │
├─────────────────────────────────────────────────────────────────┤
│  [引流导流] → [用户转化] → [收入结算]                            │
│      ↓            ↓            ↓                                │
│   落地页跳转   注册转化     CPS/CPA                              │
│   短链追踪     付费转化     平台分成                             │
└─────────────────────────────────────────────────────────────────┘
```

### 6. 自动化程度分析

| 环节 | 自动化程度 | 本项目覆盖 |
|------|-----------|-----------|
| 素材获取 | 90% | ✅ 小说爬虫 |
| 内容筛选 | 85% | ✅ 章节提取 |
| 脚本创作 | 80% | ✅ LLM 生成 |
| 视频制作 | 90% | ✅ 核心功能 |
| 内容审核 | 0% | ⚠️ 人工保留 |
| 智能发布 | 90% | ❌ 未实现 |
| 数据监控 | 95% | ❌ 未实现 |
| 收入结算 | 90% | ❌ 未实现 |

**当前项目重点**: 内容生产阶段的全自动化（脚本→图片→音频→视频）

### 7. 关键指标 (KPI)

**生产效率**:
- 单视频生成时间: < 3 分钟
- 人工审核时间: < 1 分钟/条
- 日产量目标: 50-100 条

**质量指标**:
- 人工审核通过率: > 80%
- 平台审核通过率: > 95%
- 图片质量评分: > 7.5/10

**成本指标**:
- 单视频成本: ¥0.50
- 月运营成本: < ¥5000（1000条产能）

**效果指标** (发布后):
- 平均播放量: > 5000
- 完播率: > 40%
- 点击率: > 3%

---

## 二、技术栈

### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.4.0 | 前端框架 |
| TypeScript | ^5.2.0 | 类型安全 |
| Vite | ^5.0.0 | 构建工具 |
| Vue Router | ^4.2.0 | 路由管理 |
| Pinia | ^3.0.4 | 状态管理 |
| Axios | ^1.6.0 | HTTP 请求 |
| TailwindCSS | ^3.4.3 | 样式框架 |

### 后端
| 技术 | 用途 |
|------|------|
| Python | 后端语言 |
| FastAPI | Web 框架 |
| MoviePy | 视频处理 |
| FFmpeg | 视频编解码 |
| httpx | 异步 HTTP 客户端 |
| BeautifulSoup | HTML 解析 |

### AI 服务 (全阿里系)
| 模块 | 服务 | 说明 |
|------|------|------|
| 脚本生成 | 通义千问 (qwen-turbo/plus/max) | 免费额度充足，JSON 格式稳定，支持自动模型切换 |
| AI 绘图 | 通义万相 (wanx-v1) | ¥0.05/张，国内直连，二次元风格佳 |
| 配音 | 阿里 Sambert | 免费/低成本，生成速度极快 (<1s) |
| 视频合成 | FFmpeg + MoviePy | Ken Burns 动效、转场、字幕 |

---

## 三、功能模块详解

### 3.1 首页 - 一键视频生成 (HomeView)

**路由**: `/`

**功能描述**: 
输入小说片段，一键自动生成完整短视频。这是最简化的工作流，适合快速验证。

**核心流程**:
1. 用户输入小说文本
2. 调用后端 `/api/v1/workflow/start` 启动任务
3. 轮询 `/api/v1/workflow/status/{task_id}` 获取进度
4. 后端自动完成：脚本生成 → 图片生成 → 音频生成 → 视频合成
5. 返回最终视频 URL

**UI 特性**:
- 累计 API 消耗看板（LLM tokens、图片数、语音字符）
- 实时日志面板（支持图片 prompt、旁白文本展开）
- 历史任务管理（localStorage 持久化，最多 50 条）
- 视频预览和下载

**状态管理**:
- 使用 localStorage 存储历史记录
- 包含 LLM 使用统计、图片生成统计、音频统计

---

### 3.2 章节提取 (ChapterExtractView)

**路由**: `/chapter-extract`

**功能描述**: 
上传完整小说文件，AI 自动提取精彩片段用于视频制作。

**核心流程**:
1. 用户上传 .txt/.md 文件（拖拽或点击）
2. 调用 `/api/v1/chapter/upload` 上传文件
3. 后端 LLM 分析内容，提取精彩片段
4. 返回结果包含：
   - `rewritten_script`: 完整第三人称叙事脚本
   - `highlights`: 3-5 个精彩片段（每个 500-800 字）
   - `summary`: 全文概述

**章节分段功能**:
- 调用 `/api/v1/chapter/split` 将长文分段
- 每段约 5 万字，适合分批处理
- 支持单独下载或批量下载

**输出格式**:
```typescript
interface Highlight {
  id: number
  title: string           // 片段标题（10字以内）
  script: string          // 完整片段（500-800字）
  emotion: string         // 情感标签
  video_duration: number  // 建议视频时长（秒）
  tags: string[]          // 内容标签
  scene_description: string // 场景概述
}
```

---

### 3.3 分步视频工作流 (5 步流程)

这是更精细的视频制作流程，允许用户在每一步进行调整。

#### 步骤 1: 提炼分镜 (Step1ScriptView)

**路由**: `/video/step1-script`

**功能**:
- 输入小说片段
- 调用 `/api/v1/video/script/generate` 生成分镜脚本
- 返回 8-10 个分镜，每个包含：
  - `scene_id`: 分镜编号
  - `duration`: 时长（默认 10 秒）
  - `image_prompt`: 图片生成提示词（正向 + 负向）
  - `narration`: 旁白（文本 + 情感）

**分镜要求**:
- 每段旁白至少 100 字
- 第三人称全知视角叙述
- 包含动作、表情、心理、环境描写
- 图片提示词使用英文，anime style

---

#### 步骤 2: 生成音频 (Step2AudioView)

**路由**: `/video/step2-audio`

**功能**:
- 批量生成：`/api/v1/video/audio/batch`
- 单独重新生成：`/api/v1/video/audio/regenerate`
- 使用阿里 Sambert TTS 服务
- 支持音频预览播放

**技术实现**:
```python
# AudioService
result = SpeechSynthesizer.call(
    model=voice,
    text=text,
    sample_rate=48000,
    format='mp3'
)
```

---

#### 步骤 3: 生成图片 (Step3ImagesView)

**路由**: `/video/step3-images`

**功能**:
- 每个分镜生成 3 张图片
- 批量生成：`/api/v1/video/images/batch`
- 单独重新生成：`/api/v1/video/images/regenerate`
- 使用通义万相 wanx-v1 模型

**技术实现**:
```python
# ImageService
rsp = ImageSynthesis.call(
    model='wanx-v1',
    prompt=prompt,
    n=1,
    size='1024*1024',
    style='<anime>'
)
```

---

#### 步骤 4: 生成视频 (Step4VideosView)

**路由**: `/video/step4-videos`

**功能**:
- 将图片 + 音频合成为分镜视频
- 批量生成：`/api/v1/video/scenes/batch`
- 单独重新生成：`/api/v1/video/scenes/regenerate`

**视频特效**:
- **Ken Burns 效果**: 图片缩放动画
  - 类型 0: 渐进放大 (zoom in)
  - 类型 1: 渐进缩小 (zoom out)
  - 类型 2: 平移 (pan)
- **字幕**: 自动换行，支持中文字体
- **多图切换**: 3 张图片轮流展示，自动分配时长

**技术实现**:
```python
# VideoService
class VideoService:
    def create_scene_video(self, image_paths, audio_path, text, duration, output_filename, add_subtitle=True):
        # 使用 MoviePy 合成
        # 支持单图/多图模式
        # Ken Burns 动效
        # 字幕叠加
```

---

#### 步骤 5: 合并导出 (Step5MergeView)

**路由**: `/video/step5-merge`

**功能**:
- 将所有分镜视频拼接为最终视频
- 调用 `/api/v1/video/merge`
- 支持视频预览和下载
- 可重新开始整个流程

**技术实现**:
```python
def concat_videos(self, video_paths: list[str], output_filename: str):
    clips = [VideoFileClip(p) for p in video_paths]
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
```

---

### 3.4 小说爬取 (NovelCrawlerView)

**路由**: `/novel-crawler`

**功能描述**: 
从网络爬取小说内容，目前支持特定小说站点。

**核心流程**:
1. 输入小说名称
2. 调用 `/api/v1/novel/crawl` 启动爬取任务
3. 轮询 `/api/v1/novel/status/{task_id}` 获取进度
4. 支持一次爬取最多 100 章

**技术实现**:
- 基于 httpx + BeautifulSoup
- 支持 gb18030 编码
- 章节内容过滤和清洗

**当前限制**:
- 仅支持硬编码的特定小说（天眼风水师）
- 单次最多爬取 100 章

---

## 四、状态管理设计

### 4.1 视频工作流 Store (Pinia)

**文件**: `frontend/src/stores/videoWorkflow.ts`

```typescript
interface Scene {
  id: string
  sceneId: number
  narration: { text: string; emotion: string }
  imagePrompt: { positive: string; negative: string }
  audioPath?: string
  audioUrl?: string
  imagePaths?: string[]
  imageUrls?: string[]
  videoPath?: string
  videoUrl?: string
}

// 状态
const currentStep = ref(1)          // 当前步骤 (1-5)
const novelText = ref('')           // 原始小说文本
const scenes = ref<Scene[]>([])     // 分镜数据
const finalVideoPath = ref('')      // 最终视频路径
const finalVideoUrl = ref('')       // 最终视频 URL

// 计算属性
const allAudiosGenerated   // 所有音频是否生成完成
const allImagesGenerated   // 所有图片是否生成完成（每个分镜 3 张）
const allVideosGenerated   // 所有分镜视频是否生成完成

// Actions
setNovelText(text)
setScenes(scenes)
updateSceneAudio(sceneId, path, url)
updateSceneImages(sceneId, paths, urls)
updateSceneVideo(sceneId, path, url)
setFinalVideo(path, url)
goToStep(step)
reset()
```

---

## 五、UI 组件库

### 5.1 Card 组件

**文件**: `frontend/src/components/ui/Card.vue`

**Props**:
- `title?: string` - 卡片标题
- `padding?: 'none' | 'sm' | 'md' | 'lg'` - 内边距

**样式**: 白色背景、圆角、阴影、边框

---

### 5.2 Button 组件

**文件**: `frontend/src/components/ui/Button.vue`

**Props**:
- `variant?: 'primary' | 'secondary' | 'danger' | 'ghost'`
- `size?: 'sm' | 'md' | 'lg'`
- `loading?: boolean`
- `disabled?: boolean`

**样式变体**:
- primary: 紫色渐变
- secondary: 灰色背景
- danger: 红色
- ghost: 透明背景

---

### 5.3 StepIndicator 组件

**文件**: `frontend/src/components/ui/StepIndicator.vue`

**Props**:
- `steps: string[]` - 步骤名称数组
- `currentStep: number` - 当前步骤

**功能**: 显示 5 步工作流进度，已完成步骤显示勾选图标

---

### 5.4 ProgressBar 组件

**文件**: `frontend/src/components/ui/ProgressBar.vue`

**用途**: 显示进度条

---

## 六、API 端点汇总

### 视频工作流
| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/workflow/start` | POST | 启动一键视频生成任务 |
| `/api/v1/workflow/status/{task_id}` | GET | 获取任务状态和日志 |
| `/api/v1/video/script/generate` | POST | 生成分镜脚本 |
| `/api/v1/video/audio/batch` | POST | 批量生成音频 |
| `/api/v1/video/audio/regenerate` | POST | 重新生成单个音频 |
| `/api/v1/video/images/batch` | POST | 批量生成图片 |
| `/api/v1/video/images/regenerate` | POST | 重新生成单个分镜图片 |
| `/api/v1/video/scenes/batch` | POST | 批量生成分镜视频 |
| `/api/v1/video/scenes/regenerate` | POST | 重新生成单个分镜视频 |
| `/api/v1/video/merge` | POST | 合并所有分镜视频 |

### 章节处理
| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/chapter/upload` | POST | 上传章节文件并提取精彩片段 |
| `/api/v1/chapter/status/{task_id}` | GET | 获取提取任务状态 |
| `/api/v1/chapter/split` | POST | 将长文分割为多个片段 |

### 小说爬取
| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/novel/crawl` | POST | 启动小说爬取任务 |
| `/api/v1/novel/status/{task_id}` | GET | 获取爬取任务状态 |
| `/api/v1/novel/list` | GET | 获取已爬取小说列表 |

---

## 七、后端服务架构

### 7.1 LLM 服务 (llm_service.py)

**功能**:
- 脚本生成
- 精彩片段提取和改写
- 自动模型切换（配额耗尽时）

**模型优先级**:
1. qwen-turbo
2. qwen-plus
3. qwen-max
4. qwen-turbo-latest
5. qwen-plus-latest

**JSON 解析增强**:
- 清理 Markdown 标记
- 处理字符串内的控制字符
- 状态机追踪字符串边界

---

### 7.2 图片服务 (image_service.py)

**功能**: 调用通义万相生成 AI 图片

**配置**:
- 模型: wanx-v1
- 尺寸: 1024x1024
- 风格: anime

---

### 7.3 音频服务 (audio_service.py)

**功能**: 调用阿里 Sambert TTS 生成语音

**配置**:
- 采样率: 48000
- 格式: mp3

---

### 7.4 视频服务 (video_service.py)

**功能**:
- 单场景视频合成
- 多图 Ken Burns 动效
- 字幕生成（支持中文）
- 视频拼接

**字幕特性**:
- 自动换行（每行 25 字）
- 在标点处优先换行
- 支持多种中文字体回退

---

### 7.5 小说服务 (novel_service.py)

**功能**: 从网络爬取小说内容

**技术栈**: httpx + BeautifulSoup

**限制**: 目前仅支持特定站点

---

## 八、设计风格指南

### 8.1 整体风格
- 渐变色主题（紫色系、蓝色系）
- 圆角卡片设计
- 毛玻璃效果 (backdrop-blur)
- 平滑过渡动画

### 8.2 配色方案
| 模块 | 主色调 |
|------|--------|
| 脚本生成 | indigo → purple |
| 音频生成 | orange → amber |
| 图片生成 | pink → rose |
| 视频生成 | cyan → sky |
| 合并导出 | emerald → green |
| 小说爬取 | blue → cyan |

### 8.3 交互设计
- 步骤指示器显示进度
- 实时日志面板
- Loading 状态动画
- Hover 效果和微交互
- Toast 提示和确认对话框

---

## 九、目录结构

```
Marketing/
├── frontend/
│   ├── src/
│   │   ├── App.vue                    # 应用入口，顶部导航
│   │   ├── main.ts                    # Vue 应用初始化
│   │   ├── router/
│   │   │   └── index.ts               # 路由配置
│   │   ├── stores/
│   │   │   └── videoWorkflow.ts       # Pinia 状态管理
│   │   ├── views/
│   │   │   ├── HomeView.vue           # 首页：一键视频生成
│   │   │   ├── ChapterExtractView.vue # 章节提取
│   │   │   ├── NovelCrawlerView.vue   # 小说爬取
│   │   │   ├── video/
│   │   │   │   ├── Step1ScriptView.vue   # 分镜脚本
│   │   │   │   ├── Step2AudioView.vue    # 音频生成
│   │   │   │   ├── Step3ImagesView.vue   # 图片生成
│   │   │   │   ├── Step4VideosView.vue   # 视频生成
│   │   │   │   └── Step5MergeView.vue    # 合并导出
│   │   │   └── tools/
│   │   │       ├── NovelCrawlerView.vue  # 小说爬取工具
│   │   │       └── ChapterSplitView.vue  # 章节分割工具
│   │   └── components/
│   │       └── ui/
│   │           ├── Card.vue
│   │           ├── Button.vue
│   │           ├── StepIndicator.vue
│   │           └── ProgressBar.vue
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI 入口
│   │   ├── core/
│   │   │   └── config.py              # 配置管理
│   │   ├── api/
│   │   │   ├── router.py              # API 路由汇总
│   │   │   └── endpoints/
│   │   │       ├── workflow.py        # 一键工作流
│   │   │       ├── video_workflow.py  # 分步视频工作流
│   │   │       ├── chapter_extract.py # 章节提取
│   │   │       ├── novel.py           # 小说爬取
│   │   │       ├── script.py          # 脚本生成
│   │   │       ├── audio.py           # 音频生成
│   │   │       ├── image.py           # 图片生成
│   │   │       └── video.py           # 视频处理
│   │   ├── services/
│   │   │   ├── llm_service.py         # LLM 服务
│   │   │   ├── image_service.py       # 图片生成服务
│   │   │   ├── audio_service.py       # 音频生成服务
│   │   │   ├── video_service.py       # 视频合成服务
│   │   │   ├── novel_service.py       # 小说爬取服务
│   │   │   └── chapter_splitter.py    # 章节分割服务
│   │   └── models/
│   │       ├── cost.py                # 使用量统计模型
│   │       └── novel.py               # 小说数据模型
│   └── output/                        # 生成文件输出目录
│       ├── audio/
│       ├── images/
│       └── video/
│
├── tests/                             # 测试文件
├── .env                               # 环境变量
└── PROJECT.md                         # 项目文档
```

---

## 十、待改进点

### 10.1 前端
- [ ] 组件复用性不够，代码重复较多
- [ ] 缺少统一的 API 请求封装
- [ ] 错误处理不够完善
- [ ] 缺少骨架屏加载状态
- [ ] 移动端适配不完整
- [ ] 缺少单元测试

### 10.2 后端
- [ ] 任务队列管理较简单（内存存储）
- [ ] 缺少任务超时和重试机制
- [ ] 小说爬取仅支持特定站点
- [ ] 缺少用户认证系统
- [ ] 缺少速率限制

### 10.3 功能
- [ ] 视频预设模板
- [ ] 多语言支持
- [ ] 视频水印和品牌定制
- [ ] 批量任务管理
- [ ] 任务历史持久化（数据库）

---

## 十一、成本估算

| 资源 | 单价 | 15 秒视频成本 |
|------|------|--------------|
| 通义千问 | 免费额度 | ¥0 |
| 通义万相 | ¥0.05/张 | ¥0.50 (10张) |
| 阿里 Sambert | 免费 | ¥0 |
| **总计** | | **约 ¥0.50** |

生成时间: < 3 分钟

---

## 十二、环境变量

```bash
# .env
DASHSCOPE_API_KEY=your_api_key_here
```

---

*文档生成时间: 2026-01-30*
