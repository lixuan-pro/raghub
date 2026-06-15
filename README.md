# RAGHub

RAGHub 是一个面向本地文档的检索增强问答系统，目标是逐步完成文档导入、文本切块、embedding、检索召回、问答生成与评测展示的完整链路。

当前项目已完成 Week 1 工程骨架、Week 2 文档导入与预处理链路，并进入 Week 3 embedding 与向量检索准备阶段。

当前已经支持：

- TXT/PDF 最小读取
- 统一 `Document` 对象
- 固定长度 + overlap 文本切块
- 预处理结果落盘为 `chunks_preview.jsonl`
- 本地 embedding baseline
- 将 chunks 转换为向量并保存为 `.npy`
- 内存版向量相似度 top-k 检索 baseline

当前已完成 FastAPI `/retrieve` 接口与最小 mock `/chat` 问答接口，暂未进入完整向量库、真实 LLM API、BM25、混合检索或生产级 RAG 生成阶段。

---

## Current Stage

当前阶段状态：

- Week 1：工程骨架与基础设施【已完成】
- Week 2：文档导入与预处理【已完成】
- Week 3：embedding baseline 与内存版向量检索 baseline【进行中】

当前已完成的主链路：

```text
原始 TXT / PDF 文档
→ loader 读取
→ Document 统一表示
→ 固定长度 + overlap 文本切块
→ chunks_preview.jsonl
→ embedding model
→ chunk_embeddings.npy
→ query embedding
→ cosine similarity
→ top-k chunks
```

当前重点是先完成本地检索 baseline，为后续 `/retrieve` API 和 RAG 问答接口打基础。

---

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
- `app/embeddings/local_embedder.py` 本地 embedding 模块
- `scripts/build_embeddings_demo.py` embedding 构建脚本
- `data/processed/chunk_embeddings.npy` chunk 向量矩阵
- `data/processed/chunk_embeddings_meta.json` embedding 元信息文件
- `app/retrievers/vector_retriever.py` 内存版向量相似度检索模块
- `scripts/retrieve_demo.py` 最小检索 demo 脚本
- `tests/test_vector_retriever.py` 向量相似度测试
- `eval/queries.jsonl` Week 1 / Week 2 最小评测占位样例
- `docs/design/preprocessing_pipeline.md` 文档导入与预处理链路设计说明
- `docs/design/embedding_baseline_plan.md` embedding baseline 准备说明
- `docs/weekly_logs/week1.md`
- `docs/weekly_logs/week2.md`
- `docs/weekly_logs/week3.md`
- 论文材料占位目录 `docs/thesis/`
- GitHub main / develop 分支管理

---

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
│  ├─ processors/
│  │  ├─ __init__.py
│  │  └─ text_chunker.py
│  ├─ embeddings/
│  │  ├─ __init__.py
│  │  └─ local_embedder.py
│  └─ retrievers/
│     ├─ __init__.py
│     └─ vector_retriever.py
├─ data/
│  ├─ raw/
│  │  ├─ sample.txt
│  │  └─ sample.pdf
│  └─ processed/
│     ├─ chunks_preview.jsonl
│     ├─ chunk_embeddings.npy
│     └─ chunk_embeddings_meta.json
├─ tests/
│  ├─ test_health.py
│  ├─ test_txt_loader.py
│  ├─ test_pdf_loader.py
│  ├─ test_document_loaders.py
│  ├─ test_text_chunker.py
│  └─ test_vector_retriever.py
├─ docs/
│  ├─ design/
│  │  ├─ preprocessing_pipeline.md
│  │  └─ embedding_baseline_plan.md
│  ├─ weekly_logs/
│  │  ├─ week1.md
│  │  ├─ week2.md
│  │  └─ week3.md
│  ├─ thesis/
│  │  └─ README.md
│  └─ project_explanation_week1.md
├─ eval/
│  └─ queries.jsonl
├─ scripts/
│  ├─ build_chunks_demo.py
│  ├─ build_embeddings_demo.py
│  └─ retrieve_demo.py
├─ .env.example
├─ .gitignore
├─ README.md
└─ requirements.txt
```

---

## Environment

建议使用 Python 3.10+。

安装依赖：

```bash
pip install -r requirements.txt
```

当前 embedding baseline 使用：

- `sentence-transformers`
- `BAAI/bge-base-zh-v1.5`

首次运行 embedding 或 retrieval demo 时，模型可能会从 Hugging Face 下载到本地缓存。

---

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

Windows / PowerShell：

```powershell
copy .env.example .env
```

macOS / Linux：

```bash
cp .env.example .env
```

`.env` 不应提交到 GitHub。

---

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

---

## TXT Loader

当前已实现最小 TXT 文档读取函数：

```python
from app.loaders.txt_loader import load_txt

