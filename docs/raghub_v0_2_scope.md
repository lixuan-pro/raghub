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
- README、核心 docs、RAGHub 项目知识库、RAG 工程知识库、eval 文档和自建 demo corpus 索引语料
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
- out-of-corpus answerability judgment
- keyword hit
- case type notes

Day 19 起，README/API 相关问题已调整为 `in_corpus`；真正缺少知识来源的问题使用 `out_of_corpus` 标记。

Day 21B 曾基于 85 chunks 索引补充真实 DeepSeek 小样本回答质量人工评审，当前仅作为历史对比。

Day 22 已将索引语料扩展到 254 chunks，并补充 9 条 eval query。当前 `run_eval.py` 的 source_hit_rate 为 0.61，keyword_hit_rate 为 0.70，说明扩展语料后 source 竞争更加明显，需要继续通过文档结构、chunk 策略和 eval 回归观察。

Day 22B 已基于 254 chunks 当前索引，对 `eval/queries.jsonl` 中 20 条 query 完成真实 DeepSeek 小样本人工评审。当前 review 平均人工评分为 8.65/10，out-of-corpus 拒答为 2/2，同时记录了 `/retrieve` 字段说明、项目工程问题、能力边界问题和知识库 policy 问题中的 source competition 风险。

Day 20 已在 eval 中加入 `expected_answerable`，并为 `/chat` 增加轻量 out-of-scope 防护。当前目标是降低作者手机号、未来线上用户量等明显 out-of-corpus 问题被误判为可回答的风险。

## 6. v0.2 frozen 与 v0.3-lite 实验关系

v0.2 frozen 的默认展示链路仍是：

```text
query
-> vector_retriever
-> /retrieve
-> /chat
-> mock LLM，可选 DeepSeek
```

v0.3-lite 在独立分支中增加 BM25、hybrid retrieval、lightweight rerank 和 retrieval-only source grounding 对比实验，用于分析 Day 22 后的 source competition。该实验不改变 `/retrieve` 或 `/chat` 的 response schema，默认检索 provider 仍为 `vector`。

当前 v0.3-lite 结果显示：hybrid 将 acceptable source hit 从 `0.78` 提高到 `0.83`，keyword hit 从 `0.72` 提高到 `0.80`，但 exact source hit 仍为 `0.61`。因此它是检索质量实验，不是新的生产级默认方案。

## 7. 当前边界

- `/chat` 默认使用 mock LLM client；只有显式配置 `LLM_PROVIDER=deepseek` 和 `DEEPSEEK_API_KEY` 时才调用 DeepSeek。
- 当前索引已包含 sample TXT/PDF、README、核心 docs、知识库文档、eval 文档和自建 demo corpus，但仍是本地文件级别的小规模索引。
- 多个 docs 同时包含相似风险说明时，source 命中会出现竞争，需要后续通过更细粒度 chunk、rerank 或 eval 调整继续优化。
- v0.3-lite 的 BM25/hybrid/rerank 是实验能力，默认 `/retrieve` 和 `/chat` 仍保持 v0.2 vector 行为。
- out-of-scope 防护只是 v0.2 的轻量规则，不是生产级意图分类或安全系统。
- eval 是小样本、规则化、人工辅助判断。
- 当前已记录 `eval/bad_cases.md`，用于沉淀低相关 query 拒答、mock LLM 质量有限和 source 支撑不足等 bad case。
- 当前不是生产级 RAG 平台。

## 8. 合理 Roadmap

- 继续完善 DeepSeek / OpenAI LLM provider
- 增加 streaming / SSE
- 抽象 vector store interface
- 接入 Qdrant 或 pgvector
- 将更多业务文档纳入索引
- 增加更系统的 eval
- 记录失败案例并做召回分析
- 基于更多 eval case 调整 no-answer 阈值
- 完善真实 LLM provider 的错误处理、超时、日志和质量评估
- 增加 Docker 部署

## 9. 当前不做清单

- 不做 Agent
- 不做工具调用
- 不接 LangChain
- 不接 RAGAS
- 不做生产级权限系统
- 不做复杂前端
- 不做多租户
- 不做高并发队列

## 10. 面试表达重点

这个项目的重点不是“用了很多框架”，而是把 RAG 的每一层拆开实现并验证：

- loader 负责读取文档
- chunker 负责切分文本
- embedder 负责向量化
- retriever 负责召回
- `/retrieve` 负责暴露检索能力
- `/chat` 负责组织 RAG 闭环
- eval 负责观察质量和边界

面试时可以强调：我先用最小可控实现打通主链路，再把 LLM provider 做成可配置能力，后续继续完善真实 LLM、向量数据库和更系统的 eval。
