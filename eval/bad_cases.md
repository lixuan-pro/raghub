# RAGHub Bad Case 复盘

本文档记录 RAGHub v0.2 阶段已经暴露的 bad case。它们不是生产事故，而是当前最小 RAG 链路的真实边界，用于后续迭代和面试复盘。

## CASE-001：README/API 问题未命中（历史案例，Day 19 已修复）

- query: 项目当前支持哪些接口？
- expected: 能回答 `/health`、`/version`、`/retrieve`、`/chat` 等接口信息。
- retrieved_chunks: 当前主要来自 `data/raw/sample.txt` 和 `data/raw/sample.pdf`。
- answer: mock LLM 只能基于 sample 文档片段生成简化回答，无法稳定回答 README/API 文档中的接口清单。
- problem_type: historical_boundary_case
- root_cause: Day 18 之前，向量索引主要来自 sample TXT/PDF，README 和 API 文档尚未进入向量索引。
- current_solution: Day 19 已将 README、核心 docs 和 eval 文档纳入索引，README/API 相关问题已调整为 `in_corpus`。
- next_fix: 继续观察扩展索引后的 source 命中竞争，并通过更细粒度 chunk、rerank 或更系统的 eval 改进。
- interview_explanation: 这个历史 case 说明 RAG 只能回答已经进入索引的知识。项目中我没有把 README 未命中误判为普通检索失败，而是先标记为边界问题，随后在 Day 19 把 README/docs 纳入索引并更新 eval case 类型。

## CASE-002：低相关 query 触发 no-answer

- query: RAGHub 能不能分析股票价格？
- expected: 当前知识库没有相关资料，应拒答。
- retrieved_chunks: 可能仍会返回低相似度 chunks，但 top score 低于 no-answer 阈值。
- answer: 当前知识库中没有找到足够依据回答该问题。
- problem_type: low_relevance_query
- root_cause: 向量检索总会尝试返回相似片段，但低相似度片段不一定能支撑回答。
- current_solution: Day 16 增加 `is_answerable`、`reason` 和 `sources`。当没有 chunks 或 top score 低于 `MIN_RETRIEVAL_SCORE = 0.2` 时拒答。
- next_fix: 基于更多 eval case 调整阈值，并引入 score threshold、rerank 或 answer grounding 检查。
- interview_explanation: 这个 case 体现了 no-answer 策略的重要性。RAG 系统不能因为检索到了任意片段就强行回答，需要根据证据强度判断是否拒答。

## CASE-005：明显 out-of-corpus 问题被误判为可回答

### 背景

Day 19 扩展 README/docs/eval 索引后，`RAGHub 作者的手机号是多少？` 和 `明天线上用户量是多少？` 这类问题仍能检索到项目相关片段，导致系统层 `is_answerable=true`。

### 表现

- case_type: `out_of_corpus`
- expected_answerable: `false`
- 旧表现：`out_of_corpus_answerable: 2/2`
- 风险：LLM 可能被迫基于相似但无关的项目片段回答。

### 原因

原 no-answer 逻辑主要依赖 top score 阈值。扩展索引后，明显超出项目资料范围的问题仍可能命中 README 或 review 中的相似词。

### 当前处理

Day 20 增加了轻量 out-of-scope 防护，对手机号、联系方式、未来线上用户量等明显不应由项目资料回答的问题返回：

```text
is_answerable=false
reason=query_out_of_project_scope
sources=[]
```

### 当前边界

这不是生产级意图分类器或安全系统，只是 v0.2 阶段为了降低明显 out-of-corpus 误答风险的工程规则。

## CASE-003：mock LLM 回答质量有限

