# RAGHub 面试高频问答

## RAG 基础链路

## Q：RAGHub 的完整链路是什么？

### 回答要点

RAGHub 的链路是文档导入、统一对象、切块、embedding、向量检索、检索 API、问答 API 和 eval。

### 项目中的具体实现

TXT/PDF 经过 loader 变成 `Document`，再由 `chunk_documents()` 切块，生成 `chunks_preview.jsonl` 和 `chunk_embeddings.npy`。查询时通过 `vector_retriever` 返回 chunks，`/chat` 再基于 chunks 构造回答。

### 后续可增强

接入更多文档类型、向量数据库、真实 LLM 和更系统的 eval。

## Q：为什么要切块？

### 回答要点

切块能让长文档变成适合 embedding 和检索的小单元，提高召回粒度。

### 项目中的具体实现

当前使用固定长度 + overlap 的方式，保留上下文连续性，输出较小的 `Document` chunks。

### 后续可增强

改成 token-aware chunking、标题层级切块或语义切块。

## Q：为什么 chunk 要保留 source 和 page？

### 回答要点

RAG 回答需要可追溯性。source/page 能说明答案来自哪里，便于调试和展示引用。

### 项目中的具体实现

`RetrievedChunk` 返回 `source`、`file_type`、`page` 和 `score`。
Day 16 后，`/chat` 额外返回 `sources`，其中包含 `content_preview`，用于面向用户展示引用证据。

### 后续可增强

在 `/chat` answer 中增加引用编号和 source 列表。
继续优化引用格式和 source 去重策略。

## Q：RAG 和普通 LLM 问答有什么区别？

### 回答要点

RAG 先检索外部资料，再基于资料回答，能降低模型只凭参数记忆回答的风险。

### 项目中的具体实现

`/chat` 先调用 `retrieve_chunks()`，再构造 prompt，要求只能基于检索片段回答。

### 后续可增强

接入真实 LLM 后增加引用校验和拒答策略。

## Q：为什么说当前 RAGHub 不是生产级 RAG 平台？

### 回答要点

当前没有真实 LLM、向量数据库、权限、并发、监控、复杂 eval 和部署体系。

### 项目中的具体实现

README 和 scope 文档明确写出当前边界。

### 后续可增强

加入生产级 provider、vector store、Docker、日志追踪和权限控制。

## FastAPI / 后端 API

## Q：`/retrieve` 和 `/chat` 为什么分开？

### 回答要点

`/retrieve` 关注召回，`/chat` 关注基于召回结果组织回答。分开后职责清晰、易测试、易替换。

### 项目中的具体实现

`retrieve_service.py` 封装检索，`rag_service.py` 编排 prompt 和 mock LLM。

### 后续可增强

在 `/chat` 中加入引用、真实 LLM、streaming，而 `/retrieve` 保持检索接口稳定。

## Q：FastAPI router 为什么不直接写业务逻辑？

### 回答要点

router 应该保持薄层，只负责请求和响应；业务逻辑放到 service 便于测试和复用。

### 项目中的具体实现

`app/api/chat.py` 只接收 `ChatRequest` 并调用 `generate_chat_response()`。

### 后续可增强

增加 dependency injection 和 provider interface。

## Q：为什么使用 Pydantic schema？

### 回答要点

Pydantic 能清晰定义 request/response，自动做校验和文档生成。

### 项目中的具体实现

`RetrieveRequest`、`RetrievedChunk`、`RetrieveResponse`、`ChatRequest`、`ChatResponse` 都在 `app/api/schemas.py`。

### 后续可增强

增加更细的错误响应结构和 API versioning。

## Q：为什么限制 top_k 最大值？

### 回答要点

限制 top_k 可以避免一次请求返回过多 chunks，控制响应体和检索成本。

### 项目中的具体实现

`top_k` 默认 3，最大 10。

### 后续可增强

按用户、场景或配置动态限制。

## Q：为什么返回 `score`？

### 回答要点

score 能帮助观察召回置信度，也便于 eval 和调试。

### 项目中的具体实现

`vector_retriever` 返回 cosine similarity 分数，并透出到 API response。

### 后续可增强

增加 score threshold 和低置信度拒答。

## Embedding / 向量检索

## Q：embedding 是什么？

### 回答要点

embedding 是把文本转成向量，让语义相近的文本在向量空间里距离更近。

### 项目中的具体实现

`local_embedder.py` 使用 sentence-transformers 生成 chunk 和 query embedding。

### 后续可增强

对比不同 embedding 模型并记录 eval 结果。

