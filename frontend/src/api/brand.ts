/**
 * 品牌风格 API
 *
 * 提供品牌管理、Logo处理、内容管理和风格DNA相关的API调用
 */

import axios from 'axios'

const API_BASE_URL = '/api'

// ==================== 类型定义 ====================

export interface Brand {
  id: string
  name: string
  created_at: string
  updated_at: string
  has_logo?: boolean
  has_style_dna?: boolean
  content_count?: number
  competitor_count?: number
}

export interface BrandDetail {
  id: string
  name: string
  created_at: string
  updated_at: string
  logo: {
    id?: string
    file_path: string | null
    colors: string[]
    description: string | null
    created_at?: string
  }
  logos: Array<{
    id: string
    file_path: string
    colors: string[]
    description: string | null
    created_at: string
  }>
  style_dna: {
    writing_style: WritingStyle | null
    visual_style: VisualStyle | null
    style_prompt: string | null
  }
  company_contents: ContentItem[]
  competitor_contents: ContentItem[]
}

export interface WritingStyle {
  tone?: string
  vocabulary?: string[]
  keywords?: string[]
  emoji_style?: string
  sentence_style?: string
  summary?: string
  parse_failed?: boolean
}

export interface VisualStyle {
  color_scheme?: string
  layout_style?: string
  font_style?: string
  decoration?: string
  image_style?: string
  summary?: string
  parse_failed?: boolean
  no_images?: boolean
}

export interface ContentItem {
  id: string
  type: 'link' | 'manual'
  source_url: string | null
  title: string
  text: string
  images: string[]
  created_at: string
}

export interface ParsedContent {
  title: string
  text: string
  images: string[]
  source_url: string
}

// ==================== 品牌管理 ====================

/**
 * 获取品牌列表
 */
export async function getBrands(): Promise<{
  success: boolean
  brands: Brand[]
  active_brand_id: string | null
  error?: string
}> {
  try {
    const response = await axios.get(`${API_BASE_URL}/brands`, { timeout: 10000 })
    return response.data
  } catch (error: any) {
    return handleError(error, '获取品牌列表失败')
  }
}

/**
 * 创建品牌
 */
export async function createBrand(name: string): Promise<{
  success: boolean
  brand_id?: string
  brand?: BrandDetail
  error?: string
}> {
  try {
    const response = await axios.post(`${API_BASE_URL}/brands`, { name }, { timeout: 10000 })
    return response.data
  } catch (error: any) {
    return handleError(error, '创建品牌失败')
  }
}

/**
 * 获取品牌详情
 */
export async function getBrand(brandId: string): Promise<{
  success: boolean
  brand?: BrandDetail
  error?: string
}> {
  try {
    const response = await axios.get(`${API_BASE_URL}/brands/${brandId}`, { timeout: 10000 })
    return response.data
  } catch (error: any) {
    return handleError(error, '获取品牌详情失败')
  }
}

/**
 * 更新品牌
 */
export async function updateBrand(brandId: string, name: string): Promise<{
  success: boolean
  error?: string
}> {
  try {
    const response = await axios.put(`${API_BASE_URL}/brands/${brandId}`, { name }, { timeout: 10000 })
    return response.data
  } catch (error: any) {
    return handleError(error, '更新品牌失败')
  }
}

/**
 * 删除品牌
 */
export async function deleteBrand(brandId: string): Promise<{
  success: boolean
  error?: string
}> {
  try {
    const response = await axios.delete(`${API_BASE_URL}/brands/${brandId}`, { timeout: 10000 })
    return response.data
  } catch (error: any) {
    return handleError(error, '删除品牌失败')
  }
}

/**
 * 激活品牌
 */
export async function activateBrand(brandId: string): Promise<{
  success: boolean
  error?: string
}> {
  try {
    const response = await axios.post(`${API_BASE_URL}/brands/${brandId}/activate`, {}, { timeout: 10000 })
    return response.data
  } catch (error: any) {
    return handleError(error, '激活品牌失败')
  }
}

/**
 * 获取当前激活的品牌
 */
export async function getActiveBrand(): Promise<{
  success: boolean
  brand: BrandDetail | null
  error?: string
}> {
  try {
    const response = await axios.get(`${API_BASE_URL}/brands/active`, { timeout: 10000 })
    return response.data
  } catch (error: any) {
    return handleError(error, '获取激活品牌失败')
  }
}

