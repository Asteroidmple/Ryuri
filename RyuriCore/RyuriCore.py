#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RyuriCore - 核心电子书处理工具

整合了以下功能：
1. calibre 的电子书格式互相转换能力
2. epub_tool 的文件解密、加密、格式化、图片转换、字体加密能力
3. EpubSanitizer 的标准化 epub3.0 转换技术
4. readest 的 epub3.0 适配与 html5 和较新 css 的适配与阅读能力
5. sigil 的 epub 编辑与实时浏览能力

设计目标：
- 代码简洁、清晰
- 性能强大，占用内存和CPU极低
- 功能整合到一个基础文件中，可通过命令行调用
- 跨平台兼容
- 详细的参数配置和扩展性

加密/解密兼容性说明：
- 与 epub_tool 完全兼容
- 使用相同的 MD5 哈希和文件名混淆算法
- 支持双向转换

Sanitizer 功能说明：
- 基于 EpubSanitizer 架构重新实现
- 支持多过滤器链式处理
- 支持 EPUB 2 升级到 EPUB 3
- 支持隐私数据清理
- 支持多线程处理
"""

import os
import sys
import argparse
import zipfile
import tempfile
import json
import logging
import shutil
import re
import copy
import hashlib
import time
from typing import Optional, Dict, List, Any, Set, Tuple, Callable
from contextlib import contextmanager
from hashlib import md5 as hashlibmd5
from urllib.parse import unquote, quote
from xml.etree import ElementTree as ET
from xml.dom import minidom
from difflib import SequenceMatcher
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum, auto
from abc import ABC, abstractmethod
from io import BytesIO
import base64

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('RyuriCore')


# ==================== 工具函数 ====================

def get_platform_path(path: str) -> str:
    """获取跨平台路径"""
    return os.path.normpath(path)


def get_relpath(from_path: str, to_path: str) -> str:
    """计算相对路径"""
    from_parts = re.split(r"[\\/]", from_path)
    to_parts = re.split(r"[\\/]", to_path)
    while from_parts and to_parts and from_parts[0] == to_parts[0]:
        from_parts.pop(0)
        to_parts.pop(0)
    return "../" * (len(from_parts) - 1) + "/".join(to_parts)


def get_bookpath(relative_path: str, refer_bkpath: str) -> str:
    """计算文件的绝对路径"""
    relative_parts = re.split(r"[\\/]", relative_path)
    refer_parts = re.split(r"[\\/]", refer_bkpath)
    
    back_step = 0
    while relative_parts and relative_parts[0] == "..":
        back_step += 1
        relative_parts.pop(0)
    
    if len(refer_parts) <= 1:
        return "/".join(relative_parts)
    else:
        refer_parts.pop(-1)
    
    if back_step < 1:
        return "/".join(refer_parts + relative_parts)
    elif back_step > len(refer_parts):
        return "/".join(relative_parts)
    
    while back_step > 0 and len(refer_parts) > 0:
        refer_parts.pop(-1)
        back_step -= 1
    
    return "/".join(refer_parts + relative_parts)


@contextmanager
def temporary_directory():
    """临时目录上下文管理器"""
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


def normalize_xmlns(element: ET.Element) -> ET.Element:
    """规范化 XML 命名空间"""
    ns_map = {
        'http://www.w3.org/1999/xhtml': '',
        'http://www.w3.org/2000/svg': 'svg:',
        'http://www.w3.org/1998/Math/MathML': 'math:',
    }
    
    def fix_tag(tag: str) -> str:
        for ns, prefix in ns_map.items():
            if tag.startswith(f'{{{ns}}}'):
                return prefix + tag[len(f'{{{ns}}}'):]
        return tag
    
    def process_element(elem: ET.Element):
        elem.tag = fix_tag(elem.tag)
        for child in elem:
            process_element(child)
    
    process_element(element)
    return element


def is_inline_element(tag: str) -> bool:
    """判断是否为行内元素"""
    inline_elements = {
        'a', 'abbr', 'b', 'bdi', 'bdo', 'br', 'button', 'cite', 'code', 'data',
        'datalist', 'dfn', 'em', 'i', 'iframe', 'img', 'input', 'kbd', 'label',
        'link', 'map', 'mark', 'meter', 'output', 'progress', 'q', 's', 'samp',
        'script', 'select', 'slot', 'small', 'span', 'strong', 'sub', 'sup',
        'template', 'textarea', 'time', 'u', 'var', 'video', 'wbr'
    }
    return tag.lower() in inline_elements


def add_css_class(element: ET.Element, class_name: str):
    """添加 CSS 类名（避免重复）"""
    current = element.get('class', '')
    classes = set(current.split()) if current else set()
    classes.add(class_name)
    element.set('class', ' '.join(classes))


def xml_to_string(element: ET.Element, encoding: str = 'utf-8', is_opf: bool = False, is_xhtml: bool = False) -> bytes:
    """将 XML 元素转换为字节串"""
    # 注册命名空间 - 必须在创建元素之前注册
    ET.register_namespace('', 'http://www.w3.org/1999/xhtml')
    ET.register_namespace('epub', 'http://www.idpf.org/2007/ops')
    ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
    ET.register_namespace('dcterms', 'http://purl.org/dc/terms/')
    
    # 转换为字符串
    rough_string = ET.tostring(element, encoding='unicode')
    
    # 如果是 OPF 文件，需要处理命名空间前缀
    if is_opf:
        # 替换 ns0: 为 opf:
        rough_string = re.sub(r'<ns0:', '<', rough_string)
        rough_string = re.sub(r'</ns0:', '</', rough_string)
        rough_string = re.sub(r'xmlns:ns0=', 'xmlns=', rough_string)
        # 确保 package 元素有正确的命名空间
        if '<package' in rough_string and 'xmlns=' not in rough_string.split('>')[0]:
            rough_string = rough_string.replace('<package', '<package xmlns="http://www.idpf.org/2007/opf"')
    
    # 美化格式
    try:
        reparsed = minidom.parseString(rough_string.encode('utf-8'))
        pretty = reparsed.toprettyxml(indent="  ", encoding=encoding)
    except Exception as e:
        # 如果解析失败，使用原始字符串
        pretty = rough_string.encode(encoding)
    
    # 移除空行
    if isinstance(pretty, bytes):
        lines = pretty.decode(encoding).split('\n')
    else:
        lines = pretty.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    result = '\n'.join(non_empty_lines)
    
    # 确保 XML 声明正确
    if not result.startswith('<?xml'):
        result = f'<?xml version="1.0" encoding="{encoding}"?>\n' + result
    
    # 如果是 XHTML 文件，添加 HTML5 DOCTYPE
    if is_xhtml and '<!DOCTYPE' not in result:
        # 在 XML 声明后添加 DOCTYPE
        lines = result.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.strip().startswith('<?xml'):
                new_lines.append('<!DOCTYPE html>')
        result = '\n'.join(new_lines)
    
    return result.encode(encoding)


# ==================== 配置管理器 ====================

class ConfigManager:
    """配置管理类 - 支持三层配置优先级"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._defaults = {}
        self._load_defaults()
    
    def _load_defaults(self):
        """加载默认配置"""
        self._defaults = {
            'converter': {
                'verbose': 0,
                'debug_pipeline': None,
                'input_profile': 'default',
                'output_profile': 'default'
            },
            'encryptor': {
                'enabled': True
            },
            'sanitizer': {
                'filters': 'default,privacy',
                'threads': 'multi',
                'cache': 'ram',
                'epub_ver': 0,
                'sanitize_ncx': True,
                'correct_mime': True,
                'xml_cache': True,
                'publisher_mode': False,
                'epub3_guess_toc': False,
                'epub3_correct_spine': True,
                'compress': 0
            },
            'reader': {
                'enabled': True
            },
            'editor': {
                'enabled': True
            },
            'cleaner': {
                'enabled': True
            },
            'plugins': {
                'enabled': True,
                'paths': []
            }
        }
        
        # 合并到当前配置
        for section, values in self._defaults.items():
            if section not in self.config:
                self.config[section] = {}
            for key, value in values.items():
                if key not in self.config[section]:
                    self.config[section][key] = value
    
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """获取配置值"""
        if section not in self.config:
            self.config[section] = self._defaults.get(section, {}).copy()
        
        if key is None:
            return self.config[section]
        
        return self.config[section].get(key, self._defaults.get(section, {}).get(key, default))
    
    def set(self, section: str, key: str, value: Any):
        """设置配置值"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def get_int(self, section: str, key: str) -> int:
        """获取整数配置"""
        return int(self.get(section, key, 0))
    
    def get_bool(self, section: str, key: str) -> bool:
        """获取布尔配置"""
        value = self.get(section, key, False)
        if isinstance(value, bool):
            return value
        return str(value).lower() in ('true', '1', 'yes', 'on')
    
    def get_string(self, section: str, key: str) -> str:
        """获取字符串配置"""
        return str(self.get(section, key, ''))


# ==================== 文件系统抽象 ====================

class FileSystem:
    """文件系统抽象基类"""
    
    def __init__(self):
        self.xml_cache: Dict[str, ET.Element] = {}
        self._modified_files: Set[str] = set()
    
    def read_bytes(self, path: str) -> bytes:
        """读取文件字节"""
        raise NotImplementedError
    
    def read_string(self, path: str, encoding: str = 'utf-8') -> str:
        """读取文件字符串"""
        return self.read_bytes(path).decode(encoding)
    
    def read_xml(self, path: str) -> ET.Element:
        """读取并解析 XML（带缓存）"""
        if path in self.xml_cache:
            return self.xml_cache[path]
        
        content = self.read_bytes(path)
        try:
            root = ET.fromstring(content)
            if self.config.get_bool('sanitizer', 'xml_cache'):
                self.xml_cache[path] = root
            return root
        except ET.ParseError as e:
            logger.error(f"解析 XML 失败 {path}: {e}")
            raise
    
    def write_bytes(self, path: str, data: bytes):
        """写入文件字节"""
        raise NotImplementedError
    
    def write_string(self, path: str, content: str, encoding: str = 'utf-8'):
        """写入文件字符串"""
        self.write_bytes(path, content.encode(encoding))
    
    def write_xml(self, path: str, element: ET.Element, encoding: str = 'utf-8', is_opf: bool = False, is_xhtml: bool = False):
        """写入 XML 文件"""
        data = xml_to_string(element, encoding, is_opf=is_opf, is_xhtml=is_xhtml)
        self.write_bytes(path, data)
        if path in self.xml_cache:
            self.xml_cache[path] = element
        self._modified_files.add(path)
    
    def delete_file(self, path: str):
        """删除文件"""
        raise NotImplementedError
    
    def file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        raise NotImplementedError
    
    def get_all_files(self) -> List[str]:
        """获取所有文件列表"""
        raise NotImplementedError
    
    def get_sha256(self, path: str) -> str:
        """计算文件 SHA256"""
        data = self.read_bytes(path)
        return hashlib.sha256(data).hexdigest()
    
    def flush_xml_cache(self, path: str):
        """刷新 XML 缓存"""
        if path in self.xml_cache:
            del self.xml_cache[path]
    
    def import_from_zip(self, zip_path: str):
        """从 ZIP 导入"""
        raise NotImplementedError
    
    def export_to_zip(self, zip_path: str):
        """导出到 ZIP"""
        raise NotImplementedError


class MemFS(FileSystem):
    """内存文件系统"""
    
    def __init__(self):
        super().__init__()
        self.files: Dict[str, bytes] = {}
        self.config = ConfigManager()
    
    def read_bytes(self, path: str) -> bytes:
        path = path.replace('\\', '/')
        if path not in self.files:
            raise FileNotFoundError(f"文件不存在: {path}")
        return self.files[path]
    
    def write_bytes(self, path: str, data: bytes):
        path = path.replace('\\', '/')
        self.files[path] = data
        self._modified_files.add(path)
    
    def delete_file(self, path: str):
        path = path.replace('\\', '/')
        if path in self.files:
            del self.files[path]
        if path in self.xml_cache:
            del self.xml_cache[path]
    
    def file_exists(self, path: str) -> bool:
        path = path.replace('\\', '/')
        return path in self.files
    
    def get_all_files(self) -> List[str]:
        return list(self.files.keys())
    
    def import_from_zip(self, zip_path: str):
        """从 ZIP 文件导入到内存"""
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                self.files[name.replace('\\', '/')] = zf.read(name)
    
    def export_to_zip(self, zip_path: str):
        """导出到 ZIP 文件"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for path, data in self.files.items():
                zf.writestr(path, data)


