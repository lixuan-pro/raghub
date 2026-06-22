# RAGHub

RAGHub 是一个面向本地文档的轻量级 RAG 应用后端系统，用于演示从文档导入、文本切块、embedding、向量检索、API 封装到最小 eval 的完整链路。

## 当前状态

当前 v0.2 已完成：

- TXT / PDF 文档导入
- 统一 `Document` 对象
- 固定长度 + overlap 文本切块
- 本地 embedding baseline
- 内存版向量相似度检索
- `POST /retrieve` 检索 API
- `POST /chat` 最小 RAG API
- mock LLM client
- 可选 DeepSeek LLM provider
- 最小 RAG eval
- 项目问题沉淀与面试材料
- RAGHub / RAG 工程 / demo corpus 自写索引语料

当前 `/chat` 默认使用 mock LLM client；如本地配置 `LLM_PROVIDER=deepseek` 和 `DEEPSEEK_API_KEY`，可选调用 DeepSeek。当前 eval 是小样本规则化评测，不是工业级自动评测系统。

## 核心链路

```text
TXT/PDF
-> Document
-> Chunk
-> Embedding
-> Vector Retrieval
-> /retrieve
-> /chat
-> Eval
```

当前索引数据来自：

```text
data/processed/chunks_preview.jsonl
data/processed/chunk_embeddings.npy
```

Day 22 起，当前索引包含项目说明、核心设计文档、RAG 工程知识文档、eval / bad case 文档以及自建 demo corpus。该语料用于验证本地文档 RAG 的离线索引、向量检索、引用返回、拒答和小样本评测流程，不代表生产级知识库规模。

## 快速运行

```powershell
cd E:\Code\Py\raghub
.\.venv\Scripts\Activate.ps1
python -m pytest
python scripts\run_eval.py
python scripts\run_retrieval_eval.py
```

启动 FastAPI：

```powershell
uvicorn app.main:app --reload
```

## API 示例

`POST /retrieve`

```json
{
  "query": "RAGHub 当前支持哪些文档处理能力？",
  "top_k": 3
}
```

`POST /chat`

```json
{
  "query": "RAGHub 当前支持哪些文档处理能力？",
  "top_k": 3
}
```

`/chat` 返回 `answer` 和 `retrieved_chunks`，其中 `retrieved_chunks` 保留 `source`、`page`、`score`，便于解释回答来源。
Day 16 起，`/chat` 还会返回 `sources`、`is_answerable` 和 `reason`，用于展示引用证据和无答案拒答原因。

## Eval 摘要

当前最小 eval 结果：

```text
all_total: 20
all_answerable: 18/20
all_answerability_judgment_accuracy: 1.00
all_expected_unanswerable_reject_rate: 1.00
all_source_hits: 11/18
all_source_hit_rate: 0.61
all_keyword_hit_rate: 0.70
in_corpus_total: 18
out_of_corpus_total: 2
```

注意：这里的 `answerability_judgment_accuracy` 对应 `run_eval.py` 输出中的 `all_answerable_accuracy`，衡量的是系统层 `is_answerable` 判断是否符合人工 `expected_answerable` 标注，不代表 LLM 回答准确率，也不代表生产级准确率。当前 `source_hit` 和 `keyword_hit` 仍然说明检索质量有继续改进空间。

`out_of_corpus` 用于观察当前知识库之外的问题，例如作者手机号、未来线上用户量等。

Day 22B 已基于 254 chunks 当前索引，对 `eval/queries.jsonl` 中 20 条 query 完成真实 DeepSeek 小样本人工评审：`eval/llm_answer_review.md`。本轮平均人工评分为 8.65/10，out-of-corpus 拒答为 2/2，但 `source_hit_rate` 仍为 0.61，说明扩展语料后 source competition 是主要风险。该评审不代表 LLM 准确率或生产级质量证明。

Day 20 已在 eval 中加入 `expected_answerable`，并为 `/chat` 增加轻量 out-of-scope 防护，用于降低明显 out-of-corpus 问题被误判为可回答的风险。

v0.3-lite 新增 retrieval-only 对比实验，不调用 LLM，不覆盖 `eval/results.json`，输出到 `eval/retrieval_comparison.json`。当前结果如下：

| mode | exact_source_hit_rate | acceptable_source_hit_rate | source_group_hit_rate | keyword_hit_rate | MRR@k | Recall@k |
| ---- | --------------------: | -------------------------: | --------------------: | ---------------: | ----: | -------: |
| vector | 0.61 | 0.78 | 0.61 | 0.72 | 0.69 | 0.78 |
| bm25 | 0.44 | 0.61 | 0.50 | 0.77 | 0.48 | 0.61 |
| hybrid | 0.61 | 0.83 | 0.61 | 0.80 | 0.63 | 0.83 |
| hybrid_rerank | 0.61 | 0.83 | 0.61 | 0.80 | 0.63 | 0.83 |