## Q：cosine similarity 为什么适合语义检索？

### 回答要点

cosine similarity 衡量向量方向相似度，适合比较归一化后的语义向量。

### 项目中的具体实现

`vector_retriever.py` 中实现 `cosine_similarity()`，按分数排序返回 top-k。

### 后续可增强

增加 FAISS、HNSW 或向量数据库索引。

## Q：为什么当前不用 Qdrant / Milvus？

### 回答要点

当前数据量小，目标是先验证主链路。直接引入向量数据库会增加部署和维护复杂度。

### 项目中的具体实现

当前使用 `chunk_embeddings.npy` 和 numpy 内存检索。

### 后续可增强

抽象 vector store interface 后接入 Qdrant 或 pgvector。

## Q：当前索引数据来自哪里？

### 回答要点

Day 22 后，当前索引来自 sample TXT/PDF、README、核心 docs、RAGHub 项目知识库、RAG 工程知识库、eval 文档和自建 demo corpus 生成的 chunks 与 embeddings。

### 项目中的具体实现

`chunks_preview.jsonl` 保存文本片段和 source，`chunk_embeddings.npy` 保存向量矩阵；当前索引规模是 250 chunks，embedding shape 是 `(250, 768)`。

### 后续可增强

继续纳入更多业务文档，并通过更细粒度 chunk、rerank 或向量数据库优化 source 命中。

## Q：如何判断检索结果是否合理？

### 回答要点

可以看 source 是否命中、关键词是否命中、top score 是否合理，以及人工查看 chunk 内容。

### 项目中的具体实现

`run_eval.py` 输出 source_hit、matched_keywords 和 top_score。

### 后续可增强

增加更系统的 recall@k、MRR 和失败案例分析。

## Prompt / LLM

## Q：为什么先用 mock LLM？

### 回答要点

mock LLM 能先稳定接口、prompt 和响应结构，避免 API key、网络、费用影响日常开发和测试。

### 项目中的具体实现

`app/llm/mock_client.py` 仍是默认 provider，基于 retrieved chunks 生成简化回答；Day 17 增加了可选 DeepSeek provider。

### 后续可增强

继续完善 DeepSeek provider，并可增加 OpenAI provider、超时重试和调用日志。

## Q：Prompt 里最重要的约束是什么？

### 回答要点

要求只能基于给定资料回答，资料不足时明确说明不足。

### 项目中的具体实现

`build_rag_prompt()` 保留用户问题和检索片段，并写入资料不足策略。

### 后续可增强

增加引用格式、回答风格和安全约束。

## Q：怎么减少幻觉？

### 回答要点

减少幻觉要靠检索约束、资料不足拒答、引用来源和 eval。

### 项目中的具体实现

mock LLM 在没有有效 chunk 时返回“资料不足”，API 返回 retrieved_chunks 供核查。
Day 16 增加 `is_answerable` 和 `reason`，无 chunk 或低 score 时拒答。

### 后续可增强

接真实 LLM 后加入 citation check 和 answer-grounding eval。
通过更多 eval case 调整 no-answer 阈值。

## Q：RAGHub 现在如何接入真实 LLM？

### 回答要点

把 mock client 抽象成 provider interface，保留 rag_service 的编排逻辑；默认仍走 mock，需要时通过环境变量切换到 DeepSeek。

### 项目中的具体实现

当前新增 `app/llm/base.py`、`app/llm/client_factory.py` 和 `app/llm/deepseek_client.py`。`rag_service.py` 只调用 `get_llm_client().generate(prompt)`，no-answer 分支不会调用真实 LLM。

### 后续可增强

后续可以继续增加 OpenAI provider、超时重试、streaming、调用日志和更严格的 answer-grounding eval。

## Q：后续如何支持 streaming？

### 回答要点

需要后端支持流式响应，例如 SSE，并让 LLM client 逐 token 或逐片段返回。

### 项目中的具体实现

当前 `/chat` 是普通同步返回，README 明确 streaming 是后续增强。

### 后续可增强

新增 `/chat/stream` 或通过参数控制 streaming。

## Eval / 质量评估

## Q：eval 怎么做？

### 回答要点

用问题集跑 RAG 链路，记录回答、检索片段、source hit 和 keyword hit。

### 项目中的具体实现

