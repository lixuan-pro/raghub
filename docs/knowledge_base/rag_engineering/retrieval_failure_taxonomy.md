# 检索失败类型分类

## 1. 背景

RAGHub 在语料扩展后需要区分不同类型的检索失败。第一类是 source miss，问题本来应该命中某个文档，但 top-k 没有包含 expected_source。第二类是 keyword miss，source 命中了，但答案和片段没有覆盖关键术语。第三类是 answerability miss，系统把不该回答的问题判成可回答，或者把应该回答的问题误判为资料不足。第四类是 grounding miss，模型回答看似正确，但 sources 并不能直接支撑结论。

## 2. 与当前项目的关系

Day 22 扩展语料后，source 竞争会更明显。RAGHub 项目文档、RAG 工程文档和 demo corpus 都可能包含相似词，例如 API、eval、provider、no-answer、source 等。此时不能只看 top score，还要结合 expected_source、expected_keywords 和人工 review。记录失败类型可以帮助判断下一步应该调整文档结构、切块策略、eval query，还是 prompt 约束。

## 3. 当前边界

当前项目没有 rerank，也没有 hybrid search，因此不应该把所有检索失败都包装成模型问题。内存版向量检索适合展示语义召回主链路，但对字段级、接口级、配置级问题仍可能不够精确。后续若引入 rerank 或标题感知 chunk，应先用这些失败类型做回归评估。

## 4. 面试表达

面试中可以说明：我在 RAGHub 中不是只看答案是否通顺，而是把失败拆成 source miss、keyword miss、answerability miss 和 grounding miss。这样能证明我理解 RAG 系统的质量问题通常来自多个环节，而不是简单归因于 LLM。这个分类也能指导后续 Roadmap，例如更细粒度 chunk、rerank、answer grounding 和更系统的 eval。
