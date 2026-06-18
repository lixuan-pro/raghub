# Source 竞争记录

## 1. 说明

语料扩展后，RAGHub 开始出现 source 竞争问题：同一个问题可能同时命中 README、scope、LLM review 和 bad cases。source 竞争不是错误，而是知识库变大后常见的 RAG 现象。当前项目通过 eval 和人工 review 记录这些问题，例如 /retrieve 字段问题可能命中 /chat 响应示例，导致模型混淆接口字段。解决方向包括调整 Markdown 结构、按标题切块、增加 rerank、在 prompt 中要求区分 API 名称，以及为 eval 增加更精确的 expected_source。当前阶段先记录问题，不急于引入复杂检索框架。

## 2. 说明

语料扩展后，RAGHub 开始出现 source 竞争问题：同一个问题可能同时命中 README、scope、LLM review 和 bad cases。source 竞争不是错误，而是知识库变大后常见的 RAG 现象。当前项目通过 eval 和人工 review 记录这些问题，例如 /retrieve 字段问题可能命中 /chat 响应示例，导致模型混淆接口字段。解决方向包括调整 Markdown 结构、按标题切块、增加 rerank、在 prompt 中要求区分 API 名称，以及为 eval 增加更精确的 expected_source。当前阶段先记录问题，不急于引入复杂检索框架。

## 3. 说明

语料扩展后，RAGHub 开始出现 source 竞争问题：同一个问题可能同时命中 README、scope、LLM review 和 bad cases。source 竞争不是错误，而是知识库变大后常见的 RAG 现象。当前项目通过 eval 和人工 review 记录这些问题，例如 /retrieve 字段问题可能命中 /chat 响应示例，导致模型混淆接口字段。解决方向包括调整 Markdown 结构、按标题切块、增加 rerank、在 prompt 中要求区分 API 名称，以及为 eval 增加更精确的 expected_source。当前阶段先记录问题，不急于引入复杂检索框架。

## 4. 说明

语料扩展后，RAGHub 开始出现 source 竞争问题：同一个问题可能同时命中 README、scope、LLM review 和 bad cases。source 竞争不是错误，而是知识库变大后常见的 RAG 现象。当前项目通过 eval 和人工 review 记录这些问题，例如 /retrieve 字段问题可能命中 /chat 响应示例，导致模型混淆接口字段。解决方向包括调整 Markdown 结构、按标题切块、增加 rerank、在 prompt 中要求区分 API 名称，以及为 eval 增加更精确的 expected_source。当前阶段先记录问题，不急于引入复杂检索框架。
