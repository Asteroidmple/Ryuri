# Ryuri

一个功能强大的电子书处理工具，专注于 EPUB 精排版和多平台适配。

## 功能特性

### 1. EPUB 精排版清洗
将排版结构混乱的 EPUB 源文件转换为精美的精排版电子书，支持以下特性：

- **KoboSpan 文本追踪系统**：为每个文本节点生成唯一 ID，支持阅读进度同步
- **弹出式脚注系统**：支持多看 duokan-footnote 格式，点击弹出注释内容
- **字体嵌入系统**：自动生成 @font-face 规则，支持多种中文字体
- **标准 OEBPS 结构**：使用 f{x}.xhtml 命名规范，符合行业标准
- **双 CSS 架构**：f8.css（字体定义）+ f11.css（排版样式）

### 2. 多平台适配
支持三种主流阅读平台的精排版标准：

| 平台 | 特性 |
|------|------|
| **多看 (Duokan)** | 完整 duokan-* 类支持，弹出式脚注图标，多看专用元数据 |
| **掌阅 (Zhangyue)** | 简化版本，优化排版结构 |
| **Kindle** | 标准 EPUB3 兼容版本，Send to Kindle 优化 |

### 3. 文件系统抽象
- **内存文件系统 (MemFS)**：高性能内存操作，适合批量处理
- **磁盘文件系统 (DiskFS)**：直接操作磁盘文件，适合大文件
- **XML 缓存机制**：自动缓存解析后的 XML，提升性能

### 4. 配置管理
三层配置优先级架构：
- 代码默认值
- 配置文件
- 运行时参数

## 安装

### 环境要求
- Python 3.7+
- 无需额外依赖（仅使用 Python 标准库）

### 安装步骤
```bash
# 克隆仓库
git clone https://github.com/yourusername/ryuri.git
cd ryuri

# 直接使用
python RyuriCore/RyuriCore.py --help
```

## 使用方法

### 命令行使用

#### 基本精排版清洗
```bash
# 通用精排版
python RyuriCore/RyuriCore.py clean input.epub output.epub

# 多看适配
python RyuriCore/RyuriCore.py clean input.epub output.epub --platform duokan

# 掌阅适配
python RyuriCore/RyuriCore.py clean input.epub output.epub --platform zhangyue

# Kindle 适配
python RyuriCore/RyuriCore.py clean input.epub output.epub --platform kindle
```

### Python API 使用

```python
from RyuriCore.RyuriCore import RyuriCore, EPUBCleaner

# 使用 RyuriCore 主类
core = RyuriCore()

# 精排版清洗
success = core.clean(
    input_path='input.epub',
    output_path='output.epub',
    target_platform='duokan'  # 可选: 'generic', 'duokan', 'zhangyue', 'kindle'
)

# 使用 EPUBCleaner 直接
 cleaner = EPUBCleaner(target_platform='duokan')
success = cleaner.clean('input.epub', 'output.epub')
```

### 高级用法

#### 自定义配置
```python
from RyuriCore.RyuriCore import RyuriCore, ConfigManager

# 创建自定义配置
config = {
    'cleaner': {
        'enabled': True,
        'preserve_original': False,
        'add_kobospan': True,
        'process_footnotes': True
    }
}

# 使用自定义配置初始化
core = RyuriCore(config=config)
```

#### 文件系统操作
```python
from RyuriCore.RyuriCore import MemFS, DiskFS

# 内存文件系统
mem_fs = MemFS()
mem_fs.import_from_zip('input.epub')

# 读取文件
content = mem_fs.read_string('OEBPS/Text/chapter1.xhtml')
xml_root = mem_fs.read_xml('OEBPS/content.opf')

# 写入文件
mem_fs.write_string('OEBPS/Text/new.xhtml', '<html>...</html>')
mem_fs.write_xml('OEBPS/content.opf', xml_root, is_opf=True)

# 导出到 ZIP
mem_fs.export_to_zip('output.epub')

# 磁盘文件系统
disk_fs = DiskFS('/path/to/epub')
files = disk_fs.get_all_files()
```

