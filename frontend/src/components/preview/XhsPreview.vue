<template>
  <div v-if="show" class="xhs-preview-overlay" @click="$emit('close')">
    <div class="xhs-preview-container" @click.stop>
      <!-- iPhone Mockup -->
      <div class="iphone-x">
        <div class="side-button"></div>
        <div class="volume-buttons"></div>
        <div class="screen">
          <!-- Status Bar -->
          <div class="status-bar" :class="{ 'dark-content': viewMode === 'discovery' }">
            <span class="time">{{ currentTime }}</span>
            <div class="notch"></div>
            <div class="icons">
              <span class="signal">📶</span>
              <span class="wifi">📶</span>
              <span class="battery">🔋</span>
            </div>
          </div>

          <!-- Content Switching -->
          <div class="app-content">
            <!-- Discovery View (Discovery) -->
            <div v-if="viewMode === 'discovery'" class="discovery-view">
              <div class="xhs-header">
                <div class="tabs">
                  <span>关注</span>
                  <span class="active">发现</span>
                  <span>附近</span>
                </div>
                <div class="search-icon">🔍</div>
              </div>
              <div class="feed-grid">
                <div v-for="(img, idx) in allImages" :key="idx" class="feed-card">
                  <div class="card-img-wrapper">
                    <img :src="img" />
                  </div>
                  <div class="card-info">
                    <p class="card-title">{{ title || '笔记标题' }}</p>
                    <div class="card-user">
                      <div class="user-meta">
                        <div class="avatar-mini">红</div>
                        <span class="username-small">{{ username || '红薯小编' }}</span>
                      </div>
                      <div class="likes">❤️ 137</div>
                    </div>
                  </div>
                </div>
                <!-- Mock cards for realism -->
                <div class="feed-card mock">
                  <div class="card-img-wrapper" style="background: #eee; aspect-ratio: 1/1;"></div>
                  <div class="card-info">
                    <p class="card-title">更多精彩内容正在加载...</p>
                  </div>
                </div>
              </div>
              <!-- Tab Bar -->
              <div class="xhs-tab-bar">
                <div class="tab-item active">
                  <span class="tab-icon">🏠</span>
                  <span class="tab-text">首页</span>
                </div>
                <div class="tab-item">
                  <span class="tab-icon">🛍️</span>
                  <span class="tab-text">购物</span>
                </div>
                <div class="plus-btn">+</div>
                <div class="tab-item">
                  <span class="tab-icon">💬</span>
                  <span class="tab-text">消息</span>
                </div>
                <div class="tab-item">
                  <span class="tab-icon">👤</span>
                  <span class="tab-text">我</span>
                </div>
              </div>
            </div>

            <!-- Note View (Detail) -->
            <div v-else class="note-view">
              <div class="note-header">
                <div class="header-left">
                  <span class="back-icon" @click="$emit('close')">〈</span>
                  <div class="avatar-mini">红</div>
                  <span class="username">{{ username || '红薯小编' }}</span>
                </div>
                <button class="follow-btn">关注</button>
                <div class="header-right">
                  <span>🔗</span>
                  <span>...</span>
                </div>
              </div>
              
              <div class="note-image-container">
                <div 
                  class="image-slider" 
                  :style="{ transform: `translateX(-${currentIndex * 100}%)` }"
                >
                  <div v-for="(img, idx) in allImages" :key="idx" class="slider-item">
                    <img :src="img" />
                  </div>
                </div>
                <!-- Image index indicator -->
                <div v-if="allImages.length > 1" class="image-index">
                  {{ currentIndex + 1 }}/{{ allImages.length }}
                </div>
                <!-- Mini dots -->
                <div v-if="allImages.length > 1" class="slider-dots">
                  <span 
                    v-for="(_, idx) in allImages" 
                    :key="idx" 
                    :class="{ active: currentIndex === idx }"
                    @click="currentIndex = idx"
                  ></span>
                </div>
                
                <!-- Simple arrows for simulation -->
                <button v-if="currentIndex > 0" class="slide-nav prev" @click="currentIndex--">‹</button>
                <button v-if="currentIndex < allImages.length - 1" class="slide-nav next" @click="currentIndex++">›</button>
              </div>

              <div class="note-body">
                <div class="note-title">{{ title || '笔记标题' }}</div>
                <div class="note-desc">{{ copywriting || firstPageContent }}</div>
                <div class="note-tags">
                  <span v-for="(tag, tIdx) in (tags || ['小红书', '红墨AI', '智能排版'])" :key="tIdx">
                    #{{ tag }} 
                  </span>
                </div>
                <div class="note-time">昨天 13:20</div>
                <div class="divider"></div>
                <div class="comments-preview">
                  <p class="section-title">共 12 条评论</p>
                  <div class="comment-item">
                    <div class="avatar-placeholder"></div>
                    <div class="comment-content">
                      <p class="name">路人甲</p>
                      <p class="text">这也太好看了吧！求同款风格！</p>
                    </div>
                  </div>
                </div>
              </div>

              <div class="note-footer">
                <div class="footer-input">说点什么...</div>
                <div class="footer-icons">
                  <div class="icon-item">❤️<span>137</span></div>
                  <div class="icon-item">⭐<span>45</span></div>
                  <div class="icon-item">💬<span>12</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Control Panel -->
      <div class="preview-controls">
        <div class="segmented-control">
          <button 
            :class="{ active: viewMode === 'note' }" 
            @click="viewMode = 'note'"
          >笔记详情页</button>
          <button 
            :class="{ active: viewMode === 'discovery' }" 
            @click="viewMode = 'discovery'"
          >发现页流</button>
        </div>
        <button class="btn btn-close-preview" @click="$emit('close')">退出预览</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const props = defineProps({
  show: Boolean,
  allImages: {
    type: Array as () => string[],
    default: () => []
  },
  title: String,
  username: String,
  initialIndex: {
    type: Number,
    default: 0
  },
  firstPageContent: {
    type: String,
    default: '点击图片可以左右滑动查看。这是 AI 为您生成的专属小红书笔记样式，包含了品牌标识自动识别与智能排版。'
  },
  copywriting: String,
  tags: {
    type: Array as () => string[],
    default: () => []
  }
})