- query: RAGHub 当前支持哪些文档处理能力？
- expected: 能综合说明 TXT/PDF loader、Document 对象、chunk、embedding 和检索。
- retrieved_chunks: 能命中 sample 文档中的部分内容。
- answer: mock LLM 当前只基于第一个有效 chunk 生成简化回答，不能真正综合多个片段。
- problem_type: mock_generation_limit
- root_cause: 当前 mock LLM 的目标是打通 RAG 闭环和测试 response 结构，不具备真实大模型的归纳、压缩和多片段综合能力。
- current_solution: README 和 scope 文档明确说明 `/chat` 使用 mock LLM，不代表真实生成质量。
- next_fix: 接入 DeepSeek / OpenAI 等真实 LLM provider，并增加引用校验和回答质量 eval。
- interview_explanation: 我在项目中先用 mock LLM 是为了稳定接口和数据流，而不是假装已经具备真实生成能力。这个 bad case 能说明 mock 阶段和真实 LLM 阶段的边界。

## CASE-006：真实 DeepSeek review 中 `/retrieve` 字段混入 `/chat` 字段

### 背景

Day 21B 基于扩展后的 README/docs/eval 索引重跑真实 DeepSeek 小样本人工评审。其中 query 为：

```text
RAGHub 的 /retrieve 接口返回哪些字段？
```

### 表现

系统层判断：

```text
is_answerable=true
reason=retrieval_evidence_found
```

但 DeepSeek 的回答混入了 `/chat` 的字段，例如 `answer`、`is_answerable`、`reason`、`sources`、`retrieved_chunks`。

### 原因

当前 README 中 `/retrieve` 与 `/chat` 示例距离较近，chunk 粒度按固定长度切分，导致 query 虽然问 `/retrieve`，top sources 仍可能命中 `/chat` 响应示例或 LLM review 中的相似片段。

### 当前处理

该问题已记录到 `eval/llm_answer_review.md`，作为 source 命中竞争和接口字段混淆的 bad case。

### 后续改进

- 调整 README/API 文档结构，让 `/retrieve` 和 `/chat` 字段说明更分离。
- 增加基于 Markdown 标题的 chunk 策略。
- 增加 rerank 或 source grounding 检查。
- 在 prompt 中要求模型明确区分不同 API 的字段。

### 面试表达版本

这个 case 说明 RAG 不只是接入真实 LLM 就结束了。即使 sources 来自项目文档，如果 chunk 粒度和 source 选择不够精确，模型也可能把相邻接口的字段混在一起。因此我把它记录为 bad case，后续可以通过更细粒度 chunk、rerank 和 prompt 约束改进。

## CASE-007：Day 22 扩展语料后 source 命中率下降

- query: `RAGHub 如何配置 DeepSeek provider？`、`RAGHub 为什么默认使用 mock LLM provider？`、`知识库更新策略中建议如何维护文档版本？` 等。
- expected: 命中 README、RAGHub 项目知识库或 demo corpus 中指定的 expected_source。
- actual: 扩展到 254 chunks 后，部分问题会命中 `eval/llm_answer_review.md`、相邻 policy 文档或相似的 LLM provider 文档，导致 source_hit_rate 从 0.78 左右下降到 0.61。
- retrieved_chunks: 典型情况是 DeepSeek/provider 类问题命中 LLM review，知识库更新问题命中 `document_owner_policy.md` 或 `change_log_policy.md`。
- problem_type: source_competition_after_corpus_expansion
- root_cause: 新增语料中存在大量相似主题，例如 provider、eval、source、知识库更新和安全策略。当前仍使用固定长度 chunk 和内存版向量检索，没有 rerank 或标题感知 chunk，因此容易召回语义相似但不是 expected_source 的片段。
- current_status: Day 22 保留该现象，不强行包装指标。当前 answerability_judgment_accuracy 仍为 1.00，keyword_hit_rate 为 0.70，但 source_hit_rate 只有 0.61。
- next_fix: 后续可以调整 Markdown 文档结构、增加标题感知 chunk、引入 rerank 或更细粒度 expected_source / expected_chunk 评估。
- interview_explanation: 这个 case 说明扩展知识库规模后，RAG 的难点会从“有没有资料”变成“是否命中最直接的资料”。我没有只报好看的指标，而是把 source 竞争记录为 bad case，用它说明后续为什么需要更细粒度切块和 rerank。

