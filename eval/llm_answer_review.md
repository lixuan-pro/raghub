# RAGHub LLM 回答质量人工评审

## 1. 评审目标

本评审用于记录 RAGHub 接入真实 DeepSeek provider 后的少量人工观察结果。重点检查 `/chat` 返回的回答是否基于 retrieved sources、是否能在资料不足时保持克制、sources 是否能支撑答案，以及是否出现明显幻觉。

本次评审是小样本人工评审，不代表大规模准确率，也不能证明系统生产级可用。

## 2. 评审范围

- Provider：DeepSeek
- 接口链路：`query -> retrieve_chunks -> build_rag_prompt -> DeepSeekLLMClient -> /chat response`
- 样本数量：7 条
- 样本类型：`in_corpus`、`boundary_case`、`risk_case`
- 检索数据：`data/processed/chunks_preview.jsonl` 和 `data/processed/chunk_embeddings.npy`

当前索引语料很小，只包含 sample TXT/PDF 切块；README、API 文档、设计文档尚未进入向量索引。因此，涉及 README/API/生产能力的问题需要作为边界样本看待。

## 3. 评分标准

| 维度 | 分数 | 说明 |
| --- | ---: | --- |
| 可回答性判断 | 0-2 | 该回答时回答，不该回答时拒答 |
| 证据一致性 | 0-2 | 回答是否来自 retrieved chunks |
| 引用支撑 | 0-2 | sources 是否能支撑答案 |
| 回答完整度 | 0-2 | 是否回答了用户问题 |
| 幻觉控制 | 0-2 | 是否编造资料中没有的信息 |

## 4. 评审样本表

| ID | Query | Case Type | is_answerable | Reason | Score | 主要结论 |
|---|---|---|---|---|---:|---|
| CASE-001 | RAGHub 是什么类型的项目？ | in_corpus | true | retrieval_evidence_found | 10 | 回答简洁，完全由 sample.txt 支撑。 |
| CASE-002 | RAGHub 当前支持哪些基础工程能力？ | in_corpus | true | retrieval_evidence_found | 7 | 回答偏保守，只答出项目类型，未充分利用 config/logging/tests 片段。 |
| CASE-003 | PDF loader 当前支持什么处理方式？ | in_corpus | true | retrieval_evidence_found | 8 | 能识别资料有限并拒绝展开，sources 与 PDF 相关。 |
| CASE-004 | PDF loader 下一步计划支持什么提取方式？ | in_corpus | true | retrieval_evidence_found | 8 | 能提到 page-based PDF text extraction，但回答表达偏泛。 |
| CASE-005 | RAGHub 是否已经支持 OCR 处理扫描版 PDF？ | boundary_case | true | retrieval_evidence_found | 8 | LLM 未编造 OCR 支持，明确说明资料未涉及 OCR。 |
| CASE-006 | RAGHub 是否已经接入 Qdrant 或 Milvus？ | boundary_case | true | retrieval_evidence_found | 8 | LLM 未编造向量数据库能力，但系统层 `is_answerable=true` 暴露阈值偏宽。 |
| CASE-007 | RAGHub 的 DeepSeek 接入是否代表已经是生产级 RAG 系统？ | risk_case | true | retrieval_evidence_found | 8 | LLM 保持克制，未夸大生产级能力；但 sources 对该问题支撑不足。 |

平均分：8.1/10。该平均分只用于本轮 7 条样本的人工观察，不代表系统准确率。

## 5. 样本详情

### CASE-001：项目类型问题

- Query：RAGHub 是什么类型的项目？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：RAGHub 是一个本地文档问答项目。
- Sources 摘要：
  - `data/raw/sample.txt`：`RAGHub is a local document question answering proj`
  - `data/raw/sample.pdf`：PDF loader sample 片段
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：2
  - 引用支撑：2
  - 回答完整度：2
  - 幻觉控制：2
  - 总分：10
- 评审结论：回答短但准确，完全基于 source。
- 是否进入 bad case：否

### CASE-002：基础工程能力问题

- Query：RAGHub 当前支持哪些基础工程能力？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：DeepSeek 回答为“本地文档问答项目”，并说明资料有限。
- Sources 摘要：
  - `data/raw/sample.txt`：项目类型片段
  - `data/raw/sample.txt`：`FastAPI skeleton, config, logging, and basic tests` 相关片段
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：2
  - 引用支撑：1
  - 回答完整度：0
  - 幻觉控制：2
  - 总分：7
- 评审结论：回答没有幻觉，但没有充分利用包含 FastAPI/config/logging/tests 的片段，完整度不足。
- 是否进入 bad case：是，作为“回答过度保守 / 没有充分利用证据”的样本。

### CASE-003：PDF loader 当前处理方式

- Query：PDF loader 当前支持什么处理方式？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：DeepSeek 提到资料仅包含 PDF loader sample 和 page-based PDF text extraction，认为资料不足以详细回答。
- Sources 摘要：
  - `data/raw/sample.pdf`：PDF loader sample
  - `data/raw/sample.pdf`：`The next step is page-based PDF text extraction.`
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：2
  - 引用支撑：2
  - 回答完整度：1
  - 幻觉控制：1
  - 总分：8
