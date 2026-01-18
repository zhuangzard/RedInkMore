<template>
  <!-- 图片画廊模态框 -->
  <div v-if="visible && record" class="modal-fullscreen" @click="$emit('close')">
    <div class="modal-body" @click.stop>
      <!-- 头部区域 -->
      <div class="modal-header">
        <div class="header-left">
          <button class="return-btn" @click="$emit('close')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            返回
          </button>
          <div class="header-divider"></div>
          <div class="title-container">
            <h3 v-if="!isEditingTitle" @dblclick="startEditingTitle" class="modal-title">
              {{ record.title }}
            </h3>
            <input
              v-else
              ref="titleInput"
              v-model="editingTitle"
              class="title-input"
              @blur="finishEditingTitle"
              @keyup.enter="finishEditingTitle"
              @keyup.esc="isEditingTitle = false"
            />
          </div>
        </div>

        <div class="header-actions">
          <button class="btn btn-primary download-btn" @click="handleDownloadAll">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            打包下载
          </button>
          <button class="close-icon" @click="$emit('close')">×</button>
        </div>
      </div>

      <!-- 主体内容滚动区域 -->
      <div class="modal-scroll-area">
        <div class="content-container">
          <!-- 图片卡片区域 -->
          <div class="modal-gallery-grid">
            <div
              v-for="(page, idx) in groupedImages"
              :key="idx"
              class="modal-img-card"
            >
              <div
                class="modal-img-preview"
                v-if="page.currentUrl"
                @click="viewImage(page.currentUrl)"
              >
                <img
                  :src="getSelectedUrl(idx) || page.currentUrl"
                  loading="lazy"
                  decoding="async"
                />
                
                <!-- 悬浮提示 -->
                <div class="hover-overlay">预览大图</div>

                <!-- 版本切换器 -->
                <div v-if="page.allVersions.length > 1" class="version-selector" @click.stop>
                  <button 
                    v-for="(vUrl, vIdx) in page.allVersions" 
                    :key="vIdx"
                    class="version-dot"
                    :class="{ active: (getSelectedUrl(idx) || page.currentUrl) === vUrl }"
                    @click="selectVersion(idx, vUrl)"
                    :title="`版本 ${vIdx + 1}`"
                  ></button>
                </div>
              </div>
              <div class="placeholder" v-else>等待生成...</div>

              <div class="img-card-footer">
                <span class="page-label">Page {{ idx + 1 }}</span>
                <div class="card-actions">
                  <button
                    class="action-icon-btn"
                    title="高级编辑"
                    @click="openEditor(idx, getSelectedUrl(idx) || page.currentUrl)"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                    高级编辑
                  </button>
                  <button class="action-text-btn" @click="handleDownload(idx)">下载</button>
                </div>
              </div>
            </div>
          </div>

          <!-- 文案内容区域 -->
          <div class="content-display-wrapper">
             <ContentDisplay 
              :is-history="true"
              :initial-titles="record.content?.titles?.length ? record.content.titles : [record.title]"
              :initial-copywriting="record.content?.copywriting || '暂无内容'"
              :initial-tags="record.content?.tags || []"
              :loading="isGeneratingContent"
              @generate="handleGenerateContent"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 图片编辑器模态框 (挂载在根部以避免样式干扰) -->
    <teleport to="body">
      <ImageEditor
        :show="showEditor"
        :image-url="editingImageUrl"
        :task-id="record?.images.task_id"
        :index="editingImageIndex"
        :prompt="editingImagePrompt"
        :initial-title="record?.content?.titles?.[0] || record?.title"
        :initial-copywriting="record?.content?.copywriting"
        :initial-tags="record?.content?.tags"
        @close="showEditor = false"
        @success="handleEditSuccess"
      />
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import ImageEditor from '../image/ImageEditor.vue'
import ContentDisplay from '../result/ContentDisplay.vue'
import { updateHistory, generateContent as apiGenerateContent } from '../../api'

/**
 * 图片画廊模态框组件
 *
 * 功能：
 * - 展示历史记录的所有生成图片
 * - 支持重新生成单张图片
 * - 支持下载单张/全部图片
 * - 可展开查看完整大纲
 */

