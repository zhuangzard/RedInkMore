/**
 * 品牌风格状态管理 Store
 *
 * 管理品牌列表、当前品牌、Logo、内容样本和风格DNA状态
 */
import { defineStore } from 'pinia'
import {
  getBrands,
  getBrand,
  createBrand,
  deleteBrand,
  activateBrand,
  uploadLogo,
  deleteLogo,
  getContents,
  addContent,
  deleteContent,
  getCompetitors,
  addCompetitor,
  deleteCompetitor,
  extractStyle,
  type Brand,
  type BrandDetail,
  type ContentItem
} from '../api/brand'

export interface BrandState {
  // 品牌列表
  brands: Brand[]
  // 当前激活的品牌ID
  activeBrandId: string | null
  // 当前选中的品牌详情
  currentBrand: BrandDetail | null
  // 加载状态
  loading: boolean
  // 风格提取状态
  extracting: boolean
  // 错误信息
  error: string | null
  // 错误类型（用于判断是否需要显示设置链接）
  errorType: string | null
}

export const useBrandStore = defineStore('brand', {
  state: (): BrandState => ({
    brands: [],
    activeBrandId: null,
    currentBrand: null,
    loading: false,
    extracting: false,
    error: null,
    errorType: null
  }),

  getters: {
    /**
     * 获取当前激活的品牌
     */
    activeBrand(): Brand | undefined {
      return this.brands.find(b => b.id === this.activeBrandId)
    },

    /**
     * 是否有品牌
     */
    hasBrands(): boolean {
      return this.brands.length > 0
    },

    /**
     * 当前品牌是否有Logo
     */
    hasLogo(): boolean {
      return this.currentBrand?.logo?.file_path != null
    },

    /**
     * 当前品牌是否有风格DNA
     */
    hasStyleDna(): boolean {
      return this.currentBrand?.style_dna?.style_prompt != null
    },

    /**
     * 当前品牌的公司内容数量
     */
    contentCount(): number {
      return this.currentBrand?.company_contents?.length || 0
    },

    /**
     * 当前品牌的竞品内容数量
     */
    competitorCount(): number {
      return this.currentBrand?.competitor_contents?.length || 0
    }
  },

  actions: {
    /**
     * 加载品牌列表
     */
    async loadBrands() {
      this.loading = true
      this.error = null

      try {
        const result = await getBrands()
        if (result.success) {
          this.brands = result.brands
          this.activeBrandId = result.active_brand_id
        } else {
          this.error = result.error || '加载品牌列表失败'
        }
      } catch (e: any) {
        this.error = e.message || '加载品牌列表失败'
      } finally {
        this.loading = false
      }
    },

    /**
     * 加载品牌详情
     */
    async loadBrandDetail(brandId: string) {
      this.loading = true
      this.error = null

      try {
        const result = await getBrand(brandId)
        if (result.success && result.brand) {
          this.currentBrand = result.brand
        } else {
          this.error = result.error || '加载品牌详情失败'
        }
      } catch (e: any) {
        this.error = e.message || '加载品牌详情失败'
      } finally {
        this.loading = false
      }
    },

    /**
     * 创建新品牌
     */
    async createNewBrand(name: string): Promise<string | null> {
      this.loading = true
      this.error = null

      try {
        const result = await createBrand(name)
        if (result.success && result.brand_id) {
          // 重新加载品牌列表
          await this.loadBrands()
          return result.brand_id
        } else {
          this.error = result.error || '创建品牌失败'
          return null
        }
      } catch (e: any) {
        this.error = e.message || '创建品牌失败'
        return null
      } finally {
        this.loading = false
      }
    },

    /**
     * 删除品牌
     */
    async removeBrand(brandId: string): Promise<boolean> {
      this.loading = true
      this.error = null

      try {
        const result = await deleteBrand(brandId)
        if (result.success) {
          // 重新加载品牌列表
          await this.loadBrands()
          // 如果删除的是当前品牌，清空当前品牌
          if (this.currentBrand?.id === brandId) {
            this.currentBrand = null
          }
          return true
        } else {
          this.error = result.error || '删除品牌失败'
          return false
        }
      } catch (e: any) {
        this.error = e.message || '删除品牌失败'
        return false
      } finally {
        this.loading = false
      }
    },

    /**
     * 激活品牌
     */
    async setActiveBrand(brandId: string): Promise<boolean> {
      this.error = null

      try {
        const result = await activateBrand(brandId)
        if (result.success) {
          this.activeBrandId = brandId
          return true
        } else {
          this.error = result.error || '激活品牌失败'
          return false
        }
      } catch (e: any) {
        this.error = e.message || '激活品牌失败'
        return false
      }
    },

    /**
     * 上传Logo
     */
    async uploadBrandLogo(file: File): Promise<boolean> {
      if (!this.currentBrand) {
        this.error = '请先选择品牌'
        return false
      }

      this.loading = true
      this.error = null

      try {
        const result = await uploadLogo(this.currentBrand.id, file)
        if (result.success) {
          // 更新当前品牌的Logo信息
          if (this.currentBrand) {
            // 兼容单个Logo字段
            this.currentBrand.logo.file_path = result.logo_path || result.logo?.file_path || null
            this.currentBrand.logo.colors = result.colors || result.logo?.colors || []

            // 添加到logos列表
            if (result.logo) {
              if (!this.currentBrand.logos) {
                this.currentBrand.logos = []
              }
              this.currentBrand.logos.push(result.logo)
            }
          }
          return true
        } else {
          this.error = result.error || '上传Logo失败'
          return false
        }
      } catch (e: any) {
        this.error = e.message || '上传Logo失败'
        return false
      } finally {
        this.loading = false
      }
    },

    /**
     * 删除Logo
     */
    async removeLogo(): Promise<boolean> {
      if (!this.currentBrand) {
        this.error = '请先选择品牌'
        return false
      }

      this.loading = true
      this.error = null

      try {
        const result = await deleteLogo(this.currentBrand.id)
        if (result.success) {
          // 清空Logo信息
          if (this.currentBrand) {
            this.currentBrand.logo.file_path = null
            this.currentBrand.logo.colors = []
            this.currentBrand.logo.description = null
          }
          return true
        } else {
          this.error = result.error || '删除Logo失败'
          return false
        }
      } catch (e: any) {
        this.error = e.message || '删除Logo失败'
        return false
      } finally {
        this.loading = false
      }
    },

    /**
     * 添加公司内容
     */
    async addCompanyContent(
      title: string,
      text: string,
      images?: File[],
      imageUrls?: string[],
      sourceUrl?: string,
      sourceType: 'link' | 'manual' = 'manual'
    ): Promise<boolean> {
      if (!this.currentBrand) {
        this.error = '请先选择品牌'
        return false
      }

      this.loading = true
      this.error = null

      try {
        const result = await addContent(
          this.currentBrand.id,
          title,
          text,
          images,
          imageUrls,
          sourceUrl,
          sourceType
        )
        if (result.success && result.content) {
          // 添加到列表
          if (this.currentBrand) {
            this.currentBrand.company_contents.push(result.content)
          }
          return true
        } else {
          this.error = result.error || '添加内容失败'
          return false
        }
      } catch (e: any) {
        this.error = e.message || '添加内容失败'
        return false
      } finally {
        this.loading = false
      }
    },

    /**
     * 删除公司内容
     */
    async removeCompanyContent(contentId: string): Promise<boolean> {
      if (!this.currentBrand) {
        this.error = '请先选择品牌'
        return false
      }

      this.loading = true
      this.error = null

      try {
        const result = await deleteContent(this.currentBrand.id, contentId)
        if (result.success) {
          // 从列表中移除
          if (this.currentBrand) {
            this.currentBrand.company_contents = this.currentBrand.company_contents.filter(
              c => c.id !== contentId
            )
          }
          return true
        } else {
          this.error = result.error || '删除内容失败'
          return false
        }
      } catch (e: any) {
        this.error = e.message || '删除内容失败'
        return false
      } finally {
        this.loading = false
      }
    },

    /**
     * 添加竞品内容
     */
    async addCompetitorContent(
      title: string,
      text: string,
      images?: File[],
      imageUrls?: string[],
      sourceUrl?: string,
      sourceType: 'link' | 'manual' = 'manual'
    ): Promise<boolean> {
      if (!this.currentBrand) {
        this.error = '请先选择品牌'
        return false
      }

      this.loading = true
      this.error = null

      try {
        const result = await addCompetitor(
          this.currentBrand.id,
          title,
          text,
          images,
          imageUrls,
          sourceUrl,
          sourceType
        )
        if (result.success && result.content) {
          // 添加到列表
          if (this.currentBrand) {
            this.currentBrand.competitor_contents.push(result.content)
          }
          return true
        } else {
          this.error = result.error || '添加竞品失败'
          return false
        }
      } catch (e: any) {
        this.error = e.message || '添加竞品失败'
        return false
      } finally {
        this.loading = false
      }
    },

    /**
     * 删除竞品内容
     */
    async removeCompetitorContent(contentId: string): Promise<boolean> {
      if (!this.currentBrand) {
        this.error = '请先选择品牌'
        return false
      }

      this.loading = true
      this.error = null

      try {
        const result = await deleteCompetitor(this.currentBrand.id, contentId)
        if (result.success) {
          // 从列表中移除
          if (this.currentBrand) {
            this.currentBrand.competitor_contents = this.currentBrand.competitor_contents.filter(
              c => c.id !== contentId
            )
          }
          return true
        } else {
          this.error = result.error || '删除竞品失败'
          return false
        }
      } catch (e: any) {
        this.error = e.message || '删除竞品失败'
        return false
      } finally {
        this.loading = false
      }
    },

    /**
     * 提取风格DNA
     */
    async extractStyleDna(): Promise<boolean> {
      if (!this.currentBrand) {
        this.error = '请先选择品牌'
        this.errorType = null
        return false
      }

      this.extracting = true
      this.error = null
      this.errorType = null

      try {
        const result = await extractStyle(this.currentBrand.id)
        if (result.success && result.style_dna) {
          // 更新风格DNA
          if (this.currentBrand) {
            this.currentBrand.style_dna = result.style_dna
          }
          return true
        } else {
          this.error = result.error || '提取风格DNA失败'
          this.errorType = result.error_type || null
          return false
        }
      } catch (e: any) {
        this.error = e.message || '提取风格DNA失败'
        this.errorType = null
        return false
      } finally {
        this.extracting = false
      }
    },

    /**
     * 清除错误
     */
    clearError() {
      this.error = null
      this.errorType = null
    },

    /**
     * 重置状态
     */
    reset() {
      this.brands = []
      this.activeBrandId = null
      this.currentBrand = null
      this.loading = false
      this.extracting = false
      this.error = null
      this.errorType = null
    }
  }
})
