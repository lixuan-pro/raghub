# RAGHub LLM 回答质量人工评审

## 1. 评审状态

本轮评审基于 Day 22 后的当前索引状态，不是 Day 18 的旧 7 chunks 索引，也不是 Day 21B 的 85 chunks 历史评审版本。

当前索引已扩展到 254 chunks，包含 sample TXT/PDF、README、核心 docs、RAGHub 项目知识库、RAG 工程知识库、eval / bad case 文档，以及自建 demo corpus。本轮使用真实 DeepSeek provider，对 `eval/queries.jsonl` 中 20 条 query 全量运行 `/chat` 链路：

```text
query -> retrieve_chunks -> build_rag_prompt -> DeepSeekLLMClient -> /chat response
```

本评审是小样本人工评审，不代表 LLM 准确率，不代表生产级质量证明，也不等同于自动化 eval。它主要用于观察真实 LLM 接入后，回答是否基于 retrieved sources、sources 是否能支撑答案、no-answer 是否生效，以及扩展语料后是否出现 source competition。

## 2. 评审范围

- Review date：2026-06-18
- Provider：DeepSeek
- Model：`deepseek-v4-flash`
- 样本数量：20
- `top_k`：3
- 样本类型：`in_corpus`、`out_of_corpus`
- 当前 chunk 数量：254
- Embedding shape：`(254, 768)`
- 检索数据：`data/processed/chunks_preview.jsonl`
- 向量数据：`data/processed/chunk_embeddings.npy`
- 结构化结果：`eval/llm_answer_review_results.json`

本轮重点观察：

- 回答是否基于 retrieved sources。
- sources 是否能支撑答案。
- 文档明确“不支持”的能力问题是否回答为“不支持”，而不是误拒答。
- out-of-corpus 问题是否触发 no-answer。
- 扩展语料后是否出现 expected_source 未命中、相似文档竞争、接口字段混淆等问题。

## 3. 评分标准

| 维度 | 分数 | 说明 |
| --- | ---: | --- |
| 可回答性判断 | 0-2 | 该回答时回答，不该回答时拒答 |
| 证据一致性 | 0-2 | 回答是否来自 retrieved chunks |
| 引用支撑 | 0-2 | sources 是否能支撑答案 |
| 回答完整度 | 0-2 | 是否回答了用户问题 |
| 幻觉控制 | 0-2 | 是否编造资料中没有的信息 |

## 4. 当前索引下评审样本表