// 定义记录类型
interface ViewingRecord {
  id: string
  title: string
  updated_at: string
  outline: {
    raw: string
    pages: Array<{ type: string; content: string }>
  }
  images: {
    task_id: string
    generated: string[]
  }
  content?: {
    titles: string[]
    copywriting: string
    tags: string[]
  }
}

// 定义 Props
const props = defineProps<{
  visible: boolean
  record: ViewingRecord | null
  regeneratingImages: Set<number>
}>()

// 定义 Emits
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'showOutline'): void
  (e: 'downloadAll'): void
  (e: 'download', filename: string, index: number): void
  (e: 'regenerate', index: number): void
  (e: 'editSuccess', result: { index: number; image_url: string; filename: string; content?: any }): void
  (e: 'updateTitle', title: string): void
  (e: 'refresh'): void
}>()

// 标题编辑状态
const isEditingTitle = ref(false)
const editingTitle = ref('')
const titleInput = ref<HTMLInputElement | null>(null)

/**
 * 开始编辑标题
 */
function startEditingTitle() {
  if (!props.record) return
  editingTitle.value = props.record.title
  isEditingTitle.value = true
  nextTick(() => {
    titleInput.value?.focus()
    titleInput.value?.select()
  })
}

/**
 * 完成编辑并保存
 */
function finishEditingTitle() {
  if (!isEditingTitle.value) return
  isEditingTitle.value = false
  
  if (props.record && editingTitle.value.trim() && editingTitle.value !== props.record.title) {
    emit('updateTitle', editingTitle.value.trim())
  }
}

// 分组并处理版本
const groupedImages = computed(() => {
  if (!props.record) return []
  const taskId = props.record.images.task_id
  const generated = props.record.images.generated
  const pages = props.record.outline.pages

  // 将扁平列表分组
  const groups: Record<number, string[]> = {}
  generated.forEach((filename: string) => {
    // 假设文件名格式为 "0.png" 或 "0_v1.png"
    const namePart = filename.split('.')[0]
    const pageIdxStr = namePart.split('_')[0]
    const pageIdx = parseInt(pageIdxStr)
    
    if (!isNaN(pageIdx)) {
      if (!groups[pageIdx]) groups[pageIdx] = []
      groups[pageIdx].push(filename)
    }
  })

  // 为每个大纲页面匹配图片版本
  return pages.map((_: any, idx: number) => {
    const versions = groups[idx] || []
    
    // 排序版本：0.png 在前，0_v1.png 随后等
    versions.sort()
    
    const allVersionUrls = versions.map(v => `/api/images/${taskId}/${v}`)
    
    return {
      index: idx,
      allVersions: allVersionUrls,
      currentUrl: allVersionUrls.length > 0 ? allVersionUrls[allVersionUrls.length - 1] : ''
    }
  })
})

// 选中的特定版本 (优先级高于最新的 currentUrl)
const selectedVersions = ref<Record<number, string>>({})

const getSelectedUrl = (pageIdx: number) => selectedVersions.value[pageIdx]

function selectVersion(pageIdx: number, url: string) {
  selectedVersions.value[pageIdx] = url
}

// 编辑器状态
const showEditor = ref(false)
const editingImageIndex = ref(0)
const editingImageUrl = ref('')
const editingImagePrompt = ref('')

function openEditor(index: number, url: string) {
  editingImageIndex.value = index
  editingImageUrl.value = url
  // 获取该页面的原始提示词
  if (props.record && props.record.outline.pages[index]) {
    editingImagePrompt.value = props.record.outline.pages[index].content
  }
  showEditor.value = true
}

const viewImage = (url: string) => {
  const baseUrl = url.split('?')[0]
  window.open(baseUrl + '?thumbnail=false', '_blank')
}

function handleEditSuccess(result: any) {
  if (result.success && result.image_url) {
    emit('editSuccess', result)
  }
}

// 下载处理 (优先下载选中的版本)
function handleDownloadAll() {
  emit('downloadAll')
}


const isGeneratingContent = ref(false)

