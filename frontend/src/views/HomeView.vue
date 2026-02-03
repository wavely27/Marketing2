<template>
  <div class="home-view">
    <!-- Hero Section -->
    <section class="hero">
      <h1 class="hero-title">
        <span class="gradient-text">小说转视频</span>
        <span class="subtitle">AI驱动的创意引擎</span>
      </h1>
    </section>

    <!-- Input Section -->
    <section class="input-section">
      <div class="card">
        <div class="card-header">
          <h2>📝 输入小说文本</h2>
          <span class="char-counter">{{ novelText.length }} / 5000 字符</span>
        </div>

        <!-- Textarea -->
        <textarea
          v-model="novelText"
          class="novel-input"
          placeholder="在此粘贴小说段落，最多5000字符..."
          maxlength="5000"
          :disabled="isGenerating"
        ></textarea>

        <!-- File Upload -->
        <div class="file-upload-area">
          <input
            ref="fileInput"
            type="file"
            accept=".txt"
            @change="handleFileUpload"
            style="display: none"
            :disabled="isGenerating"
          />
          <button
            @click="$refs.fileInput?.click()"
            class="btn-secondary"
            :disabled="isGenerating"
          >
            📁 上传 .txt 文件
          </button>
        </div>

        <!-- Generate Button -->
        <button
          @click="handleGenerate"
          class="btn-primary btn-generate"
          :disabled="!novelText.trim() || isGenerating"
          :class="{ 'btn-loading': isGenerating }"
        >
          <span v-if="!isGenerating">🎬 一键生成视频</span>
          <span v-else>
            <span class="spinner"></span>
            生成中...
          </span>
        </button>

        <!-- Success/Error Messages -->
        <div v-if="successMessage" class="message message-success">
          ✅ {{ successMessage }}
        </div>
        <div v-if="errorMessage" class="message message-error">
          ❌ {{ errorMessage }}
        </div>
      </div>
    </section>

    <!-- Recent Projects (Mock for Phase 1) -->
    <section class="projects-section">
      <h2>📂 最近项目</h2>
      <div class="projects-grid">
        <!-- New Project Card -->
        <div class="project-card project-card-new" @click="resetForm">
          <div class="new-project-icon">＋</div>
          <p>新建项目</p>
        </div>

        <!-- Mock recent projects -->
        <div
          v-for="project in recentProjects"
          :key="project.id"
          class="project-card"
        >
          <div class="project-thumbnail">
            <div class="placeholder-image">🎬</div>
          </div>
          <div class="project-info">
            <h3>{{ project.title }}</h3>
            <p class="project-date">{{ project.date }}</p>
            <span class="project-status" :class="`status-${project.status}`">
              {{ getStatusText(project.status) }}
            </span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { workflowAPI } from '@/api';

// State
const novelText = ref('');
const isGenerating = ref(false);
const successMessage = ref('');
const errorMessage = ref('');
const fileInput = ref<HTMLInputElement | null>(null);

// Mock recent projects
const recentProjects = ref([
  {
    id: '1',
    title: '玄幻小说片段_001',
    date: '2024-02-01',
    status: 'success',
  },
  {
    id: '2',
    title: '都市爱情_测试',
    date: '2024-01-30',
    status: 'processing',
  },
]);

// Methods
const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  
  if (file && file.type === 'text/plain') {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      novelText.value = text.slice(0, 5000); // Limit to 5000 chars
    };
    reader.readAsText(file);
  } else {
    errorMessage.value = '请上传 .txt 文件';
    setTimeout(() => {
      errorMessage.value = '';
    }, 3000);
  }
};

const handleGenerate = async () => {
  if (!novelText.value.trim()) {
    errorMessage.value = '请输入小说文本';
    return;
  }

  isGenerating.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    // Call the backend API
    const response = await workflowAPI.create({
      novel_text: novelText.value,
      role_setting: undefined, // Can be added later
      style: 'default',
    });

    // Success!
    const taskId = response.data.task_id;
    successMessage.value = `任务创建成功！Task ID: ${taskId}`;
    
    console.log('✅ Workflow created:', response.data);
    
    // TODO Phase 3: Navigate to workbench view or poll for progress
    // For now, just show success message
    
  } catch (error: any) {
    console.error('❌ Failed to create workflow:', error);
    errorMessage.value = error.response?.data?.detail || '生成失败，请稍后重试';
  } finally {
    isGenerating.value = false;
  }
};