| ID | Query | Case Type | Expected Answerable | is_answerable | Reason | Source Hit | Keyword Hit | Score | 主要结论 |
|---|---|---|---|---|---|---|---:|---:|---|
| q001 | RAGHub 当前支持哪些接口？ | in_corpus | true | true | retrieval_evidence_found | true | 2/4 | 9 | 命中 README，回答覆盖 `/retrieve` 和 `/chat`，但没有覆盖 `/health`、`/version`。 |
| q002 | RAGHub 的 `/retrieve` 接口返回哪些字段？ | in_corpus | true | true | retrieval_evidence_found | false | 4/6 | 7 | 命中 retrieve 设计文档但 expected_source 未命中，回答偏保守，体现 source competition。 |
| q003 | RAGHub 的 `/chat` 接口会返回哪些引用和拒答字段？ | in_corpus | true | true | retrieval_evidence_found | true | 3/4 | 10 | 能说明 `sources`、`is_answerable`、`reason` 等字段，整体可用。 |
| q004 | RAGHub 如何配置 DeepSeek provider？ | in_corpus | true | true | retrieval_evidence_found | true | 4/4 | 10 | 能基于 README 给出环境变量和 demo 运行方式。 |
| q005 | RAGHub 当前是不是生产级 RAG 平台？ | in_corpus | true | true | retrieval_evidence_found | true | 1/4 | 7 | 结论正确，但对学习型、求职展示、边界等关键词覆盖不足。 |
| q006 | RAGHub 当前是否支持 OCR 处理扫描版 PDF？ | in_corpus | true | true | retrieval_evidence_found | false | 3/4 | 8 | 回答“不支持”正确，但 sources 主要命中旧 review 文档，直接支撑不够理想。 |
| q007 | RAGHub 当前是否已经接入 Qdrant 或 Milvus？ | in_corpus | true | true | retrieval_evidence_found | false | 3/5 | 8 | 结论正确，但 expected_source 未命中，仍受 review 文档竞争影响。 |
| q008 | RAGHub 的 LLM 回答质量人工评审发现了什么风险？ | in_corpus | true | true | retrieval_evidence_found | true | 4/5 | 10 | 能基于 review 和 grounding 文档总结风险。 |
| q009 | RAGHub 项目中遇到过哪些工程问题？ | in_corpus | true | true | retrieval_evidence_found | false | 1/5 | 6 | 未命中 `docs/problems_and_solutions.md`，回答偏离问题，是本轮明显 bad case。 |
| q010 | RAGHub 作者的手机号是多少？ | out_of_corpus | false | false | query_out_of_project_scope | false | 1/3 | 10 | 正确拒答，未调用真实 LLM 生成无依据信息。 |
| q011 | 明天线上用户量是多少？ | out_of_corpus | false | false | query_out_of_project_scope | false | 1/3 | 10 | 正确拒答，符合 no-answer 目标。 |
| q012 | RAGHub 为什么默认使用 mock LLM provider？ | in_corpus | true | true | retrieval_evidence_found | false | 3/5 | 7 | 回答可用但 expected_source 未命中，demo corpus 的 provider 文档产生竞争。 |
| q013 | RAGHub 的 no-answer 策略有哪些边界？ | in_corpus | true | true | retrieval_evidence_found | true | 5/5 | 9 | 命中 no-answer 策略文档，回答较完整。 |
| q014 | RAGHub 为什么当前没有接入 Qdrant 或 Milvus？ | in_corpus | true | true | retrieval_evidence_found | false | 3/5 | 8 | 结论正确，但 sources 命中旧 review，直接支撑不足。 |
| q015 | `chunk_size` 过大或过小分别有什么问题？ | in_corpus | true | true | retrieval_evidence_found | true | 5/5 | 9 | 命中 chunk tradeoff 文档，回答整体可用。 |
| q016 | 为什么 RAG 系统需要 bad case 复盘？ | in_corpus | true | true | retrieval_evidence_found | true | 4/5 | 10 | 能结合 bad case 与 failure taxonomy 说明复盘价值。 |
| q017 | RAGHub 当前的向量检索有什么局限？ | in_corpus | true | true | retrieval_evidence_found | true | 5/5 | 9 | 命中向量检索局限文档，回答整体可用。 |
| q018 | AI 应用后端项目交付手册中如何处理 API key 安全？ | in_corpus | true | true | retrieval_evidence_found | true | 5/5 | 9 | 命中 demo corpus 安全文档，回答可用。 |
| q019 | 知识库更新策略中建议如何维护文档版本？ | in_corpus | true | true | retrieval_evidence_found | false | 4/5 | 8 | 命中文档责任人和变更记录策略，未命中 expected_source，属于相似 policy 竞争。 |
| q020 | demo corpus 中对 LLM provider 的使用边界是什么？ | in_corpus | true | true | retrieval_evidence_found | true | 5/5 | 9 | 命中 demo corpus provider 文档，回答可用。 |

整体结果：

- reviewed_queries：20
- average_score：8.65/10
- in_corpus_average_score：8.50/10
- out_of_corpus_rejected：2/2
- source_hit_rate：0.61
- keyword_hit_rate：0.72
- bad_case_candidates：q002、q006、q007、q009、q012、q014、q019

这些数字只描述本轮小样本人工 review，不代表大规模准确率。尤其是 `average_score` 不是“LLM 准确率”，`source_hit_rate` 和 bad case 更能反映当前需要继续改进的检索质量问题。

## 5. 代表性样本详情

### CASE-001：`/retrieve` 字段问题

- Query：RAGHub 的 `/retrieve` 接口返回哪些字段？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：DeepSeek 表示当前资料没有完整列出 `/retrieve` 返回字段，只提到 `query`、`top_k`、`RetrievedChunk`、`source`、`score` 等相关信息，因此回答偏保守。
- Sources 摘要：
  - `docs/knowledge_base/raghub/retrieve_api_design.md`
  - `eval/llm_answer_review.md`
  - `eval/llm_answer_review.md`
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：1
  - 引用支撑：1
  - 回答完整度：2
  - 幻觉控制：1
  - 总分：7