// ==================== Logo 管理 ====================

/**
 * 上传Logo
 */
export async function uploadLogo(brandId: string, file: File): Promise<{
  success: boolean
  logo?: {
    id: string
    file_path: string
    colors: string[]
    description: string | null
    created_at: string
  }
  logo_path?: string
  colors?: string[]
  error?: string
}> {
  try {
    const formData = new FormData()
    formData.append('logo', file)

    const response = await axios.post(
      `${API_BASE_URL}/brands/${brandId}/logo`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000
      }
    )
    return response.data
  } catch (error: any) {
    return handleError(error, '上传Logo失败')
  }
}

/**
 * 删除Logo
 */
export async function deleteLogo(brandId: string): Promise<{
  success: boolean
  error?: string
}> {
  try {
    const response = await axios.delete(`${API_BASE_URL}/brands/${brandId}/logo`, { timeout: 10000 })
    return response.data
  } catch (error: any) {
    return handleError(error, '删除Logo失败')
  }
}

/**
 * 获取Logo URL
 */
export function getLogoUrl(brandId: string): string {
  return `${API_BASE_URL}/brands/${brandId}/logo`
}

/**
 * 更新Logo描述
 */
export async function updateLogoDescription(brandId: string, description: string): Promise<{
  success: boolean
  error?: string
}> {
  try {
    const response = await axios.put(
      `${API_BASE_URL}/brands/${brandId}/logo/description`,
      { description },
      { timeout: 10000 }
    )
    return response.data
  } catch (error: any) {
    return handleError(error, '更新Logo描述失败')
  }
}

// ==================== 内容管理 ====================

/**
 * 获取公司内容列表
 */
export async function getContents(brandId: string): Promise<{
  success: boolean
  contents: ContentItem[]
  error?: string
}> {
  try {
    const response = await axios.get(`${API_BASE_URL}/brands/${brandId}/contents`, { timeout: 10000 })
    return response.data
  } catch (error: any) {
    return handleError(error, '获取内容列表失败')
  }
}

/**
 * 添加公司内容
 */
export async function addContent(
  brandId: string,
  title: string,
  text: string,
  images?: File[],
  imageUrls?: string[],
  sourceUrl?: string,
  sourceType: 'link' | 'manual' = 'manual'
): Promise<{
  success: boolean
  content_id?: string
  content?: ContentItem
  error?: string
}> {
  try {
    const formData = new FormData()
    formData.append('title', title)
    formData.append('text', text)
    formData.append('source_type', sourceType)
    if (sourceUrl) {
      formData.append('source_url', sourceUrl)
    }
    if (imageUrls && imageUrls.length > 0) {
      imageUrls.forEach(url => {
        formData.append('image_urls', url)
      })
    }
    if (images) {
      images.forEach(file => {
        formData.append('images', file)
      })
    }

    const response = await axios.post(
      `${API_BASE_URL}/brands/${brandId}/contents`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000
      }
    )
    return response.data
  } catch (error: any) {
    return handleError(error, '添加内容失败')
  }
}

/**
 * 删除公司内容
 */
export async function deleteContent(brandId: string, contentId: string): Promise<{
  success: boolean
  error?: string
}> {
  try {
    const response = await axios.delete(
      `${API_BASE_URL}/brands/${brandId}/contents/${contentId}`,
      { timeout: 10000 }
    )
    return response.data
  } catch (error: any) {
    return handleError(error, '删除内容失败')
  }
}

/**
 * 解析小红书链接
 */