const resetForm = () => {
  novelText.value = '';
  successMessage.value = '';
  errorMessage.value = '';
};

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    success: '✅ 完成',
    processing: '⏳ 处理中',
    failed: '❌ 失败',
  };
  return statusMap[status] || status;
};
</script>

<style scoped>
.home-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

/* Hero Section */
.hero {
  text-align: center;
  margin-bottom: 3rem;
  animation: fadeIn 0.6s ease-out;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.gradient-text {
  background: linear-gradient(135deg, #00c3ff 0%, #7d3cff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 1.5rem;
  color: #888;
  font-weight: 400;
}

/* Input Section */
.input-section {
  margin-bottom: 3rem;
}

.card {
  background: #1e1e24;
  border: 1px solid #2a2a35;
  border-radius: 16px;
  padding: 2rem;
  transition: all 0.3s ease;
}

.card:hover {
  border-color: #00c3ff;
  box-shadow: 0 8px 32px rgba(0, 195, 255, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.card-header h2 {
  font-size: 1.5rem;
  color: #fff;
}

.char-counter {
  color: #888;
  font-size: 0.9rem;
}

.novel-input {
  width: 100%;
  min-height: 200px;
  padding: 1rem;
  background: #0f0f11;
  border: 2px solid #2a2a35;
  border-radius: 12px;
  color: #fff;
  font-size: 1rem;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.3s ease;
}

.novel-input:focus {
  outline: none;
  border-color: #00c3ff;
}

.novel-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.file-upload-area {
  margin: 1.5rem 0;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: #2a2a35;
  color: #fff;
  border: 1px solid #3a3a45;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
}

.btn-secondary:hover:not(:disabled) {
  background: #3a3a45;
  border-color: #00c3ff;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  width: 100%;
  padding: 1.25rem;
  background: linear-gradient(135deg, #00c3ff 0%, #7d3cff 100%);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 1.25rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 1.5rem;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 195, 255, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-loading {
  position: relative;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Messages */
.message {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 8px;
  font-weight: 500;
}

.message-success {
  background: rgba(0, 195, 100, 0.1);
  border: 1px solid rgba(0, 195, 100, 0.3);
  color: #00c364;
}

.message-error {
  background: rgba(255, 100, 100, 0.1);
  border: 1px solid rgba(255, 100, 100, 0.3);
  color: #ff6464;
}

/* Projects Section */
.projects-section h2 {
  font-size: 2rem;
  margin-bottom: 1.5rem;
  color: #fff;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.project-card {
  background: #1e1e24;
  border: 1px solid #2a2a35;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.project-card:hover {
  border-color: #00c3ff;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 195, 255, 0.2);
}

.project-card-new {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  border-style: dashed;
}

.new-project-icon {
  font-size: 3rem;
  color: #00c3ff;
  margin-bottom: 1rem;
}

.project-thumbnail {
  width: 100%;
  aspect-ratio: 16/9;
  background: #0f0f11;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.placeholder-image {
  font-size: 3rem;
}

.project-info h3 {
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
  color: #fff;
}

.project-date {
  color: #888;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.project-status {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-success {
  background: rgba(0, 195, 100, 0.2);
  color: #00c364;
}

.status-processing {
  background: rgba(255, 195, 0, 0.2);
  color: #ffc300;
}

.status-failed {
  background: rgba(255, 100, 100, 0.2);
  color: #ff6464;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive */
@media (max-width: 768px) {
  .hero-title {
    font-size: 2.5rem;
  }
  
  .subtitle {
    font-size: 1.2rem;
  }
  
  .projects-grid {
    grid-template-columns: 1fr;
  }
}
</style>
