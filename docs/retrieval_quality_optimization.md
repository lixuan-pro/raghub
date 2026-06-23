# RAGHub v0.3-lite 检索质量优化实验

## 1. 背景

RAGHub v0.2 frozen 阶段已经完成本地文档 RAG 主链路。Day 22 扩展到 254 chunks 后，`eval/results.json` 中的 exact `source_hit_rate` 为 `11/18 = 0.61`，说明系统经常能召回语义相关片段，但不一定命中最直接的 `expected_source`。

本实验不接 FAISS、Qdrant、Milvus、pgvector、LangChain、CrossEncoder 或 LLM rerank。目标是用轻量、可测试的方式观察 source competition：

```text
vector baseline
-> bm25 baseline
-> hybrid fusion
-> hybrid + lightweight rerank
-> source grounding comparison
```

## 2. 实现范围

新增模块：

- `app/retrievers/base.py`：最小 retriever protocol。
- `app/retrievers/bm25_retriever.py`：无新依赖的 tokenizer + BM25 scorer。
- `app/retrievers/hybrid_retriever.py`：vector/BM25 merge、score normalization、source/path visible match、轻量 rerank。
- `scripts/run_retrieval_eval.py`：不调用 LLM 的 retrieval-only 对比实验。

兼容约束：

- `/retrieve` response schema 不变。
- `/chat` response schema 不变。
- 默认 `RETRIEVER_PROVIDER=vector`。
- hybrid score 不是 cosine score，因此不默认替代 `/chat` 的 no-answer 判断。
- `eval/results.json` 继续由 `/chat` eval 生成；retrieval 对比单独输出到 `eval/retrieval_comparison.json`。

## 3. BM25 / Lexical Retriever

BM25 retriever 读取现有 `data/processed/chunks_preview.jsonl`，不加载 sentence-transformers，不读取 eval label。

Tokenizer 覆盖：

- 中文 char unigram + bigram。
- 英文单词和数字。
- `/retrieve`、`/chat` 这类 API token。
- `chunk_id`、`source_hit_rate` 这类字段名。
- `API key`、`DEEPSEEK_API_KEY`、`.env`、`Qdrant`、`Milvus`、`pgvector` 等工程实体。

BM25 参数固定为：

```text
k1 = 1.5
b = 0.75
idf = log((N - df + 0.5) / (df + 0.5) + 1)
```

## 4. Hybrid Fusion

Hybrid retriever 使用：

```text
vector_top_n = 10
bm25_top_n = 10
alpha = 0.50
beta = 0.40
gamma = 0.10
```

融合流程：

```text
query
-> vector top_n
-> bm25 top_n
-> merge by chunk_id
-> normalize vector/bm25 scores in candidate set
-> final_score = alpha * vector_score_norm
                + beta * bm25_score_norm
                + gamma * source_match_score
-> optional lightweight rerank
-> top_k
```

`source_match_score` 和 rerank 只使用 query、content、source path、filename 等检索时真实可见信息，不读取 `expected_source`，也不针对具体 q002/q019 写规则。

## 5. Source Grounding Eval

`eval/queries.jsonl` 保留旧字段：

```json
"expected_source": "README.md"
```

并新增：

```json
"expected_sources": ["README.md", "docs/knowledge_base/raghub/retrieve_api_design.md"],
"expected_source_group": "raghub_api_docs"
```

指标定义：

- `exact_source_hit`：top-k 中任一 source 等于 `expected_source`。
- `acceptable_source_hit`：top-k 中任一 source 属于 `expected_sources`。
- `source_group_hit`：top-k 中任一 source 属于同一 `expected_source_group`。
- `MRR@k`：第一个 acceptable source 命中的 reciprocal rank。
- `Recall@k`：top-k 是否至少命中一个 acceptable source。
- `keyword_hit_rate`：retrieved chunks 覆盖 expected keywords 的比例。

## 6. 对比实验结果

命令：

```powershell
.\.venv\Scripts\python.exe scripts\run_retrieval_eval.py
```

输出：

```text
eval/retrieval_comparison.json
```

当前结果：

