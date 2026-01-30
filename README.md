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

### 3. EPUB 加密/解密
支持与 epub_tool 完全兼容的加密解密功能：

- **文件加密**：使用 MD5 哈希和文件名混淆算法保护 EPUB 内容
- **文件解密**：支持解密受保护的 EPUB 文件
- **字体加密**：支持字体文件的特殊加密处理
- **双向兼容**：与 epub_tool 生成的加密文件完全兼容

### 4. 电子书格式转换
支持多种电子书格式之间的互相转换：

- **EPUB 转换**：支持 EPUB 2.0/3.0 格式转换
- **MOBI/AZW3 转换**：支持 Kindle 格式的生成
- **FB2 转换**：支持 FictionBook 格式
- **批量处理**：支持批量文件转换，提高效率

### 5. EPUB 3.0 标准化
基于 EpubSanitizer 架构的标准化功能：

- **EPUB 2 升级**：自动将 EPUB 2.0 升级到 EPUB 3.0 标准
- **HTML5 适配**：将旧版 HTML 转换为 HTML5 标准
- **CSS 优化**：清理和优化 CSS 样式表
- **隐私清理**：自动清理阅读器元数据和个人信息
- **多过滤器链**：支持多个过滤器链式处理
- **多线程处理**：利用多线程提升处理速度

### 6. 文件系统抽象
- **内存文件系统 (MemFS)**：高性能内存操作，适合批量处理
- **磁盘文件系统 (DiskFS)**：直接操作磁盘文件，适合大文件
- **XML 缓存机制**：自动缓存解析后的 XML，提升性能

### 7. 配置管理
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
git clone https://github.com/Asteroidmple/Ryuri.git
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

#### EPUB 加密/解密
```bash
# 加密 EPUB 文件
python RyuriCore/RyuriCore.py encrypt input.epub output_encrypted.epub --password your_password

# 解密 EPUB 文件
python RyuriCore/RyuriCore.py decrypt input_encrypted.epub output_decrypted.epub --password your_password

# 字体加密
python RyuriCore/RyuriCore.py encrypt-fonts input.epub output_fonts_encrypted.epub
```

#### 电子书格式转换
```bash
# EPUB 转 MOBI
python RyuriCore/RyuriCore.py convert input.epub output.mobi --output-format mobi

# EPUB 转 AZW3
python RyuriCore/RyuriCore.py convert input.epub output.azw3 --output-format azw3

# EPUB 转 FB2
python RyuriCore/RyuriCore.py convert input.epub output.fb2 --output-format fb2

# MOBI 转 EPUB
python RyuriCore/RyuriCore.py convert input.mobi output.epub --output-format epub
```

#### EPUB 3.0 标准化
```bash
# 标准化 EPUB（升级到 EPUB 3.0）
python RyuriCore/RyuriCore.py sanitize input.epub output_sanitized.epub

# 标准化并清理隐私数据
python RyuriCore/RyuriCore.py sanitize input.epub output_clean.epub --filters privacy,metadata

# 标准化并优化 CSS
python RyuriCore/RyuriCore.py sanitize input.epub output_optimized.epub --optimize-css
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

# EPUB 加密/解密
from RyuriCore.RyuriCore import EPUBEncryptor

# 创建加密器
encryptor = EPUBEncryptor(password='your_password')

# 加密 EPUB
encryptor.encrypt('input.epub', 'output_encrypted.epub')

# 解密 EPUB
encryptor.decrypt('input_encrypted.epub', 'output_decrypted.epub')

# 字体加密
encryptor.encrypt_fonts('input.epub', 'output_fonts_encrypted.epub')

# 电子书格式转换
from RyuriCore.RyuriCore import EbookConverter

# 创建转换器
converter = EbookConverter(
    output_format='mobi',  # 可选: 'epub', 'mobi', 'azw3', 'fb2'
    input_profile='default',
    output_profile='kindle'
)

# 执行转换
converter.convert('input.epub', 'output.mobi')

# EPUB 3.0 标准化
from RyuriCore.RyuriCore import EPUBSanitizer, SanitizerConfig

# 创建配置
sanitizer_config = SanitizerConfig(
    filters=['default', 'privacy'],  # 过滤器列表
    epub_version='3.0',              # 目标 EPUB 版本
    threads='multi',                 # 多线程模式
    optimize_css=True,               # 优化 CSS
    remove_metadata=True             # 移除隐私元数据
)

# 创建标准化器
sanitizer = EPUBSanitizer(config=sanitizer_config)

# 执行标准化
sanitizer.sanitize('input.epub', 'output_sanitized.epub')

# 批量处理
from RyuriCore.RyuriCore import BatchProcessor

# 创建批处理器
batch = BatchProcessor(
    processor='sanitizer',  # 可选: 'cleaner', 'encryptor', 'converter', 'sanitizer'
    config={'target_platform': 'duokan'}
)

# 添加任务
batch.add_task('input1.epub', 'output1.epub')
batch.add_task('input2.epub', 'output2.epub')
batch.add_task('input3.epub', 'output3.epub')

# 执行批量处理
batch.process()
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
    },
    'encryptor': {
        'enabled': True,
        'algorithm': 'md5',           # 加密算法
        'obfuscate_filenames': True,  # 混淆文件名
        'encrypt_fonts': True         # 加密字体文件
    },
    'converter': {
        'verbose': 1,                 # 详细输出级别
        'input_profile': 'default',   # 输入配置文件
        'output_profile': 'kindle',   # 输出配置文件
        'preserve_cover': True,       # 保留封面
        'embed_fonts': False          # 嵌入字体
    },
    'sanitizer': {
        'enabled': True,
        'filters': 'default,privacy', # 过滤器列表
        'threads': 'multi',           # 线程模式
        'epub_ver': '3.0',            # 目标 EPUB 版本
        'sanitize_ncx': True,         # 清理 NCX
        'correct_mime': True,         # 修正 MIME 类型
        'optimize_css': True,         # 优化 CSS
        'remove_metadata': True,      # 移除隐私元数据
        'publisher_mode': False       # 出版商模式
    }
}

# 使用自定义配置初始化
core = RyuriCore(config=config)
```

