# RAGHub Bad Case 复盘

本文档记录 RAGHub v0.2 阶段已经暴露的 bad case。它们不是生产事故，而是当前最小 RAG 链路的真实边界，用于后续迭代和面试复盘。

## CASE-001：README/API 问题未命中

- query: 项目当前支持哪些接口？
- expected: 能回答 `/health`、`/version`、`/retrieve`、`/chat` 等接口信息。
- retrieved_chunks: 当前主要来自 `data/raw/sample.txt` 和 `data/raw/sample.pdf`。
- answer: mock LLM 只能基于 sample 文档片段生成简化回答，无法稳定回答 README/API 文档中的接口清单。
- problem_type: boundary_case
- root_cause: 当前向量索引只包含 `chunks_preview.jsonl` 中的 sample 文档内容，README 和 API 文档尚未进入向量索引。
- current_solution: 在 `eval/queries.jsonl` 中将 README/API 相关问题标记为 `boundary_case`，并在 eval summary 中单独统计。
- next_fix: 将 README、docs 和 API 说明纳入文档导入与索引构建流程。
- interview_explanation: 这个 case 说明 RAG 只能回答已经进入索引的知识。项目中我没有把 README 未命中误判为普通检索失败，而是把它标记为 boundary case，明确暴露当前索引范围限制。

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
