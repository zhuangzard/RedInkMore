"""
大纲生成相关 API 路由

包含功能：
- 生成大纲（支持图片上传）
"""

import time
import base64
import logging
from flask import Blueprint, request, jsonify
from backend.services.outline import get_outline_service
from .utils import log_request, log_error

logger = logging.getLogger(__name__)


def create_outline_blueprint():
    """创建大纲路由蓝图（工厂函数，支持多次调用）"""
    outline_bp = Blueprint('outline', __name__)

    @outline_bp.route('/outline', methods=['POST'])
    def generate_outline():
        """
        生成大纲（支持图片上传）

        请求格式：
        1. multipart/form-data（带图片文件）
           - topic: 主题文本
           - images: 图片文件列表

        2. application/json（无图片或 base64 图片）
           - topic: 主题文本
           - images: base64 编码的图片数组（可选）

        返回：
        - success: 是否成功
        - outline: 原始大纲文本
        - pages: 解析后的页面列表
        """
        start_time = time.time()

        try:
            # 解析请求数据
            topic, images = _parse_outline_request()

            log_request('/outline', {'topic': topic, 'images': images})

            # 验证必填参数
            if not topic:
                logger.warning("大纲生成请求缺少 topic 参数")
                return jsonify({
                    "success": False,
                    "error": "参数错误：topic 不能为空。\n请提供要生成图文的主题内容。"
                }), 400

            # 调用大纲生成服务
            logger.info(f"🔄 开始生成大纲，主题: {topic[:50]}...")
            outline_service = get_outline_service()
            
            # 检查 topic 是否为 URL (微信公众号链接)
            import re
            is_url = re.match(r'^https?://', topic.strip())
            
            if is_url:
                logger.info(f"检测到 URL 输入，尝试解析内容: {topic}")
                from backend.services.content_parser import get_content_parser_service
                
                parser = get_content_parser_service()
                parse_result = parser.parse_url(topic.strip())
                
                if parse_result['success']:
                    article_data = parse_result['data']
                    logger.info(f"URL 解析成功: {article_data.get('title')}")
                    
                    # 下载该文章的图片作为参考图
                    # 如果用户没有上传图片，才使用文章图片
                    if not images and article_data.get('images'):
                        import requests
                        from concurrent.futures import ThreadPoolExecutor
                        
                        logger.info(f"下载文章图片作为参考: {len(article_data['images'])} 张")
                        
                        def download_img(url):
                            try:
                                r = requests.get(url, timeout=10)
                                if r.status_code == 200:
                                    return r.content
                            except:
                                return None
                                
                        with ThreadPoolExecutor(max_workers=5) as executor:
                            downloaded = list(executor.map(download_img, article_data['images']))
                            images = [img for img in downloaded if img]
                            
                        logger.info(f"成功下载参考图片: {len(images)} 张")
                    
                    # 使用改写模式生成大纲
                    result = outline_service.generate_outline_from_article(article_data, images)
                else:
                    logger.warning(f"URL 解析失败: {parse_result.get('error')}, 降级为普通生成")
                    # 解析失败，把 URL 当作普通文本处理（或者提示用户）
                    result = outline_service.generate_outline(topic, images if images else None)
            else:
                # 普通文本/图片生成模式
                result = outline_service.generate_outline(topic, images if images else None)

            # 记录结果
            elapsed = time.time() - start_time
            if result["success"]:
                logger.info(f"✅ 大纲生成成功，耗时 {elapsed:.2f}s，共 {len(result.get('pages', []))} 页")
                return jsonify(result), 200
            else:
                logger.error(f"❌ 大纲生成失败: {result.get('error', '未知错误')}")
                return jsonify(result), 500

        except Exception as e:
            log_error('/outline', e)
            error_msg = str(e)
            return jsonify({
                "success": False,
                "error": f"大纲生成异常。\n错误详情: {error_msg}\n建议：检查后端日志获取更多信息"
            }), 500

    return outline_bp


def _parse_outline_request():
    """
    解析大纲生成请求

    支持两种格式：
    1. multipart/form-data - 用于文件上传
    2. application/json - 用于 base64 图片

    返回：
        tuple: (topic, images) - 主题和图片列表
    """
    # 检查是否是 multipart/form-data（带图片文件）
    if request.content_type and 'multipart/form-data' in request.content_type:
        topic = request.form.get('topic')
        images = []

        # 获取上传的图片文件
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename:
                    image_data = file.read()
                    images.append(image_data)

        return topic, images

    # JSON 请求（无图片或 base64 图片）
    data = request.get_json()
    topic = data.get('topic')
    images = []

    # 支持 base64 格式的图片
    images_base64 = data.get('images', [])
    if images_base64:
        for img_b64 in images_base64:
            # 移除可能的 data URL 前缀
            if ',' in img_b64:
                img_b64 = img_b64.split(',')[1]
            images.append(base64.b64decode(img_b64))

    return topic, images