| mode | exact_source_hit_rate | acceptable_source_hit_rate | source_group_hit_rate | keyword_hit_rate | MRR@k | Recall@k |
| ---- | --------------------: | -------------------------: | --------------------: | ---------------: | ----: | -------: |
| vector | 0.61 | 0.78 | 0.78 | 0.72 | 0.69 | 0.78 |
| bm25 | 0.44 | 0.61 | 0.61 | 0.77 | 0.48 | 0.61 |
| hybrid | 0.61 | 0.83 | 0.83 | 0.80 | 0.63 | 0.83 |
| hybrid_rerank | 0.61 | 0.83 | 0.83 | 0.80 | 0.63 | 0.83 |

## 7. 结论

本实验没有提高 exact source hit：vector、hybrid 和 hybrid_rerank 都是 `0.61`。这说明轻量 hybrid 能扩大合理来源覆盖，但没有完全解决“最直接 source grounding”。

有改善的指标：

- acceptable source hit 从 `0.78` 到 `0.83`。
- source group hit 从 `0.78` 到 `0.83`。
- keyword hit 从 `0.72` 到 `0.80`。
- Recall@k 从 `0.78` 到 `0.83`。

没有改善的指标：

- exact source hit 仍为 `0.61`。
- hybrid_rerank 与 hybrid 指标一致，本轮 lightweight rerank 没有带来额外收益。
- MRR@k 从 `0.69` 下降到 `0.63`，说明 hybrid 有时能召回可接受来源，但排序不一定更靠前。

因此当前不建议把 hybrid 设为默认检索模式。更合理的表达是：

```text
Hybrid 能找到更多合理来源，但未完全解决最直接 source grounding。
后续更应该继续做 heading-aware chunk、metadata filter 或检索分层。
```

## 8. DeepSeek End-to-End A/B Review

为了观察 retrieval-only 指标是否会传导到最终 `/chat` 回答，v0.3-lite 新增 DeepSeek A/B review：

```text
vector + DeepSeek /chat + 20 eval queries
hybrid + DeepSeek /chat + 20 eval queries
```

本轮没有默认运行 `hybrid_rerank`。输出文件：

```text
eval/llm_ab_review_v0_3_results.json
eval/llm_ab_review_v0_3.md
```

评分方式是轻量规则化 review：DeepSeek 负责生成 `/chat` 答案，脚本基于 answerability、source grounding、keyword coverage 和 out-of-corpus 拒答状态计算 0-10 分。它不是 LLM-as-judge，也不是人工评分或生产级准确率。

当前结果：

| metric | vector | hybrid |
| --- | ---: | ---: |
| average_score | 8.50 | 8.75 |
| exact_source_hit_rate | 0.61 | 0.61 |
| acceptable_source_hit_rate | 0.78 | 0.83 |
| source_group_hit_rate | 0.78 | 0.83 |
| keyword_hit_rate | 0.72 | 0.78 |
| out_of_corpus_rejected | 2/2 | 2/2 |

Winner 分布：

```text
vector wins: 2
hybrid wins: 3
ties: 15
```

代表性 case：

- hybrid 更好：q001、q005、q009。
- vector 更好：q008、q016。
- 持平：q002、q003、q004、q006、q007 等。
- out-of-corpus：q010、q011，vector 与 hybrid 都正确拒答。

结论：hybrid 在 20 条小样本 A/B review 中平均分略高，但大多数 query 持平，exact source hit 仍为 `0.61`。因此不能说 hybrid 全面优于 vector，也不建议把 hybrid 设为默认检索模式。

## 9. 主要残留 bad case

Hybrid 仍未解决的 exact miss 包括：

- q006：OCR 能力边界问题仍容易命中 `eval/llm_answer_review.md`。
- q007/q014：Qdrant/Milvus 边界问题仍容易命中 review 文档。
- q012：mock provider 问题命中 demo corpus provider 文档或 README，但没有命中最直接 `mock_vs_deepseek.md`。
- q019：知识库更新问题能命中 `change_log_policy.md`，但最直接 `knowledge_base_update_policy.md` 仍不稳定。

## 10. 后续方向

优先级高于继续调 fusion 权重：

- Heading-aware Markdown chunking，让 `/retrieve`、`/chat`、能力边界、provider 等主题不被固定长度切块混在一起。
- Metadata/source type filter，例如普通问答默认降低 `eval/llm_answer_review.md` 的竞争权重。
- Source group metadata 入库，而不是只在 eval label 中维护。
- 对 q006/q007/q014 这类边界问题增加更明确的能力边界文档结构。

当前 v0.3-lite 是实验版，不是生产级检索系统。
