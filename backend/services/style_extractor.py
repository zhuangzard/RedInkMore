"""
风格DNA提取服务

负责分析品牌内容样本，提取文风和视觉风格特点。
"""

import os
import re
import json
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from backend.utils.text_client import get_text_chat_client
from backend.services.brand import get_brand_service

logger = logging.getLogger(__name__)


class StyleExtractorService:
    """风格DNA提取服务类"""

    def __init__(self):
        """初始化风格提取服务"""
        logger.debug("初始化 StyleExtractorService...")
        self.text_config = self._load_text_config()
        self._init_error = None
        self._init_error_type = None

        try:
            self.client = self._get_client()
        except ValueError as e:
            # 保存初始化错误，在调用时返回
            self._init_error = str(e)
            if "未配置 API Key" in str(e):
                self._init_error_type = "missing_api_key"
            elif "未找到任何文本生成服务商配置" in str(e):
                self._init_error_type = "no_provider"
            elif "未找到文本生成服务商配置" in str(e):
                self._init_error_type = "no_provider"
            else:
                self._init_error_type = "config_error"
            self.client = None

        self.writing_prompt_template = self._load_prompt_template("style_analysis_writing.txt")
        self.visual_prompt_template = self._load_prompt_template("style_analysis_visual.txt")
        logger.info(f"StyleExtractorService 初始化完成")

    def _load_text_config(self) -> dict:
        """加载文本生成配置"""
        config_path = Path(__file__).parent.parent.parent / 'text_providers.yaml'

        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                return config
            except yaml.YAMLError as e:
                logger.error(f"文本配置 YAML 解析失败: {e}")
                raise ValueError(f"文本配置文件格式错误: {e}")

        return {
            'active_provider': 'google_gemini',
            'providers': {}
        }

    def _get_client(self):
        """根据配置获取客户端"""
        active_provider = self.text_config.get('active_provider', 'google_gemini')
        providers = self.text_config.get('providers', {})

        if not providers:
            raise ValueError("未找到任何文本生成服务商配置")

        if active_provider not in providers:
            raise ValueError(f"未找到文本生成服务商配置: {active_provider}")

        provider_config = providers.get(active_provider, {})

        if not provider_config.get('api_key'):
            raise ValueError(f"文本服务商 {active_provider} 未配置 API Key")

        return get_text_chat_client(provider_config)

    def _load_prompt_template(self, filename: str) -> str:
        """加载Prompt模板"""
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            filename
        )
        if not os.path.exists(prompt_path):
            return ""
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _get_model_params(self) -> Dict[str, Any]:
        """获取模型参数"""
        active_provider = self.text_config.get('active_provider', 'google_gemini')
        providers = self.text_config.get('providers', {})
        provider_config = providers.get(active_provider, {})

        return {
            'model': provider_config.get('model', 'gemini-2.0-flash-exp'),
            'temperature': provider_config.get('temperature', 0.7),
            'max_output_tokens': provider_config.get('max_output_tokens', 4000)
        }

    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """从响应文本中提取JSON"""
        if not text or not text.strip():
            return None

        # 清理常见的格式问题
        cleaned_text = text.strip()

        # 尝试直接解析
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass

        # 尝试从markdown代码块中提取
        json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', cleaned_text)
        if json_match:
            try:
                json_content = json_match.group(1).strip()
                return json.loads(json_content)
            except json.JSONDecodeError:
                pass

        # 尝试找到第一个{到最后一个}
        start = cleaned_text.find('{')
        end = cleaned_text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = cleaned_text[start:end + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # 尝试修复常见的 JSON 格式问题
                try:
                    # 移除可能的尾随逗号
                    fixed_json = re.sub(r',(\s*[}\]])', r'\1', json_str)
                    return json.loads(fixed_json)
                except json.JSONDecodeError:
                    pass

        return None

    def extract_style(self, brand_id: str) -> Dict:
        """
        提取品牌风格DNA

        Args:
            brand_id: 品牌ID

        Returns:
            提取结果
        """
        # 检查初始化错误
        if self._init_error:
            error_type = self._init_error_type or "config_error"
            if error_type == "missing_api_key":
                error_msg = "请先配置 API Key\n\n请前往「系统设置」页面添加文本生成服务商配置。"
            elif error_type == "no_provider":
                error_msg = "未配置文本生成服务商\n\n请前往「系统设置」页面添加文本生成服务商。"
            else:
                error_msg = f"配置错误: {self._init_error}"

            return {
                "success": False,
                "error": error_msg,
                "error_type": error_type
            }

        try:
            brand_service = get_brand_service()
            brand = brand_service.get_brand(brand_id)

            if brand is None:
                return {"success": False, "error": "品牌不存在"}

            # 获取内容样本
            company_contents = brand.get("company_contents", [])
            competitor_contents = brand.get("competitor_contents", [])

            if not company_contents and not competitor_contents:
                return {
                    "success": False,
                    "error": "请先添加内容样本（公司内容或竞品内容）"
                }

            # 分析文风
            writing_style = self._analyze_writing_style(company_contents, competitor_contents)

            # 分析视觉风格（如果有图片）
            visual_style = self._analyze_visual_style(brand_id, company_contents, competitor_contents)

            # 生成综合风格Prompt
            style_prompt = self._generate_style_prompt(
                brand,
                writing_style,
                visual_style
            )

            # 保存到品牌配置
            brand_service.update_style_dna(
                brand_id,
                writing_style=writing_style,
                visual_style=visual_style,
                style_prompt=style_prompt
            )

            return {
                "success": True,
                "style_dna": {
                    "writing_style": writing_style,
                    "visual_style": visual_style,
                    "style_prompt": style_prompt
                }
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"风格提取失败: {error_msg}")

            # 判断错误类型
            error_type = "unknown"
            if "api_key" in error_msg.lower() or "未配置 API Key" in error_msg:
                error_type = "missing_api_key"
                error_msg = "请先配置 API Key\n\n请前往「系统设置」页面添加文本生成服务商配置。"
            elif "unauthorized" in error_msg.lower() or "401" in error_msg:
                error_type = "auth_failed"
                error_msg = "API 认证失败\n\nAPI Key 无效或已过期，请在「系统设置」中检查并更新。"
            elif "timeout" in error_msg.lower() or "连接" in error_msg:
                error_type = "network_error"
                error_msg = "网络连接失败\n\n请检查网络连接，或稍后重试。"
            elif "rate" in error_msg.lower() or "429" in error_msg:
                error_type = "rate_limit"
                error_msg = "API 配额限制\n\nAPI 调用次数超限，请稍后重试。"
            elif "json" in error_msg.lower() or "decode" in error_msg.lower() or '"tone"' in error_msg:
                error_type = "parse_error"
                error_msg = "AI 返回格式异常\n\n模型返回的内容无法解析，请重试。如果问题持续存在，可能需要更换模型。"

            return {
                "success": False,
                "error": error_msg,
                "error_type": error_type
            }

    def _analyze_writing_style(
        self,
        company_contents: List[Dict],
        competitor_contents: List[Dict]
    ) -> Optional[Dict]:
        """分析文风"""
        if not self.writing_prompt_template:
            return None

        # 准备内容样本
        samples = []

        for content in company_contents[:5]:  # 最多5个
            samples.append(f"【公司内容】\n标题: {content.get('title', '')}\n正文: {content.get('text', '')}")

        for content in competitor_contents[:3]:  # 最多3个竞品
            samples.append(f"【竞品参考】\n标题: {content.get('title', '')}\n正文: {content.get('text', '')}")

        if not samples:
            return None

        content_samples = "\n\n---\n\n".join(samples)
        prompt = self.writing_prompt_template.replace("{content_samples}", content_samples)

        try:
            params = self._get_model_params()
            response = self.client.generate_text(
                prompt=prompt,
                model=params['model'],
                temperature=0.5,  # 使用较低温度以获得更稳定的结果
                max_output_tokens=params['max_output_tokens']
            )

            writing_style = self._parse_json_response(response)

            if writing_style:
                return writing_style
            else:
                logger.warning(f"无法解析文风分析结果，原始响应: {response[:500]}")
                # 尝试从文本中提取关键信息
                return {
                    "summary": response[:500] if response else "AI 未返回有效内容",
                    "parse_failed": True
                }

        except Exception as e:
            logger.error(f"文风分析失败: {e}")
            # 抛出异常而不是返回 None，让上层处理
            raise

    def _analyze_visual_style(
        self,
        brand_id: str,
        company_contents: List[Dict],
        competitor_contents: List[Dict]
    ) -> Optional[Dict]:
        """分析视觉风格"""
        if not self.visual_prompt_template:
            return None

        # 收集图片
        brand_service = get_brand_service()
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        images = []

        # 收集公司内容图片
        for content in company_contents[:3]:
            for img_path in content.get('images', [])[:2]:  # 每个内容最多2张
                full_path = os.path.join(root_dir, img_path)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'rb') as f:
                            images.append(f.read())
                    except Exception as e:
                        logger.warning(f"读取图片失败: {img_path}, {e}")

        # 收集竞品图片
        for content in competitor_contents[:2]:
            for img_path in content.get('images', [])[:1]:  # 每个竞品最多1张
                full_path = os.path.join(root_dir, img_path)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'rb') as f:
                            images.append(f.read())
                    except Exception as e:
                        logger.warning(f"读取图片失败: {img_path}, {e}")

        if not images:
            return {
                "summary": "无图片样本，无法分析视觉风格",
                "no_images": True
            }

        try:
            params = self._get_model_params()
            response = self.client.generate_text(
                prompt=self.visual_prompt_template,
                model=params['model'],
                temperature=0.5,
                max_output_tokens=params['max_output_tokens'],
                images=images
            )

            visual_style = self._parse_json_response(response)

            if visual_style:
                return visual_style
            else:
                logger.warning(f"无法解析视觉风格分析结果，原始响应: {response[:500]}")
                return {
                    "summary": response[:500] if response else "AI 未返回有效内容",
                    "parse_failed": True
                }

        except Exception as e:
            logger.error(f"视觉风格分析失败: {e}")
            # 视觉风格分析失败不阻止整体流程，返回 None
            return None

    def _generate_style_prompt(
        self,
        brand: Dict,
        writing_style: Optional[Dict],
        visual_style: Optional[Dict]
    ) -> str:
        """
        生成综合风格Prompt

        用于在图片生成时注入品牌风格
        """
        parts = []

        # Logo信息
        logo = brand.get("logo", {})
        if logo.get("colors"):
            colors_str = ", ".join(logo["colors"])
            parts.append(f"品牌主色调: {colors_str}")

        if logo.get("description"):
            parts.append(f"品牌Logo特征: {logo['description']}")

        # 文风信息
        if writing_style and not writing_style.get("parse_failed"):
            if writing_style.get("tone"):
                parts.append(f"文字风格: {writing_style['tone']}")
            if writing_style.get("summary"):
                parts.append(f"内容特点: {writing_style['summary']}")

        # 视觉风格信息
        if visual_style and not visual_style.get("parse_failed") and not visual_style.get("no_images"):
            if visual_style.get("color_scheme"):
                parts.append(f"配色风格: {visual_style['color_scheme']}")
            if visual_style.get("image_style"):
                parts.append(f"图片风格: {visual_style['image_style']}")
            if visual_style.get("layout_style"):
                parts.append(f"排版风格: {visual_style['layout_style']}")
            if visual_style.get("summary"):
                parts.append(f"视觉特点: {visual_style['summary']}")

        if not parts:
            return ""

        # 组合成完整的风格Prompt
        style_prompt = "【品牌风格要求】\n" + "\n".join(f"- {p}" for p in parts)
        style_prompt += "\n\n请确保生成的图片符合以上品牌风格特点，保持视觉统一性。"

        return style_prompt


# 全局服务实例
_service_instance = None


def get_style_extractor_service() -> StyleExtractorService:
    """获取风格提取服务实例"""
    global _service_instance
    # 如果之前初始化失败，尝试重新初始化（用户可能已配置API Key）
    if _service_instance is not None and _service_instance._init_error:
        _service_instance = None
    if _service_instance is None:
        _service_instance = StyleExtractorService()
    return _service_instance


def reset_style_extractor_service():
    """重置风格提取服务实例（配置更新后调用）"""
    global _service_instance
    _service_instance = None