defineEmits(['close'])

const viewMode = ref('note')
const currentIndex = ref(props.initialIndex)
const currentTime = ref('13:20')

onMounted(() => {
  const now = new Date()
  currentTime.value = `${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`
})
</script>

<style scoped>
.xhs-preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.92);
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.xhs-preview-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 25px;
  animation: modalIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes modalIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}

/* iPhone X Mockup CSS */
.iphone-x {
  position: relative;
  width: 375px;
  height: 780px;
  background: #1a1a1a;
  border-radius: 54px;
  border: 12px solid #333;
  box-shadow: 0 0 80px rgba(0,0,0,0.6), inset 0 0 10px rgba(255,255,255,0.05);
  overflow: hidden;
  user-select: none;
}

/* iPhone detail highlights */
.iphone-x::after {
  content: '';
  position: absolute;
  top: 150px; left: -14px; width: 3px; height: 60px; background: #444; border-radius: 0 2px 2px 0;
}
.iphone-x::before {
  content: '';
  position: absolute;
  top: 220px; left: -14px; width: 3px; height: 100px; background: #444; border-radius: 0 2px 2px 0;
}

.screen {
  width: 100%;
  height: 100%;
  background: white;
  display: flex;
  flex-direction: column;
  position: relative;
}

.status-bar {
  height: 48px;
  padding: 0 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  position: absolute;
  top: 0; left: 0; right: 0;
  z-index: 100;
  color: white;
}

.status-bar.dark-content {
  color: #1a1a1a;
}

.notch {
  width: 140px;
  height: 30px;
  background: #1a1a1a;
  border-radius: 0 0 18px 18px;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.app-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Discovery View Styles */
.discovery-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fdfdfd;
}

.xhs-header {
  height: 88px;
  padding: 48px 15px 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 0.5px solid #f0f0f0;
}

.tabs {
  flex: 1;
  display: flex;
  justify-content: center;
  gap: 25px;
  font-size: 16px;
  color: #888;
}

.tabs span.active {
  color: #1a1a1a;
  font-weight: bold;
  position: relative;
}

.tabs span.active::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: -2px;
  right: -2px;
  height: 3px;
  background: #ff2442;
  border-radius: 2px;
}

.search-icon {
  font-size: 18px;
  color: #666;
}

.feed-grid {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  padding: 6px;
  background: #f4f5f7;
}

.feed-card {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  height: fit-content;
}

.card-img-wrapper {
  aspect-ratio: 3/4;
  overflow: hidden;
}

.card-img-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-info {
  padding: 8px;
}

.card-title {
  font-size: 13px;
  font-weight: 500;
  line-height: 1.4;
  color: #1a1a1a;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0 0 6px 0;
}

.card-user {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 10px;
  color: #999;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 4px;
}

