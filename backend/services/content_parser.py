"""
内容解析服务

负责解析小红书链接，提取内容信息。
采用渐进式降级策略：直接请求 -> 提示手动输入
"""

import re
import json
import requests
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs


class ContentParserService:
    """内容解析服务类"""

    # 小红书链接正则
    XHS_URL_PATTERNS = [
        r'xiaohongshu\.com/explore/([a-zA-Z0-9]+)',
        r'xiaohongshu\.com/discovery/item/([a-zA-Z0-9]+)',
        r'xhslink\.com/([a-zA-Z0-9]+)',
        r'mp\.weixin\.qq\.com/s',
    ]


    # 请求头
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    def __init__(self):
        """初始化内容解析服务"""
        pass

    def parse_url(self, url: str) -> Dict:
        """
        统一解析入口
        支持小红书和微信公众号链接
        """
        # 移除 URL 中的多余空白字符
        url = url.strip()

        # 1. 判断是否为微信链接
        if 'mp.weixin.qq.com' in url:
            return self.parse_wechat_url(url)
        
        # 2. 默认为小红书链接（兼容旧逻辑）
        return self.parse_xiaohongshu_url(url)

    def parse_wechat_url(self, url: str) -> Dict:
        """
        解析微信公众号链接
        """
        try:
            print(f"正在解析微信链接: {url}")
            response = requests.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            html = response.text

            # 1. 提取标题
            #var msg_title = '标题';
            title_match = re.search(r"var\s+msg_title\s*=\s*['\"](.*?)['\"];", html)
            if not title_match:
                # 尝试从 og:title 提取
                title_match = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
            
            title = title_match.group(1) if title_match else ""
            # 解码 HTML 实体
            title = title.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")

            # 2. 提取描述/摘要
            # var msg_desc = "摘要";
            desc_match = re.search(r"var\s+msg_desc\s*=\s*['\"](.*?)['\"];", html)
            desc = desc_match.group(1) if desc_match else ""

            # 3. 提取正文文本 (简单提取，去除HTML标签)
            # 微信正文通常在 id="js_content" 中
            content_match = re.search(r'<div[^>]*id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
            text_content = desc # 默认为摘要
            if content_match:
                raw_content = content_match.group(1)
                # 简单去除标签
                text = re.sub(r'<[^>]+>', '', raw_content)
                # 去除多余空白
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) > len(desc):
                    text_content = text

            # 4. 提取图片
            # data-src="..."
            images = []
            # 查找正文图
            img_matches = re.findall(r'data-src="([^"]+)"', html)
            for img_url in img_matches:
                # 过滤一些非正文图片（如表情包、广告等）
                if 'mmbiz_png' in img_url or 'mmbiz_jpg' in img_url:
                    if img_url not in images:
                        images.append(img_url)
            
            # 限制图片数量，取前10张
            images = images[:10]

            if not title:
                return {"success": False, "error": "无法解析微信文章标题"}

            return {
                "success": True,
                "data": {
                    "title": title,
                    "text": text_content,
                    "desc": desc,
                    "images": images,
                    "source_url": url,
                    "source_type": "wechat"
                }
            }

        except Exception as e:
            print(f"微信解析失败: {e}")
            return {
                "success": False,
                "error": f"微信链接解析失败: {str(e)}",
                "fallback": "manual"
            }

    def parse_xiaohongshu_url(self, url: str) -> Dict:
        """
        解析小红书链接

        Args:
            url: 小红书链接

        Returns:
            解析结果，包含标题、正文、图片等信息
        """
        # 验证链接格式
        if not self._is_valid_xhs_url(url):
            return {
                "success": False,
                "error": "无效的小红书链接",
                "fallback": "manual"
            }

        # 尝试直接请求解析
        try:
            result = self._parse_by_request(url)
            if result.get("success"):
                return result
        except Exception as e:
            print(f"直接请求解析失败: {e}")

        # 解析失败，提示手动输入
        return {
            "success": False,
            "error": "无法自动解析该链接，请手动输入内容",
            "fallback": "manual",
            "url": url
        }

    def _is_valid_xhs_url(self, url: str) -> bool:
        """检查是否为有效的小红书链接"""
        for pattern in self.XHS_URL_PATTERNS:
            if re.search(pattern, url):
                return True

        # 检查是否为小红书域名
        try:
            parsed = urlparse(url)
            if 'xiaohongshu.com' in parsed.netloc or 'xhslink.com' in parsed.netloc:
                return True
        except:
            pass

        return False

    def _parse_by_request(self, url: str) -> Dict:
        """
        通过HTTP请求解析内容

        尝试从页面HTML中提取__INITIAL_STATE__数据
        """
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10, allow_redirects=True)
            response.raise_for_status()

            html = response.text

            # 尝试提取__INITIAL_STATE__
            state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>', html, re.DOTALL)

            if state_match:
                try:
                    # 处理可能的undefined值
                    state_str = state_match.group(1)
                    state_str = state_str.replace('undefined', 'null')

                    state = json.loads(state_str)
                    return self._extract_from_state(state, url)
                except json.JSONDecodeError as e:
                    print(f"JSON解析失败: {e}")

            # 尝试从meta标签提取
            title_match = re.search(r'<title>([^<]+)</title>', html)
            desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html)

            if title_match or desc_match:
                return {
                    "success": True,
                    "data": {
                        "title": title_match.group(1) if title_match else "",
                        "text": desc_match.group(1) if desc_match else "",
                        "images": [],
                        "source_url": url
                    },
                    "partial": True,
                    "message": "仅提取到部分信息，建议补充完善"
                }

            return {"success": False, "error": "无法从页面中提取内容"}

        except requests.RequestException as e:
            return {"success": False, "error": f"请求失败: {str(e)}"}

    def _extract_from_state(self, state: Dict, url: str) -> Dict:
        """从__INITIAL_STATE__中提取内容"""
        try:
            # 尝试不同的数据结构路径
            note_data = None

            # 路径1: note.noteDetailMap
            if 'note' in state and 'noteDetailMap' in state['note']:
                note_map = state['note']['noteDetailMap']
                if note_map:
                    # 获取第一个笔记
                    first_key = list(note_map.keys())[0]
                    note_data = note_map[first_key].get('note')

            # 路径2: noteData
            if note_data is None and 'noteData' in state:
                note_data = state['noteData']

            if note_data:
                title = note_data.get('title', '')
                desc = note_data.get('desc', '')

                # 提取图片
                images = []
                image_list = note_data.get('imageList', [])
                for img in image_list:
                    img_url = img.get('urlDefault') or img.get('url')
                    if img_url:
                        images.append(img_url)

                return {
                    "success": True,
                    "data": {
                        "title": title,
                        "text": desc,
                        "images": images,
                        "source_url": url
                    }
                }

            return {"success": False, "error": "无法从状态数据中提取内容"}

        except Exception as e:
            return {"success": False, "error": f"提取内容失败: {str(e)}"}


# 全局服务实例
_service_instance = None


def get_content_parser_service() -> ContentParserService:
    """获取内容解析服务实例（单例模式）"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ContentParserService()
    return _service_instance
