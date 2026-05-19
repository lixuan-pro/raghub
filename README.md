# RAGHub

RAGHub 是一个面向本地文档的检索增强问答系统，目标是逐步完成文档导入、文本切块、检索召回、问答生成与评测展示的完整链路。

当前项目已完成 Week 1 工程骨架收口，并进入 Week 2：文档导入与预处理阶段。当前已完成 TXT/PDF 最小读取、统一 `Document` 对象、固定长度 + overlap 文本切块，并能通过预处理脚本生成可查看的 chunk 预览文件。

## Current Stage

当前阶段目标是完成本地文档导入与预处理的最小输入链路，目前已完成：

- TXT 文档基础读取
- PDF 文档按页读取
- TXT/PDF 统一输出为 `list[Document]`
- 固定长度 + overlap 文本切块
- `Document` 级切块输出
- 预处理链路脚本
- chunk 预览结果落盘

当前暂不进入 DOCX loader、metadata 扩展、token 切块、语义切块、embedding、向量检索和 `/chat` 问答接口。

## Features

当前已完成：

- FastAPI 最小后端服务
- `/health` 健康检查接口
- `/version` 版本信息接口
- `.env.example` 配置模板
- `app/core/config.py` 配置模块
- `app/core/logger.py` 日志模块
- FastAPI lifespan 启动日志
- pytest 基础接口测试
- `app/loaders/txt_loader.py` TXT 文档读取模块
- `data/raw/sample.txt` 最小 TXT 样本文档
- `tests/test_txt_loader.py` TXT loader 测试
- `pypdf` PDF 读取依赖
- `app/loaders/pdf_loader.py` PDF 文档读取模块
- `data/raw/sample.pdf` 最小 PDF 样本文档
- `tests/test_pdf_loader.py` PDF loader 测试
- `app/models/document.py` 最小 Document 数据对象
- `load_txt_documents()` TXT 文档统一包装函数
- `load_pdf_documents()` PDF 文档统一包装函数
- `tests/test_document_loaders.py` Document 输出测试
- `app/processors/text_chunker.py` 文本切块模块
- `chunk_text()` 固定长度 + overlap 纯文本切块函数
- `chunk_documents()` Document 级切块函数
- `tests/test_text_chunker.py` 文本切块测试
- `scripts/build_chunks_demo.py` 最小预处理链路脚本
- `data/processed/chunks_preview.jsonl` chunk 预览输出文件
- `eval/queries.jsonl` Week 2 最小评测占位样例
- README 与周志
- 论文材料占位目录 `docs/thesis/`
- GitHub main / develop 分支管理

## Project Structure

```text
raghub/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ core/
│  │  ├─ __init__.py
│  │  ├─ config.py
│  │  └─ logger.py
│  ├─ loaders/
│  │  ├─ __init__.py
│  │  ├─ txt_loader.py
│  │  └─ pdf_loader.py
│  ├─ models/
│  │  ├─ __init__.py
│  │  └─ document.py
│  └─ processors/
│     ├─ __init__.py
│     └─ text_chunker.py
├─ data/
│  ├─ raw/
│  │  ├─ sample.txt
│  │  └─ sample.pdf
│  └─ processed/
│     └─ chunks_preview.jsonl
├─ tests/
│  ├─ test_health.py
│  ├─ test_txt_loader.py
│  ├─ test_pdf_loader.py
│  ├─ test_document_loaders.py
│  └─ test_text_chunker.py
├─ docs/
│  ├─ weekly_logs/
│  │  ├─ week1.md
│  │  └─ week2.md
│  ├─ thesis/
│  │  └─ README.md
│  └─ project_explanation_week1.md
├─ eval/
│  └─ queries.jsonl
├─ scripts/
│  └─ build_chunks_demo.py
├─ .env.example
├─ .gitignore
├─ README.md
└─ requirements.txt
```

## Environment

建议使用 Python 3.10+。

安装依赖：

```bash
pip install -r requirements.txt
```

## Configuration

项目使用 `.env.example` 作为配置模板。

当前配置项：

```env
APP_NAME=RAGHub
APP_VERSION=0.1.0
DEBUG=true
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=INFO
```

如需本地自定义配置，可复制一份 `.env`：

```bash
copy .env.example .env
```

`.env` 不应提交到 GitHub。

## Run

启动服务：

```bash
uvicorn app.main:app --reload
```

访问接口：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/version
```

预期结果：

```json
{"status":"ok"}
```

```json
{"version":"0.1.0"}
```

## TXT Loader

当前已实现最小 TXT 文档读取函数：

```python
from app.loaders.txt_loader import load_txt

content = load_txt("data/raw/sample.txt")
print(content)
```

当前 TXT loader 只负责读取本地 `.txt` 文件并返回字符串内容。

同时新增统一包装函数：

```python
from app.loaders.txt_loader import load_txt_documents

documents = load_txt_documents("data/raw/sample.txt")
print(documents)
```

`load_txt_documents()` 会返回 `list[Document]`，当前 TXT 文件会被包装成一个 `Document`。

暂不处理：

- metadata 扩展
- 批量导入
- 编码自动识别
- 复杂格式解析

## PDF Loader

当前已实现最小 PDF 文档读取函数：

```python
from app.loaders.pdf_loader import load_pdf

