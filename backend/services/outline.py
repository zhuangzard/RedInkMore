import logging
import os
import re
import base64
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from backend.utils.text_client import get_text_chat_client

logger = logging.getLogger(__name__)


class OutlineService:
    def __init__(self):
        logger.debug("初始化 OutlineService...")
        self.text_config = self._load_text_config()
        self.client = self._get_client()
        self.prompt_template = self._load_prompt_template()
        logger.info(f"OutlineService 初始化完成，使用服务商: {self.text_config.get('active_provider')}")

    def _load_text_config(self) -> dict:
        """加载文本生成配置"""
        config_path = Path(__file__).parent.parent.parent / 'text_providers.yaml'
        logger.debug(f"加载文本配置: {config_path}")

        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                logger.debug(f"文本配置加载成功: active={config.get('active_provider')}")
                return config
            except yaml.YAMLError as e:
                logger.error(f"文本配置 YAML 解析失败: {e}")
                raise ValueError(
                    f"文本配置文件格式错误: text_providers.yaml\n"
                    f"YAML 解析错误: {e}\n"
                    "解决方案：检查 YAML 缩进和语法"
                )

        logger.warning("text_providers.yaml 不存在，使用默认配置")
        # 默认配置
        return {
            'active_provider': 'google_gemini',
            'providers': {
                'google_gemini': {
                    'type': 'google_gemini',
                    'model': 'gemini-2.0-flash-exp',
                    'temperature': 1.0,
                    'max_output_tokens': 8000
                }
            }
        }

    def _get_client(self):
        """根据配置获取客户端"""
        active_provider = self.text_config.get('active_provider', 'google_gemini')
        providers = self.text_config.get('providers', {})

        if not providers:
            logger.error("未找到任何文本生成服务商配置")
            raise ValueError(
                "未找到任何文本生成服务商配置。\n"
                "解决方案：\n"
                "1. 在系统设置页面添加文本生成服务商\n"
                "2. 或手动编辑 text_providers.yaml 文件"
            )

        if active_provider not in providers:
            available = ', '.join(providers.keys())
            logger.error(f"文本服务商 [{active_provider}] 不存在，可用: {available}")
            raise ValueError(
                f"未找到文本生成服务商配置: {active_provider}\n"
                f"可用的服务商: {available}\n"
                "解决方案：在系统设置中选择一个可用的服务商"
            )

        provider_config = providers.get(active_provider, {})

        if not provider_config.get('api_key'):
            logger.error(f"文本服务商 [{active_provider}] 未配置 API Key")
            raise ValueError(
                f"文本服务商 {active_provider} 未配置 API Key\n"
                "解决方案：在系统设置页面编辑该服务商，填写 API Key"
            )

        logger.info(f"使用文本服务商: {active_provider} (type={provider_config.get('type')})")
        return get_text_chat_client(provider_config)

    def _load_prompt_template(self) -> str:
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "outline_prompt.txt"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_rewrite_prompt_template(self) -> str:
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "outline_rewrite_prompt.txt"
        )
        if not os.path.exists(prompt_path):
            # Fallback to default if rewrite prompt missing
            return self.prompt_template
            
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_outline(self, outline_text: str) -> List[Dict[str, Any]]:
        # 按 <page> 分割页面（兼容旧的 --- 分隔符）
        if '<page>' in outline_text:
            pages_raw = re.split(r'<page>', outline_text, flags=re.IGNORECASE)
        else:
            # 向后兼容：如果没有 <page> 则使用 ---
            pages_raw = outline_text.split("---")

        pages = []

        for index, page_text in enumerate(pages_raw):
            page_text = page_text.strip()
            if not page_text:
                continue

            page_type = "content"
            type_match = re.match(r"\[(\S+)\]", page_text)
            if type_match:
                type_cn = type_match.group(1)
                type_mapping = {
                    "封面": "cover",
                    "内容": "content",
                    "总结": "summary",
                }
                page_type = type_mapping.get(type_cn, "content")

            pages.append({
                "index": index,
                "type": page_type,
                "content": page_text
            })

        return pages

    def generate_outline(
        self,
        topic: str,
        images: Optional[List[bytes]] = None
    ) -> Dict[str, Any]:
        try:
            logger.info(f"开始生成大纲: topic={topic[:50]}..., images={len(images) if images else 0}")
            prompt = self.prompt_template.format(topic=topic)

            if images and len(images) > 0:
                prompt += f"\n\n注意：用户提供了 {len(images)} 张参考图片，请在生成大纲时考虑这些图片的内容和风格。这些图片可能是产品图、个人照片或场景图，请根据图片内容来优化大纲，使生成的内容与图片相关联。"
                logger.debug(f"添加了 {len(images)} 张参考图片到提示词")

            # 从配置中获取模型参数
            active_provider = self.text_config.get('active_provider', 'google_gemini')
            providers = self.text_config.get('providers', {})
            provider_config = providers.get(active_provider, {})

            model = provider_config.get('model', 'gemini-2.0-flash-exp')
            temperature = provider_config.get('temperature', 1.0)
            max_output_tokens = provider_config.get('max_output_tokens', 8000)

            logger.info(f"调用文本生成 API: model={model}, temperature={temperature}")
            outline_text = self.client.generate_text(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                images=images
            )

            logger.debug(f"API 返回文本长度: {len(outline_text)} 字符")
            pages = self._parse_outline(outline_text)
            logger.info(f"大纲解析完成，共 {len(pages)} 页")

            return {
                "success": True,
                "outline": outline_text,
                "pages": pages,
                "has_images": images is not None and len(images) > 0
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"大纲生成失败: {error_msg}")

            # 根据错误类型提供更详细的错误信息
            error_type = "unknown"

            if "未配置 API Key" in error_msg or "api_key" in error_msg.lower():
                error_type = "missing_api_key"
                detailed_error = (
                    "请先配置 API Key\n\n"
                    "请前往「系统设置」页面添加文本生成服务商配置，"
                    "或手动编辑 text_providers.yaml 文件。"
                )
            elif "未找到任何文本生成服务商配置" in error_msg:
                error_type = "no_provider"
                detailed_error = (
                    "未配置文本生成服务商\n\n"
                    "请前往「系统设置」页面添加文本生成服务商，"
                    "支持 OpenAI、Google Gemini 等多种服务商。"
                )
            elif "unauthorized" in error_msg.lower() or "401" in error_msg:
                error_type = "auth_failed"
                detailed_error = (
                    "API 认证失败\n\n"
                    "API Key 无效或已过期，请在「系统设置」中检查并更新。"
                )
            elif "model" in error_msg.lower() or "404" in error_msg:
                error_type = "model_error"
                detailed_error = (
                    "模型访问失败\n\n"
                    "模型名称可能不正确，请在「系统设置」中检查配置。"
                )
            elif "timeout" in error_msg.lower() or "连接" in error_msg:
                error_type = "network_error"
                detailed_error = (
                    "网络连接失败\n\n"
                    "请检查网络连接，或稍后重试。"
                )
            elif "rate" in error_msg.lower() or "429" in error_msg or "quota" in error_msg.lower():
                error_type = "rate_limit"
                detailed_error = (
                    "API 配额限制\n\n"
                    "API 调用次数超限，请等待配额重置或升级套餐。"
                )
            else:
                error_type = "unknown"
                detailed_error = (
                    "大纲生成失败\n\n"
                    f"{error_msg}\n\n"
                    "请检查「系统设置」中的服务商配置。"
                )

            return {
                "success": False,
                "error": detailed_error,
                "error_type": error_type
            }

    def generate_outline_from_article(
        self,
        article_data: Dict,
        images: Optional[List[bytes]] = None
    ) -> Dict[str, Any]:
        """
        根据文章内容生成大纲（改写模式）
        
        Args:
            article_data: 文章数据 {title, text, ...}
            images: 图片二进制列表（可选）
        """
        try:
            logger.info(f"开始改写文章: title={article_data.get('title')}, images={len(images) if images else 0}")
            
            # 加载改写 Prompt
            rewrite_prompt = self._load_rewrite_prompt_template()
            
            # 构建 Prompt (使用 replace 而不是 format，防止 JSON 中的花括号被错误解析)
            prompt = rewrite_prompt.replace('{title}', article_data.get('title', '无标题'))
            prompt = prompt.replace('{content}', article_data.get('text', '')[:3000])
            prompt = prompt.replace('{image_count}', str(len(images) if images else 0))

            # 从配置中获取模型参数
            active_provider = self.text_config.get('active_provider', 'google_gemini')
            providers = self.text_config.get('providers', {})
            provider_config = providers.get(active_provider, {})

            model = provider_config.get('model', 'gemini-2.0-flash-exp')
            temperature = provider_config.get('temperature', 0.8) # 改写需要稍微严谨一点，但也需要创意
            max_output_tokens = provider_config.get('max_output_tokens', 8000)

            logger.info(f"调用改写 API: model={model}")
            
            # 这里的 images 主要是为了让模型知道有这些图，未必能直接读懂所有图（取决于模型能力）
            # 对于 Gemini Pro Vision，传入图片可以帮助它理解上下文
            outline_text = self.client.generate_text(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                images=images
            )
            
            # 尝试解析 JSON 格式的返回
            # 因为 Prompt 要求返回 JSON，所以尝试解析
            pages = []
            final_outline = outline_text
            
            try:
                # 尝试找到 JSON 字符串
                # 使用非贪婪匹配寻找最外层的花括号
                json_match = re.search(r'\{[\s\S]*\}', outline_text)
                if json_match:
                    json_str = json_match.group(0)
                    # 尝试清理一下常见的Markdown格式标记
                    if json_str.startswith('```json'):
                        json_str = json_str[7:]
                    if json_str.endswith('```'):
                        json_str = json_str[:-3]
                    
                    data = json.loads(json_str)
                    if 'outline' in data:
                        final_outline = data['outline']
                    if 'pages' in data:
                        pages = data['pages']
                        # 补全 index
                        for i, p in enumerate(pages):
                            p['index'] = i
            except Exception as e:
                logger.warning(f"解析改写结果 JSON 失败: {e}，尝试使用普通解析")
                # 如果 JSON 解析失败，而且 outline_text 本身看起来不像 JSON，那就直接用 text
                pages = self._parse_outline(outline_text)

            # 如果 JSON 解析失败导致 pages 为空，使用普通解析
            if not pages:
                pages = self._parse_outline(outline_text)

            logger.info(f"改写完成，共 {len(pages)} 页")

            return {
                "success": True,
                "outline": final_outline,
                "pages": pages,
                "has_images": images is not None and len(images) > 0,
                "source_type": "article_rewrite"
            }

        except Exception as e:
            logger.error(f"文章改写失败: {e}")
            return {
                "success": False,
                "error": f"文章改写失败: {str(e)}",
                "error_type": "generation_error"
            }


def get_outline_service() -> OutlineService:
    """
    获取大纲生成服务实例
    每次调用都创建新实例以确保配置是最新的
    """
    return OutlineService()
