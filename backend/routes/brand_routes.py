"""
品牌风格 API 路由

提供品牌管理、Logo处理、内容管理和风格DNA相关的API端点。
"""

import os
import base64
from flask import Blueprint, request, jsonify, send_file
from backend.services.brand import get_brand_service


def create_brand_blueprint():
    """创建品牌API蓝图"""
    bp = Blueprint('brand', __name__)

    # ==================== 品牌管理 ====================

    @bp.route('/brands', methods=['GET'])
    def list_brands():
        """获取品牌列表"""
        try:
            service = get_brand_service()
            brands = service.list_brands()
            active_brand = service.get_active_brand()

            return jsonify({
                "success": True,
                "brands": brands,
                "active_brand_id": active_brand.get("id") if active_brand else None
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands', methods=['POST'])
    def create_brand():
        """创建品牌"""
        try:
            data = request.get_json()
            name = data.get('name')

            if not name:
                return jsonify({"success": False, "error": "品牌名称不能为空"}), 400

            service = get_brand_service()
            result = service.create_brand(name)

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands/<brand_id>', methods=['GET'])
    def get_brand(brand_id):
        """获取品牌详情"""
        try:
            service = get_brand_service()
            brand = service.get_brand(brand_id)

            if brand is None:
                return jsonify({"success": False, "error": "品牌不存在"}), 404

            return jsonify({
                "success": True,
                "brand": brand
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands/<brand_id>', methods=['PUT'])
    def update_brand(brand_id):
        """更新品牌"""
        try:
            data = request.get_json()
            name = data.get('name')

            service = get_brand_service()
            result = service.update_brand(brand_id, name=name)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands/<brand_id>', methods=['DELETE'])
    def delete_brand(brand_id):
        """删除品牌"""
        try:
            service = get_brand_service()
            result = service.delete_brand(brand_id)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands/<brand_id>/activate', methods=['POST'])
    def activate_brand(brand_id):
        """激活品牌"""
        try:
            service = get_brand_service()
            result = service.activate_brand(brand_id)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands/active', methods=['GET'])
    def get_active_brand():
        """获取当前激活的品牌"""
        try:
            service = get_brand_service()
            brand = service.get_active_brand()

            return jsonify({
                "success": True,
                "brand": brand
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ==================== Logo 管理 ====================

    @bp.route('/brands/<brand_id>/logo', methods=['POST'])
    def upload_logo(brand_id):
        """上传Logo"""
        try:
            # 支持两种上传方式：multipart/form-data 或 JSON (base64)
            if 'logo' in request.files:
                # 文件上传方式
                file = request.files['logo']
                if file.filename == '':
                    return jsonify({"success": False, "error": "未选择文件"}), 400

                image_data = file.read()
                filename = file.filename
            else:
                # JSON base64方式
                data = request.get_json()
                if not data or 'logo' not in data:
                    return jsonify({"success": False, "error": "未提供Logo数据"}), 400

                logo_data = data['logo']
                # 处理data URL格式
                if logo_data.startswith('data:'):
                    # data:image/png;base64,xxxxx
                    header, base64_data = logo_data.split(',', 1)
                    image_data = base64.b64decode(base64_data)
                else:
                    image_data = base64.b64decode(logo_data)

                filename = data.get('filename', 'logo.png')

            service = get_brand_service()
            result = service.upload_logo(brand_id, image_data, filename)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands/<brand_id>/logo', methods=['DELETE'])
    def delete_logo(brand_id):
        """删除Logo"""
        try:
            service = get_brand_service()
            result = service.delete_logo(brand_id)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands/<brand_id>/logo', methods=['GET'])
    def get_logo(brand_id):
        """获取Logo图片"""
        try:
            service = get_brand_service()
            logo_path = service.get_logo_path(brand_id)

            if logo_path is None or not os.path.exists(logo_path):
                return jsonify({"success": False, "error": "Logo不存在"}), 404

            return send_file(logo_path)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands/<brand_id>/logo/description', methods=['PUT'])
    def update_logo_description(brand_id):
        """更新Logo描述"""
        try:
            data = request.get_json()
            description = data.get('description')

            if description is None:
                return jsonify({"success": False, "error": "描述不能为空"}), 400

            service = get_brand_service()
            result = service.update_logo_description(brand_id, description)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ==================== 内容管理 ====================

    @bp.route('/brands/<brand_id>/contents', methods=['GET'])
    def get_contents(brand_id):
        """获取公司内容列表"""
        try:
            service = get_brand_service()
            contents = service.get_contents(brand_id, "company")

            return jsonify({
                "success": True,
                "contents": contents
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands/<brand_id>/contents', methods=['POST'])
    def add_content(brand_id):
        """添加公司内容"""
        try:
            # 支持multipart/form-data或JSON
            if request.content_type and 'multipart/form-data' in request.content_type:
                title = request.form.get('title', '')
                text = request.form.get('text', '')
                source_url = request.form.get('source_url')
                source_type = request.form.get('source_type', 'manual')

                # 处理图片
                images = []
                if 'images' in request.files:
                    for file in request.files.getlist('images'):
                        images.append(file.read())
            else:
                data = request.get_json()
                title = data.get('title', '')
                text = data.get('text', '')
                source_url = data.get('source_url')
                source_type = data.get('source_type', 'manual')

                # 处理base64图片
                images = []
                for img_data in data.get('images', []):
                    if img_data.startswith('data:'):
                        _, base64_data = img_data.split(',', 1)
                        images.append(base64.b64decode(base64_data))
                    else:
                        images.append(base64.b64decode(img_data))

            service = get_brand_service()
            result = service.add_content(
                brand_id,
                "company",
                title,
                text,
                images=images if images else None,
                source_url=source_url,
                source_type=source_type
            )

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands/<brand_id>/contents/<content_id>', methods=['DELETE'])
    def delete_content(brand_id, content_id):
        """删除公司内容"""
        try:
            service = get_brand_service()
            result = service.delete_content(brand_id, "company", content_id)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ==================== 竞品内容管理 ====================

    @bp.route('/brands/<brand_id>/competitors', methods=['GET'])
    def get_competitors(brand_id):
        """获取竞品内容列表"""
        try:
            service = get_brand_service()
            contents = service.get_contents(brand_id, "competitor")

            return jsonify({
                "success": True,
                "contents": contents
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands/<brand_id>/competitors', methods=['POST'])
    def add_competitor(brand_id):
        """添加竞品内容"""
        try:
            # 支持multipart/form-data或JSON
            if request.content_type and 'multipart/form-data' in request.content_type:
                title = request.form.get('title', '')
                text = request.form.get('text', '')
                source_url = request.form.get('source_url')
                source_type = request.form.get('source_type', 'manual')

                images = []
                if 'images' in request.files:
                    for file in request.files.getlist('images'):
                        images.append(file.read())
            else:
                data = request.get_json()
                title = data.get('title', '')
                text = data.get('text', '')
                source_url = data.get('source_url')
                source_type = data.get('source_type', 'manual')

                images = []
                for img_data in data.get('images', []):
                    if img_data.startswith('data:'):
                        _, base64_data = img_data.split(',', 1)
                        images.append(base64.b64decode(base64_data))
                    else:
                        images.append(base64.b64decode(img_data))

            service = get_brand_service()
            result = service.add_content(
                brand_id,
                "competitor",
                title,
                text,
                images=images if images else None,
                source_url=source_url,
                source_type=source_type
            )

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands/<brand_id>/competitors/<content_id>', methods=['DELETE'])
    def delete_competitor(brand_id, content_id):
        """删除竞品内容"""
        try:
            service = get_brand_service()
            result = service.delete_content(brand_id, "competitor", content_id)

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ==================== 内容解析 ====================

    @bp.route('/brands/<brand_id>/contents/parse', methods=['POST'])
    def parse_content(brand_id):
        """
        解析小红书链接

        尝试从链接中提取内容，如果失败则返回错误提示用户手动输入
        """
        try:
            data = request.get_json()
            url = data.get('url')

            if not url:
                return jsonify({"success": False, "error": "URL不能为空"}), 400

            # 导入内容解析服务
            from backend.services.content_parser import get_content_parser_service

            parser = get_content_parser_service()
            result = parser.parse_xiaohongshu_url(url)

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ==================== 风格DNA ====================

    @bp.route('/brands/<brand_id>/style-dna', methods=['GET'])
    def get_style_dna(brand_id):
        """获取风格DNA"""
        try:
            service = get_brand_service()
            style_dna = service.get_style_dna(brand_id)

            if style_dna is None:
                return jsonify({"success": False, "error": "品牌不存在"}), 404

            return jsonify({
                "success": True,
                "style_dna": style_dna
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands/<brand_id>/style-dna', methods=['PUT'])
    def update_style_dna(brand_id):
        """更新风格DNA"""
        try:
            data = request.get_json()

            service = get_brand_service()
            result = service.update_style_dna(
                brand_id,
                writing_style=data.get('writing_style'),
                visual_style=data.get('visual_style'),
                style_prompt=data.get('style_prompt')
            )

            if not result.get("success"):
                return jsonify(result), 404

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route('/brands/<brand_id>/extract-style', methods=['POST'])
    def extract_style(brand_id):
        """
        提取风格DNA

        分析品牌的内容样本，生成文风和视觉风格分析
        """
        try:
            # 导入风格提取服务
            from backend.services.style_extractor import get_style_extractor_service

            extractor = get_style_extractor_service()
            result = extractor.extract_style(brand_id)

            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    return bp