结论：hybrid 提高了 acceptable source hit 和 keyword hit，但没有提高 exact source hit，因此当前不建议设为默认检索模式。完整实验记录见 `docs/retrieval_quality_optimization.md`。

## 当前边界

RAGHub v0.2 是学习型和求职展示型项目，不是生产级 RAG 平台。

当前不包含：

- 默认配置下不调用外部 LLM API
- streaming / SSE
- Agent 或工具调用
- Qdrant / Milvus / pgvector
- 默认链路不启用 BM25 / hybrid retrieval / rerank；这些能力仅作为 v0.3-lite 实验模式保留
- Docker 部署
- 多租户、权限和生产级并发能力

## 后续规划

- 继续完善 DeepSeek / OpenAI 等真实 LLM provider
- 增加 streaming/SSE
- 抽象 vector store interface
- 接入 Qdrant 或 pgvector
- 将更多业务文档纳入索引
- 扩展 eval 问题集和失败案例分析
- 增加 Docker 部署

## 当前实现明细

当前项目已完成从文档导入到最小 RAG API、eval 和问题复盘的 v0.2 主链路：

```text
原始 TXT / PDF / Markdown 文档
→ loader 读取
→ Document 统一表示
→ 固定长度 + overlap 文本切块
→ chunks_preview.jsonl
→ embedding model
→ chunk_embeddings.npy
→ query embedding
→ cosine similarity
→ top-k chunks
→ /retrieve
→ /chat
→ eval / bad cases / LLM answer review
```

当前默认链路仍使用内存版向量检索，尚未接入 Qdrant / Milvus / pgvector。v0.3-lite 分支中新增了 BM25、hybrid retrieval 和 lightweight rerank 的 retrieval-only 对比实验，但默认 `/retrieve` 和 `/chat` 仍保持 vector 行为。

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
- `app/retrievers/bm25_retriever.py` v0.3-lite 轻量 BM25 检索实验模块
- `app/retrievers/hybrid_retriever.py` v0.3-lite hybrid fusion 与 lightweight rerank 实验模块
- `scripts/retrieve_demo.py` 最小检索 demo 脚本
- `scripts/run_retrieval_eval.py` v0.3-lite retrieval-only 对比实验脚本
- `tests/test_vector_retriever.py` 向量相似度测试
- `eval/queries.jsonl` 最小 RAG eval 样例，包含 `in_corpus` 与 `out_of_corpus`
- `eval/results.json` eval 运行结果
- `eval/bad_cases.md` bad case 复盘
- `eval/llm_answer_review.md` DeepSeek 小样本人工评审记录
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
README.md
docs/raghub_v0_2_scope.md
docs/problems_and_solutions.md
eval/bad_cases.md
eval/llm_answer_review.md
→ loader
→ list[Document]
→ chunk_documents()
→ data/processed/chunks_preview.jsonl
```

运行后会输出类似结果：

```text
txt documents: 1
pdf documents: 1
markdown documents: 49
chunks: 254
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
chunks: 254
embedding shape: (254, 768)
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

当前已新增 `POST /chat` 接口，用于把用户 query 交给检索服务，基于召回 chunks 构造 RAG prompt，并通过配置化 LLM client 返回最小问答结果。默认 provider 是 mock，也可以通过环境变量切换到 DeepSeek。

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
  "is_answerable": true,
  "reason": "retrieval_evidence_found",
  "sources": [
    {
      "chunk_id": "0",
      "source": "data/raw/sample.txt",
      "file_type": "txt",
      "page": null,
      "score": 0.83,
      "content_preview": "..."
    }
  ],
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

- 默认使用 mock LLM client；仅当显式配置 `LLM_PROVIDER=deepseek` 和 `DEEPSEEK_API_KEY` 时才调用 DeepSeek。
- `/chat` 复用 Day 12 的内存版 `/retrieve` 检索链路。
- 当前不支持 streaming、Agent、工具调用、复杂 prompt 模板或多轮对话。
- 如果没有有效检索片段，会返回资料不足提示。

后续增强方向：

- 可继续完善 DeepSeek / OpenAI 等真实 LLM provider 的错误处理、超时和流式输出。
- 可增加 streaming 输出。
- 可增加更严格的 RAG eval、引用校验和失败案例分析。

---

## 可选真实 LLM：DeepSeek

Day 17 起，`/chat` 支持通过配置切换 LLM provider。默认仍然是 `mock`，不会调用外部大模型 API，便于本地测试和面试演示。

如果本地需要验证 DeepSeek，可以复制 `.env.example` 并配置：

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

也可以运行：

```powershell
python scripts\chat_deepseek_demo.py
```

注意：
- 不要把真实 `DEEPSEEK_API_KEY` 提交到 Git。
- 缺少 `DEEPSEEK_API_KEY` 时，demo 会提示并跳过真实调用。
- 当 `/chat` 判断为 no-answer 时，不会调用真实 LLM，只返回本地拒答文案。
- 当前 DeepSeek 接入只是可选 provider，不代表 RAGHub 已经是生产级 RAG 系统。