## CASE-008：Day 22B DeepSeek 全量 review 中的 source competition

- query: `RAGHub 项目中遇到过哪些工程问题？`、`RAGHub 当前是否支持 OCR 处理扫描版 PDF？`、`知识库更新策略中建议如何维护文档版本？` 等。
- expected: 可回答问题应命中对应的项目文档、能力边界文档或 demo corpus policy 文档，并由这些 sources 支撑真实 DeepSeek 回答。
- actual: Day 22B 对 20 条 eval query 进行真实 DeepSeek 小样本人工评审后，平均人工评分为 8.65/10，out-of-corpus 拒答为 2/2，但 q002、q006、q007、q009、q012、q014、q019 仍被记录为 bad case candidates。
- retrieved_chunks: 典型情况包括能力边界问题命中旧 `eval/llm_answer_review.md`，工程问题未命中 `docs/problems_and_solutions.md`，知识库更新问题命中相邻的 `document_owner_policy.md` 或 `change_log_policy.md`。
- problem_type: llm_review_source_competition
- root_cause: 当前索引包含 README、项目知识库、RAG 工程知识库、eval 文档和 demo corpus，多个文档会使用相似术语，例如 provider、source、eval、policy、知识库更新。内存版向量检索只做 top-k 相似度排序，没有 metadata filter、rerank 或标题感知 chunk，因此真实 LLM 虽然能生成较稳回答，但引用来源不一定是最直接证据。
- current_status: Day 22B 不把 8.65/10 包装成准确率，而是把 source competition 作为主要风险记录在 `eval/llm_answer_review.md` 和结构化结果 `eval/llm_answer_review_results.json` 中。
- next_fix: 后续可以将 review / eval 文档与正式知识库文档做检索分层，增加 source_group metadata，或引入 rerank 和 source grounding 检查。
- interview_explanation: 这个 case 可以说明我没有只看模型回答是否“像是对的”，还会检查 sources 是否真正支撑回答。扩展语料后，RAG 的核心问题从 no-answer 变成 source grounding 和相似文档竞争，这是后续引入 rerank、metadata filter 和标题感知 chunk 的依据。

## CASE-009：v0.3-lite hybrid 未提升 exact source hit

- query: `RAGHub 当前是否支持 OCR 处理扫描版 PDF？`、`RAGHub 当前是否已经接入 Qdrant 或 Milvus？`、`RAGHub 为什么当前没有接入 Qdrant 或 Milvus？`、`知识库更新策略中建议如何维护文档版本？` 等。
- expected: hybrid retrieval 能提高合理来源覆盖，同时不牺牲 v0.2 frozen 的默认 vector 行为。
- actual: `scripts/run_retrieval_eval.py` 显示 vector exact source hit 为 `0.61`，hybrid 和 hybrid_rerank exact source hit 仍为 `0.61`。hybrid 的 acceptable source hit 和 source_group hit 从 `0.78` 提高到 `0.83`，keyword hit 从 `0.72` 提高到 `0.80`；hybrid_rerank 与 hybrid 指标一致，未带来额外收益，也未解决最直接 source grounding。
- problem_type: hybrid_ablation_exact_source_not_improved
- root_cause: 当前失败不只是 score fusion 问题。OCR、Qdrant/Milvus、provider、知识库更新等主题在 README、scope、eval review、demo policy 文档中高度相似，固定长度 chunk 和普通 source path 加分无法稳定区分最直接来源。
- current_status: v0.3-lite 保留 hybrid 作为实验能力，不设为默认 `RETRIEVER_PROVIDER`。默认 `/retrieve` 和 `/chat` 仍走 vector，避免 hybrid final_score 改变 no-answer 阈值语义。
- next_fix: 优先考虑 heading-aware Markdown chunk、metadata filter、eval/review 文档检索分层，或将 source_group metadata 写入索引；不要继续为当前 20 条 query 写硬编码规则。
- interview_explanation: 这个 case 说明我不是只追求局部指标变好。hybrid 提升了合理来源覆盖，但没有提升 exact source hit，所以我把它记录为 ablation 结果，并明确不把实验能力升级为默认方案。