- 评审结论：回答避免了明显编造，但没有给出完整字段，说明当前 `/retrieve` 字段说明在 top sources 中仍不够稳定。
- 是否进入 bad case：是。

### CASE-002：项目工程问题

- Query：RAGHub 项目中遇到过哪些工程问题？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：回答没有稳定基于 `docs/problems_and_solutions.md` 展开，未覆盖 Python 环境、测试 monkeypatch、分层设计、mock LLM、内存向量检索等核心工程问题。
- Sources 摘要：
  - `data/raw/sample.txt`
  - `docs/knowledge_base/rag_engineering/how_to_reduce_hallucination.md`
  - `docs/knowledge_base/raghub/embedding_design.md`
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：1
  - 引用支撑：1
  - 回答完整度：1
  - 幻觉控制：1
  - 总分：6
- 评审结论：这是本轮最明显的 source miss。问题应命中问题复盘文档，但实际召回偏向 sample 和泛 RAG 文档。
- 是否进入 bad case：是。

### CASE-003：out-of-corpus 拒答

- Query：RAGHub 作者的手机号是多少？
- Case Type：out_of_corpus
- is_answerable：false
- reason：query_out_of_project_scope
- Answer 摘要：当前知识库中没有找到足够依据回答该问题。
- Sources 摘要：`sources=[]`。系统保留 retrieved_chunks 供调试，但不会展示为回答引用。
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：2
  - 引用支撑：2
  - 回答完整度：2
  - 幻觉控制：2
  - 总分：10
- 评审结论：符合 Day 20 no-answer 策略预期，没有向真实 LLM 请求编造隐私信息。
- 是否进入 bad case：否。

### CASE-004：明确不支持的能力问题

- Query：RAGHub 当前是否支持 OCR 处理扫描版 PDF？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：DeepSeek 明确回答当前不支持 OCR 处理扫描版 PDF。
- Sources 摘要：
  - `eval/llm_answer_review.md`
  - `eval/llm_answer_review.md`
  - `eval/llm_answer_review.md`
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：1
  - 引用支撑：1
  - 回答完整度：2
  - 幻觉控制：2
  - 总分：8
- 评审结论：结论正确，但 sources 主要来自 review 文档，不是 README 或 scope 的直接能力边界说明，后续需要降低旧 review 文档对能力边界问题的干扰。
- 是否进入 bad case：是。

### CASE-005：no-answer 策略边界

- Query：RAGHub 的 no-answer 策略有哪些边界？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：能够说明 no-answer 依赖 retrieved chunks、score 阈值和轻量 out-of-scope 规则，但不是完整意图识别或事实验证系统。
- Sources 摘要：
  - `docs/knowledge_base/raghub/no_answer_strategy.md`
  - `eval/bad_cases.md`
  - `eval/bad_cases.md`
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：2
  - 引用支撑：2
  - 回答完整度：2
  - 幻觉控制：1
  - 总分：9
- 评审结论：回答整体可用，说明 Day 20 的 no-answer 设计已经进入索引并能被真实 LLM 使用。
- 是否进入 bad case：否。

### CASE-006：demo corpus 安全策略

- Query：AI 应用后端项目交付手册中如何处理 API key 安全？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：回答围绕不提交 `.env`、使用占位符、日志脱敏、本地配置、最小权限和泄漏处理展开。
- Sources 摘要：
  - `data/demo_corpus/ai_project_handbook/security_and_api_key_policy.md`
  - `data/demo_corpus/ai_project_handbook/api_design_guidelines.md`
  - `data/demo_corpus/ai_project_handbook/onboarding.md`
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：2
  - 引用支撑：2
  - 回答完整度：2
  - 幻觉控制：1
  - 总分：9
- 评审结论：demo corpus 扩展后可以支撑更像真实项目文档的问题，但回答仍应避免把 demo corpus 包装成真实公司制度。
- 是否进入 bad case：否。

### CASE-007：知识库更新策略 source competition

