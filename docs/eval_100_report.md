# RAGHub Eval-100 评测报告

## 1. 分支与版本

- branch: `feature/eval-100`
- latest commit: `2f88a87 fix: improve out-of-corpus answerability guard`
- upstream: `origin/feature/eval-100`
- status: 已 push，工作区 clean
- final recorded pytest: `73 passed`

本报告用于记录 Eval-100 的工程评测结果、质量边界和后续技术取舍。Eval-100 是项目级小型评测，不是生产级 benchmark；默认 `/retrieve` 和 `/chat` 仍保持 vector 检索，hybrid 只作为实验模式保留。

## 2. Query 分布

`eval/queries.jsonl` 共 100 条：

| case_type | count |
| --------- | ----: |
| in_corpus | 88 |
| out_of_corpus | 12 |
| total | 100 |

按主题分布：

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

## 3. Retrieval-only Eval-100

结果文件：`eval/retrieval_comparison_100.json`

| mode | exact_source_hit_rate | acceptable_source_hit_rate | source_group_hit_rate | keyword_hit_rate | MRR@k | Recall@k |
| ---- | --------------------: | -------------------------: | --------------------: | ---------------: | ----: | -------: |
| vector | 0.5909 | 0.7955 | 0.9091 | 0.6391 | 0.6629 | 0.7955 |
| bm25 | 0.4432 | 0.6932 | 0.8295 | 0.6736 | 0.5720 | 0.6932 |
| hybrid | 0.5909 | 0.8068 | 0.9205 | 0.6805 | 0.6553 | 0.8068 |
| hybrid_rerank | 0.6023 | 0.8068 | 0.9205 | 0.6805 | 0.6629 | 0.8068 |

观察：hybrid 和 hybrid_rerank 对 acceptable/source_group/keyword 有轻微提升，但 exact source hit 提升有限，不能证明应该默认替换 vector。

## 4. Default `/chat` Eval-100

结果文件：`eval/results_100.json`

| metric | value |
| ------ | ----: |
| answerability_accuracy | 0.99 |
| expected_answerable_accept_rate | 0.9886 |
| expected_unanswerable_reject_rate | 1.00 |
| out_of_corpus_rejected | 12/12 |
| exact_source_hit_rate | 0.5909 |
| acceptable_source_hit_rate | 0.7955 |
| source_group_hit_rate | 0.9091 |
| keyword_hit_rate | 0.6414 |

这里的 answerability 指标衡量系统层 `is_answerable` 是否符合人工标注，不代表 LLM 回答准确率，也不代表生产级安全能力。

## 5. DeepSeek A/B Eval-100

结果文件：`eval/llm_ab_review_100_results.json`

| metric | vector | hybrid |
| ------ | -----: | -----: |
| average_score | 8.83 | 8.90 |
| out_of_corpus_rejected | 12/12 | 12/12 |

Winner 分布：

| winner | count |
| ------ | ----: |
| vector | 12 |
| hybrid | 12 |
| tie | 76 |

结论：hybrid 平均分略高，但 winner 分布完全打平，大多数 query 持平。它可以作为实验 provider 保留，但不适合默认替换 vector。

## 6. No-answer 修复前后对比

| metric | before fix | after fix |
| ------ | ---------: | --------: |
| out_of_corpus_rejected | 4/12 | 12/12 |
| answerability_accuracy | 0.91 | 0.99 |
| expected_answerable_accept_rate | - | 0.9886 |
| expected_unanswerable_reject_rate | - | 1.00 |

Eval-100 初版暴露出 out-of-corpus 拒答不足：真实密钥、未来预测、内部业务数据、医疗诊断、未发布信息等问题并不都能被原有轻量规则覆盖。本轮修复新增 `classify_out_of_scope_query()`，并在 `assess_answerability()` 中优先执行 out-of-scope intent guard，再进入 score threshold 判断。

## 7. 结论

- Eval-100 比 20 条 eval 更可信，因为它覆盖 100 条分层 query，并单独保留 12 条 out-of-corpus 风险样本。
- hybrid 有轻微收益，但 exact source hit 改善有限，DeepSeek A/B winner 分布为 12/12/76，不适合默认替换 vector。
- no-answer 修复是本轮最大收益，out-of-corpus 拒答从 4/12 到 12/12，answerability_accuracy 从 0.91 到 0.99。
- 当前 no-answer guard 是规则化工程防护，不是完整意图识别器，也不是生产级安全系统。
- 当前建议冻结 `feature/eval-100`，停止继续扩 RAGHub 功能或调检索参数，将本分支作为 Eval-100 工程评测增强分支保留。