## Citation and No-answer Strategy

`POST /chat` 当前会返回引用证据和可回答性判断：

- `sources`：面向用户展示的引用证据摘要。
- `is_answerable`：当前检索结果是否足以支撑回答。
- `reason`：可回答或拒答的原因。
- `retrieved_chunks`：保留完整检索片段，用于调试和 eval。

`sources` 中包含：

- `chunk_id`
- `source`
- `file_type`
- `page`
- `score`
- `content_preview`

当前 v0.2 使用一个简单规则判断是否拒答：

```text
如果没有 retrieved_chunks -> no_retrieved_chunks
如果 top_score < 0.2 -> retrieval_score_below_threshold
否则 -> retrieval_evidence_found
```

无检索结果或低相关检索结果时，`/chat` 会返回类似“当前知识库中没有找到足够依据回答该问题”的拒答文本。

当前阈值 `0.2` 是 v0.2 的经验规则，只用于最小可解释 no-answer 策略。Day 20 起，no-answer 不只看检索分数，也会对手机号、联系方式、未来线上用户量等明显超出项目资料范围的问题做轻量 out-of-scope 防护。

这仍不是生产级意图分类器或安全系统，只是为了降低明显 out-of-corpus 问题被误判为可回答的风险。

默认仍然使用 mock LLM client；可选 DeepSeek provider 只用于本地验证真实 LLM 链路，不代表生产级生成质量。

---

## Evaluation

当前已新增最小 RAG eval 流程，用于检查 `/chat` 链路返回的回答和检索片段是否大致命中预期。

运行方式：

```bash
python scripts/run_eval.py
```

输入文件：

```text
eval/queries.jsonl
```

该文件保存最小问题集，当前包含 20 条样例。每条样例包含：

- `id`
- `query`
- `expected_keywords`
- `expected_source`
- `expected_sources`
- `expected_source_group`
- `case_type`
- `note`
- `expected_answerable`

输出文件：

```text
eval/results.json
```

该文件记录每条 query 的：

- `answer`
- `retrieved_chunks`
- `top_score`
- `matched_keywords`
- `keyword_hit_count`
- `source_hit`
- `exact_source_hit`
- `acceptable_source_hit`
- `source_group_hit`
- `mrr_at_k`
- `recall_at_k`
- `is_answerable`
- `expected_answerable`
- `answerable_correct`

控制台会输出简短 summary，包括 all cases、in-corpus cases 和 out-of-corpus cases 的 source 命中、keyword 命中和可回答性判断统计。

注意：`all_answerable_accuracy` 衡量的是系统层 `is_answerable` 判断是否符合人工 `expected_answerable` 标注，不代表 LLM 生成答案准确率，也不代表生产级准确率。

当前评测边界：

- 这是小样本、规则化、人工辅助判断的最小 eval。
- eval 包含主评测样例和 `out_of_corpus` 风险样例；后者用于观察 no-answer 策略，不应直接视为普通检索失败。
- 默认使用 mock LLM client；DeepSeek 仅作为可选 provider，需要本地环境变量配置。
- eval 会走真实 embedding 检索，首次运行可能因为模型加载或下载而较慢。
- 当前索引语料已包含 sample TXT/PDF、README、核心 docs、RAGHub 项目知识库、RAG 工程知识库、eval / bad case 文档和自建 demo corpus，但仍是小规模本地索引。
- keyword 命中只能作为粗粒度信号，不能代表完整回答质量。

后续增强方向：

- 扩展更多问题集和不同来源文档。
- 增加自动化指标，例如 source hit rate、keyword hit rate、answer 引用覆盖率。
- 持续沉淀失败案例，分析召回失败和回答不足的原因。

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
44 passed
```

---

## 后续规划

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

3. Week 3：embedding 与最小向量检索 baseline【已完成】
   - 读取 `chunks_preview.jsonl`【已完成】
   - 提取 chunk content【已完成】
   - 调用 embedding 模型【已完成】
   - 生成 `chunk_embeddings.npy`【已完成】
   - 生成 `chunk_embeddings_meta.json`【已完成】
   - 实现内存版 cosine similarity 检索【已完成】
   - 返回 top-k chunk 及来源信息【已完成】
   - 封装 `/retrieve` API【已完成】
   - 封装 mock `/chat` API【已完成】

4. v0.2 展示收口【已完成】
   - `/retrieve` API【已完成】
   - `/chat` API【已完成】
   - sources / citation【已完成】
   - no-answer 与轻量 out-of-scope 防护【已完成】
   - 可选 DeepSeek provider【已完成】
   - 最小 eval、bad cases 和 LLM answer review【已完成】
   - README、docs 和 eval 文档入库索引【已完成】

---

## 当前边界

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
- 默认检索链路不启用 BM25 / hybrid retrieval / rerank
- 生产级真实 LLM RAG 问答接口
- 前端页面
- Docker 部署

这些内容会在后续阶段按优先级逐步评估，不属于当前 v0.2 已完成能力。