#### 加密/解密高级配置
```python
from RyuriCore.RyuriCore import EPUBEncryptor, EncryptorConfig

# 创建加密配置
encryptor_config = EncryptorConfig(
    password='your_password',
    algorithm='md5',              # 加密算法: 'md5', 'sha256'
    obfuscate_filenames=True,     # 是否混淆文件名
    encrypt_fonts=True,           # 是否加密字体
    encrypt_images=False,         # 是否加密图片
    compatibility='epub_tool'     # 兼容性模式: 'epub_tool', 'ryuri'
)

# 创建加密器
encryptor = EPUBEncryptor(config=encryptor_config)

# 加密
encryptor.encrypt('input.epub', 'output.epub')

# 解密
encryptor.decrypt('input.epub', 'output.epub')
```

#### 格式转换高级配置
```python
from RyuriCore.RyuriCore import EbookConverter, ConverterConfig

# 创建转换配置
converter_config = ConverterConfig(
    output_format='mobi',         # 输出格式: 'epub', 'mobi', 'azw3', 'fb2'
    input_profile='default',      # 输入配置文件
    output_profile='kindle',      # 输出配置文件
    preserve_cover=True,          # 保留封面
    embed_fonts=False,            # 嵌入字体
    compress_images=True,         # 压缩图片
    image_quality=85,             # 图片质量 (0-100)
    max_image_size=1024,          # 最大图片尺寸
    table_of_contents=True,       # 生成目录
    metadata_handling='preserve'  # 元数据处理: 'preserve', 'remove', 'update'
)

# 创建转换器
converter = EbookConverter(config=converter_config)

# 执行转换
converter.convert('input.epub', 'output.mobi')
```

