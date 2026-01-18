<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <h3>高级图片编辑 - Page {{ (index ?? 0) + 1 }}</h3>
        <button class="close-btn" @click="close">&times;</button>
      </div>

      <div class="modal-body">
        <!-- 画布工作区 (左侧) -->
        <div class="workspace-area">
          <div class="canvas-container">
            <canvas ref="imageCanvas" class="main-canvas"></canvas>
            <canvas
              ref="maskCanvas"
              class="mask-canvas"
              @mousedown="startDrawing"
              @mousemove="handleMouseMove"
              @mouseup="stopDrawing"
              @mouseleave="handleMouseLeave"
              @mouseenter="handleMouseEnter"
            ></canvas>
            
            <!-- 动态画笔光标 -->
            <div
              v-if="showBrushCursor"
              class="brush-cursor"
              :style="brushCursorStyle"
            ></div>
          </div>
          
          <div v-if="isLoading" class="loader-overlay">
            <div class="spinner"></div>
            <p>{{ loadingText }}</p>
          </div>
        </div>

        <!-- 侧边工具栏 (右侧) -->
        <div class="sidebar">
          <!-- 画笔设置 -->
          <div class="tool-group">
            <label>画笔粗细: {{ brushSize }}px</label>
            <div class="slider-row">
              <input type="range" v-model.number="brushSize" min="5" max="150" @change="updateBrushSize" />
              <button class="btn btn-outline btn-sm" @click="clearMask">重置涂抹</button>
            </div>
          </div>

          <!-- 修改要求 -->
          <div class="tool-group">
            <label>局部重绘：在图上涂抹，输入修改要求</label>
            <textarea
              v-model="editPrompt"
              placeholder="例如：换一个红色的气球..."
              rows="3"
            ></textarea>
            <button
              class="btn btn-primary"
              :disabled="isLoading || !editPrompt.trim()"
              @click="handleEdit"
            >
              {{ isLoading ? '正在重绘...' : '确认修改并重绘' }}
            </button>
          </div>

          <div class="divider"></div>

          <!-- 重绘全部 -->
          <div class="tool-group">
            <label>全图重绘：修改描述词生成新图</label>
            <textarea
              v-model="regeneratePrompt"
              placeholder="修改提示词以改变生成内容..."
              rows="3"
            ></textarea>
            
            <div class="ref-row">
              <span class="ref-label">风格参考图 (可选)</span>
              <div class="ref-upload-container">
                <div v-if="customRefImage" class="ref-preview">
                  <img :src="customRefImage" />
                  <button class="ref-remove" @click="customRefImage = null">×</button>
                </div>
                <label v-else class="ref-upload-btn">
                  <input type="file" accept="image/*" @change="handleRefUpload" hidden />
                  <span class="plus">+</span>
                  <span>上传</span>
                </label>
              </div>
            </div>

            <div class="options-grid">
              <div class="option-item">
                <label>质量</label>
                <select v-model="quality">
                  <option value="standard">标准</option>
                  <option value="hd">高清</option>
                </select>
              </div>
              <div class="option-item">
                <label>尺寸</label>
                <select v-model="size">
                  <option :value="originalSizeValue">原图</option>
                  <option value="1024x1024">1:1</option>
                  <option value="1024x1365">3:4</option>
                </select>
              </div>
            </div>

            <button class="btn btn-primary-outline" :disabled="isLoading" @click="handleRegenerate">
              🔄 {{ isLoading ? '重绘中...' : '一键重绘全部' }}
            </button>
          </div>

          <div class="divider"></div>

          <!-- 品牌 Logo -->
          <div class="tool-group">
            <label>品牌标识</label>
          <div class="logo-style-row">
            <span class="logo-style-label">Logo 样式</span>
            <select v-model="logoStyle">
              <option value="auto">自动</option>
              <option value="light">浅色 Logo</option>
              <option value="dark">深色 Logo</option>
            </select>
          </div>
            <button
              class="btn logo-btn"
              :class="{ active: isLogoApplied }"
              :disabled="isLoading"
              @click="handleToggleLogo"
            >
              {{ isLogoApplied ? '✅ 撤销 Logo' : '🏷️ 智能叠加 Logo' }}
            </button>
          </div>

          <!-- 文案编辑 -->
          <div class="tool-group">
            <label>编辑文案与标签</label>
            <div class="xhs-editor-box">
              <input v-model="xhsTitle" class="xhs-title-input" placeholder="贴子标题..." />
              <textarea v-model="xhsCopywriting" class="xhs-copy-textarea" placeholder="正文内容..." rows="4"></textarea>
              <div class="tags-row">
                <span v-for="(tag, i) in xhsTags" :key="i" class="tag-chip">
                  #{{ tag }}
                  <button @click="removeTag(i)">×</button>
                </span>
                <input v-model="newTag" class="tag-input" placeholder="+标签" @keyup.enter="addTag" />
              </div>
              <button class="btn btn-outline btn-block btn-sm" @click="handleRewrite" :disabled="isRewriting">
                ✍️ {{ isRewriting ? '正在润色...' : 'AI 润色文案' }}
              </button>
            </div>
          </div>

          <div class="sidebar-footer">
            <button
              v-if="!editPrompt.trim()"
              class="btn btn-primary save-btn"
              :disabled="isLoading"
              @click="handleSaveCanvas"
            >
              {{ isLoading ? '保存中...' : '确认修改并保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import { editImage, applyLogo, saveCanvas, regenerateImage, generateContent } from '../../api'

const props = defineProps({
  show: Boolean,
  imageUrl: String,
  taskId: String,
  index: Number,
  prompt: String,
  initialTitle: String,
  initialCopywriting: String,
  initialTags: { type: Array as () => string[], default: () => [] }
})

const emit = defineEmits(['close', 'success'])

// Canvas refs
const imageCanvas = ref<HTMLCanvasElement | null>(null)
const maskCanvas = ref<HTMLCanvasElement | null>(null)

// 状态
const isDrawing = ref(false)
const brushSize = ref(40)
const editPrompt = ref('')
const isLoading = ref(false)
const loadingText = ref('处理中...')
const quality = ref('standard')
const originalSizeLabel = ref('1024x1024')
const originalSizeValue = ref('1024x1024')
const size = ref('1024x1024')
const isLogoApplied = ref(false)
const preLogoImage = ref<string | null>(null)
const logoStyle = ref<'auto' | 'light' | 'dark'>('auto')
const regeneratePrompt = ref('')
const customRefImage = ref<string | null>(null)

// 文案
const xhsTitle = ref('')
const xhsCopywriting = ref('')
const xhsTags = ref<string[]>([])
const newTag = ref('')
const isRewriting = ref(false)

// 画笔光标
const showBrushCursor = ref(false)
const cursorX = ref(0)
const cursorY = ref(0)
const displayScale = ref(1)

let ctx: CanvasRenderingContext2D | null = null

const brushCursorStyle = computed(() => {
  const sz = brushSize.value * displayScale.value
  return {
    left: `${cursorX.value}px`,
    top: `${cursorY.value}px`,
    width: `${sz}px`,
    height: `${sz}px`
  }
})

function close() {
  emit('close')
}

function clearMask() {
  if (ctx && maskCanvas.value) {
    ctx.clearRect(0, 0, maskCanvas.value.width, maskCanvas.value.height)
  }
}

function addTag() {
  const t = newTag.value.trim().replace(/^#/, '')
  if (t && !xhsTags.value.includes(t)) xhsTags.value.push(t)
  newTag.value = ''
}

function removeTag(i: number) {
  xhsTags.value.splice(i, 1)
}

async function handleRewrite() {
  if (isRewriting.value) return
  isRewriting.value = true
  try {
    const res = await generateContent(xhsTitle.value || xhsCopywriting.value || '继续描述', xhsCopywriting.value)
    if (res.success && res.copywriting) {
      xhsCopywriting.value = res.copywriting
      if (res.titles?.length) xhsTitle.value = res.titles[0]
      if (res.tags) xhsTags.value = res.tags
    }
  } catch (e) {
    console.error('Rewrite failed:', e)
  } finally {
    isRewriting.value = false
  }
}

function handleRefUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => { customRefImage.value = ev.target?.result as string }
  reader.readAsDataURL(file)
}

function initCanvas() {
  if (!imageCanvas.value || !maskCanvas.value || !props.imageUrl) return

  const img = new Image()
  img.crossOrigin = 'anonymous'
  let src = props.imageUrl
  if (!src.includes('thumbnail=false')) {
    src += (src.includes('?') ? '&' : '?') + 'thumbnail=false'
  }
  img.src = src

  img.onload = () => {
    const canvas = imageCanvas.value!
    const mCanvas = maskCanvas.value!
    
    // 设置画布物理尺寸（原图大小）
    canvas.width = mCanvas.width = img.width
    canvas.height = mCanvas.height = img.height
    
    // 绘制图片
    const imgCtx = canvas.getContext('2d')
    imgCtx?.drawImage(img, 0, 0)
    
    // 初始化涂抹上下文
    ctx = mCanvas.getContext('2d')
    if (ctx) {
      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'
      ctx.strokeStyle = 'rgba(255, 36, 66, 0.4)'
      ctx.lineWidth = brushSize.value
    }

    // 记录原始尺寸
    originalSizeValue.value = `${img.width}x${img.height}`
    originalSizeLabel.value = `${img.width}x${img.height}`
    size.value = originalSizeValue.value
    
    // 触发尺寸探测
    nextTick(updateDisplayScale)
  }
}

function updateDisplayScale() {
  if (maskCanvas.value) {
    const rect = maskCanvas.value.getBoundingClientRect()
    displayScale.value = rect.width / maskCanvas.value.width
  }
}

function updateBrushSize() {
  if (ctx) ctx.lineWidth = brushSize.value
}

function handleMouseMove(e: MouseEvent) {
  if (!maskCanvas.value) return
  const rect = maskCanvas.value.getBoundingClientRect()
  cursorX.value = e.clientX - rect.left
  cursorY.value = e.clientY - rect.top
  if (isDrawing.value) draw(e)
}

function handleMouseEnter() { showBrushCursor.value = true }
function handleMouseLeave() { showBrushCursor.value = false; stopDrawing() }

function startDrawing(e: MouseEvent) {
  isDrawing.value = true
  draw(e)
}

function draw(e: MouseEvent) {
  if (!isDrawing.value || !ctx || !maskCanvas.value) return
  const rect = maskCanvas.value.getBoundingClientRect()
  const scaleX = maskCanvas.value.width / rect.width
  const scaleY = maskCanvas.value.height / rect.height
  const x = (e.clientX - rect.left) * scaleX
  const y = (e.clientY - rect.top) * scaleY
  ctx.lineTo(x, y)
  ctx.stroke()
  ctx.beginPath()
  ctx.moveTo(x, y)
}

function stopDrawing() {
  isDrawing.value = false
  if (ctx) ctx.beginPath()
}

async function handleEdit() {
  if (!maskCanvas.value || !imageCanvas.value || !props.taskId || props.index === undefined) return
  isLoading.value = true
  loadingText.value = '正在重绘...'
  try {
    const exportCanvas = document.createElement('canvas')
    exportCanvas.width = maskCanvas.value.width
    exportCanvas.height = maskCanvas.value.height
    const eCtx = exportCanvas.getContext('2d')!
    eCtx.fillStyle = 'black'
    eCtx.fillRect(0, 0, exportCanvas.width, exportCanvas.height)
    eCtx.globalCompositeOperation = 'destination-out'
    eCtx.drawImage(maskCanvas.value, 0, 0)
    const maskBase64 = exportCanvas.toDataURL('image/png')

    const result = await editImage({
      task_id: props.taskId,
      index: props.index,
      prompt: editPrompt.value,
      mask: maskBase64,
      size: size.value,
      quality: quality.value
    })
    emit('success', {
      ...result,
      index: props.index,
      content: { title: xhsTitle.value, copywriting: xhsCopywriting.value, tags: xhsTags.value }
    })
    close()
  } catch (e: any) {
    alert('编辑失败: ' + (e.message || String(e)))
  } finally {
    isLoading.value = false
  }
}

async function handleSaveCanvas() {
  if (isLoading.value || !props.taskId || props.index === undefined || !imageCanvas.value) return
  isLoading.value = true
  loadingText.value = '正在保存...'
  try {
    const imageBase64 = imageCanvas.value.toDataURL('image/png')
    const result = await saveCanvas({ image: imageBase64, task_id: props.taskId, index: props.index })
    emit('success', {
      ...result,
      index: props.index,
      content: { title: xhsTitle.value, copywriting: xhsCopywriting.value, tags: xhsTags.value }
    })
    close()
  } catch (e: any) {
    alert('保存出错: ' + (e.message || String(e)))
  } finally {
    isLoading.value = false
  }
}

async function handleRegenerate() {
  if (isLoading.value || !props.taskId || props.index === undefined) return
  isLoading.value = true
  loadingText.value = '正在重绘...'
  try {
    const result = await regenerateImage(props.taskId, {
      index: props.index,
      type: 'content' as any,
      content: regeneratePrompt.value
    }, true, { customReferenceImage: customRefImage.value || undefined })

    if (result.success && result.image_url) {
      updateCanvasFromUrl(result.image_url)
      isLogoApplied.value = false
      emit('success', {
        index: props.index,
        image_url: result.image_url,
        filename: result.image_url.split('/').pop()?.split('?')[0] || ''
      })
    } else {
      alert('重绘失败: ' + (result.error || '未知错误'))
    }
  } catch (e) {
    alert('重绘出错: ' + String(e))
  } finally {
    isLoading.value = false
  }
}

async function handleToggleLogo() {
  if (isLogoApplied.value) {
    if (preLogoImage.value) {
      updateCanvasFromDataUrl(preLogoImage.value)
      isLogoApplied.value = false
    }
  } else {
    if (!imageCanvas.value) return
    preLogoImage.value = imageCanvas.value.toDataURL('image/png')
    isLoading.value = true
    loadingText.value = '叠加Logo...'
    try {
      const result = await applyLogo(preLogoImage.value, logoStyle.value)
      if (result.success) {
        updateCanvasFromDataUrl(result.image)
        isLogoApplied.value = true
      } else {
        alert('叠加 Logo 失败: ' + result.error)
      }
    } catch (e) {
      alert('叠加 Logo 出错: ' + String(e))
    } finally {
      isLoading.value = false
    }
  }
}

function updateCanvasFromUrl(url: string) {
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    const canvas = imageCanvas.value
    if (!canvas) return
    const c = canvas.getContext('2d')
    if (c) {
      c.clearRect(0, 0, canvas.width, canvas.height)
      c.drawImage(img, 0, 0)
    }
  }
  img.src = url
}

function updateCanvasFromDataUrl(dataUrl: string) {
  const img = new Image()
  img.onload = () => {
    const canvas = imageCanvas.value
    if (!canvas) return
    const c = canvas.getContext('2d')
    if (c) {
      c.clearRect(0, 0, canvas.width, canvas.height)
      c.drawImage(img, 0, 0)
    }
  }
  img.src = dataUrl
}

watch(() => props.show, (val) => {
  if (val) {
    regeneratePrompt.value = props.prompt || ''
    customRefImage.value = null
    xhsTitle.value = props.initialTitle || ''
    xhsCopywriting.value = props.initialCopywriting || ''
    xhsTags.value = [...props.initialTags]
    logoStyle.value = 'auto'
    nextTick(initCanvas)
  }
})

watch(
  () => [props.imageUrl, props.index],
  ([newUrl], [oldUrl]) => {
    if (!props.show || !newUrl || newUrl === oldUrl) return
    // 切换页面时清理 Logo 状态，避免跨页误用
    isLogoApplied.value = false
    preLogoImage.value = null
    nextTick(initCanvas)
  }
)

watch(brushSize, (val) => {
  if (ctx) ctx.lineWidth = val
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  width: fit-content;
  max-width: 100vw;
  height: 92vh;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0,0,0,0.3);
}

.modal-header {
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #aaa;
  line-height: 1;
}
.close-btn:hover { color: #333; }

.modal-body {
  flex: 1;
  display: flex;
  flex-direction: row;
  overflow: hidden;
  background: #f8f9fa;
  padding: 0 !important;
  margin: 0 !important;
  justify-content: center;
  align-items: center;
}

/* 左侧工作区 */
.workspace-area {
  flex: 1;
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  overflow: auto;
  padding: 0;
  background: #fff;
  height: 100%;
}

.canvas-container {
  position: relative;
  background: transparent;
  box-shadow: none;
  width: 100%;
  height: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.main-canvas {
  display: block;
  width: 100%;
  height: auto;
  max-width: 100%;
  max-height: none;
  object-fit: contain;
}

.mask-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  cursor: none;
}

.brush-cursor {
  position: absolute;
  pointer-events: none;
  border: 2px solid #ff2442;
  border-radius: 50%;
  background: rgba(255,36,66,0.15);
  z-index: 100;
  pointer-events: none;
  transform: translate(-50%, -50%);
}

.loader-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255,255,255,0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #eee;
  border-top-color: #ff2442;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* 右侧侧边栏 */
.sidebar {
  width: 520px;
  min-width: 320px;
  max-width: 520px;
  flex-shrink: 0;
  background: #fff;
  border-left: 1px solid #eee;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0 !important;
  margin: 0 !important;
  box-sizing: border-box;
  height: 100%;
}

.tool-group {
  padding: 12px 12px !important;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-sizing: border-box;
}

.tool-group label {
  font-size: 13px;
  font-weight: 600;
  color: #444;
}

.slider-row {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
}

.slider-row input[type="range"] {
  flex: 1;
  accent-color: #ff2442;
}

.divider {
  height: 1px;
  background: #eee;
  margin: 0 !important;
}

.options-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-top: 5px;
}

.option-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

textarea, select, input.xhs-title-input {
  width: 100% !important;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

textarea:focus, select:focus, input:focus {
  outline: none;
  border-color: #ff2442;
}

.btn {
  width: 100% !important;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-sizing: border-box;
}

.btn-primary {
  background: #ff2442;
  color: #fff;
}
.btn-primary:hover { background: #e02039; }
.btn-primary:disabled { background: #ffc2ca; cursor: not-allowed; }

.btn-primary-outline {
  background: #fff;
  border: 1.5px solid #ff2442;
  color: #ff2442;
}
.btn-primary-outline:hover { background: #fff0f2; }

.btn-outline {
  border: 1px solid #ddd;
  background: #fff;
  color: #666;
}
.btn-outline:hover { border-color: #ff2442; color: #ff2442; }

.btn-block { width: 100%; }
.btn-sm { padding: 6px 12px; font-size: 12px; }

.logo-btn {
  background: #f8f9fa;
  border: 1px solid #eee;
  color: #555;
  width: 100%;
  font-weight: 600;
}
.logo-btn.active {
  background: #fff0f2;
  color: #ff2442;
  border-color: #ff2442;
}

.logo-style-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-style-label {
  font-size: 13px;
  color: #666;
  white-space: nowrap;
}

/* 文案编辑器插件化样式 */
.xhs-editor-box {
  background: #f8fbff;
  border: 1px solid #e1e8f5;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.xhs-title-input { font-weight: 600; background: #fff; }
.xhs-copy-textarea { font-size: 13px; line-height: 1.5; background: #fff; }

.tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-chip {
  background: #ebf0ff;
  color: #3b82f6;
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.tag-chip button {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
}

.tag-input {
  border: 1px dashed #ccc;
  background: transparent;
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 4px;
  width: 60px;
}

.sidebar-footer {
  margin-top: auto;
  padding: 20px;
  background: #fff;
  border-top: 1px solid #eee;
  position: sticky;
  bottom: 0;
}

.save-btn {
  width: 100%;
  padding: 14px;
  font-size: 16px;
}

/* 移动端适配 */
@media (max-width: 900px) {
  .modal-body {
    flex-direction: column;
  }
  .sidebar {
    width: 100%;
    min-width: 100%;
    border-left: none;
    border-top: 1px solid #ddd;
  }
}
</style>
