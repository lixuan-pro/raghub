# RAGHub Eval-100 评测报告

## 1. 背景

本轮把 `eval/queries.jsonl` 从 20 条扩展到 100 条，用于补强 RAGHub 检索质量和端到端回答质量的面试可信度。它不是继续扩功能，也不是生产级 benchmark；默认 `/retrieve` 和 `/chat` 仍保持 vector 检索。

Eval-100 仍是项目级小型评测，不是生产级 benchmark。

## 2. Query 分布

| category | count |
| -------- | ----: |
| api | 12 |
| loader_chunking | 10 |
| embedding_retrieval | 10 |
| llm_provider | 10 |
| citation_no_answer | 10 |
| eval_badcase | 12 |
| rag_engineering | 14 |
| demo_corpus | 10 |
| out_of_corpus | 12 |

| difficulty | count |
| ---------- | ----: |
| basic | 27 |
| medium | 39 |
| hard | 34 |

| case_type | count |
| --------- | ----: |
| in_corpus | 88 |
| out_of_corpus | 12 |

## 3. Retrieval-only 四模式对比

命令：

```powershell
.\.venv\Scripts\python.exe scripts\run_retrieval_eval.py --queries eval\queries.jsonl --output eval\retrieval_comparison_100.json
```

| mode | exact | acceptable | source_group | keyword | MRR@k | Recall@k |
| ---- | ----: | ---------: | -----------: | ------: | ----: | -------: |
| vector | 0.59 | 0.80 | 0.91 | 0.64 | 0.66 | 0.80 |
| bm25 | 0.44 | 0.69 | 0.83 | 0.67 | 0.57 | 0.69 |
| hybrid | 0.59 | 0.81 | 0.92 | 0.68 | 0.66 | 0.81 |
| hybrid_rerank | 0.60 | 0.81 | 0.92 | 0.68 | 0.66 | 0.81 |

观察：

- hybrid 相比 vector 的 acceptable source hit 从 0.80 到 0.81，source_group hit 从 0.91 到 0.92。
- exact source hit 基本没有改善：vector=0.59，hybrid=0.59。
- hybrid_rerank 只把 exact source hit 从 0.59 到 0.60，不足以证明应改变默认检索模式。

## 4. Default `/chat` Eval-100

命令：

```powershell
.\.venv\Scripts\python.exe scripts\run_eval.py --queries eval\queries.jsonl --output eval\results_100.json
```

核心结果：

- answerability_accuracy: 0.99
- expected_answerable_accept_rate: 0.99 (87/88)
- expected_unanswerable_reject_rate: 1.00 (12/12)
- exact_source_hit_rate: 0.59
- acceptable_source_hit_rate: 0.80
- source_group_hit_rate: 0.91
- keyword_hit_rate: 0.64
- out_of_corpus_rejected: 12/12

Eval-100 初版暴露了 out-of-corpus 拒答不足：100 条中 12 条 out-of-corpus 只拒答 4 条。本轮 no-answer 修复后，`assess_answerability()` 增加通用 out-of-scope intent guard，覆盖作者隐私、真实密钥、未来预测、实时/内部业务数据和不受支持的外部知识请求，拒答提升到 12/12。

当前策略仍是规则化 guard，不是完整意图识别器，也不代表生产级安全拒答能力。后续可以用 LLM-based answerability judge 或轻量 classifier 继续优化。

## 5. DeepSeek A/B Eval-100

命令：

```powershell
.\.venv\Scripts\python.exe scripts\run_llm_ab_review_v0_3.py --queries eval\queries.jsonl --modes vector hybrid --output eval\llm_ab_review_100_results.json --summary-output eval\llm_ab_review_100.md
```

| metric | vector | hybrid |
| ------ | -----: | -----: |
| average_score | 8.83 | 8.90 |
| exact_source_hit_rate | 0.59 | 0.59 |
| acceptable_source_hit_rate | 0.80 | 0.81 |
| source_group_hit_rate | 0.91 | 0.92 |
| keyword_hit_rate | 0.75 | 0.78 |
| out_of_corpus_rejected | 12/12 | 12/12 |

Winner 分布：

```text
vector wins: 12
hybrid wins: 12
ties: 76
```

在 100 条小型分层评测中，hybrid 相比 vector 有一定提升。

同时要注意：虽然 hybrid 平均分从 8.83 到 8.90 略高，winner 分布是 vector 12、hybrid 12、tie 76。这说明端到端质量提升有限，不能写成 hybrid 全面优于 vector。

## 6. Category Breakdown

DeepSeek A/B category breakdown：

| category | count | vector_exact | hybrid_exact | vector_avg | hybrid_avg |
| -------- | ----: | -----------: | -----------: | ---------: | ---------: |
| api | 12 | 0.67 | 0.58 | 9.25 | 8.58 |
| loader_chunking | 10 | 0.50 | 0.60 | 8.40 | 9.00 |
| embedding_retrieval | 10 | 0.60 | 0.50 | 8.50 | 8.50 |
| llm_provider | 10 | 0.70 | 0.70 | 9.30 | 9.30 |
| citation_no_answer | 10 | 0.60 | 0.60 | 8.50 | 8.50 |
| eval_badcase | 12 | 0.42 | 0.42 | 8.33 | 8.67 |
| rag_engineering | 14 | 0.50 | 0.50 | 8.14 | 8.14 |
| demo_corpus | 10 | 0.80 | 0.90 | 9.10 | 9.60 |
| out_of_corpus | 12 | 0.00 | 0.00 | 10.00 | 10.00 |