- 评审结论：回答没有编造额外能力，但对“当前支持什么处理方式”的回答偏保守。
- 是否进入 bad case：否

### CASE-004：PDF loader 下一步计划

- Query：PDF loader 下一步计划支持什么提取方式？
- Case Type：in_corpus
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：DeepSeek 提到基于页面的 PDF 文本提取，但同时说明资料不足。
- Sources 摘要：
  - `data/raw/sample.pdf`：`The next step is page-based PDF text extraction.`
  - `data/raw/sample.pdf`：PDF loader sample
- 人工评分：
  - 可回答性判断：2
  - 证据一致性：2
  - 引用支撑：2
  - 回答完整度：1
  - 幻觉控制：1
  - 总分：8
- 评审结论：核心信息命中，但回答可以更直接。
- 是否进入 bad case：否

### CASE-005：OCR 边界问题

- Query：RAGHub 是否已经支持 OCR 处理扫描版 PDF？
- Case Type：boundary_case
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：DeepSeek 表示无法确定是否支持 OCR，资料只涉及 PDF 加载和基于页面的文本提取，未涉及 OCR。
- Sources 摘要：
  - `data/raw/sample.pdf`：PDF loader sample
  - `data/raw/sample.pdf`：page-based PDF text extraction
- 人工评分：
  - 可回答性判断：1
  - 证据一致性：2
  - 引用支撑：1
  - 回答完整度：2
  - 幻觉控制：2
  - 总分：8
- 评审结论：LLM 没有编造 OCR 能力；但系统层 `is_answerable=true` 说明当前 no-answer 阈值仍偏宽。
- 是否进入 bad case：是，作为“检索分数较高但实际是边界能力问题”的样本。

### CASE-006：向量数据库边界问题

- Query：RAGHub 是否已经接入 Qdrant 或 Milvus？
- Case Type：boundary_case
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：DeepSeek 表示资料未涉及 Qdrant 或 Milvus，资料不足，无法基于当前文档回答。
- Sources 摘要：
  - `data/raw/sample.txt`：RAGHub local document QA project
  - `data/raw/sample.pdf`：PDF loader sample
- 人工评分：
  - 可回答性判断：1
  - 证据一致性：2
  - 引用支撑：1
  - 回答完整度：2
  - 幻觉控制：2
  - 总分：8
- 评审结论：LLM 拒绝编造 Qdrant/Milvus 能力；但 retrieved sources 对该问题支撑不足，系统层仍返回 answerable。
- 是否进入 bad case：是

### CASE-007：生产级能力风险问题

- Query：RAGHub 的 DeepSeek 接入是否代表已经是生产级 RAG 系统？
- Case Type：risk_case
- is_answerable：true
- reason：retrieval_evidence_found
- Answer 摘要：DeepSeek 表示资料未提及 DeepSeek 与 RAG 的具体关系，资料不足，无法基于当前文档回答。
- Sources 摘要：
  - `data/raw/sample.txt`：RAGHub local document QA project
  - `data/raw/sample.pdf`：PDF loader sample
- 人工评分：
  - 可回答性判断：1
  - 证据一致性：2
  - 引用支撑：1
  - 回答完整度：2
  - 幻觉控制：2
  - 总分：8
- 评审结论：回答没有夸大生产级能力，但该问题的真正答案来自 README/docs，而当前 README/docs 尚未进入索引。
- 是否进入 bad case：是

## 6. bad cases / 风险样本

- CASE-002：模型没有充分利用 `FastAPI skeleton, config, logging, and basic tests` 片段，回答过于保守。
- CASE-005：OCR 问题被检索为 `is_answerable=true`，但 sources 未直接支持 OCR 能力判断。
- CASE-006：Qdrant/Milvus 问题被检索为 `is_answerable=true`，实际应更接近 no-answer。
- CASE-007：生产级能力判断依赖 README/docs，但当前 README/docs 尚未进入向量索引。

这些样本说明：真实 LLM 能在一定程度上减少幻觉，但不能替代检索质量、索引范围和 no-answer 策略本身。

## 7. 当前结论

本次评审是小样本人工评审，主要用于验证真实 LLM 接入后，回答是否能基于 retrieved sources 生成，是否能在边界问题上避免无依据扩展。

在本轮样本中，in-corpus 问题整体能基于 sources 生成回答；boundary/risk 问题中，DeepSeek 多数能主动说明资料不足，没有明显编造 OCR、Qdrant、Milvus 或生产级能力。

但当前系统仍存在边界：`is_answerable` 只基于 top score 阈值判断，当 query 与 RAGHub/PDF 等词高度相关时，即使 sources 不能直接回答问题，也可能返回 `retrieval_evidence_found`。因此，当前评审不能代表大规模准确率，也不能证明生产级可用。

## 8. 后续改进

- 将 README、API 文档和设计文档纳入索引，减少 boundary case 被误判。
- Day 19 将 README 和核心 docs 纳入索引后，需要重新评审 sources 支撑情况。
- 基于更多 bad cases 调整 no-answer 阈值。
- 在 prompt 中要求模型显式指出“哪些 source 支撑了哪些结论”。
- 增加 answer-grounding 检查，避免回答和 retrieved sources 脱节。
- 扩展人工评审样本，并沉淀成周期性 eval 报告。
