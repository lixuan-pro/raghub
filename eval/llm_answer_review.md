# RAGHub LLM 回答质量人工评审

## 1. 评审状态

本轮评审基于 Day 20 / Day 21 后的新索引状态，不是 Day 18 时的旧 7 chunks 索引。

当前索引已包含 sample TXT/PDF、README、核心 docs 和 eval 文档。评审使用真实 DeepSeek provider，通过现有 `/chat` 服务链路完成：

```text
query -> retrieve_chunks -> build_rag_prompt -> DeepSeekLLMClient -> /chat response
```

本评审是小样本人工评审，不代表 LLM 准确率，不代表生产级质量证明，也不等同于自动化 eval。

## 2. 评审范围

- Provider：DeepSeek
- 样本数量：7
- 样本类型：`in_corpus`、明确不支持但可回答的能力问题、`out_of_corpus`
- 检索数据：`data/processed/chunks_preview.jsonl`
- 向量数据：`data/processed/chunk_embeddings.npy`
- 当前 chunk 数量：75

本轮重点观察：

- 回答是否基于 retrieved sources。
- sources 是否能支撑答案。
- 文档明确“不支持”的能力问题是否能回答“不支持”。
- out-of-corpus 问题是否触发 no-answer。
- 是否出现明显幻觉或字段混淆。

## 3. 评分标准

| 维度 | 分数 | 说明 |
| --- | ---: | --- |
| 可回答性判断 | 0-2 | 该回答时回答，不该回答时拒答 |
| 证据一致性 | 0-2 | 回答是否来自 retrieved chunks |
| 引用支撑 | 0-2 | sources 是否能支撑答案 |
| 回答完整度 | 0-2 | 是否回答了用户问题 |
| 幻觉控制 | 0-2 | 是否编造资料中没有的信息 |

## 4. 当前索引下评审样本表

| ID | Query | Case Type | is_answerable | Reason | Score | 主要结论 |
|---|---|---|---|---|---:|---|
| CASE-001 | RAGHub 当前索引语料包括哪些文档？ | in_corpus | true | retrieval_evidence_found | 6 | 回答过于保守，没有列出当前已纳入索引的 README/docs/eval 文档。 |
| CASE-002 | RAGHub 的 `/retrieve` 接口返回哪些字段？ | in_corpus | true | retrieval_evidence_found | 5 | 回答混入 `/chat` 字段，说明 source 选择和生成约束仍需改进。 |
| CASE-003 | RAGHub 如何接入 DeepSeek LLM provider？ | in_corpus | true | retrieval_evidence_found | 9 | 能基于 README 给出环境变量和 demo 运行方式。 |
| CASE-004 | RAGHub 是否支持 OCR 处理扫描版 PDF？ | in_corpus | true | retrieval_evidence_found | 7 | 结论正确，但 top sources 对 OCR 的直接支撑不够强。 |
| CASE-005 | RAGHub 是否已经接入 Qdrant 或 Milvus？ | in_corpus | true | retrieval_evidence_found | 9 | 能明确回答未接入，并说明当前使用内存版向量检索。 |
| CASE-006 | RAGHub 作者的手机号是多少？ | out_of_corpus | false | query_out_of_project_scope | 10 | 正确拒答，未调用真实 LLM 生成无依据信息。 |
| CASE-007 | RAGHub 明天的线上用户量是多少？ | out_of_corpus | false | query_out_of_project_scope | 10 | 正确拒答，符合 Day 20 no-answer 目标。 |

平均分：8.0/10。该分数只代表本轮 7 条样本的人工观察，不代表系统准确率。

## 5. 样本详情

### CASE-001：当前索引语料范围

- Query：RAGHub 当前索引语料包括哪些文档？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：DeepSeek 表示无法确定当前索引语料具体包括哪些文档，只说明资料支持 TXT/PDF 导入。
- Sources 摘要：
  - `README.md`：API 示例和当前状态片段。
  - `README.md`：项目状态与能力列表。
  - `data/raw/sample.txt`：早期 sample 项目描述。
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：1
  - 引用支撑：1
  - 回答完整度：0
  - 幻觉控制：2
  - 总分：6
- 评审结论：这是一个真实 bad case。当前 README/scope 中有索引范围说明，但本次 top sources 没有稳定命中最直接片段，导致回答过于保守。
- 是否进入 bad case：是。

### CASE-002：`/retrieve` 返回字段

- Query：RAGHub 的 `/retrieve` 接口返回哪些字段？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：DeepSeek 回答包含 `query`、`answer`、`is_answerable`、`reason`、`sources`、`retrieved_chunks` 等字段。
- Sources 摘要：
  - `README.md`：命中 `/chat` 响应示例附近片段。
  - `eval/llm_answer_review.md`：评审样本建议片段。
  - `data/raw/sample.txt`：早期 sample 项目描述。
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：1
  - 引用支撑：1
  - 回答完整度：0
  - 幻觉控制：1
  - 总分：5
- 评审结论：这是一个真实 bad case。问题问 `/retrieve`，回答混入了 `/chat` 的字段，暴露了 chunk 命中位置和 prompt 约束不足。
- 是否进入 bad case：是。

### CASE-003：DeepSeek provider 接入方式

