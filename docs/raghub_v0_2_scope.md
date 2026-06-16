# RAGHub v0.2 范围说明

## 1. 项目定位

RAGHub v0.2 是一个面向本地文档的轻量级 RAG 应用后端系统。它的目标不是直接做成生产级平台，而是清晰展示 RAG 主链路：文档导入、文本切块、embedding、向量检索、API 封装、最小问答和 eval。

## 2. 当前已完成能力

- TXT 文档读取
- PDF 文档读取
- 统一 `Document` 对象
- 固定长度 + overlap 文本切块
- chunk 预览文件 `chunks_preview.jsonl`
- 本地 embedding baseline
- chunk 向量矩阵 `chunk_embeddings.npy`
- 内存版 cosine similarity top-k 检索
- `POST /retrieve`
- `POST /chat`
- mock LLM client
- 可选 DeepSeek LLM provider
- 最小 RAG eval
- 问题沉淀文档
- 面试材料和项目讲解材料

## 3. 当前系统链路

```text
TXT/PDF
-> loader
-> Document
-> chunk_documents()
-> chunks_preview.jsonl
-> embedding model
-> chunk_embeddings.npy
-> vector_retriever
-> /retrieve
-> rag_service
-> LLM client，默认 mock，可选 DeepSeek
-> /chat
-> run_eval.py
```

## 4. 当前 API

### GET /health

用于健康检查。

### GET /version

返回当前应用版本。

### POST /retrieve

输入 query 和 top_k，返回 top-k retrieved chunks。每个 chunk 包含：

- `chunk_id`
- `score`
- `content`
- `source`
- `file_type`
- `page`

### POST /chat

输入 query 和 top_k，复用检索结果构造 RAG prompt，调用配置化 LLM client 返回 answer 和 retrieved chunks。默认 provider 是 mock，可选 provider 是 DeepSeek。

Day 16 起，`/chat` 还返回：

- `sources`：用于展示引用证据的片段摘要
- `is_answerable`：是否有足够检索证据回答
- `reason`：可回答或拒答原因

## 5. 当前 eval 能力

当前 eval 使用 `eval/queries.jsonl` 作为最小问题集，运行：

```powershell
python scripts/run_eval.py
```

输出：

```text
eval/results.json
```

当前统计：

- all cases source hit
- in-corpus source hit
- boundary case source hit
- keyword hit
- boundary case notes

其中 `boundary_case` 用于标记当前索引范围外的问题，例如 README 尚未进入向量索引。

## 6. 当前边界

- `/chat` 默认使用 mock LLM client；只有显式配置 `LLM_PROVIDER=deepseek` 和 `DEEPSEEK_API_KEY` 时才调用 DeepSeek。
- 当前索引只来自 `chunks_preview.jsonl` 和 `chunk_embeddings.npy`。
- README 和 API 文档尚未进入向量索引。
- eval 是小样本、规则化、人工辅助判断。
- 当前已记录 `eval/bad_cases.md`，用于沉淀 README 未入索引、低相关 query 拒答、mock LLM 质量有限等 bad case。
- 当前不是生产级 RAG 平台。

## 7. 合理 Roadmap

- 继续完善 DeepSeek / OpenAI LLM provider
- 增加 streaming / SSE
- 抽象 vector store interface
- 接入 Qdrant 或 pgvector
- 将 README、设计文档和更多业务文档纳入索引
- 增加更系统的 eval
- 记录失败案例并做召回分析
- 基于更多 eval case 调整 no-answer 阈值
- 完善真实 LLM provider 的错误处理、超时、日志和质量评估
- 增加 Docker 部署

## 8. 当前不做清单

- 不做 Agent
- 不做工具调用
- 不接 LangChain
- 不接 RAGAS
- 不做生产级权限系统
- 不做复杂前端
- 不做多租户
- 不做高并发队列

## 9. 面试表达重点

这个项目的重点不是“用了很多框架”，而是把 RAG 的每一层拆开实现并验证：

- loader 负责读取文档
- chunker 负责切分文本
- embedder 负责向量化
- retriever 负责召回
- `/retrieve` 负责暴露检索能力
- `/chat` 负责组织 RAG 闭环
- eval 负责观察质量和边界

面试时可以强调：我先用最小可控实现打通主链路，再把 LLM provider 做成可配置能力，后续继续完善真实 LLM、向量数据库和更系统的 eval。