#### 标准化高级配置
```python
from RyuriCore.RyuriCore import EPUBSanitizer, SanitizerConfig

# 创建标准化配置
sanitizer_config = SanitizerConfig(
    # 基础配置
    epub_version='3.0',           # 目标 EPUB 版本: '2.0', '3.0'
    threads='multi',              # 线程模式: 'single', 'multi'
    
    # 过滤器配置
    filters=['default', 'privacy', 'metadata', 'css'],
    # 可选过滤器:
    # - 'default': 默认清理
    # - 'privacy': 清理隐私数据
    # - 'metadata': 清理元数据
    # - 'css': 优化 CSS
    # - 'html': 优化 HTML
    # - 'fonts': 优化字体
    # - 'images': 优化图片
    
    # 处理选项
    sanitize_ncx=True,            # 清理 NCX 文件
    correct_mime=True,            # 修正 MIME 类型
    xml_cache=True,               # 启用 XML 缓存
    
    # 优化选项
    optimize_css=True,            # 优化 CSS
    optimize_html=True,           # 优化 HTML
    minify_css=False,             # 压缩 CSS
    minify_html=False,            # 压缩 HTML
    
    # 隐私选项
    remove_metadata=True,         # 移除隐私元数据
    remove_reading_data=True,     # 移除阅读数据
    remove_annotations=False,     # 移除注释
    
    # 高级选项
    publisher_mode=False,         # 出版商模式
    epub3_guess_toc=False,        # 猜测目录
    epub3_correct_spine=True,     # 修正 spine
    compress=0                    # 压缩级别 (0-9)
)

# 创建标准化器
sanitizer = EPUBSanitizer(config=sanitizer_config)

# 执行标准化
sanitizer.sanitize('input.epub', 'output.epub')

# 批量标准化
sanitizer.sanitize_batch([
    ('input1.epub', 'output1.epub'),
    ('input2.epub', 'output2.epub'),
    ('input3.epub', 'output3.epub')
])
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
        'enabled': True,           # 是否启用加密
        'algorithm': 'md5',        # 加密算法: 'md5', 'sha256'
        'obfuscate_filenames': True,  # 是否混淆文件名
        'encrypt_fonts': True,     # 是否加密字体
        'encrypt_images': False,   # 是否加密图片
        'compatibility': 'epub_tool'  # 兼容性模式
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
        'compress': 0,                 # 压缩级别
        'optimize_css': True,          # 是否优化 CSS
        'optimize_html': True,         # 是否优化 HTML
        'remove_metadata': True,       # 是否移除隐私元数据
        'remove_reading_data': True    # 是否移除阅读数据
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

### 加密/解密配置 (EncryptorConfig)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `password` | str | 必填 | 加密密码 |
| `algorithm` | str | 'md5' | 加密算法: 'md5', 'sha256' |
| `obfuscate_filenames` | bool | True | 是否混淆文件名 |
| `encrypt_fonts` | bool | True | 是否加密字体文件 |
| `encrypt_images` | bool | False | 是否加密图片文件 |
| `compatibility` | str | 'epub_tool' | 兼容性模式: 'epub_tool', 'ryuri' |

### 格式转换配置 (ConverterConfig)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `output_format` | str | 'epub' | 输出格式: 'epub', 'mobi', 'azw3', 'fb2' |
| `input_profile` | str | 'default' | 输入设备配置文件 |
| `output_profile` | str | 'default' | 输出设备配置文件 |
| `preserve_cover` | bool | True | 是否保留封面 |
| `embed_fonts` | bool | False | 是否嵌入字体 |
| `compress_images` | bool | True | 是否压缩图片 |
| `image_quality` | int | 85 | 图片质量 (0-100) |
| `max_image_size` | int | 1024 | 最大图片尺寸 |
| `table_of_contents` | bool | True | 是否生成目录 |
| `metadata_handling` | str | 'preserve' | 元数据处理: 'preserve', 'remove', 'update' |

### 标准化配置 (SanitizerConfig)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `epub_version` | str | '3.0' | 目标 EPUB 版本: '2.0', '3.0' |
| `threads` | str | 'multi' | 线程模式: 'single', 'multi' |
| `filters` | list | ['default'] | 过滤器列表 |
| `sanitize_ncx` | bool | True | 是否清理 NCX 文件 |
| `correct_mime` | bool | True | 是否修正 MIME 类型 |
| `xml_cache` | bool | True | 是否启用 XML 缓存 |
| `optimize_css` | bool | True | 是否优化 CSS |
| `optimize_html` | bool | True | 是否优化 HTML |
| `minify_css` | bool | False | 是否压缩 CSS |
| `minify_html` | bool | False | 是否压缩 HTML |
| `remove_metadata` | bool | True | 是否移除隐私元数据 |
| `remove_reading_data` | bool | True | 是否移除阅读数据 |
| `remove_annotations` | bool | False | 是否移除注释 |
| `publisher_mode` | bool | False | 是否启用出版商模式 |
| `epub3_guess_toc` | bool | False | 是否猜测目录 |
| `epub3_correct_spine` | bool | True | 是否修正 spine |
| `compress` | int | 0 | 压缩级别 (0-9) |

#### 过滤器说明

| 过滤器 | 说明 |
|--------|------|
| `default` | 默认清理，包括修复常见错误 |
| `privacy` | 清理隐私数据，如阅读进度、书签等 |
| `metadata` | 清理和标准化元数据 |
| `css` | 优化和清理 CSS 样式表 |
| `html` | 优化和清理 HTML 结构 |
| `fonts` | 优化字体文件和引用 |
| `images` | 优化图片文件 |
| `ncx` | 清理和修复 NCX 目录文件 |
| `opf` | 清理和修复 OPF 包文件 |

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

### EPUBEncryptor 类

EPUB 加密/解密器，支持与 epub_tool 兼容的加密算法。

#### 构造函数
```python
EPUBEncryptor(password: str, config: Optional[EncryptorConfig] = None)
```

**参数：**
- `password` (str): 加密/解密密码
- `config` (EncryptorConfig, optional): 加密配置

#### 主要方法

##### encrypt
```python
encrypt(input_path: str, output_path: str) -> bool
```
加密 EPUB 文件。

**参数：**
- `input_path` (str): 输入 EPUB 文件路径
- `output_path` (str): 输出加密文件路径

**返回：**
- `bool`: 是否成功

##### decrypt
```python
decrypt(input_path: str, output_path: str) -> bool
```
解密 EPUB 文件。

**参数：**
- `input_path` (str): 输入加密文件路径
- `output_path` (str): 输出解密文件路径

**返回：**
- `bool`: 是否成功

##### encrypt_fonts
```python
encrypt_fonts(input_path: str, output_path: str) -> bool
```
仅加密字体文件。

**参数：**
- `input_path` (str): 输入 EPUB 文件路径
- `output_path` (str): 输出文件路径

**返回：**
- `bool`: 是否成功

### EbookConverter 类

电子书格式转换器，支持多种格式之间的互相转换。

#### 构造函数
```python
EbookConverter(
    output_format: str = 'epub',
    input_profile: str = 'default',
    output_profile: str = 'default',
    config: Optional[ConverterConfig] = None
)
```

**参数：**
- `output_format` (str): 输出格式 ('epub', 'mobi', 'azw3', 'fb2')
- `input_profile` (str): 输入设备配置文件
- `output_profile` (str): 输出设备配置文件
- `config` (ConverterConfig, optional): 转换配置

#### 主要方法

##### convert
```python
convert(input_path: str, output_path: str) -> bool
```
执行格式转换。

**参数：**
- `input_path` (str): 输入文件路径
- `output_path` (str): 输出文件路径

**返回：**
- `bool`: 是否成功

**示例：**
```python
converter = EbookConverter(
    output_format='mobi',
    output_profile='kindle'
)
converter.convert('input.epub', 'output.mobi')
```

### EPUBSanitizer 类

EPUB 标准化器，用于将 EPUB 升级到 3.0 标准并清理优化。

#### 构造函数
```python
EPUBSanitizer(config: Optional[SanitizerConfig] = None)
```

**参数：**
- `config` (SanitizerConfig, optional): 标准化配置

#### 主要方法

##### sanitize
```python
sanitize(input_path: str, output_path: str) -> bool
```
执行标准化处理。

**参数：**
- `input_path` (str): 输入 EPUB 文件路径
- `output_path` (str): 输出文件路径

**返回：**
- `bool`: 是否成功

##### sanitize_batch
```python
sanitize_batch(tasks: List[Tuple[str, str]]) -> List[bool]
```
批量标准化处理。

**参数：**
- `tasks` (list): 任务列表，每个任务为 (input_path, output_path) 元组

**返回：**
- `list`: 每个任务的处理结果

**示例：**
```python
config = SanitizerConfig(
    epub_version='3.0',
    filters=['default', 'privacy', 'css'],
    threads='multi'
)
sanitizer = EPUBSanitizer(config=config)
sanitizer.sanitize('input.epub', 'output.epub')
```

### BatchProcessor 类

批量处理器，用于批量处理多个文件。

#### 构造函数
```python
BatchProcessor(
    processor: str,
    config: Optional[Dict[str, Any]] = None,
    max_workers: int = 4
)
```

**参数：**
- `processor` (str): 处理器类型 ('cleaner', 'encryptor', 'converter', 'sanitizer')
- `config` (dict, optional): 处理器配置
- `max_workers` (int): 最大并行工作线程数

#### 主要方法

##### add_task
```python
add_task(input_path: str, output_path: str, **kwargs) -> None
```
添加处理任务。

**参数：**
- `input_path` (str): 输入文件路径
- `output_path` (str): 输出文件路径
- `**kwargs`: 额外参数

##### process
```python
process() -> List[bool]
```
执行所有任务。

**返回：**
- `list`: 每个任务的处理结果

**示例：**
```python
batch = BatchProcessor(processor='sanitizer', max_workers=4)
batch.add_task('input1.epub', 'output1.epub')
batch.add_task('input2.epub', 'output2.epub')
batch.add_task('input3.epub', 'output3.epub')
results = batch.process()
```

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
│   └── RyuriCore.py      # 核心功能实现
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

### v1.1.0
- 新增 EPUB 加密/解密功能
  - 支持 MD5/SHA256 加密算法
  - 支持文件名混淆
  - 支持字体文件加密
  - 与 epub_tool 完全兼容
- 新增电子书格式转换功能
  - 支持 EPUB/MOBI/AZW3/FB2 互转
  - 支持设备配置文件
  - 支持图片压缩和优化
- 新增 EPUB 3.0 标准化功能
  - 支持 EPUB 2.0 升级到 3.0
  - 支持 HTML5 适配
  - 支持多过滤器链式处理
  - 支持隐私数据清理
- 新增批量处理功能
  - 支持多线程并行处理
  - 支持任务队列管理

### v1.0.0
- 初始版本发布
- 实现 EPUB 精排版清洗功能
- 支持多看、掌阅、Kindle 三平台适配
- 实现 KoboSpan 文本追踪系统
- 实现弹出式脚注系统

## 联系方式

- GitHub: [https://github.com/Asteroidmple/Ryuri](https://github.com/Asteroidmple/Ryuri)