## CASE-010：v0.3-lite DeepSeek A/B review 只有轻微端到端收益

- query: 全部 20 条 `eval/queries.jsonl`。
- expected: 验证 retrieval-only coverage 提升是否会传导到真实 DeepSeek `/chat` 回答质量。
- actual: `scripts/run_llm_ab_review_v0_3.py` 显示 vector 平均分为 `8.50`，hybrid 平均分为 `8.75`；winner 分布为 vector wins `2`、hybrid wins `3`、ties `15`。hybrid 的 acceptable source hit 和 source_group hit 为 `0.83`，高于 vector 的 `0.78`，但 exact source hit 仍同为 `0.61`。
- representative_cases: hybrid 在 q001、q005、q009 上更好；vector 在 q008、q016 上更好；q010、q011 两个 out-of-corpus 问题两种模式都正确拒答。
- problem_type: hybrid_end_to_end_gain_is_small
- root_cause: hybrid 能扩大合理来源覆盖，但固定长度 chunk、eval/review 文档竞争和相似主题 source 竞争仍存在。当前 lightweight scoring 也只是规则化 review，不是人工复审或生产级评测。
- current_status: v0.3-lite 保留 hybrid 作为实验能力，不设为默认检索模式。本评测是 20 条 eval query 的小样本 review，不代表生产级准确率。
- next_fix: 优先做 heading-aware Markdown chunk、metadata/source type filter、eval/review 文档检索分层，而不是继续调 fusion 权重。
- interview_explanation: 这个 case 可以说明我做了端到端验证，而不是只看 retrieval-only 指标。结果显示 hybrid 有轻微收益，但大多数问题持平，所以我没有把它包装成“全面优于 vector”。

## CASE-011：Eval-100 暴露 out-of-corpus 拒答不足

- query: q091-q100 中的 API key、身份证号、未来 QPS、真实客户合同、医疗诊断、未发布上线日期、住址、未来评测分数、token、薪资表等问题。
- expected: 全部应拒答，`expected_answerable=false`。
- actual: default `/chat` Eval-100 中 out-of-corpus rejected 为 `4/12`；DeepSeek A/B 中 vector 和 hybrid 都是 `4/12`。
- problem_type: out_of_corpus_rejection_gap
- root_cause: 当前 out-of-scope 防护是轻量规则，能覆盖手机号、未来用户量等少数模板，但不能覆盖所有隐私、未来数据、外部业务数据和高风险请求。
- current_status: 不把 Eval-100 的 answerability accuracy 包装成生产安全能力。该问题应作为下一轮 no-answer 分类和安全边界改进的首要 bad case。
- next_fix: 引入更系统的 query scope classifier、source_type filter、answerability eval 扩展，或者在 `/chat` 前增加更严格的项目资料范围判断。

## CASE-012：Eval-100 hybrid 收益有限且不适合作为默认

- query: 100 条 Eval-100 分层问题。
- expected: 验证 hybrid 在更大样本上是否稳定优于 vector。
- actual: retrieval-only 中 hybrid acceptable/source_group/keyword 略高于 vector，但 exact source hit 与 vector 同为 `0.59`。DeepSeek A/B 中 vector 平均分 `8.03`，hybrid 平均分 `8.09`，winner 分布为 vector `17`、hybrid `13`、ties `70`。
- problem_type: hybrid_eval_100_gain_is_limited
- root_cause: hybrid 能带来更多相关上下文，但固定长度 chunk、eval/review 文档竞争和相似主题 source competition 仍存在；部分类别中 hybrid 也会引入噪声。
- current_status: 保持默认 `RETRIEVER_PROVIDER=vector`，hybrid 仍作为实验模式保留。
- next_fix: 优先做 source_type filter、heading-aware chunk、metadata filter 和 answer-level source selection，不继续盲调 fusion 权重。