async function handleGenerateContent() {
  if (!props.record || isGeneratingContent.value) return
  
  isGeneratingContent.value = true
  try {
    const res = await apiGenerateContent(props.record.title, props.record.outline.raw)
    if (res.success && res.titles && res.copywriting && res.tags) {
      // 1. 更新后端
      await updateHistory(props.record.id, {
        content: {
          titles: res.titles,
          copywriting: res.copywriting,
          tags: res.tags
        }
      })
      
      // 2. 更新本地显示 (注意：props 是只读的，所以我们只能修改 record 内部)
      // 在 Vue3 中，如果 props.record 是从父组件传来的 reactive 对象，这样修改可能生效，
      // 但更安全的方式是触发 refresh 让父组件重新加载。
      if (props.record.content) {
        props.record.content.titles = res.titles
        props.record.content.copywriting = res.copywriting
        props.record.content.tags = res.tags
      } else {
        props.record.content = {
          titles: res.titles,
          copywriting: res.copywriting,
          tags: res.tags
        }
      }
      
      alert('内容生成成功！')
      emit('refresh')
    } else {
      alert('生成内容失败: ' + (res.error || '未知错误'))
    }
  } catch (e: any) {
    alert('请求失败: ' + (e.message || String(e)))
  } finally {
    isGeneratingContent.value = false
  }
}


function handleDownload(pageIdx: number) {
  if (!props.record) return
  
  const selectedUrl = getSelectedUrl(pageIdx)
  let filename = ''
  
  if (selectedUrl) {
    // 从 URL 提取文件名 (例如 /api/images/task_id/0_v1.png -> 0_v1.png)
    filename = selectedUrl.split('/').pop()?.split('?')[0] || ''
  } else {
    const page = groupedImages.value[pageIdx]
    if (page && page.currentUrl) {
      filename = page.currentUrl.split('/').pop()?.split('?')[0] || ''
    }
  }
  
  if (filename) {
    emit('download', filename, pageIdx)
  }
}
</script>

<style scoped>
/* 全屏模态框遮罩 */
.modal-fullscreen {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

/* 模态框主体 */
.modal-body {
  background: var(--bg-body, #f8f9fa);
  width: 100%;
  max-width: 1200px;
  height: 95vh;
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

/* 头部区域 */
.modal-header {
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.return-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  font-size: 15px;
  color: var(--text-main);
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background 0.2s;
}

.return-btn:hover {
  background: var(--bg-body);
}

.header-divider {
  width: 1px;
  height: 24px;
  background: var(--border-color);
}

.title-container {
  flex: 1;
  min-width: 0;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: text;
}

.title-input {
  width: 100%;
  font-size: 18px;
  font-weight: 600;
  padding: 4px 8px;
  border: 1px solid var(--primary);
  border-radius: 4px;
  outline: none;
}

.close-icon {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: var(--text-sub);
  padding: 0 8px;
  line-height: 1;
}

/* 滚动区域 */
.modal-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding: 32px 24px;
  background: var(--bg-body);
}

.content-container {
  max-width: 1000px;
  margin: 0 auto;
}

/* 图片网格 */
.modal-gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 24px;
  margin-bottom: 48px;
}

.modal-img-card {
  background: white;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s, box-shadow 0.2s;
}

.modal-img-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.modal-img-preview {
  position: relative;
  aspect-ratio: 3/4;
  overflow: hidden;
  cursor: pointer;
}

.modal-img-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.modal-img-preview:hover img {
  transform: scale(1.05);
}

.hover-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  opacity: 0;
  transition: opacity 0.2s;
}

.modal-img-preview:hover .hover-overlay {
  opacity: 1;
}

.version-selector {
  position: absolute;
  bottom: 12px;
  left: 12px;
  display: flex;
  gap: 6px;
  background: rgba(0, 0, 0, 0.4);
  padding: 4px 8px;
  border-radius: 12px;
  backdrop-filter: blur(4px);
}

.version-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  padding: 0;
  border: none;
  cursor: pointer;
}

.version-dot.active {
  background: white;
}

.img-card-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-label {
  font-size: 13px;
  color: var(--text-sub);
  font-weight: 500;
}

.card-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.action-icon-btn {
  background: none;
  border: none;
  color: var(--text-sub);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.action-icon-btn:hover {
  color: var(--primary);
  background: var(--primary-light);
}

.action-text-btn {
  background: none;
  border: none;
  color: var(--primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

/* 文案包装 */
.content-display-wrapper {
  background: white;
  border-radius: var(--radius-xl);
  padding: 32px;
  box-shadow: var(--shadow-sm);
}

.placeholder {
  width: 100%;
  aspect-ratio: 3/4;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}

@media (max-width: 768px) {
  .modal-gallery-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 16px;
  }
}
</style>