pages = load_pdf("data/raw/sample.pdf")
print(pages)
```

当前 PDF loader 按页提取文本，并返回 `list[str]`。

每个列表元素对应 PDF 中的一页文本内容。

同时新增统一包装函数：

```python
from app.loaders.pdf_loader import load_pdf_documents

documents = load_pdf_documents("data/raw/sample.pdf")
print(documents)
```

`load_pdf_documents()` 会把每一页 PDF 文本包装成一个 `Document`，并保留页码信息。

暂不处理：

- metadata 扩展
- 扫描版 PDF / OCR
- 批量导入
- 复杂版面解析

## Document Model

当前已新增最小版 `Document` 对象：

```python
from dataclasses import dataclass


@dataclass
class Document:
    content: str
    source: str
    file_type: str
    page: int | None = None
```

字段说明：

- `content`：文档内容
- `source`：原始文件路径
- `file_type`：文件类型，例如 `txt` 或 `pdf`
- `page`：页码，TXT 当前为 `None`，PDF 从第 1 页开始记录

当前 `Document` 对象的作用是统一 TXT 和 PDF 的输出结构，为后续文本切块提供统一输入。

## Text Chunker

当前已实现最小文本切块模块：

```python
from app.processors.text_chunker import chunk_text

chunks = chunk_text(
    text="abcdefghijklmnopqrstuvwxyz",
    chunk_size=10,
    overlap=2,
)
print(chunks)
```

`chunk_text()` 当前按字符长度进行固定长度切块，并支持 overlap。

同时支持 `Document` 级切块：

```python
from app.loaders.txt_loader import load_txt_documents
from app.processors.text_chunker import chunk_documents

documents = load_txt_documents("data/raw/sample.txt")
chunks = chunk_documents(documents, chunk_size=50, overlap=10)
print(len(chunks))
print(chunks[0].content)
```

`chunk_documents()` 会将 `list[Document]` 切分为更小的 `list[Document]`，并保留原始 `source`、`file_type` 和 `page` 信息。

暂不处理：

- `chunk_id`
- metadata 扩展
- token 切块
- 中文分词切块
- 语义切块
- 向量化
- 检索

## Preprocessing Demo

当前已新增最小预处理脚本：

```bash
python scripts/build_chunks_demo.py
```

该脚本会串联以下流程：

```text
data/raw/sample.txt
data/raw/sample.pdf
→ loader
→ list[Document]
→ chunk_documents()
→ data/processed/chunks_preview.jsonl
```

运行后会输出类似结果：

```text
txt documents: 1
pdf documents: 1
chunks: 7
output: data/processed/chunks_preview.jsonl
```

`chunks_preview.jsonl` 当前每行包含：

- `content`
- `source`
- `file_type`
- `page`

示例格式：

```json
{"content": "RAGHub is a local document question answering proj", "source": "data/raw/sample.txt", "file_type": "txt", "page": null}
```

该文件用于预览 Week 2 文档导入与预处理链路的阶段成果，暂不作为最终检索索引格式。

## Evaluation Placeholders

当前 `eval/queries.jsonl` 保存最小评测占位样例。

Week 1 已包含基础接口相关问题。  
Week 2 新增了基于样本文档内容的占位问题，用于后续检索评测扩展。

当前仍不是正式评测集，只作为后续检索命中测试和问答评测的最小起点。

## Test

运行测试：

```bash
python -m pytest
```

当前测试内容：

- `/health` 状态码和返回内容
- `/version` 状态码和版本字段
- TXT loader 能读取 `data/raw/sample.txt`
- TXT loader 返回内容为字符串
- TXT loader 返回内容包含指定关键词
- PDF loader 能读取 `data/raw/sample.pdf`
- PDF loader 返回内容为列表
- PDF loader 返回内容包含指定关键词
- TXT 能统一输出为 `list[Document]`
- PDF 能统一输出为 `list[Document]`
- PDF Document 保留页码信息
- `chunk_text()` 能完成固定长度切块
- `chunk_text()` 支持 overlap
- `chunk_text()` 对空字符串返回空列表
- `chunk_documents()` 能输出 chunk 后的 `list[Document]`
- `chunk_documents()` 保留原始 `source`、`file_type` 和 `page`

当前测试结果：

```text
10 passed
```

## Roadmap

接下来计划：

1. Week 1：工程骨架与基础设施【已完成】
   - FastAPI 最小服务
   - `/health` 和 `/version`
   - 配置模块
   - 日志模块
   - pytest 基础测试
   - README、周志、论文占位、评测占位和讲解稿

2. Week 2：文档导入与预处理【进行中】
   - TXT loader 最小版【已完成】
   - PDF loader 最小版【已完成】
   - 最小版 `Document` 对象【已完成】
   - 固定长度 + overlap 文本切块【已完成】
   - 预处理结果落盘与 chunk 预览【已完成】

3. 后续逐步实现
   - 评测样例扩展
   - embedding 最小向量化准备
   - 向量检索
   - RAG 问答接口
   - 评测与展示