content = load_txt("data/raw/sample.txt")
print(content)
```

同时支持统一包装函数：

```python
from app.loaders.txt_loader import load_txt_documents

documents = load_txt_documents("data/raw/sample.txt")
print(documents)
```

`load_txt_documents()` 会返回 `list[Document]`，当前 TXT 文件会被包装成一个 `Document`。

当前暂不处理：

- metadata 扩展
- 批量导入
- 编码自动识别
- 复杂格式解析

---

## PDF Loader

当前已实现最小 PDF 文档读取函数：

```python
from app.loaders.pdf_loader import load_pdf

pages = load_pdf("data/raw/sample.pdf")
print(pages)
```

当前 PDF loader 按页提取文本，并返回 `list[str]`。

同时支持统一包装函数：

```python
from app.loaders.pdf_loader import load_pdf_documents

documents = load_pdf_documents("data/raw/sample.pdf")
print(documents)
```

`load_pdf_documents()` 会把每一页 PDF 文本包装成一个 `Document`，并保留页码信息。

当前暂不处理：

- metadata 扩展
- 扫描版 PDF / OCR
- 批量导入
- 复杂版面解析

---

## Document Model

当前最小版 `Document` 对象：

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

当前 `Document` 对象的作用是统一 TXT 和 PDF 的输出结构，为后续文本切块、embedding 和检索提供统一输入。

---

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

当前暂不处理：

- 复杂 metadata 扩展
- token 切块
- 中文分词切块
- 语义切块

---

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

该文件用于预览文档导入与预处理链路的阶段成果，并作为 embedding baseline 的输入。

---

## Embedding Baseline

当前已实现本地 embedding baseline。

核心模块：

```text
app/embeddings/local_embedder.py
```

构建脚本：

```bash
python scripts/build_embeddings_demo.py
```

该脚本会读取：

```text
data/processed/chunks_preview.jsonl
```

并生成：

```text
data/processed/chunk_embeddings.npy
data/processed/chunk_embeddings_meta.json
```

当前使用模型：

```text
BAAI/bge-base-zh-v1.5
```

当前运行结果：

```text
chunks: 7
embedding shape: (7, 768)
model: BAAI/bge-base-zh-v1.5
output: data/processed/chunk_embeddings.npy
meta: data/processed/chunk_embeddings_meta.json
```

其中：

- `chunk_embeddings.npy` 保存 chunk 向量矩阵
- `chunk_embeddings_meta.json` 记录模型名、chunk 数量、向量维度、是否归一化、输入输出路径

当前暂不处理：

- 多 embedding 模型对比
- 向量数据库
- 索引持久化封装
- 批量增量更新

---

## Vector Retrieval Baseline

当前已实现内存版向量相似度检索 baseline。

核心模块：

```text
app/retrievers/vector_retriever.py
```

demo 脚本：

```bash
python scripts/retrieve_demo.py
```

当前检索流程：

```text
query
→ query embedding
→ load chunk_embeddings.npy
→ cosine similarity
→ top-k chunks
```

当前返回字段包括：

- `chunk_id`
- `score`
- `content`
- `source`
- `file_type`
- `page`

示例输出：

```text
query: RAGHub 当前支持哪些文档处理能力？
top_k: 3
--------------------------------------------------------------------------------
rank: 1
chunk_id: 0
score: 0.6051
source: data/raw/sample.txt
file_type: txt
page: None
content:
RAGHub is a local document question answering proj
--------------------------------------------------------------------------------
rank: 2
chunk_id: 4
score: 0.5645
source: data/raw/sample.pdf
file_type: pdf
page: 1
content:
RAGHub PDF loader sample.
--------------------------------------------------------------------------------
rank: 3
chunk_id: 5
score: 0.3998
source: data/raw/sample.pdf
file_type: pdf
page: 1
content:
le is used to test document loading.
--------------------------------------------------------------------------------
```

当前暂不处理：

- FAISS
- Qdrant / Milvus / pgvector
- BM25
- 混合检索
- rerank

---

## Retrieve API

当前已新增 `POST /retrieve` 接口，用于把用户 query 交给内存版向量检索模块，并返回相似度最高的 top-k chunks。

请求示例：

```json
{
  "query": "RAGHub 当前支持哪些文档处理能力？",
  "top_k": 3
}
```

响应示例：

```json
{
  "query": "RAGHub 当前支持哪些文档处理能力？",
  "top_k": 3,
  "results": [
    {
      "chunk_id": "0",
      "score": 0.83,
      "content": "...",
      "source": "data/raw/sample.txt",
      "file_type": "txt",
      "page": null
    }
  ]
}
```

当前边界：

- 仍然是内存版向量检索。
- 数据来自 `data/processed/chunk_embeddings.npy` 和 `data/processed/chunks_preview.jsonl`。
- 请求进入 FastAPI 后，由 service 层调用现有 `vector_retriever` 完成召回。
- 该接口本身不包含 LLM 生成、Agent、rerank 或混合检索。

后续增强方向：

- 可将当前内存检索替换为 Chroma、Qdrant、pgvector 等向量数据库。
- 可继续增加检索评测、召回质量分析和失败案例整理。

---

## Chat API

当前已新增 `POST /chat` 接口，用于把用户 query 交给检索服务，基于召回 chunks 构造 RAG prompt，并通过 mock LLM client 返回最小问答结果。

请求示例：

```json
{
  "query": "RAGHub 当前支持哪些文档处理能力？",
  "top_k": 3
}
```

响应示例：

```json
{
  "query": "RAGHub 当前支持哪些文档处理能力？",
  "answer": "这是基于检索片段生成的简化回答：...",
  "retrieved_chunks": [
    {
      "chunk_id": "0",
      "score": 0.83,
      "content": "...",
      "source": "data/raw/sample.txt",
      "file_type": "txt",
      "page": null
    }
  ]
}
```

当前边界：

- 当前使用 mock LLM client，不调用外部大模型 API。
- `/chat` 复用 Day 12 的内存版 `/retrieve` 检索链路。
- 当前不支持 streaming、Agent、工具调用、复杂 prompt 模板或多轮对话。
- 如果没有有效检索片段，会返回资料不足提示。

后续增强方向：

- 可接入 DeepSeek / OpenAI 等真实 LLM provider。
- 可增加 streaming 输出。
- 可增加更严格的 RAG eval、引用校验和失败案例分析。

---

## Evaluation Placeholders

当前 `eval/queries.jsonl` 保存最小评测占位样例。

Week 1 已包含基础接口相关问题。  
Week 2 新增了基于样本文档内容的占位问题，用于后续检索评测扩展。

当前仍不是正式评测集，只作为后续检索命中测试和问答评测的最小起点。

---

## Design Docs

当前已有设计说明：

- `docs/design/preprocessing_pipeline.md`
  - 说明 Week 2 文档导入与预处理主链路
  - 包括 TXT/PDF 输入、Document 统一、固定长度 + overlap 切块、chunk 预览输出

- `docs/design/embedding_baseline_plan.md`
  - 说明 Week 3 embedding baseline 的准备方向
  - 包括 embedding 选型标准、最小验证目标和当前边界

---

## Test

运行测试：

```bash
python -m pytest
```

当前测试覆盖内容：

- `/health` 状态码和返回内容
- `/version` 状态码和版本字段
- `/retrieve` 能返回 query、top_k 和 results
- `/chat` 能返回 query、answer 和 retrieved_chunks
- `/chat` 能在无检索结果时返回资料不足提示
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
- `cosine_similarity()` 能正确计算向量相似度排序
- `cosine_similarity()` 能处理非法零向量输入

当前测试结果：

```text
20 passed
```

---

## Roadmap

接下来计划：

1. Week 1：工程骨架与基础设施【已完成】
   - FastAPI 最小服务
   - `/health` 和 `/version`
   - 配置模块
   - 日志模块
   - pytest 基础测试
   - README、周志、论文占位、评测占位和讲解稿

2. Week 2：文档导入与预处理【已完成】
   - TXT loader 最小版【已完成】
   - PDF loader 最小版【已完成】
   - 最小版 `Document` 对象【已完成】
   - 固定长度 + overlap 文本切块【已完成】
   - 预处理结果落盘与 chunk 预览【已完成】
   - Week 2 设计说明与阶段小结【已完成】

3. Week 3：embedding 与最小向量检索 baseline【进行中】
   - 读取 `chunks_preview.jsonl`【已完成】
   - 提取 chunk content【已完成】
   - 调用 embedding 模型【已完成】
   - 生成 `chunk_embeddings.npy`【已完成】
   - 生成 `chunk_embeddings_meta.json`【已完成】
   - 实现内存版 cosine similarity 检索【已完成】
   - 返回 top-k chunk 及来源信息【已完成】
   - 封装 `/retrieve` API【已完成】
   - 封装 mock `/chat` API【已完成】

4. 后续逐步实现
   - 检索评测扩展
   - 接入真实 LLM 的 RAG 问答接口
   - 回答引用来源
   - 失败案例整理
   - README / Demo / 简历 / 论文材料完善

---

## Current Boundary

当前项目仍是学习型与求职展示型工程项目，不承诺生产级能力。

当前暂不包含：

- DOCX loader
- OCR
- 扫描版 PDF 解析
- 复杂表格解析
- GraphRAG
- 多租户权限
- 高并发任务队列
- 完整向量数据库
- BM25 / hybrid retrieval
- rerank
- 真实 LLM RAG 问答接口
- 前端页面
- Docker 部署

这些内容会在后续阶段按优先级逐步评估，不进入当前 Day 13 范围。
