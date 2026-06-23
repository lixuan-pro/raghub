# RAGHub v0.3-lite DeepSeek A/B Review

本评测使用现有 `/chat` 链路和 DeepSeek provider，对 `eval/queries.jsonl` 的 20 条 query 做 vector 与 hybrid 的端到端对比。评分为轻量规则化 review，不是 LLM-as-judge，也不是生产级准确率。

## Summary

| metric | vector | hybrid |
| --- | ---: | ---: |
| average_score | 8.50 | 8.75 |
| exact_source_hit_rate | 0.61 | 0.61 |
| acceptable_source_hit_rate | 0.78 | 0.83 |
| source_group_hit_rate | 0.78 | 0.83 |
| keyword_hit_rate | 0.72 | 0.78 |
| out_of_corpus_rejected | 2/2 | 2/2 |

## Winner Distribution

- vector wins: 2
- hybrid wins: 3
- ties: 15

## Representative Cases

### Hybrid better

- `q001` RAGHub 当前支持哪些接口？ (vector=9, hybrid=10)
- `q005` RAGHub 当前是不是生产级 RAG 平台？ (vector=9, hybrid=10)
- `q009` RAGHub 项目中遇到过哪些工程问题？ (vector=4, hybrid=9)

### Vector better

- `q008` RAGHub 的 LLM 回答质量人工评审发现了什么风险？ (vector=10, hybrid=9)
- `q016` 为什么 RAG 系统需要 bad case 复盘？ (vector=10, hybrid=9)

### Tie

- `q002` RAGHub 的 /retrieve 接口返回哪些字段？ (vector=8, hybrid=8)
- `q003` RAGHub 的 /chat 接口会返回哪些引用和拒答字段？ (vector=10, hybrid=10)
- `q004` RAGHub 如何配置 DeepSeek provider？ (vector=10, hybrid=10)
- `q006` RAGHub 当前是否支持 OCR 处理扫描版 PDF？ (vector=5, hybrid=5)
- `q007` RAGHub 当前是否已经接入 Qdrant 或 Milvus？ (vector=4, hybrid=4)

### Out-of-corpus

- `q010` RAGHub 作者的手机号是多少？ (vector=10, hybrid=10)
- `q011` 明天线上用户量是多少？ (vector=10, hybrid=10)

## Conclusion

Hybrid 在本轮小样本 A/B review 中平均分略高（vector=8.50, hybrid=8.75），winner 分布为 vector 2、hybrid 3、tie 15。这说明 hybrid 有轻微端到端收益，但多数 query 持平，且 exact source hit 没有提升，因此不建议设为默认检索模式。

本评测是 20 条 eval query 的小样本 review，不代表生产级准确率。
