# 索引构建工作流

## 1. 说明

RAGHub 的索引构建从本地文件开始，包含 sample TXT/PDF、README、核心 docs、eval 文档和 Day 22 新增知识库。构建流程先读取 Document，再按固定 chunk_size 和 overlap 切块，最后生成 chunks_preview.jsonl、chunk_embeddings.npy 和 chunk_embeddings_meta.json。这个流程强调可复现和可检查：每次语料变化后都要重新构建 chunks 与 embeddings，并运行 eval 观察 source_hit、keyword_hit 和 answerability。当前实现不是增量索引系统，也没有复杂任务队列；它更像一个面试展示阶段的离线构建流水线。后续如接入 Qdrant 或 pgvector，需要保留相同的 metadata 口径，确保 source、file_type、page、chunk_id 不丢失。

## 2. 说明

RAGHub 的索引构建从本地文件开始，包含 sample TXT/PDF、README、核心 docs、eval 文档和 Day 22 新增知识库。构建流程先读取 Document，再按固定 chunk_size 和 overlap 切块，最后生成 chunks_preview.jsonl、chunk_embeddings.npy 和 chunk_embeddings_meta.json。这个流程强调可复现和可检查：每次语料变化后都要重新构建 chunks 与 embeddings，并运行 eval 观察 source_hit、keyword_hit 和 answerability。当前实现不是增量索引系统，也没有复杂任务队列；它更像一个面试展示阶段的离线构建流水线。后续如接入 Qdrant 或 pgvector，需要保留相同的 metadata 口径，确保 source、file_type、page、chunk_id 不丢失。

## 3. 说明

RAGHub 的索引构建从本地文件开始，包含 sample TXT/PDF、README、核心 docs、eval 文档和 Day 22 新增知识库。构建流程先读取 Document，再按固定 chunk_size 和 overlap 切块，最后生成 chunks_preview.jsonl、chunk_embeddings.npy 和 chunk_embeddings_meta.json。这个流程强调可复现和可检查：每次语料变化后都要重新构建 chunks 与 embeddings，并运行 eval 观察 source_hit、keyword_hit 和 answerability。当前实现不是增量索引系统，也没有复杂任务队列；它更像一个面试展示阶段的离线构建流水线。后续如接入 Qdrant 或 pgvector，需要保留相同的 metadata 口径，确保 source、file_type、page、chunk_id 不丢失。

## 4. 说明

RAGHub 的索引构建从本地文件开始，包含 sample TXT/PDF、README、核心 docs、eval 文档和 Day 22 新增知识库。构建流程先读取 Document，再按固定 chunk_size 和 overlap 切块，最后生成 chunks_preview.jsonl、chunk_embeddings.npy 和 chunk_embeddings_meta.json。这个流程强调可复现和可检查：每次语料变化后都要重新构建 chunks 与 embeddings，并运行 eval 观察 source_hit、keyword_hit 和 answerability。当前实现不是增量索引系统，也没有复杂任务队列；它更像一个面试展示阶段的离线构建流水线。后续如接入 Qdrant 或 pgvector，需要保留相同的 metadata 口径，确保 source、file_type、page、chunk_id 不丢失。