## 配置参数

### 配置管理器 (ConfigManager)

配置采用三层优先级架构：
1. **代码默认值**：内建默认配置
2. **配置文件**：JSON 格式配置文件
3. **运行时参数**：API 调用时传入的参数

#### 默认配置结构
```python
{
    'converter': {
        'verbose': 0,              # 详细输出级别 (0-3)
        'debug_pipeline': None,     # 调试管道
        'input_profile': 'default', # 输入配置文件
        'output_profile': 'default' # 输出配置文件
    },
    'encryptor': {
        'enabled': True            # 是否启用加密
    },
    'sanitizer': {
        'filters': 'default,privacy',  # 过滤器列表
        'threads': 'multi',            # 线程模式
        'cache': 'ram',                # 缓存模式
        'epub_ver': 0,                 # EPUB 版本
        'sanitize_ncx': True,          # 是否清理 NCX
        'correct_mime': True,          # 是否修正 MIME 类型
        'xml_cache': True,             # 是否启用 XML 缓存
        'publisher_mode': False,       # 出版商模式
        'epub3_guess_toc': False,      # 是否猜测目录
        'epub3_correct_spine': True,   # 是否修正 spine
        'compress': 0                  # 压缩级别
    },
    'reader': {
        'enabled': True             # 是否启用阅读器
    },
    'editor': {
        'enabled': True             # 是否启用编辑器
    },
    'cleaner': {
        'enabled': True             # 是否启用清洗器
    },
    'plugins': {
        'enabled': True,            # 是否启用插件
        'paths': []                 # 插件路径列表
    }
}
```

#### 配置操作方法
```python
from RyuriCore.RyuriCore import ConfigManager

# 创建配置管理器
config = ConfigManager()

# 获取配置值
value = config.get('sanitizer', 'threads', default='single')

# 设置配置值
config.set('sanitizer', 'threads', 'multi')

# 获取特定类型
int_value = config.get_int('converter', 'verbose')
bool_value = config.get_bool('sanitizer', 'xml_cache')
str_value = config.get_string('cleaner', 'enabled')
```

## API 文档

### EPUBCleaner 类

EPUB 精排版清洗器的核心类。

#### 构造函数
```python
EPUBCleaner(target_platform: str = "generic")
```

**参数：**
- `target_platform` (str): 目标平台
  - `"generic"` - 通用精排版
  - `"duokan"` - 多看适配
  - `"zhangyue"` - 掌阅适配
  - `"kindle"` - Kindle 适配

#### 主要方法

##### clean
```python
clean(input_path: str, output_path: str) -> bool
```
执行精排版清洗。

**参数：**
- `input_path` (str): 输入 EPUB 文件路径
- `output_path` (str): 输出 EPUB 文件路径

**返回：**
- `bool`: 是否成功

**示例：**
```python
cleaner = EPUBCleaner(target_platform='duokan')
success = cleaner.clean('input.epub', 'output.epub')
```

### RyuriCore 类

主入口类，整合所有功能。

#### 构造函数
```python
RyuriCore(config: Optional[Dict[str, Any]] = None)
```

**参数：**
- `config` (dict, optional): 自定义配置字典

#### 主要方法

##### clean
```python
clean(input_path: str, output_path: str, target_platform: str = "generic", **kwargs) -> bool
```
精排版清洗入口方法。

**参数：**
- `input_path` (str): 输入文件路径
- `output_path` (str): 输出文件路径
- `target_platform` (str): 目标平台
- `**kwargs`: 额外参数

### FileSystem 抽象类

文件系统抽象基类，提供统一的文件操作接口。

#### 主要方法

| 方法 | 说明 |
|------|------|
| `read_bytes(path)` | 读取文件字节 |
| `read_string(path, encoding)` | 读取文件字符串 |
| `read_xml(path)` | 读取并解析 XML |
| `write_bytes(path, data)` | 写入文件字节 |
| `write_string(path, content, encoding)` | 写入文件字符串 |
| `write_xml(path, element, encoding, is_opf, is_xhtml)` | 写入 XML 文件 |
| `delete_file(path)` | 删除文件 |
| `file_exists(path)` | 检查文件是否存在 |
| `get_all_files()` | 获取所有文件列表 |
| `get_sha256(path)` | 计算文件 SHA256 |

