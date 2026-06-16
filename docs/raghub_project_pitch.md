# RAGHub 项目讲解稿

## 1. 30 秒版本

RAGHub 是我做的一个本地文档 RAG 后端项目。它从 TXT/PDF 文档导入开始，完成了 Document 对象、文本切块、embedding、内存向量检索、`/retrieve`、mock `/chat` 和最小 eval。当前重点是展示完整 RAG 主链路和工程分层，而不是包装成生产级平台。

## 2. 2 分钟版本

RAGHub 是一个面向本地文档的轻量级 RAG 应用后端系统。我从最基础的文档导入开始做，支持 TXT 和 PDF，把不同来源的文本统一成 `Document` 对象，然后用固定长度加 overlap 的方式切块。

切块结果会保存成 `chunks_preview.jsonl`，再通过本地 embedding 模型生成 `chunk_embeddings.npy`。检索阶段先用 numpy 实现内存版 cosine similarity top-k，避免早期引入向量数据库带来额外复杂度。

在 API 层，我做了 `POST /retrieve`，它返回 top-k chunks、source、page 和 score。然后在 Day 13 增加 `POST /chat`，复用检索结果构造 RAG prompt，通过 mock LLM client 返回最小回答。mock LLM 不是真实大模型，它的作用是先把 RAG 闭环打通，并保证测试稳定。

最后我补了最小 eval 流程，用 `eval/queries.jsonl` 记录问题、预期关键词和预期来源，运行 `scripts/run_eval.py` 输出 `results.json`，区分 in-corpus 和 boundary case。这个项目现在适合作为 RAG 主链路、FastAPI 分层和工程问题处理能力的展示。

## 3. 5 分钟版本

RAGHub 的设计目标是把 RAG 系统拆成可理解、可测试、可替换的几层，而不是一开始就接入复杂框架。

第一层是文档导入。当前支持 TXT 和 PDF。TXT 读取返回文本，PDF 按页提取文本。为了让后续处理统一，我定义了 `Document` 对象，包含 `content`、`source`、`file_type` 和 `page`。

第二层是文本切块。当前使用固定长度加 overlap 的方式。虽然这不是最先进的语义切块，但它简单、可控，适合早期验证主链路。切块结果会落盘到 `data/processed/chunks_preview.jsonl`。

第三层是 embedding 和检索。项目使用 sentence-transformers 的本地 embedding baseline，把 chunks 转为向量并保存成 `chunk_embeddings.npy`。检索时把用户 query 向量化，再用 cosine similarity 和所有 chunk 向量计算相似度，返回 top-k。当前没有接 Qdrant 或 pgvector，因为数据规模很小，阶段目标是先验证召回逻辑和 API 契约。

第四层是 API。`/retrieve` 只做检索，不做回答生成。`/chat` 复用 retrieve service，构造 RAG prompt，然后调用 mock LLM client。这样拆分的好处是后续更换向量数据库或真实 LLM 时，不需要重写 router。

第五层是 eval。项目提供 `scripts/run_eval.py`，读取 `eval/queries.jsonl`，调用 RAG service，输出每个问题的 answer、retrieved_chunks、top_score、matched_keywords、source_hit。eval 还区分 in-corpus 和 boundary_case，避免把 README 尚未入库这类索引范围问题误判成普通检索失败。

项目过程中我也沉淀了问题文档，比如 Python `.venv` 损坏、测试中如何避免加载 embedding 模型、为什么先用 mock LLM、为什么先用内存向量检索。这些内容体现了我对工程边界和迭代顺序的理解。

## 4. 面试开场版

我可以介绍一个自己从零搭的 RAG 后端项目 RAGHub。它不是简单调用 LangChain，而是把 RAG 主链路拆开实现：文档读取、切块、embedding、向量检索、FastAPI API、mock chat 和 eval。这个项目最能体现的是我对 RAG 数据流、API 分层、测试隔离和工程边界的理解。

## 5. 简历项目描述版本

RAGHub：本地文档 RAG 后端系统。实现 TXT/PDF 文档导入、统一 Document 模型、文本切块、本地 embedding、内存向量检索、FastAPI `/retrieve` 与 mock `/chat` 接口，并构建最小 eval 流程统计 source hit 和 keyword hit，沉淀工程问题与面试材料。

## 6. 项目亮点

- 从文档到 eval 的完整 RAG 闭环
- 不依赖 LangChain，核心链路可解释
- `/retrieve` 与 `/chat` 分层清晰
- API 测试使用 monkeypatch 避免加载 embedding 模型
- eval 区分 in-corpus 和 boundary case
- 明确记录当前能力和边界

## 7. 当前边界怎么说

当前 `/chat` 用的是 mock LLM，不代表真实大模型回答质量。当前检索是内存版 cosine similarity，不是生产级向量数据库。当前 eval 是小样本规则化评测，主要用于观察召回来源和关键词命中。

这样设计是有意的：先用最小实现把主链路打通，再逐步替换真实 LLM、向量数据库和更系统的评测。

## 8. 被追问时的回答策略

如果被问为什么不用 LangChain：回答重点是学习和展示底层链路，先自己实现可解释的最小版本。

如果被问为什么不用向量数据库：回答当前数据量小，先用 numpy 检索验证主链路，后续可以抽象 vector store interface 后替换 Qdrant 或 pgvector。

如果被问 mock LLM 是否有意义：回答 mock LLM 用于稳定接口、prompt 和 response 结构，真实 LLM 是后续 provider 替换问题。

如果被问 eval 准不准：回答当前 eval 是最小规则化评测，只用于观察 source hit 和 keyword hit，不代表完整回答质量，后续会扩展问题集、引用校验和失败案例分析。
