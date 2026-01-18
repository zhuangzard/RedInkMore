<template>
  <div class="content-display">
    <!-- 生成按钮 -->
    <div v-if="displayStatus === 'idle'" class="generate-section">
      <button class="btn btn-primary generate-btn" @click="handleGenerate" :disabled="loading">
        <template v-if="loading">
          <span class="spinner"></span>
          生成中...
        </template>
        <template v-else>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          {{ isHistory ? '一键补全标题、文案和标签' : '一键生成小红书爆款内容' }}
        </template>
      </button>
      <p class="generate-hint">
        {{ isHistory ? '该历史记录目前没有正文内容，点击上方按钮即可一键补全' : '基于大纲 AI 自动生成适配小红书的爆款标题、正文及标签' }}
      </p>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="displayStatus === 'generating'" class="loading-section">
      <div class="loading-spinner"></div>
      <p>正在生成标题、文案和标签...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="displayStatus === 'error'" class="error-section">
      <div class="error-icon">!</div>
      <p class="error-message">{{ displayError || '生成失败，请重试' }}</p>
      <button class="btn btn-secondary" @click="handleGenerate">重新生成</button>
    </div>

    <!-- 生成结果 -->
    <div v-else-if="displayStatus === 'done'" class="result-section">
      <!-- 标题区域 -->
      <div class="content-card">
        <div class="card-header">
          <h3>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 6h16M4 12h16M4 18h10"/>
            </svg>
            标题
          </h3>
          <button class="copy-btn" @click="copyTitles" :class="{ copied: copiedTitles }">
            <svg v-if="!copiedTitles" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            {{ copiedTitles ? '已复制' : '复制' }}
          </button>
        </div>
        <div class="titles-list">
          <div v-for="(title, index) in displayTitles" :key="index" class="title-item" @click="copyTitle(title, index)">
            <span class="title-badge">{{ index === 0 ? '推荐' : `备选${index}` }}</span>
            <span class="title-text">{{ title }}</span>
            <span class="copy-hint" :class="{ show: copiedTitleIndex === index }">
              {{ copiedTitleIndex === index ? '已复制' : '点击复制' }}
            </span>
          </div>
        </div>
      </div>

      <!-- 文案区域 -->
      <div class="content-card">
        <div class="card-header">
          <h3>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
            文案
          </h3>
          <button class="copy-btn" @click="copyCopywriting" :class="{ copied: copiedCopywriting }">
            <svg v-if="!copiedCopywriting" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            {{ copiedCopywriting ? '已复制' : '复制' }}
          </button>
        </div>
        <div class="copywriting-content">
          <p v-for="(paragraph, index) in formattedCopywriting" :key="index">{{ paragraph }}</p>
          <p v-if="formattedCopywriting.length === 0" class="empty-hint">暂无文案正文</p>
        </div>
      </div>

      <!-- 标签区域 -->
      <div class="content-card">
        <div class="card-header">
          <h3>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
              <line x1="7" y1="7" x2="7.01" y2="7"/>
            </svg>
            标签
          </h3>
          <button class="copy-btn" @click="copyTags" :class="{ copied: copiedTags }">
            <svg v-if="!copiedTags" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            {{ copiedTags ? '已复制' : '复制全部' }}
          </button>
        </div>
        <div class="tags-list">
          <span
            v-for="(tag, index) in displayTags"
            :key="index"
            class="tag-item"
            @click="copyTag(tag, index)"
            :class="{ copied: copiedTagIndex === index }"
          >
            #{{ tag }}
          </span>
          <p v-if="displayTags.length === 0" class="empty-hint">暂无标签</p>
        </div>
      </div>

      <!-- 重新生成按钮 -->
      <div v-if="displayStatus === 'done'" class="regenerate-section">
        <button class="btn btn-outline" @click="handleGenerate" :disabled="loading">
          <template v-if="loading">
            <span class="spinner"></span>
            正在重新生成...
          </template>
          <template v-else>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 4v6h-6"></path>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
            重新生成文案
          </template>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useGeneratorStore } from '../../stores/generator'
import { generateContent } from '../../api'

const props = defineProps<{
  isHistory?: boolean
  initialTitles?: string[]
  initialCopywriting?: string
  initialTags?: string[]
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'generate'): void
}>()

const store = useGeneratorStore()

const internalLoading = ref(false)
const loading = computed(() => props.loading || internalLoading.value)
const copiedTitles = ref(false)
const copiedCopywriting = ref(false)
const copiedTags = ref(false)
const copiedTitleIndex = ref<number | null>(null)
const copiedTagIndex = ref<number | null>(null)

const contentState = computed(() => store.content)

const displayStatus = computed(() => {
  if (props.isHistory) {
    // 如果是历史记录模式，且没有任何有效内容，则允许生成
    const hasContent = (props.initialTitles && props.initialTitles.length > 0 && !props.initialTitles[0].startsWith('http')) || 
                      (props.initialCopywriting && props.initialCopywriting !== '暂无内容')
    return hasContent ? 'done' : 'idle'
  }
  return contentState.value.status
})

const displayError = computed(() => contentState.value.error)

const displayTitles = computed(() => {
  return props.initialTitles || contentState.value.titles
})

const displayCopywriting = computed(() => {
  return props.initialCopywriting || contentState.value.copywriting
})

