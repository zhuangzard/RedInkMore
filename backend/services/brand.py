"""
品牌风格服务

负责品牌配置的CRUD操作、Logo处理、颜色提取等功能。
"""

import os
import uuid
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import yaml
from PIL import Image
import io
import colorsys
from collections import Counter


class BrandService:
    """品牌风格服务类"""

    def __init__(self):
        """初始化品牌服务"""
        # 项目根目录
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        # 品牌配置文件路径
        self.config_file = os.path.join(self.root_dir, "brand_styles.yaml")

        # 品牌资源目录
        self.assets_dir = os.path.join(self.root_dir, "brand_assets")
        os.makedirs(self.assets_dir, exist_ok=True)

        # 初始化配置文件
        self._init_config()

    def _init_config(self) -> None:
        """初始化配置文件"""
        if not os.path.exists(self.config_file):
            default_config = {
                "active_brand": None,
                "brands": {}
            }
            self._save_config(default_config)

    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                # 确保必要的键存在
                if "active_brand" not in config:
                    config["active_brand"] = None
                if "brands" not in config:
                    config["brands"] = {}
                return config
        except Exception as e:
            print(f"加载品牌配置失败: {e}")
            return {"active_brand": None, "brands": {}}

    def _save_config(self, config: Dict) -> None:
        """保存配置文件"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def _get_brand_dir(self, brand_id: str) -> str:
        """获取品牌资源目录"""
        return os.path.join(self.assets_dir, brand_id)

    def _ensure_brand_dirs(self, brand_id: str) -> None:
        """确保品牌目录结构存在"""
        brand_dir = self._get_brand_dir(brand_id)
        os.makedirs(os.path.join(brand_dir, "contents"), exist_ok=True)
        os.makedirs(os.path.join(brand_dir, "competitors"), exist_ok=True)

    # ==================== 品牌 CRUD ====================

    def list_brands(self) -> List[Dict]:
        """获取所有品牌列表"""
        config = self._load_config()
        brands = []
        for brand_id, brand_data in config.get("brands", {}).items():
            brands.append({
                "id": brand_id,
                "name": brand_data.get("name", ""),
                "created_at": brand_data.get("created_at", ""),
                "updated_at": brand_data.get("updated_at", ""),
                "has_logo": brand_data.get("logo", {}).get("file_path") is not None,
                "has_style_dna": brand_data.get("style_dna", {}).get("style_prompt") is not None,
                "content_count": len(brand_data.get("company_contents", [])),
                "competitor_count": len(brand_data.get("competitor_contents", []))
            })
        # 按创建时间倒序
        brands.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return brands

    def create_brand(self, name: str) -> Dict:
        """创建新品牌"""
        config = self._load_config()

        # 生成唯一ID
        brand_id = f"brand_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        # 创建品牌数据
        brand_data = {
            "name": name,
            "created_at": now,
            "updated_at": now,
            "logo": {
                "file_path": None,
                "colors": [],
                "description": None
            },
            "style_dna": {
                "writing_style": None,
                "visual_style": None,
                "style_prompt": None
            },
            "company_contents": [],
            "competitor_contents": []
        }

        config["brands"][brand_id] = brand_data

        # 如果是第一个品牌，自动激活
        if config["active_brand"] is None:
            config["active_brand"] = brand_id

        self._save_config(config)

        # 创建目录结构
        self._ensure_brand_dirs(brand_id)

        return {
            "success": True,
            "brand_id": brand_id,
            "brand": {
                "id": brand_id,
                **brand_data
            }
        }

    def get_brand(self, brand_id: str) -> Optional[Dict]:
        """获取品牌详情"""
        config = self._load_config()
        brand_data = config.get("brands", {}).get(brand_id)

        if brand_data is None:
            return None

        return {
            "id": brand_id,
            **brand_data
        }

    def update_brand(self, brand_id: str, name: str = None) -> Dict:
        """更新品牌信息"""
        config = self._load_config()

        if brand_id not in config.get("brands", {}):
            return {"success": False, "error": "品牌不存在"}

        if name is not None:
            config["brands"][brand_id]["name"] = name

        config["brands"][brand_id]["updated_at"] = datetime.now().isoformat()
        self._save_config(config)

        return {"success": True}

    def delete_brand(self, brand_id: str) -> Dict:
        """删除品牌"""
        config = self._load_config()

        if brand_id not in config.get("brands", {}):
            return {"success": False, "error": "品牌不存在"}

        # 删除品牌数据
        del config["brands"][brand_id]

        # 如果删除的是激活品牌，清空激活状态
        if config["active_brand"] == brand_id:
            # 如果还有其他品牌，激活第一个
            remaining_brands = list(config["brands"].keys())
            config["active_brand"] = remaining_brands[0] if remaining_brands else None

        self._save_config(config)

        # 删除品牌资源目录
        brand_dir = self._get_brand_dir(brand_id)
        if os.path.exists(brand_dir):
            shutil.rmtree(brand_dir)

        return {"success": True}

    def activate_brand(self, brand_id: str) -> Dict:
        """激活品牌"""
        config = self._load_config()

        if brand_id not in config.get("brands", {}):
            return {"success": False, "error": "品牌不存在"}

        config["active_brand"] = brand_id
        self._save_config(config)

        return {"success": True}

    def get_active_brand(self) -> Optional[Dict]:
        """获取当前激活的品牌"""
        config = self._load_config()
        active_id = config.get("active_brand")

        if active_id is None:
            return None

        return self.get_brand(active_id)

    # ==================== Logo 处理 ====================

    def upload_logo(self, brand_id: str, image_data: bytes, filename: str = "logo.png") -> Dict:
        """
        上传Logo并提取颜色

        Args:
            brand_id: 品牌ID
            image_data: 图片二进制数据
            filename: 文件名

        Returns:
            上传结果，包含提取的颜色
        """
        config = self._load_config()

        if brand_id not in config.get("brands", {}):
            return {"success": False, "error": "品牌不存在"}

        # 确保目录存在
        self._ensure_brand_dirs(brand_id)
        brand_dir = self._get_brand_dir(brand_id)

        # 确定文件扩展名
        ext = os.path.splitext(filename)[1].lower() or ".png"
        logo_filename = f"logo{ext}"
        logo_path = os.path.join(brand_dir, logo_filename)

        # 保存Logo
        with open(logo_path, "wb") as f:
            f.write(image_data)

        # 提取颜色
        colors = self._extract_colors(image_data)

        # 更新配置
        relative_path = f"brand_assets/{brand_id}/{logo_filename}"
        config["brands"][brand_id]["logo"]["file_path"] = relative_path
        config["brands"][brand_id]["logo"]["colors"] = colors
        config["brands"][brand_id]["updated_at"] = datetime.now().isoformat()
        self._save_config(config)

        return {
            "success": True,
            "logo_path": relative_path,
            "colors": colors
        }

    def delete_logo(self, brand_id: str) -> Dict:
        """删除Logo"""
        config = self._load_config()

        if brand_id not in config.get("brands", {}):
            return {"success": False, "error": "品牌不存在"}

        logo_path = config["brands"][brand_id].get("logo", {}).get("file_path")

        if logo_path:
            # 删除文件
            full_path = os.path.join(self.root_dir, logo_path)
            if os.path.exists(full_path):
                os.remove(full_path)

        # 清空Logo配置
        config["brands"][brand_id]["logo"] = {
            "file_path": None,
            "colors": [],
            "description": None
        }
        config["brands"][brand_id]["updated_at"] = datetime.now().isoformat()
        self._save_config(config)

        return {"success": True}

    def _extract_colors(self, image_data: bytes, num_colors: int = 5) -> List[str]:
        """
        从图片中提取主要颜色

        使用k-means聚类算法提取主要颜色

        Args:
            image_data: 图片二进制数据
            num_colors: 提取的颜色数量

        Returns:
            十六进制颜色列表
        """
        try:
            # 打开图片
            img = Image.open(io.BytesIO(image_data))

            # 转换为RGB模式
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # 缩小图片以加快处理
            img = img.resize((100, 100))

            # 获取所有像素
            pixels = list(img.getdata())

            # 过滤掉接近白色和接近黑色的像素
            filtered_pixels = []
            for r, g, b in pixels:
                # 转换为HSV来判断
                h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
                # 排除太亮（接近白色）和太暗（接近黑色）的颜色
                if 0.1 < v < 0.9 and s > 0.1:
                    filtered_pixels.append((r, g, b))

            # 如果过滤后像素太少，使用原始像素
            if len(filtered_pixels) < 100:
                filtered_pixels = pixels

            # 量化颜色（将相似颜色归为一类）
            quantized = []
            for r, g, b in filtered_pixels:
                # 量化到16级
                qr = (r // 16) * 16
                qg = (g // 16) * 16
                qb = (b // 16) * 16
                quantized.append((qr, qg, qb))

            # 统计颜色频率
            color_counter = Counter(quantized)

            # 获取最常见的颜色
            most_common = color_counter.most_common(num_colors)

            # 转换为十六进制
            hex_colors = []
            for (r, g, b), _ in most_common:
                hex_color = f"#{r:02x}{g:02x}{b:02x}".upper()
                hex_colors.append(hex_color)

            return hex_colors

        except Exception as e:
            print(f"提取颜色失败: {e}")
            return []

    def update_logo_description(self, brand_id: str, description: str) -> Dict:
        """更新Logo描述"""
        config = self._load_config()

        if brand_id not in config.get("brands", {}):
            return {"success": False, "error": "品牌不存在"}

        config["brands"][brand_id]["logo"]["description"] = description
        config["brands"][brand_id]["updated_at"] = datetime.now().isoformat()
        self._save_config(config)

        return {"success": True}

    # ==================== 内容管理 ====================

    def add_content(
        self,
        brand_id: str,
        content_type: str,  # "company" 或 "competitor"
        title: str,
        text: str,
        images: List[bytes] = None,
        source_url: str = None,
        source_type: str = "manual"  # "link" 或 "manual"
    ) -> Dict:
        """
        添加内容（公司内容或竞品内容）

        Args:
            brand_id: 品牌ID
            content_type: 内容类型，"company"或"competitor"
            title: 内容标题
            text: 内容正文
            images: 图片二进制数据列表
            source_url: 来源URL
            source_type: 来源类型，"link"或"manual"

        Returns:
            添加结果
        """
        config = self._load_config()

        if brand_id not in config.get("brands", {}):
            return {"success": False, "error": "品牌不存在"}

        # 确保目录存在
        self._ensure_brand_dirs(brand_id)
        brand_dir = self._get_brand_dir(brand_id)

        # 确定存储目录
        content_key = "company_contents" if content_type == "company" else "competitor_contents"
        content_dir_name = "contents" if content_type == "company" else "competitors"
        content_dir = os.path.join(brand_dir, content_dir_name)

        # 生成内容ID
        content_id = f"{content_type}_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        # 保存图片
        image_paths = []
        if images:
            for i, img_data in enumerate(images):
                img_filename = f"{content_id}_{i}.jpg"
                img_path = os.path.join(content_dir, img_filename)
                with open(img_path, "wb") as f:
                    f.write(img_data)
                image_paths.append(f"brand_assets/{brand_id}/{content_dir_name}/{img_filename}")

        # 创建内容记录
        content_data = {
            "id": content_id,
            "type": source_type,
            "source_url": source_url,
            "title": title,
            "text": text,
            "images": image_paths,
            "created_at": now
        }

        config["brands"][brand_id][content_key].append(content_data)
        config["brands"][brand_id]["updated_at"] = now
        self._save_config(config)

        return {
            "success": True,
            "content_id": content_id,
            "content": content_data
        }

    def delete_content(self, brand_id: str, content_type: str, content_id: str) -> Dict:
        """删除内容"""
        config = self._load_config()

        if brand_id not in config.get("brands", {}):
            return {"success": False, "error": "品牌不存在"}

        content_key = "company_contents" if content_type == "company" else "competitor_contents"
        contents = config["brands"][brand_id].get(content_key, [])

        # 找到并删除内容
        content_to_delete = None
        for i, content in enumerate(contents):
            if content.get("id") == content_id:
                content_to_delete = contents.pop(i)
                break

        if content_to_delete is None:
            return {"success": False, "error": "内容不存在"}

        # 删除关联的图片文件
        for img_path in content_to_delete.get("images", []):
            full_path = os.path.join(self.root_dir, img_path)
            if os.path.exists(full_path):
                os.remove(full_path)

        config["brands"][brand_id]["updated_at"] = datetime.now().isoformat()
        self._save_config(config)

        return {"success": True}

    def get_contents(self, brand_id: str, content_type: str) -> List[Dict]:
        """获取内容列表"""
        config = self._load_config()

        if brand_id not in config.get("brands", {}):
            return []

        content_key = "company_contents" if content_type == "company" else "competitor_contents"
        return config["brands"][brand_id].get(content_key, [])

    # ==================== 风格DNA ====================

    def update_style_dna(
        self,
        brand_id: str,
        writing_style: Dict = None,
        visual_style: Dict = None,
        style_prompt: str = None
    ) -> Dict:
        """
        更新风格DNA

        Args:
            brand_id: 品牌ID
            writing_style: 文风分析结果
            visual_style: 视觉风格分析结果
            style_prompt: 综合风格Prompt

        Returns:
            更新结果
        """
        config = self._load_config()

        if brand_id not in config.get("brands", {}):
            return {"success": False, "error": "品牌不存在"}

        if writing_style is not None:
            config["brands"][brand_id]["style_dna"]["writing_style"] = writing_style

        if visual_style is not None:
            config["brands"][brand_id]["style_dna"]["visual_style"] = visual_style

        if style_prompt is not None:
            config["brands"][brand_id]["style_dna"]["style_prompt"] = style_prompt

        config["brands"][brand_id]["updated_at"] = datetime.now().isoformat()
        self._save_config(config)

        return {"success": True}

    def get_style_dna(self, brand_id: str) -> Optional[Dict]:
        """获取风格DNA"""
        config = self._load_config()

        if brand_id not in config.get("brands", {}):
            return None

        return config["brands"][brand_id].get("style_dna", {})

    def get_active_style_prompt(self) -> Optional[str]:
        """获取当前激活品牌的风格Prompt"""
        active_brand = self.get_active_brand()

        if active_brand is None:
            return None

        style_dna = active_brand.get("style_dna", {})
        return style_dna.get("style_prompt")

    def get_logo_path(self, brand_id: str) -> Optional[str]:
        """获取Logo文件的完整路径"""
        config = self._load_config()

        if brand_id not in config.get("brands", {}):
            return None

        logo_path = config["brands"][brand_id].get("logo", {}).get("file_path")

        if logo_path:
            return os.path.join(self.root_dir, logo_path)

        return None


# 全局服务实例
_service_instance = None


def get_brand_service() -> BrandService:
    """获取品牌服务实例（单例模式）"""
    global _service_instance
    if _service_instance is None:
        _service_instance = BrandService()
    return _service_instance