`scripts/run_eval.py` 读取 `eval/queries.jsonl`，输出 `eval/results.json`。Day 20 增加 `expected_answerable`，用于统计可回答性判断是否符合预期。Day 22 将 eval 扩展到 20 条 query，用于覆盖新增的项目知识库、RAG 工程知识库和 demo corpus。Day 22B 已基于 254 chunks 当前索引，对 20 条 eval query 完成真实 DeepSeek 小样本人工评审；Day 21B 的 85 chunks review 仅作为历史对比。

### 后续可增强

增加更多问题、人工标注、自动指标和失败案例分析。

## Q：为什么 Day 19 后 README 相关问题不再是 boundary_case？

### 回答要点

Day 18 之前 README 没有进入索引，所以 README/API 问题是 boundary_case。Day 19 已将 README 和核心 docs 纳入索引，因此这些问题应调整为 in_corpus。

### 项目中的具体实现

`queries.jsonl` 中 README/API 问题已标记为 `in_corpus`，真正没有知识来源的问题使用 `out_of_corpus`，例如作者手机号或未来线上用户量。Day 20 后，`out_of_corpus` 样本会结合 `expected_answerable=false` 统计 reject rate。

### 后续可增强

后续可以把更多业务文档纳入索引，并针对 source 竞争问题做 eval 和 rerank 优化。当前 out-of-scope 防护只是轻量规则，不是生产级意图分类器。

## Q：keyword hit 有什么局限？

### 回答要点

关键词命中只能说明粗粒度相关，不代表回答完整、准确或无幻觉。

### 项目中的具体实现

README 明确 eval 是小样本规则化评测。

### 后续可增强

增加 LLM-as-judge、引用校验和人工评审。

## Q：source hit 为什么重要？

### 回答要点

source hit 能判断检索是否找到了预期文档，是 RAG 召回质量的基础信号。

### 项目中的具体实现

eval 会检查 retrieved_chunks 中是否包含 expected_source。

### 后续可增强

进一步统计 page hit、chunk hit 和 rank。

## Q：eval 结果怎么看？

### 回答要点

先看 in-corpus 的 source hit，再看 keyword hit；再看 `expected_answerable` 与 `is_answerable` 是否一致。`out_of_corpus` 样本要单独解释，因为它主要检验 no-answer 策略。

### 项目中的具体实现

当前 eval 已区分 `in_corpus` 和 `out_of_corpus`。README/API 相关问题在 Day 19 后已经进入索引，不再作为 README 未入库的 boundary case；Day 20 重点观察作者手机号、未来线上用户量等真正无知识来源问题是否被拒答。Day 22 扩展语料后，source_hit_rate 为 0.61、keyword_hit_rate 为 0.70，进一步暴露了 source 命中竞争问题。

### 后续可增强

建立历史 eval 报告，对比每次改动前后的结果。

## 工程问题与边界

## Q：项目中遇到过什么问题？

### 回答要点

遇到过 Python `.venv` 损坏、测试加载模型过慢、README 未入索引造成 eval 边界等问题。

### 项目中的具体实现

`docs/problems_and_solutions.md` 记录了问题、原因、解决方案和面试表达。
`eval/bad_cases.md` 记录 README 未入索引、低相关 query 触发 no-answer、mock LLM 质量有限等 bad case。

### 后续可增强

持续记录失败案例和工程复盘。

## Q：Python 环境坏了怎么解决？

### 回答要点

先诊断 `python/py/pip`、PATH 和 `pyvenv.cfg`，再重建 `.venv`。

### 项目中的具体实现

项目旧 `.venv` 指向已不存在的 Python 3.10，后来用官方 Python 3.11.6 重建。

### 后续可增强

增加环境初始化脚本或 Docker。

## Q：测试为什么要 monkeypatch？

### 回答要点

避免 API 测试依赖 embedding 模型加载，让测试快速稳定。

### 项目中的具体实现

`test_retrieve_api.py` 和 `test_chat_api.py` 用 monkeypatch 替换检索调用。

### 后续可增强

把集成测试和单元测试分层管理。

## Q：为什么不引入 LangChain？

### 回答要点

当前目标是理解和展示 RAG 底层链路，直接引入框架会隐藏关键细节。

### 项目中的具体实现

loader、chunker、retriever、service、prompt 都是显式实现。

### 后续可增强

在主链路稳定后再评估是否接入框架。

## Q：这个项目最能体现什么工程能力？

### 回答要点

体现分层设计、可测试性、渐进式技术选型、边界意识和问题复盘能力。

### 项目中的具体实现

从 `/retrieve` 到 `/chat` 再到 eval，每一步都有明确边界和测试。

### 后续可增强

继续扩展真实 LLM、向量数据库和系统化 eval。