.username-small {
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.xhs-tab-bar {
  height: 64px;
  border-top: 0.5px solid #eee;
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding-bottom: 20px;
  background: white;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  color: #999;
}

.tab-item.active { color: #1a1a1a; font-weight: bold; }

.tab-icon { font-size: 20px; }
.tab-text { font-size: 10px; }

/* Note View Styles */
.note-view {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.note-header {
  height: 92px;
  padding: 48px 15px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-bottom: 0.5px solid #f5f5f5;
}

.header-left { display: flex; align-items: center; gap: 12px; }
.back-icon { font-size: 20px; color: #333; cursor: pointer; }

.avatar-mini {
  width: 32px; height: 32px; border-radius: 50%;
  background: #ff2442; color: white;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: bold;
}

.follow-btn {
  padding: 4px 14px; border-radius: 20px;
  border: 1px solid #ff2442; background: transparent;
  color: #ff2442; font-size: 12px; font-weight: bold;
}

.header-right { display: flex; gap: 15px; font-size: 20px; color: #666; }

.note-image-container {
  width: 100%; aspect-ratio: 3/4;
  overflow: hidden; position: relative;
  background: #f0f0f0;
}

.image-slider {
  height: 100%; display: flex;
  transition: transform 0.4s cubic-bezier(0.23, 1, 0.32, 1);
}

.slider-item { min-width: 100%; height: 100%; }
.slider-item img { width: 100%; height: 100%; object-fit: contain; }

.image-index {
  position: absolute; top: 15px; right: 15px;
  background: rgba(0,0,0,0.4); color: white;
  padding: 2px 10px; border-radius: 12px; font-size: 11px;
}

.slider-dots {
  position: absolute; bottom: 15px; left: 0; right: 0;
  display: flex; justify-content: center; gap: 5px;
}

.slider-dots span {
  width: 4px; height: 4px; border-radius: 50%;
  background: rgba(255,255,255,0.4); cursor: pointer;
}

.slider-dots span.active { background: white; transform: scale(1.3); }

.slide-nav {
  position: absolute; top: 50%; transform: translateY(-50%);
  background: rgba(0,0,0,0.2); color: white; border: none;
  width: 30px; height: 40px; font-size: 24px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}

.slide-nav.prev { left: 0; border-radius: 0 4px 4px 0; }
.slide-nav.next { right: 0; border-radius: 4px 0 0 4px; }

.note-body { padding: 15px; flex: 1; overflow-y: auto; }
.note-title { font-size: 17px; font-weight: 600; margin-bottom: 12px; color: #1a1a1a; }
.note-desc { font-size: 15px; line-height: 1.6; color: #333; white-space: pre-wrap; }
.note-tags { margin-top: 15px; color: #3b66f5; font-size: 14px; }
.note-time { margin-top: 12px; font-size: 12px; color: #999; }
.divider { height: 0.5px; background: #eee; margin: 20px 0; }

.section-title { font-size: 14px; font-weight: 600; color: #666; margin-bottom: 15px; }
.comment-item { display: flex; gap: 10px; margin-bottom: 15px; }
.avatar-placeholder { width: 30px; height: 30px; border-radius: 50%; background: #eee; }
.comment-content .name { font-size: 12px; color: #999; margin-bottom: 2px; }
.comment-content .text { font-size: 14px; color: #444; }

.note-footer {
  height: 64px; border-top: 0.5px solid #eee;
  display: flex; align-items: center; padding: 0 15px 15px; gap: 12px;
  background: white;
}

.footer-input {
  flex: 1; height: 36px; background: #f5f5f5; border-radius: 18px;
  display: flex; align-items: center; padding-left: 15px;
  font-size: 13px; color: #999;
}

.footer-icons { display: flex; gap: 15px; }
.icon-item { display: flex; flex-direction: column; align-items: center; gap: 2px; font-size: 16px; color: #333; }
.icon-item span { font-size: 9px; font-weight: 500; }

/* Control Panel */
.preview-controls {
  display: flex; flex-direction: column; align-items: center; gap: 15px;
}

.segmented-control {
  background: rgba(255,255,255,0.08); padding: 4px; border-radius: 12px; display: flex;
}

.segmented-control button {
  padding: 8px 20px; border: none; background: transparent;
  color: #999; border-radius: 8px; cursor: pointer; transition: all 0.2s;
}

.segmented-control button.active {
  background: white; color: #1a1a1a; font-weight: 600;
}

.btn-close-preview {
  background: transparent; border: 1px solid rgba(255,255,255,0.3);
  color: white; padding: 8px 30px; border-radius: 20px; font-size: 14px;
}
.btn-close-preview:hover { background: rgba(255,255,255,0.1); }
</style>