export async function parseXhsUrl(brandId: string, url: string): Promise<{
  success: boolean
  data?: ParsedContent
  partial?: boolean
  message?: string
  fallback?: string
  error?: string
}> {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/brands/${brandId}/contents/parse`,
      { url },
      { timeout: 30000 }
    )
    return response.data
  } catch (error: any) {
    return handleError(error, '解析链接失败')
  }
}

// ==================== 竞品内容管理 ====================

/**
 * 获取竞品内容列表
 */
export async function getCompetitors(brandId: string): Promise<{
  success: boolean
  contents: ContentItem[]
  error?: string
}> {
  try {
    const response = await axios.get(`${API_BASE_URL}/brands/${brandId}/competitors`, { timeout: 10000 })
    return response.data
  } catch (error: any) {
    return handleError(error, '获取竞品列表失败')
  }
}

/**
 * 添加竞品内容
 */
export async function addCompetitor(
  brandId: string,
  title: string,
  text: string,
  images?: File[],
  imageUrls?: string[],
  sourceUrl?: string,
  sourceType: 'link' | 'manual' = 'manual'
): Promise<{
  success: boolean
  content_id?: string
  content?: ContentItem
  error?: string
}> {
  try {
    const formData = new FormData()
    formData.append('title', title)
    formData.append('text', text)
    formData.append('source_type', sourceType)
    if (sourceUrl) {
      formData.append('source_url', sourceUrl)
    }
    if (imageUrls && imageUrls.length > 0) {
      imageUrls.forEach(url => {
        formData.append('image_urls', url)
      })
    }
    if (images) {
      images.forEach(file => {
        formData.append('images', file)
      })
    }

    const response = await axios.post(
      `${API_BASE_URL}/brands/${brandId}/competitors`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000
      }
    )
    return response.data
  } catch (error: any) {
    return handleError(error, '添加竞品失败')
  }
}

/**
 * 删除竞品内容
 */
export async function deleteCompetitor(brandId: string, contentId: string): Promise<{
  success: boolean
  error?: string
}> {
  try {
    const response = await axios.delete(
      `${API_BASE_URL}/brands/${brandId}/competitors/${contentId}`,
      { timeout: 10000 }
    )
    return response.data
  } catch (error: any) {
    return handleError(error, '删除竞品失败')
  }
}

// ==================== 风格DNA ====================

/**
 * 获取风格DNA
 */
export async function getStyleDna(brandId: string): Promise<{
  success: boolean
  style_dna?: {
    writing_style: WritingStyle | null
    visual_style: VisualStyle | null
    style_prompt: string | null
  }
  error?: string
}> {
  try {
    const response = await axios.get(`${API_BASE_URL}/brands/${brandId}/style-dna`, { timeout: 10000 })
    return response.data
  } catch (error: any) {
    return handleError(error, '获取风格DNA失败')
  }
}

/**
 * 提取风格DNA
 */
export async function extractStyle(brandId: string): Promise<{
  success: boolean
  style_dna?: {
    writing_style: WritingStyle | null
    visual_style: VisualStyle | null
    style_prompt: string | null
  }
  error?: string
  error_type?: string
}> {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/brands/${brandId}/extract-style`,
      {},
      { timeout: 120000 }  // 2分钟超时，因为需要AI分析
    )
    return response.data
  } catch (error: any) {
    return handleErrorWithType(error, '提取风格DNA失败')
  }
}

/**
 * 更新风格DNA
 */
export async function updateStyleDna(
  brandId: string,
  data: {
    writing_style?: WritingStyle
    visual_style?: VisualStyle
    style_prompt?: string
  }
): Promise<{
  success: boolean
  error?: string
}> {
  try {
    const response = await axios.put(
      `${API_BASE_URL}/brands/${brandId}/style-dna`,
      data,
      { timeout: 10000 }
    )
    return response.data
  } catch (error: any) {
    return handleError(error, '更新风格DNA失败')
  }
}

// ==================== 工具函数 ====================

function handleError(error: any, defaultMessage: string): any {
  if (axios.isAxiosError(error)) {
    if (error.code === 'ECONNABORTED') {
      return { success: false, error: '请求超时，请检查网络连接' }
    }
    if (!error.response) {
      return { success: false, error: '网络连接失败，请检查网络设置' }
    }
    const errorMessage = error.response?.data?.error || error.message || defaultMessage
    return { success: false, error: errorMessage }
  }
  return { success: false, error: defaultMessage }
}

function handleErrorWithType(error: any, defaultMessage: string): any {
  if (axios.isAxiosError(error)) {
    if (error.code === 'ECONNABORTED') {
      return { success: false, error: '请求超时，请检查网络连接', error_type: 'timeout' }
    }
    if (!error.response) {
      return { success: false, error: '网络连接失败，请检查网络设置', error_type: 'network_error' }
    }
    const errorData = error.response?.data
    const errorMessage = errorData?.error || error.message || defaultMessage
    const errorType = errorData?.error_type || 'unknown'
    return { success: false, error: errorMessage, error_type: errorType }
  }
  return { success: false, error: defaultMessage, error_type: 'unknown' }
}