Default `/chat` category breakdown：

| category | answerability | exact | acceptable | source_group | keyword |
| -------- | ------------: | ----: | ---------: | -----------: | ------: |
| api | 1.00 | 0.67 | 0.92 | 1.00 | 0.64 |
| loader_chunking | 1.00 | 0.50 | 0.70 | 0.80 | 0.82 |
| embedding_retrieval | 1.00 | 0.60 | 0.70 | 0.90 | 0.61 |
| llm_provider | 1.00 | 0.70 | 1.00 | 1.00 | 0.65 |
| citation_no_answer | 0.90 | 0.60 | 0.90 | 1.00 | 0.84 |
| eval_badcase | 1.00 | 0.42 | 0.67 | 0.92 | 0.35 |
| rag_engineering | 1.00 | 0.50 | 0.64 | 0.79 | 0.60 |
| demo_corpus | 1.00 | 0.80 | 0.90 | 0.90 | 0.69 |
| out_of_corpus | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## 7. Difficulty Breakdown

| difficulty | count | vector_avg | hybrid_avg | vector_exact | hybrid_exact |
| ---------- | ----: | ---------: | ---------: | -----------: | -----------: |
| basic | 27 | 9.19 | 9.11 | 0.70 | 0.61 |
| medium | 39 | 8.90 | 8.79 | 0.54 | 0.51 |
| hard | 34 | 8.47 | 8.85 | 0.57 | 0.67 |

## 8. Bad Cases

本轮新增或强化的 bad case：

- Eval-100 初版 `q091`、`q093`、`q094`、`q095`、`q096`、`q098`、`q099`、`q100` 未拒答，集中在真实密钥、未来预测、内部业务数据、医疗诊断和薪资表等超出项目知识库的问题。
- no-answer 修复后，这 8 条均被通用 out-of-scope intent guard 拒答，reason 分别落到 `privacy_personal_info`、`future_prediction`、`internal_business_data`、`unsupported_external_knowledge` 等类别。
- `q006` 未命中 acceptable source：RAGHub 当前是否支持 OCR 处理扫描版 PDF？，expected=README.md，top_sources=eval/llm_answer_review.md。
- `q007` 未命中 acceptable source：RAGHub 当前是否已经接入 Qdrant 或 Milvus？，expected=README.md，top_sources=eval/llm_answer_review.md。
- `q009` 未命中 acceptable source：RAGHub 项目中遇到过哪些工程问题？，expected=docs/problems_and_solutions.md，top_sources=data/raw/sample.txt。
- `q014` 未命中 acceptable source：RAGHub 为什么当前没有接入 Qdrant 或 Milvus？，expected=docs/knowledge_base/raghub/project_scope_and_boundaries.md，top_sources=eval/llm_answer_review.md。
- `q021` 未命中 acceptable source：/retrieve 为什么只负责召回而不生成 LLM 回答？，expected=docs/knowledge_base/raghub/retrieve_api_design.md，top_sources=docs/raghub_v0_2_scope.md。
- `q032` 未命中 acceptable source：Markdown 文档进入索引后会如何参与 chunk、embedding 和 eval？，expected=docs/knowledge_base/raghub/chunking_strategy.md，top_sources=README.md。
- `q037` 未命中 acceptable source：RAGHub 当前对复杂表格和扫描版 PDF 的处理边界是什么？，expected=README.md，top_sources=eval/llm_answer_review.md。
- `q042` 未命中 acceptable source：向量检索为什么会召回语义相关但不是最直接 source 的片段？，expected=docs/knowledge_base/rag_engineering/vector_search_limitations.md，top_sources=README.md。

主要归因：

- exact_source_hit 仍受 source competition 影响，尤其是 eval/review 文档、README、设计文档之间的相似主题竞争。
- out-of-corpus 拒答从 20 条时代的 2/2 暴露为 Eval-100 初版中的 4/12，修复后提升到 12/12；但该能力仍是规则化 guard，不是完整意图识别器。
- hybrid 提升了部分 reasonable source coverage，但也会在 API、embedding、RAG engineering 类别里引入相邻来源噪声。

## 9. 结论

- Eval-100 比 20 条更可信：它覆盖 9 个 category、3 个 difficulty、12 条 out-of-corpus，比 20 条样本更能暴露分层问题。
- Hybrid 在 100 条上仍有收益，但收益很小：retrieval-only 的 acceptable/source_group/keyword 略有提升，修复后 DeepSeek 平均分也从 8.83 到 8.90，但 exact source hit 没提升。
- 不建议 hybrid 设为默认：默认 `/retrieve` 和 `/chat` 应继续保持 vector。
- 仍存在 source competition：Eval/review 文档与 README、RAGHub 设计文档、demo corpus policy 文档会竞争 top-k。
- 当前应停止 RAGHub 功能扩张，优先把结论沉淀为展示材料和后续 Roadmap。

## 10. Roadmap

后续优先级高于继续调 fusion 权重：

- source_type filter：降低 eval/review 文档对普通问答的竞争权重。
- heading-aware chunk：减少 README、API 示例、设计段落被固定长度 chunk 混在一起。
- metadata filter：按 source_group、文档类型、知识库分层过滤。
- answer-level source selection：回答层再选择真正支撑答案的来源，而不是简单展示 top-k。
- LLM-based answerability judge 或轻量 classifier：替代当前规则化 guard，降低误伤和漏拒风险。