class DiskFS(FileSystem):
    """磁盘文件系统"""
    
    def __init__(self, base_path: str):
        super().__init__()
        self.base_path = base_path
        self.config = ConfigManager()
    
    def _get_full_path(self, path: str) -> str:
        """获取完整路径"""
        if os.path.isabs(path):
            return path
        return os.path.join(self.base_path, path)
    
    def read_bytes(self, path: str) -> bytes:
        full_path = self._get_full_path(path)
        with open(full_path, 'rb') as f:
            return f.read()
    
    def write_bytes(self, path: str, data: bytes):
        full_path = self._get_full_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(data)
        self._modified_files.add(path)
    
    def delete_file(self, path: str):
        full_path = self._get_full_path(path)
        if os.path.exists(full_path):
            os.remove(full_path)
        if path in self.xml_cache:
            del self.xml_cache[path]
    
    def file_exists(self, path: str) -> bool:
        full_path = self._get_full_path(path)
        return os.path.exists(full_path)
    
    def get_all_files(self) -> List[str]:
        files = []
        for root, dirs, filenames in os.walk(self.base_path):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, self.base_path)
                files.append(rel_path.replace('\\', '/'))
        return files


# ==================== EPUB 精排版清洗器（重构版）====================

class EPUBCleaner:
    """
    EPUB 精排版清洗器 - 支持多看、掌阅、Send to Kindle 适配
    
    核心特性：
    1. KoboSpan 文本追踪系统 - 为每个文本节点生成唯一ID
    2. 弹出式脚注系统 - 支持多看 duokan-footnote 格式
    3. 字体嵌入系统 - 自动生成 @font-face 规则
    4. 标准 OEBPS 结构 - f{x}.xhtml 命名规范
    5. 双 CSS 架构 - f8.css(字体) + f11.css(样式)
    """
    
    def __init__(self, target_platform: str = "generic"):
        """
        初始化清洗器
        
        Args:
            target_platform: 目标平台 - "duokan"(多看), "zhangyue"(掌阅), "kindle"(Send to Kindle), "generic"(通用)
        """
        self.target_platform = target_platform
        self.temp_dir = None
        self.work_dir = None
        self.oebps_dir = None
        self.text_dir = None
        self.styles_dir = None
        self.images_dir = None
        self.fonts_dir = None
        
        # 文件计数器
        self.file_counter = 0
        self.kobo_counter = 1
        self.span_counter = 1
        
        # 脚注管理
        self.footnotes = {}  # {note_id: note_content}
        self.note_counter = 1
        
        # 字体定义
        self.font_definitions = []
        
        # 元数据
        self.metadata = {
            'title': '',
            'author': '',
            'language': 'zh-CN',
            'identifier': ''
        }
        
    def clean(self, input_path: str, output_path: str) -> bool:
        """
        清洗 EPUB 文件
        
        Args:
            input_path: 输入 EPUB 文件路径
            output_path: 输出 EPUB 文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            logger.info(f"开始精排版清洗: {input_path} -> {output_path}")
            logger.info(f"目标平台: {self.target_platform}")
            
            # 创建临时工作目录
            self.temp_dir = tempfile.mkdtemp()
            self.work_dir = os.path.join(self.temp_dir, 'epub')
            os.makedirs(self.work_dir)
            
            # 设置目录路径
            self.oebps_dir = os.path.join(self.work_dir, 'OEBPS')
            self.text_dir = os.path.join(self.oebps_dir, 'Text')
            self.styles_dir = os.path.join(self.oebps_dir, 'Styles')
            self.images_dir = os.path.join(self.oebps_dir, 'Images')
            self.fonts_dir = os.path.join(self.oebps_dir, 'Fonts')
            
            # 解压 EPUB
            self._extract_epub(input_path)
            
            # 解析原始 OPF 获取元数据
            self._parse_metadata()
            
            # 重组文件结构
            self._reorganize_structure()
            
            # 处理 HTML 文件（核心精排版步骤）
            self._process_html_files()
            
            # 生成字体 CSS
            self._generate_font_css()
            
            # 生成样式 CSS
            self._generate_style_css()
            
            # 处理图片
            self._process_images()
            
            # 生成新的 OPF
            self._generate_opf()
            
            # 生成 NCX
            self._generate_ncx()
            
            # 重新打包
            self._repack_epub(output_path)
            
            logger.info("精排版清洗完成")
            return True
            
        except Exception as e:
            logger.error(f"清洗失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
        finally:
            # 清理临时目录
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
    
    def _extract_epub(self, input_path: str):
        """解压 EPUB 文件"""
        with zipfile.ZipFile(input_path, 'r') as zf:
            zf.extractall(self.work_dir)
    
    def _parse_metadata(self):
        """从原始 OPF 解析元数据"""
        opf_path = self._find_opf()
        if not opf_path:
            return
        
        try:
            tree = ET.parse(opf_path)
            root = tree.getroot()
            
            # 定义命名空间
            ns = {
                'dc': 'http://purl.org/dc/elements/1.1/',
                'opf': 'http://www.idpf.org/2007/opf'
            }
            
            # 提取标题
            title_elem = root.find('.//dc:title', ns)
            if title_elem is not None and title_elem.text:
                self.metadata['title'] = title_elem.text
            
            # 提取作者
            creator_elem = root.find('.//dc:creator', ns)
            if creator_elem is not None and creator_elem.text:
                self.metadata['author'] = creator_elem.text
            
            # 提取语言
            language_elem = root.find('.//dc:language', ns)
            if language_elem is not None and language_elem.text:
                self.metadata['language'] = language_elem.text
            
            # 提取标识符
            identifier_elem = root.find('.//dc:identifier', ns)
            if identifier_elem is not None and identifier_elem.text:
                self.metadata['identifier'] = identifier_elem.text
            
        except Exception as e:
            logger.warning(f"解析元数据失败: {e}")
    
    def _find_opf(self) -> Optional[str]:
        """查找 content.opf 文件"""
        for root, dirs, files in os.walk(self.work_dir):
            for f in files:
                if f.endswith('.opf'):
                    return os.path.join(root, f)
        return None
    
    def _reorganize_structure(self):
        """重组文件结构为标准 OEBPS 格式"""
        # 创建标准目录
        os.makedirs(self.text_dir, exist_ok=True)
        os.makedirs(self.styles_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.fonts_dir, exist_ok=True)
        
        # 移动现有文件到标准位置
        for root, dirs, files in os.walk(self.work_dir):
            # 跳过已经标准化的目录
            if 'OEBPS' in root and any(x in root for x in ['Text', 'Styles', 'Images', 'Fonts']):
                continue
            
            for f in files:
                src = os.path.join(root, f)
                
                # 根据文件类型移动
                if f.endswith(('.html', '.xhtml', '.htm')):
                    dst = os.path.join(self.text_dir, f)
                elif f.endswith('.css'):
                    dst = os.path.join(self.styles_dir, f)
                elif f.endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg')):
                    dst = os.path.join(self.images_dir, f)
                elif f.endswith(('.ttf', '.otf', '.woff', '.woff2')):
                    dst = os.path.join(self.fonts_dir, f)
                elif f == 'mimetype' or f == 'container.xml':
                    continue
                else:
                    continue
                
                if src != dst and os.path.exists(src):
                    shutil.move(src, dst)
    
    def _process_html_files(self):
        """处理 HTML 文件 - 核心精排版步骤"""
        if not os.path.exists(self.text_dir):
            return
        
        # 获取所有 HTML 文件
        html_files = sorted([f for f in os.listdir(self.text_dir) 
                            if f.endswith(('.html', '.xhtml', '.htm'))])
        
        # 处理每个文件
        processed_files = []
        for html_file in html_files:
            path = os.path.join(self.text_dir, html_file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                
                # 精排版处理
                processed = self._process_single_html(content, html_file)
                
                # 生成新的文件名
                new_name = f'f{self.file_counter}.xhtml'
                self.file_counter += 1
                new_path = os.path.join(self.text_dir, new_name)
                
                with open(new_path, 'w', encoding='utf-8') as fp:
                    fp.write(processed)
                
                # 删除原文件
                if path != new_path:
                    os.remove(path)
                
                processed_files.append({
                    'old_name': html_file,
                    'new_name': new_name,
                    'title': self._extract_title_from_html(processed)
                })
                
            except Exception as e:
                logger.warning(f"处理文件 {html_file} 失败: {e}")
        
        self.processed_files = processed_files
    
    def _process_single_html(self, html: str, filename: str) -> str:
        """
        处理单个 HTML 文件 - 核心精排版逻辑
        """
        # 解析 HTML
        try:
            # 使用 html.parser 更宽容
            from html.parser import HTMLParser
            
            # 提取 body 内容
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
            if body_match:
                body_content = body_match.group(1)
            else:
                body_content = html
            
            # 提取标题
            title = self._extract_title_from_html(html) or 'Chapter'
            
            # 处理脚注
            body_content = self._process_footnotes(body_content, filename)
            
            # 添加 KoboSpan
            body_content = self._add_kobospan(body_content)
            
            # 构建标准 HTML 结构
            result = self._build_standard_html(title, body_content)
            
            return result
            
        except Exception as e:
            logger.warning(f"处理 HTML 内容失败: {e}")
            return html
    
    def _process_footnotes(self, content: str, filename: str) -> str:
        """处理脚注 - 转换为多看弹出式格式"""
        # 查找所有脚注引用
        noteref_pattern = r'<a[^>]*epub:type=["\']noteref["\'][^>]*href=["\']#([^"\']+)["\'][^>]*>(.*?)</a>'
        
        def replace_noteref(match):
            note_id = match.group(1)
            note_text = match.group(2)
            
            # 生成新的脚注 ID
            new_note_id = f'B_{self.note_counter}'
            anchor_id = f'A_{self.note_counter}'
            self.note_counter += 1
            
            # 保存脚注内容（稍后处理）
            self.footnotes[new_note_id] = {
                'original_id': note_id,
                'text': note_text,
                'content': ''
            }
            
            # 根据平台生成不同的脚注引用
            if self.target_platform == 'duokan':
                # 多看格式：使用图片图标
                return f'<a style="text-decoration:none!important;color:black;" class="duokan-footnote" epub:type="noteref" href="#{new_note_id}" id="{anchor_id}"><span class="koboSpan" id="kobo.{self.kobo_counter}.{self.span_counter}"><img alt="note" src="../Images/f13.png"/></span></a>'
            else:
                # 其他平台：使用上标数字
                return f'<a class="duokan-footnote" epub:type="noteref" href="#{new_note_id}" id="{anchor_id}"><sup>{self.note_counter-1}</sup></a>'
        
        content = re.sub(noteref_pattern, replace_noteref, content, flags=re.DOTALL | re.IGNORECASE)
        
        # 查找脚注内容（通常在 aside 或单独的元素中）
        footnote_pattern = r'<aside[^>]*epub:type=["\']footnote["\'][^>]*id=["\']([^"\']+)["\'][^>]*>(.*?)</aside>'
        
        def extract_footnote(match):
            note_id = match.group(1)
            note_content = match.group(2)
            
            # 查找对应的引用
            for new_id, info in self.footnotes.items():
                if info['original_id'] == note_id:
                    info['content'] = note_content
                    break
            
            return ''  # 移除原位置的内容
        
        content = re.sub(footnote_pattern, extract_footnote, content, flags=re.DOTALL | re.IGNORECASE)
        
        return content
    
    def _add_kobospan(self, content: str) -> str:
        """为文本节点添加 KoboSpan 追踪"""
        # 这个函数需要递归处理 HTML 树
        # 简化版本：为段落内的文本添加 span
        
        def wrap_text_in_spans(match):
            tag = match.group(1)
            attrs = match.group(2) or ''
            text = match.group(3)
            
            # 跳过已经包含 koboSpan 的标签
            if 'koboSpan' in text:
                return match.group(0)
            
            # 为纯文本添加 koboSpan
            if text.strip() and not re.match(r'<', text):
                kobo_id = f'kobo.{self.kobo_counter}.{self.span_counter}'
                self.span_counter += 1
                return f'<{tag}{attrs}><span class="koboSpan" id="{kobo_id}">{text}</span></{tag}>'
            
            return match.group(0)
        
        # 为段落添加 koboSpan
        content = re.sub(r'<p([^>]*)>([^<]+)</p>', wrap_text_in_spans, content, flags=re.IGNORECASE)
        
        return content
    
    def _build_standard_html(self, title: str, body_content: str) -> str:
        """构建标准 HTML 结构"""
        # 重置 span 计数器
        self.span_counter = 1
        
        html = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">

<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{self.metadata['language']}">
<head>
  <title>{title}</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link href="../Styles/f8.css" type="text/css" rel="stylesheet"/>
  <link href="../Styles/f11.css" type="text/css" rel="stylesheet"/>
  <style type="text/css" class="kobostylehacks">div#book-inner {{ margin-top: 0; margin-bottom: 0;}}</style>
</head>

<body>
  <div id="book-columns">
    <div id="book-inner">
{body_content}
    </div>
  </div>
</body>
</html>'''
        
        # 增加 kobo 计数器
        self.kobo_counter += 1
        
        return html
    
    def _extract_title_from_html(self, html: str) -> str:
        """从 HTML 中提取标题"""
        # 查找 h1 标签
        match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL | re.IGNORECASE)
        if match:
            title = re.sub(r'<[^>]+>', '', match.group(1))
            return title.strip()
        
        # 查找 title 标签
        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return 'Chapter'
    
    def _generate_font_css(self):
        """生成字体 CSS (f8.css)"""
        css_content = '''@font-face {
    font-family: "st";
    src:  url("../Fonts/st.ttf"),
        local("st"),
        local("宋体"),
        local("DK-SONGTI"),
        local("STSongti"),
        local("STSong"),
        local("Song S"),
        local("Songti"), 
        local("Songti SC"), 
        local("Songti TC");
}
@font-face {
    font-family: "kt";
    src:  url("../Fonts/f81.ttf"),
        local("kt"),
        local("楷体"),
        local("方正楷体"),
        local("方正楷体_GBK"),
        local("方正新楷体_GBK"),
        local("DK-KAITI"),
        local("STKaiti"),
        local("STKai"),
        local("MKai PRC"),
        local("Kaiti"), 
        local("Kaiti SC"), 
        local("Kaiti TC");
}
@font-face {
    font-family: "ht";
    src:  url("../Fonts/ht.ttf"),
        local("ht"),
        local("DK-XIHEITI"),
        local("黑体"),
        local("微软雅黑"),
        local("STHeiti"),
        local("STHei"),
        local("MYing Hei S"),
        local("Heiti"),
        local("Heiti SC"),
        local("Heiti TC");
}
@font-face {
    font-family: "fs";
    src:  url("../Fonts/f76.ttf"),
        local("fs"),
        local("DK-FANGSONG"),
        local("仿宋"),
        local("方正仿宋"),
        local("方正仿宋_GBK"),
        local("STKaiti"),
        local("STKai"),
        local("MKai PRC"),
        local("Kaiti"), 
        local("Kaiti SC"), 
        local("Kaiti TC");
}
@font-face {
    font-family: "h2";
    src:  url("../Fonts/f79.ttf"),
        local("h2"),
        local("DK-XIAOBIAOSONG"),
        local("方正大标宋_GBK"),
        local("方正大标宋简体"), 
        local("方正大标宋繁体"),
        local("STHeiti"),
        local("STHei"),
        local("MYing Hei S"),
        local("Heiti"),
        local("Heiti SC"),
        local("Heiti TC");     
}
@font-face {
    font-family: "h3";
    src:  url("../Fonts/h3.ttf"),
        local("h3"),   
        local("DK-XIAOBIAOSONG"),   
        local("h2"),
        local("方正小标宋_GBK"),
        local("方正小标宋_GB18030"), 
        local("方正大标宋繁体"),
        local("STHeiti"),
        local("STHei"),
        local("MYing Hei S"),
        local("Heiti"),
        local("Heiti SC"),
        local("Heiti TC");     
}
@font-face {
    font-family: "fs2";
    src:  url("../Fonts/f77.ttf"),
        local("fs2"),
        local("DK-FANGSONG"),
        local("DFJadeFangSongU W6"),
        local("仿宋"),
        local("方正仿宋"),
        local("方正仿宋_GBK"),
        local("STKaiti"),
        local("STKai"),
        local("MKai PRC"),
        local("Kaiti"), 
        local("Kaiti SC"), 
        local("Kaiti TC");
}
@font-face{
    font-family: "fzqys";
    src:  url("../Fonts/f78.ttf"),
        local("fzqys"),
        local("方正轻妍宋 简");
}
@font-face{
    font-family: "hywfs";
    src:  url("../Fonts/f80.ttf"),
        local("hywfs"),
        local("汉仪婉风宋 65W");
}'''
        
        with open(os.path.join(self.styles_dir, 'f8.css'), 'w', encoding='utf-8') as f:
            f.write(css_content)
    
    def _generate_style_css(self):
        """生成样式 CSS (f11.css)"""
        css_content = '''body.fen {
    background-image: url(../Images/f7.jpg);
    background-repeat: no-repeat;
    background-position: center;
    background-attachment: fixed;
    background-size: cover;
}
h1{
    text-indent: 0em;
    font-weight: normal;
    line-height: 1.8;
}
h1.h1{
    font-family: "hywfs","ZY-KAITI","kt";
    color: #2e5b60;
    text-align: left;
    font-size: 1.3em;
    margin: -2em 0em 1.5em 0em;
}
.h1kt {
    font-family: "fs2","ZY-KAITI","kt";
    font-size: 0.92em;
}
h1.h2{
    font-family: "fzqys","ZY-XIAOBIAOSONG","h2";
    font-size: 1.2em;
    line-height: 1.8;
    color: #2e5b60;
    margin-top: 47%;
    padding-top: 1.3em;
    padding-bottom: 1.25em;
    text-align: center;
    background-color: rgba(255,255,255,0.8);
    border-radius: 2px;
}
div.logo {
    text-align: right;
    text-indent: 0em;
    duokan-text-indent: 0em;
    width: 70%;
    margin-top: 0.5em;
    margin-bottom: 0em;
    margin-right: -1em;
    margin-left: auto;
    duokan-bleed: right;
}
h2{
    text-indent: 0em;
    font-weight: normal;
    line-height: 1.8;
    font-family: "hywfs","ZY-KAITI","kt";
    color: #2e5b60;
    text-align: left;
    font-size: 1.25em;
    margin: -2em 0em 1.5em 0em;
}
.h2kt {
    font-size: 0.95em;
}
h3{
    font-family: "fs2","ZY-KAITI","kt";
    text-indent: 0em;
    duokan-text-indent: 0em;
    font-weight: normal;
    line-height: 1.8em;
    color: #2e5b60;
    font-size: 1.08em;
    text-align: center;
    margin: 2.2em 0em 1.8em 0em;
}
h4{
    font-family: "fs2","ZY-KAITI","kt";
    text-indent: 2em;
    duokan-text-indent: 2em;
    font-weight: normal;
    line-height: 1.8em;
    color: #2e5b60;
    font-size: 1.03em;
    text-align: justify;
    margin: 1.8em 0em 1.5em 0em;
}
blockquote {
    margin: 1.4em 0 1.4em 1em;
}
blockquote p {
    font-family: "ZY-FANGSONG","fs";
    line-height: 1.8em;
    font-size: 1em;
    margin: 1em 0;
    color: #412938;   
}
.quote {
    margin: 1.8em 0 1.8em 1em;
    font-family: "ZY-FANGSONG","fs";
    line-height: 1.8em;
    font-size: 1em;
    color: #412938;
}
.center {
   text-align: center!important;
   text-indent: 0;
}
.right {
    margin: 2em 0 2em 0em;
    font-size: 0.97em;
    text-align: right!important;
}
.kh {
    font-size: 0.98em;
    font-family: "ZY-KAITI","kt";
    color: #412938;
}
html, body {
   margin-top: 0;
   margin-bottom: 0;
   margin-left: 0;
   margin-right: 0;
   padding: 0;
   text-align: justify;
}
                         
.cover {
   text-align: center;
   text-indent: 0;
}
p{
   text-indent: 2em;
   margin: 1em 0;
   line-height: 1.8em;
   text-align: justify;
   text-justify: inter-ideograph;
   word-break: break-all;
}
.fs{font-family: "ZY-FANGSONG","fs";}
.kt{font-family: "ZY-KAITI","kt";}
.fs2{font-family: "fs2","ZY-FANGSONG","fs";}

body.cp-back {
   background-color: #fcf8f7;
}
div.cp-box {
    text-align: justify;
    margin-top: 20%;
    margin-left: 3%;
    margin-bottom: auto;
    margin-right: 3%;
    padding-top: 1em;
    padding-left: 1em;
    padding-bottom: 1em;
    padding-right: 1em;
    border-style: solid;
    border-width: 1px;
    border-radius: 2px;
    border-color: rgba(255, 255, 255, 0.9);
    background-color: rgba(255, 255, 255, 0.9);
    box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.1);
}
p.cp-title {
    font-family: "ZY-XIAOBIAOSONG","h2";
    font-size: 90%;
    font-weight: normal;
    color: #333;
    text-indent: 0em;
    duokan-text-indent: 0em;
}
p.cp {
    font-family: "ZY-KAITI","kt";
    color: #333;
    font-size: 90%;
    text-indent: 0em;
    duokan-text-indent: 0em;
}
hr{
    width: 100%;
    height: 1px;
    margin: 0.9em 0 0.9em 0;
    border-style: none;
    border-top: 1px dotted gray;
    color: #A2906A;
}
a.duokan-footnote img{
    width:0.65em;
}
hr.xian{
    text-align: left;
    duokan-text-align: left;
    width: 60%;
    height: 1px;
    margin: 1.5em 0 1.5em -0.5em;
    border-style: none;
    border-top: 1px solid gray;
}
ol{
    padding: 0;
    list-style-type: none;
    list-style-position: outside;
}
.duokan-footnote-content{
    text-align: justify;
    margin-left: 1em;
}
.footnote{
    font-size: 0.95em;
    line-height: 1.8em;
    font-family: "ZY-KAITI","kt";
    margin: 0 0 0 0em;
    text-indent: -1em;
}
a{color: black;}

.duokan-image-single {  
     text-align: center;
     text-indent: 0em;
     duokan-text-indent: 0em;
     margin: 1.5em 0;
}
.duokan-image-maintitle {
	  font-family: "ZY-KAITI","kt";
	  font-size: 0.9em;
     font-weight: normal;
     text-align: center;
     duokan-text-indent: 0em;
     text-indent: 0em;
     margin: 0.5em 0 0.5em 0;
     color: #412938;
}
div.red {
    border: solid 1px #a3adaf;
    margin: 0.5em;
    padding:0.5em; 
}'''
        
        with open(os.path.join(self.styles_dir, 'f11.css'), 'w', encoding='utf-8') as f:
            f.write(css_content)
    
    def _process_images(self):
        """处理图片文件"""
        if not os.path.exists(self.images_dir):
            return
        
        # 重命名图片为统一格式
        image_files = [f for f in os.listdir(self.images_dir) 
                      if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        
        for i, old_name in enumerate(sorted(image_files)):
            ext = os.path.splitext(old_name)[1].lower()
            if ext == '.jpeg':
                ext = '.jpg'
            new_name = f'f{i+2}{ext}'
            
            old_path = os.path.join(self.images_dir, old_name)
            new_path = os.path.join(self.images_dir, new_name)
            
            if old_path != new_path:
                shutil.move(old_path, new_path)
    
    def _generate_opf(self):
        """生成新的 OPF 文件"""
        # 获取所有文件
        text_files = sorted([f for f in os.listdir(self.text_dir) if f.endswith('.xhtml')])
        image_files = sorted([f for f in os.listdir(self.images_dir) if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))])
        font_files = sorted([f for f in os.listdir(self.fonts_dir) if f.endswith(('.ttf', '.otf'))])
        
        # 构建 manifest
        manifest_items = []
        spine_items = []
        
        # 添加 CSS
        manifest_items.append('    <item id="f8" href="Styles/f8.css" media-type="text/css"/>')
        manifest_items.append('    <item id="f11" href="Styles/f11.css" media-type="text/css"/>')
        
        # 添加文本文件
        for i, f in enumerate(text_files):
            file_id = f.replace('.xhtml', '')
            manifest_items.append(f'    <item id="{file_id}" href="Text/{f}" media-type="application/xhtml+xml"/>')
            spine_items.append(f'    <itemref idref="{file_id}"/>')
        
        # 添加图片
        for i, f in enumerate(image_files):
            file_id = f.replace('.', '')
            ext = os.path.splitext(f)[1].lower()
            if ext == '.jpg' or ext == '.jpeg':
                media_type = 'image/jpeg'
            elif ext == '.png':
                media_type = 'image/png'
            elif ext == '.gif':
                media_type = 'image/gif'
            else:
                media_type = 'image/jpeg'
            manifest_items.append(f'    <item id="{file_id}" href="Images/{f}" media-type="{media_type}"/>')
        
        # 添加字体
        for i, f in enumerate(font_files):
            file_id = f.replace('.', '')
            manifest_items.append(f'    <item id="{file_id}" href="Fonts/{f}" media-type="application/x-font-ttf"/>')
        
        # 添加 NCX
        manifest_items.append('    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
        
        # 生成 OPF 内容
        opf_content = f'''<?xml version='1.0' encoding='UTF-8'?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="duokan-book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>{self.metadata['title']}</dc:title>
    <dc:creator>{self.metadata['author']}</dc:creator>
    <dc:language>{self.metadata['language']}</dc:language>
    <dc:identifier id="duokan-book-id">{self.metadata['identifier'] or '1212'}</dc:identifier>
    <meta name="cover" content="f2"/>
    <meta content="0.9.10" name="Sigil version"/>
    <dc:date xmlns:opf="http://www.idpf.org/2007/opf" opf:event="modification">{datetime.now().strftime("%Y-%m-%d")}</dc:date>
    <meta content="DK-SONGTI" name="duokan-body-font"/>
  </metadata>
  <manifest>
{chr(10).join(manifest_items)}
  </manifest>
  <spine toc="ncx">
{chr(10).join(spine_items)}
  </spine>
  <guide>
    <reference type="cover" title="Cover" href="Text/f3.xhtml"/>
  </guide>
</package>'''
        
        with open(os.path.join(self.oebps_dir, 'content.opf'), 'w', encoding='utf-8') as f:
            f.write(opf_content)
    
    def _generate_ncx(self):
        """生成 NCX 目录文件"""
        # 获取文本文件列表
        text_files = sorted([f for f in os.listdir(self.text_dir) if f.endswith('.xhtml')])
        
        # 生成 navPoint
        nav_points = []
        for i, f in enumerate(text_files, 1):
            file_id = f.replace('.xhtml', '')
            # 尝试获取标题
            title = f'Chapter {i}'
            try:
                with open(os.path.join(self.text_dir, f), 'r', encoding='utf-8') as fp:
                    content = fp.read()
                    match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
                    if match:
                        title = match.group(1)
            except:
                pass
            
            nav_points.append(f'''    <navPoint id="navPoint-{i}" playOrder="{i}">
      <navLabel>
        <text>{title}</text>
      </navLabel>
      <content src="Text/{f}"/>
    </navPoint>''')
        
        # 生成 NCX 内容
        ncx_content = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{self.metadata['identifier'] or ''}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>{self.metadata['title']}</text>
  </docTitle>
  <navMap>
{chr(10).join(nav_points)}
  </navMap>
</ncx>'''
        
        with open(os.path.join(self.oebps_dir, 'toc.ncx'), 'w', encoding='utf-8') as f:
            f.write(ncx_content)
    
    def _repack_epub(self, output_path: str):
        """重新打包 EPUB"""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 添加 mimetype（不压缩）
            mimetype_path = os.path.join(self.work_dir, 'mimetype')
            if os.path.exists(mimetype_path):
                zf.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
            else:
                zf.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            
            # 添加其他文件
            for root, dirs, files in os.walk(self.work_dir):
                for f in files:
                    if f == 'mimetype':
                        continue
                    
                    file_path = os.path.join(root, f)
                    arcname = os.path.relpath(file_path, self.work_dir)
                    zf.write(file_path, arcname)


# ==================== RyuriCore 主类 ====================

class RyuriCore:
    """RyuriCore 核心类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config_manager = ConfigManager(config)
        self.config = self.config_manager.config
    
    def clean(self, input_path: str, output_path: str, target_platform: str = "generic", **kwargs) -> bool:
        """
        精排版清洗 EPUB 文件
        
        Args:
            input_path: 输入 EPUB 文件路径
            output_path: 输出 EPUB 文件路径
            target_platform: 目标平台 - "duokan"(多看), "zhangyue"(掌阅), "kindle"(Send to Kindle), "generic"(通用)
        """
        cleaner = EPUBCleaner(target_platform=target_platform)
        return cleaner.clean(input_path, output_path)


# ==================== 命令行入口 ====================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RyuriCore - 核心电子书处理工具')
    parser.add_argument('command', choices=['clean'],
                        help='要执行的命令')
    parser.add_argument('input_path', help='输入文件路径')
    parser.add_argument('output_path', help='输出文件路径')
    parser.add_argument('--platform', '-p', default='generic',
                        choices=['generic', 'duokan', 'zhangyue', 'kindle'],
                        help='精排版目标平台 (默认: generic)')
    
    args = parser.parse_args()
    
    core = RyuriCore()
    
    if args.command == 'clean':
        success = core.clean(args.input_path, args.output_path, target_platform=args.platform)
    
    sys.exit(0 if success else 1)