- Query：RAGHub 如何接入 DeepSeek LLM provider？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：DeepSeek 回答需要配置 `LLM_PROVIDER=deepseek`、`DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`，并可运行 `scripts/chat_deepseek_demo.py`。
- Sources 摘要：
  - `README.md`：当前状态和可选 DeepSeek provider 说明。
  - `README.md`：DeepSeek 配置示例。
  - `eval/llm_answer_review.md`：真实 DeepSeek review 说明。
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：2
  - 引用支撑：2
  - 回答完整度：2
  - 幻觉控制：1
  - 总分：9
- 评审结论：回答基本完整，能基于 README 说明接入方式。扣分点是模型名和配置细节需要以当前 README 为准，后续可减少从 review 文档命中生成配置说明。
- 是否进入 bad case：否。

### CASE-004：OCR 能力边界

- Query：RAGHub 是否支持 OCR 处理扫描版 PDF？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：DeepSeek 明确回答当前不支持 OCR 处理扫描版 PDF。
- Sources 摘要：
  - `eval/llm_answer_review.md`：待重跑样本中包含 OCR 问题。
  - `data/raw/sample.txt`：早期 sample 项目描述。
  - `README.md`：当前状态片段。
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：1
  - 引用支撑：1
  - 回答完整度：2
  - 幻觉控制：1
  - 总分：7
- 评审结论：结论正确，但 sources 对“不支持 OCR”的直接支撑不够强，说明当前 chunk/source 命中仍有优化空间。
- 是否进入 bad case：观察项。

### CASE-005：向量数据库能力边界

- Query：RAGHub 是否已经接入 Qdrant 或 Milvus？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：DeepSeek 回答当前未接入 Qdrant 或 Milvus，现阶段使用内存版 numpy 矩阵进行向量相似度检索。
- Sources 摘要：
  - `data/raw/sample.txt`：早期 sample 项目描述。
  - `docs/problems_and_solutions.md`：说明为什么当前不用 Qdrant / Milvus / pgvector。
  - `README.md`：当前状态片段。
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：2
  - 引用支撑：2
  - 回答完整度：2
  - 幻觉控制：1
  - 总分：9
- 评审结论：回答符合当前项目边界，sources 中 `docs/problems_and_solutions.md` 支撑较好。
- 是否进入 bad case：否。

### CASE-006：作者手机号

- Query：RAGHub 作者的手机号是多少？
- Case Type：out_of_corpus
- is_answerable：false
- reason：query_out_of_project_scope
- Answer 摘要：当前知识库中没有找到足够依据回答该问题。
- Sources 摘要：`sources=[]`。系统仍保留 retrieved_chunks 供调试，但不会向用户展示引用来源。
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：2
  - 引用支撑：2
  - 回答完整度：2
  - 幻觉控制：2
  - 总分：10
- 评审结论：符合 Day 20 out-of-scope 防护预期。
- 是否进入 bad case：否。

### CASE-007：未来线上用户量

- Query：RAGHub 明天的线上用户量是多少？
- Case Type：out_of_corpus
- is_answerable：false
- reason：query_out_of_project_scope
- Answer 摘要：当前知识库中没有找到足够依据回答该问题。
- Sources 摘要：`sources=[]`。系统仍保留 retrieved_chunks 供调试，但不会向用户展示引用来源。
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：2
  - 引用支撑：2
  - 回答完整度：2
  - 幻觉控制：2
  - 总分：10
- 评审结论：符合 Day 20 out-of-scope 防护预期。
- 是否进入 bad case：否。

## 6. 与 Day 18 历史评审的差异

Day 18 评审基于旧索引，当时 README/docs 尚未进入向量索引，因此 README/API/生产边界类问题容易被标成 boundary case。

当前评审基于 Day 20 / Day 21 后的新索引，README、核心 docs 和 eval 文档已经进入检索链路。GitHub 展示和面试复盘时，应优先引用本轮评审，而不是 Day 18 的旧结论。

变化总结：

- README/API/DeepSeek/provider/项目边界类问题已经可以从当前索引中检索到相关资料。
- out-of-corpus 样本能够通过 `query_out_of_project_scope` 拒答。
- 真实 DeepSeek 对“明确不支持”的能力问题整体较克制。
- 新问题是 source 命中竞争和字段混淆，例如 `/retrieve` 问题命中 `/chat` 响应示例。

## 7. 当前结论

本轮小样本人工评审说明：在扩展索引后，RAGHub 对项目事实、DeepSeek 配置、能力边界和 out-of-corpus 拒答的整体可信度比 Day 18 更高。

但它仍不是生产级评测。当前主要风险不是“有没有真实 LLM”，而是：

- chunk 粒度和 source 选择不够精确。
- `/retrieve` 与 `/chat` 字段容易在相邻文档片段中混淆。
- mock LLM 与真实 DeepSeek 的质量差异需要分开说明。
- `answerable_accuracy` 只能表示系统层可回答性判断一致性，不能表示 LLM 答案准确率。

## 8. 后续改进

- 调整 README/API 文档结构，让 `/retrieve` 和 `/chat` 的字段说明更分离。
- 增加更细粒度 chunk 或基于标题的 Markdown chunk 策略。
- 增加 rerank 或 source grounding 检查，减少命中相似但不直接支撑的片段。
- 扩展 LLM answer review 样本集，记录每次变更后的 bad case。
- 在 prompt 中要求模型明确区分 `/retrieve` 与 `/chat` 字段，避免接口字段混淆。