- Query：知识库更新策略中建议如何维护文档版本？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：回答提到变更原因、重建索引、小样本评估等，但没有稳定命中 `knowledge_base_update_policy.md`。
- Sources 摘要：
  - `data/demo_corpus/ai_project_handbook/document_owner_policy.md`
  - `data/demo_corpus/ai_project_handbook/change_log_policy.md`
  - `data/demo_corpus/ai_project_handbook/document_owner_policy.md`
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：1
  - 引用支撑：1
  - 回答完整度：2
  - 幻觉控制：2
  - 总分：8
- 评审结论：这是扩展语料后的典型相似 policy 竞争。回答方向部分正确，但 expected_source 未命中。
- 是否进入 bad case：是。

## 6. 与 Day 18 / Day 21B 历史评审的差异

Day 18 评审基于旧索引，当时 README/docs 尚未进入向量索引，因此 README/API/生产边界类问题容易被标成 boundary case。

Day 21B 评审基于 85 chunks 索引，覆盖 7 条样本，平均分为 8.0/10。它证明 README、核心 docs 和 eval 文档入库后，项目事实类问题比 Day 18 更可回答，但仍不是 Day 22 后的当前主结论。

Day 22B 评审基于 254 chunks 索引，覆盖 `eval/queries.jsonl` 中全部 20 条 query。当前应优先引用本轮结果：

- 语料规模更接近当前仓库状态。
- 覆盖 RAGHub 项目知识库、RAG 工程知识库和自建 demo corpus。
- out-of-corpus 拒答保持 2/2。
- 平均人工分从 8.0/10 提升到 8.65/10，但 source_hit_rate 只有 0.61，暴露了扩展语料后的 source competition。

## 7. 当前结论

本轮完整 DeepSeek review 说明：在 254 chunks 当前索引下，RAGHub 已经可以用真实 LLM 基于 retrieved sources 回答多数项目事实、RAG 工程和 demo corpus 问题；明显 out-of-corpus 问题能够被 no-answer 策略拒答。

但当前结论必须保守表达：

- 这是 20 条 query 的小样本人工评审，不是大规模准确率。
- `average_score=8.65/10` 不是 LLM 准确率。
- `answerable_accuracy=1.00` 只表示系统层 `is_answerable` 与人工 `expected_answerable` 标注一致。
- `source_hit_rate=0.61` 说明扩展知识库后，最直接来源命中仍不稳定。
- `eval/llm_answer_review.md` 被纳入索引后，会对部分能力边界类 query 形成竞争，需要后续优化语料分层或检索策略。

## 8. bad cases / 风险样本

本轮进入 bad case 候选的 query：

- q002：`/retrieve` 字段问题回答偏保守，expected_source 未命中。
- q006：OCR 能力边界结论正确，但 sources 主要命中旧 review 文档。
- q007：Qdrant / Milvus 能力边界结论正确，但 sources 主要命中旧 review 文档。
- q009：项目工程问题没有命中 `docs/problems_and_solutions.md`，回答质量较低。
- q012：mock LLM 默认策略命中 demo corpus provider 文档，expected_source 未命中。
- q014：Qdrant / Milvus 设计边界命中旧 review 文档，expected_source 未命中。
- q019：知识库更新策略命中相邻 policy 文档，expected_source 未命中。

这些风险不是 DeepSeek API 调用失败，而是 RAG 检索与 source grounding 的工程问题。后续可以通过标题感知 chunk、metadata filtering、rerank 和更细粒度 expected_source / expected_chunk 评估来改进。

## 9. 后续改进

- 将 `eval/llm_answer_review.md` 这类评审文档与正式知识库文档做检索分层，减少 review 文档反向干扰项目能力问题。
- 调整 README/API 文档结构，让 `/retrieve` 和 `/chat` 的字段说明更分离。
- 增加基于 Markdown 标题的 chunk 策略。
- 增加 rerank 或 source grounding 检查，减少命中相似但不直接支撑的片段。
- 引入 metadata filter，例如按 `source_group` 区分 README、project docs、RAG engineering docs、demo corpus、eval docs。
- 扩展 LLM answer review 样本集，并记录每次索引变更后的 bad case。
