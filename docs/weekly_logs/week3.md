# Week 3 - Embedding 与检索准备

## 本周目标

本周目标是进入 RAGHub 的 embedding 与最小检索准备阶段。

当前项目已经完成 Week 1 工程骨架与 Week 2 文档导入、预处理链路，主链路已经达到：

```text
原始 TXT / PDF
→ loader
→ list[Document]
→ chunk_documents()
→ data/processed/chunks_preview.jsonl