const displayTags = computed(() => {
  return props.initialTags || contentState.value.tags
})

// 格式化文案（按换行分段）
const formattedCopywriting = computed(() => {
  const text = displayCopywriting.value
  if (!text) return []
  return text.split('\n').filter((p: string) => p.trim())
})

// 生成内容
async function handleGenerate() {
  if (loading.value) return

  if (props.isHistory) {
    emit('generate')
    return
  }

  internalLoading.value = true
  store.startContentGeneration()

  try {
    const result = await generateContent(store.topic, store.outline.raw)

    if (result.success && result.titles && result.copywriting && result.tags) {
      store.setContent(result.titles, result.copywriting, result.tags)
    } else {
      store.setContentError(result.error || '生成失败')
    }
  } catch (error: any) {
    store.setContentError(error.message || '生成失败，请重试')
  } finally {
    internalLoading.value = false
  }
}

// 复制到剪贴板
async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    // 降级方案
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    try {
      document.execCommand('copy')
      return true
    } catch {
      return false
    } finally {
      document.body.removeChild(textarea)
    }
  }
}

// 复制所有标题
async function copyTitles() {
  const text = displayTitles.value.join('\n')
  if (await copyToClipboard(text)) {
    copiedTitles.value = true
    setTimeout(() => copiedTitles.value = false, 2000)
  }
}

// 复制单个标题
async function copyTitle(title: string, index: number) {
  if (await copyToClipboard(title)) {
    copiedTitleIndex.value = index
    setTimeout(() => copiedTitleIndex.value = null, 2000)
  }
}

// 复制文案
async function copyCopywriting() {
  const text = displayCopywriting.value || ''
  if (await copyToClipboard(text)) {
    copiedCopywriting.value = true
    setTimeout(() => copiedCopywriting.value = false, 2000)
  }
}

// 复制所有标签
async function copyTags() {
  const text = displayTags.value.map((t: string) => `#${t}`).join(' ')
  if (await copyToClipboard(text)) {
    copiedTags.value = true
    setTimeout(() => copiedTags.value = false, 2000)
  }
}

// 复制单个标签
async function copyTag(tag: string, index: number) {
  if (await copyToClipboard(`#${tag}`)) {
    copiedTagIndex.value = index
    setTimeout(() => copiedTagIndex.value = null, 2000)
  }
}
</script>

<style scoped>
.content-display {
  margin-top: 32px;
}

.generate-section {
  text-align: center;
  padding: 40px 20px;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 2px dashed var(--border-color);
}

.generate-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 16px 32px;
  font-size: 16px;
}

.generate-btn svg {
  width: 20px;
  height: 20px;
}

.loading-section {
  text-align: center;
  padding: 60px 20px;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

.loading-section p {
  color: var(--text-sub);
  font-size: 16px;
}

.error-section {
  text-align: center;
  padding: 40px 20px;
  background: #FFF2F0;
  border-radius: var(--radius-xl);
  border: 1px solid #FFCCC7;
}

.error-icon {
  width: 48px;
  height: 48px;
  background: #FF4D4F;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
  margin: 0 auto 16px;
}

.error-message {
  color: #CF1322;
  margin-bottom: 20px;
  white-space: pre-line;
}

.result-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.content-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-sm);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.card-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-main);
  margin: 0;
}

.card-header h3 svg {
  width: 20px;
  height: 20px;
  color: var(--primary);
}

.copy-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-sub);
  background: var(--bg-body);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
}

.copy-btn:hover {
  background: var(--primary-light);
  color: var(--primary);
  border-color: var(--primary);
}

.copy-btn.copied {
  background: #E6FFFB;
  color: #13C2C2;
  border-color: #13C2C2;
}

.copy-btn svg {
  width: 14px;
  height: 14px;
}

/* 标题列表 */
.titles-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.title-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-body);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.title-item:hover {
  background: var(--primary-light);
}

.title-badge {
  flex-shrink: 0;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 4px;
  background: var(--primary);
  color: white;
}

.title-item:not(:first-child) .title-badge {
  background: var(--text-sub);
}

.title-text {
  flex: 1;
  font-size: 15px;
  color: var(--text-main);
  line-height: 1.5;
}

.copy-hint {
  font-size: 12px;
  color: var(--text-sub);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.title-item:hover .copy-hint {
  opacity: 1;
}

.copy-hint.show {
  opacity: 1;
  color: #13C2C2;
}

/* 文案内容 */
.copywriting-content {
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-main);
}

.copywriting-content p {
  margin: 0 0 12px;
}

.copywriting-content p:last-child {
  margin-bottom: 0;
}

/* 标签列表 */
.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-item {
  padding: 8px 16px;
  font-size: 14px;
  color: var(--primary);
  background: var(--primary-light);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tag-item:hover {
  background: var(--primary);
  color: white;
}

.tag-item.copied {
  background: #13C2C2;
  color: white;
}

/* 重新生成 */
.regenerate-section {
  text-align: center;
  padding-top: 8px;
}

.regenerate-section .btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.regenerate-section .btn svg {
  width: 16px;
  height: 16px;
}

/* 动画 */
@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.empty-hint {
  color: var(--text-sub, #999);
  font-size: 14px;
  font-style: italic;
  margin: 0;
  padding: 8px 0;
}
</style>