### MemFS 类

内存文件系统实现，适合高性能批量处理。

#### 特有方法
```python
# 从 ZIP 导入
mem_fs.import_from_zip('input.epub')

# 导出到 ZIP
mem_fs.export_to_zip('output.epub')
```

### DiskFS 类

磁盘文件系统实现，适合大文件处理。

#### 构造函数
```python
DiskFS(base_path: str)
```

**参数：**
- `base_path` (str): 基础目录路径

## 精排版特性详解

### 1. KoboSpan 文本追踪
为每个文本节点添加唯一 ID，格式为 `kobo.{段落号}.{句子号}`：

```html
<p>
  <span class="koboSpan" id="kobo.4.1">晚明江南地区，市镇这一聚落形态大规模发育...</span>
  <a class="duokan-footnote" epub:type="noteref" href="#B_745" id="A_745">
    <span class="koboSpan" id="kobo.6.1">
      <img alt="note" src="../Images/f13.png"/>
    </span>
  </a>
</p>
```

### 2. 弹出式脚注系统

#### 多看格式
```html
<!-- 正文中的脚注引用 -->
<a class="duokan-footnote" epub:type="noteref" href="#B_1" id="A_1">
  <span class="koboSpan" id="kobo.6.1">
    <img alt="note" src="../Images/f13.png"/>
  </span>
</a>

<!-- 脚注内容 -->
<aside epub:type="footnote" id="B_1">
  <ol class="duokan-footnote-content">
    <li class="duokan-footnote-item" value="1">
      <p class="footnote">脚注内容...</p>
    </li>
  </ol>
</aside>
```

### 3. 字体定义

#### f8.css - 字体定义文件
```css
@font-face {
    font-family: "st";
    src: url("../Fonts/st.ttf"),
         local("宋体"),
         local("DK-SONGTI"),
         local("STSongti");
}
@font-face {
    font-family: "kt";
    src: url("../Fonts/f81.ttf"),
         local("楷体"),
         local("DK-KAITI"),
         local("STKaiti");
}
/* ... 更多字体定义 ... */
```

### 4. 标准 HTML 结构
```html
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" 
      xmlns:epub="http://www.idpf.org/2007/ops" 
      xml:lang="zh-CN">
<head>
  <title>章节标题</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link href="../Styles/f8.css" type="text/css" rel="stylesheet"/>
  <link href="../Styles/f11.css" type="text/css" rel="stylesheet"/>
</head>
<body>
  <div id="book-columns">
    <div id="book-inner">
      <!-- 内容 -->
    </div>
  </div>
</body>
</html>
```

## 项目结构

```
Ryuri/
├── RyuriCore/
│   ├── RyuriCore.py      # 核心功能实现
│   └── example/          # 示例文件
│       ├── a.epub        # 源文件示例
│       ├── dk.epub       # 多看精排版示例
│       ├── zy.epub       # 掌阅精排版示例
│       └── stk.epub      # Kindle 精排版示例
├── README.md             # 本文件
└── LICENSE               # 许可证
```

## 兼容性

### 输入格式
- EPUB 2.0
- EPUB 3.0
- 带有 calibre 标记的 EPUB

### 输出格式
- 标准 EPUB 3.0
- 多看精排版 EPUB
- 掌阅精排版 EPUB
- Kindle 优化 EPUB

## 性能

- **内存占用**：低（使用流式处理）
- **CPU 使用**：低（纯 Python 实现，无复杂计算）
- **处理速度**：约 1-2 秒/本（取决于文件大小）

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0
- 初始版本发布
- 实现 EPUB 精排版清洗功能
- 支持多看、掌阅、Kindle 三平台适配
- 实现 KoboSpan 文本追踪系统
- 实现弹出式脚注系统

## 联系方式

- GitHub: [https://github.com/yourusername/ryuri](https://github.com/yourusername/ryuri)
- Email: your.email@example.com
