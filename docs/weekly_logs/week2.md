# Week 2 - 文档导入阶段

## 本周目标

本周目标是进入 RAGHub 的文档导入阶段，先完成 TXT 和 PDF 两类文档的最小读取能力，为后续统一 Document 对象、文本切块和检索模块打基础。

## Day 4 - TXT Loader 最小闭环

### 今日目标

完成 TXT 文档导入的最小正向路径：给定一个 `.txt` 文件路径，程序可以成功读取文件内容，并通过 pytest 测试验证。

### 今日完成

- 新建 `app/loaders/` 目录，作为文档加载模块入口。
- 新建 `data/raw/sample.txt`，作为 TXT loader 的最小样本文档。
- 新建 `app/loaders/txt_loader.py`。
- 实现 `load_txt(path: str) -> str`，用于读取 TXT 文件内容。
- 新建 `tests/test_txt_loader.py`。
- 编写 TXT loader 最小测试，验证：
  - 能成功读取样本文档
  - 返回内容是字符串
  - 返回内容包含 `RAGHub` 和 `document loading`
- 运行 `python -m pytest`，结果为 `3 passed`。

### 当前边界

今天只完成 TXT 文件读取，不进入以下内容：

- PDF loader
- DOCX loader
- Document 对象
- 文本切块
- 批量导入
- 编码自动识别
- embedding
- 向量库
- `/chat`

### 当前理解

TXT loader 是 RAGHub 输入链路的第一步。  
它的作用不是完成 RAG，而是先验证系统可以从本地文档中读取原始文本。后续 PDF 导入、统一文档对象和文本切块都会建立在这个输入链路基础上。



---

## Day 5 - PDF Loader 最小闭环

### 今日目标

完成 PDF 文档导入的最小正向路径：给定一个 `.pdf` 文件路径，程序可以按页提取文本内容，并通过 pytest 测试验证。

### 今日完成

- 安装 `pypdf` 作为 PDF 文本读取依赖。
- 更新 `requirements.txt`，加入 `pypdf==6.11.0`。
- 新建 `app/loaders/pdf_loader.py`。
- 实现 `load_pdf(path: str) -> list[str]`，用于按页读取 PDF 文本。
- 新建 `data/raw/sample.pdf`，作为 PDF loader 的最小样本文档。
- 新建 `tests/test_pdf_loader.py`。
- 编写 PDF loader 最小测试，验证：
  - `load_pdf()` 返回列表
  - PDF 至少包含 1 页
  - 提取文本中包含 `RAGHub`
  - 提取文本中包含 `PDF loader`
  - 提取文本中包含 `page-based PDF text extraction`
- 运行 `python -m pytest`，结果为 `4 passed`。

### 当前边界

今天只完成 PDF 文件的按页文本读取，不进入以下内容：

- 统一 Document 对象
- TXT/PDF 统一接口抽象
- metadata 整理
- 文本切块
- `data/processed/`
- PDF OCR
- DOCX loader
- embedding
- 向量库
- `/chat`

### 当前理解

PDF loader 是 RAGHub 输入链路中的第二个文档加载模块。

与 TXT loader 直接返回字符串不同，PDF loader 当前返回 `list[str]`，每个元素对应一页提取出的文本。这样做是为了保留页级边界，方便后续设计统一 Document 对象、记录页码信息和进入文本切块流程。

当前 PDF loader 只处理可提取文本的普通 PDF，不处理扫描版 PDF 和 OCR。


---

## Day 6 - 统一 Document 对象最小闭环

### 今日目标

设计并落地最小版 `Document` 对象，让 TXT 和 PDF 两类文档都能被统一包装成 `list[Document]`，为后续文本切块提供统一输入。

### 今日完成

- 新建 `app/models/` 目录。
- 新建 `app/models/__init__.py`。
- 新建 `app/models/document.py`。
- 使用 `dataclass` 定义最小版 `Document` 对象。
- 当前 `Document` 包含 4 个字段：
  - `content: str`
  - `source: str`
  - `file_type: str`
  - `page: int | None = None`
- 保留原有 `load_txt(path: str) -> str`。
- 新增 `load_txt_documents(path: str) -> list[Document]`。
- 保留原有 `load_pdf(path: str) -> list[str]`。
- 新增 `load_pdf_documents(path: str) -> list[Document]`。
- 新建 `tests/test_document_loaders.py`。
- 编写 TXT 和 PDF 的统一 Document 输出测试。
- 运行 `python -m pytest`，结果为 `6 passed`。

### 当前边界

今天只完成统一输入对象，不进入以下内容：

- chunk 切块
- chunk overlap
- metadata 扩展
- title / author / time
- `data/processed/`
- eval 扩展
- DOCX loader
- embedding
- 向量库
- `/chat`

### 当前理解

`Document` 是 RAGHub 文档处理链路里的统一数据结构。

在 Day 4 和 Day 5 中，TXT 和 PDF 已经分别能够读取原始文本。Day 6 的作用是把不同文件格式的读取结果统一包装成 `Document` 列表，让后续切块模块不用关心原始文件来自 TXT 还是 PDF。

当前 `Document` 仍然是最小字段版，只保留内容、来源、文件类型和页码信息。后续如果需要 metadata、标题、作者、时间等字段，再逐步扩展。



---

## Day 7 - 文本切块最小闭环

### 今日目标

完成文本切块最小闭环：将 `Document` 列表按照固定长度和 overlap 切成更小的文本块，并继续输出为 `list[Document]`，为后续检索模块做准备。

### 今日完成

- 新建 `app/processors/` 目录。
- 新建 `app/processors/__init__.py`。
- 新建 `app/processors/text_chunker.py`。
- 实现 `chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]`。
- 实现 `chunk_documents(documents: list[Document], chunk_size: int, overlap: int) -> list[Document]`。
- 新建 `tests/test_text_chunker.py`。
- 编写文本切块测试，验证：
  - 长文本可以被切成多个块
  - 每个 chunk 长度不超过 `chunk_size`
  - overlap 能正常生效
  - 空字符串返回空列表
  - `chunk_documents()` 能保留原始 `source`、`file_type` 和 `page`
- 运行 `python -m pytest`，结果为 `10 passed`。
- 使用 `sample.txt` 实际跑通一次最小切块流程：
  - `load_txt_documents()`
  - `chunk_documents()`
  - 输出结果：`documents: 1`，`chunks: 4`

### 当前边界

今天只完成固定长度 + overlap 的最小切块策略，不进入以下内容：

- `chunk_id`
- metadata 扩展
- title / author / time
- token 切块
- 中文分词切块
- 语义切块
- embedding
- FAISS / 向量库
- BM25
- `/retrieve`
- `/chat`

### 当前理解

文本切块是 RAG 检索前处理的重要步骤。

Day 6 已经将 TXT/PDF 统一输出为 `list[Document]`。Day 7 在此基础上，让系统能够把较长的 `Document.content` 切成更小的片段，并继续保留 `source`、`file_type` 和 `page` 信息。

今天先选择固定长度 + overlap 的最小策略，是为了尽快跑通稳定的检索前处理链路。更复杂的 token 切块、语义切块和 metadata 扩展放到后续优化阶段。

