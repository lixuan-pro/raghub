# RAG 基础链路

## 1. 定位

本文是 RAG 工程知识库的一部分，用 RAGHub 的实现解释常见工程概念。它不是大模型百科，也不声称 RAGHub 已经实现所有高级能力。本篇关注的关键词包括：文档导入、chunk、embedding、retrieval、prompt、answer。这些内容会被 Markdown loader 当作普通文本读取，然后进入 chunk、embedding、vector retrieval、/retrieve、/chat 和 eval 链路。

## 2. 与 RAGHub 当前实现的关系

RAGHub 目前使用 TXT、PDF 和 Markdown loader 读取本地文件，再统一包装为 Document 对象。Document 会保留 source、file_type 和 page 等元信息，后续切块时继续保留这些字段。这样做的价值是：当用户提问时，系统不仅返回答案，也能展示 retrieved chunks 和 sources，让面试官看到回答来自哪些文档。

围绕 文档导入、chunk、embedding、retrieval、prompt、answer 的设计，当前项目选择先做可解释、可测试、可回滚的本地方案。比如检索仍是内存版向量相似度检索，LLM provider 默认仍是 mock，DeepSeek 只是可选 provider。这样可以先验证 RAG 主链路，再决定是否接入更复杂的向量数据库、rerank 或 streaming。

## 3. 工程边界

当前文档必须明确边界：RAGHub 不是生产级 RAG 平台，不包含多租户权限，不承诺高并发，不包含完整安全审核系统，也没有接入 Qdrant、Milvus、pgvector、BM25 或 rerank。涉及这些能力时，只能作为 Roadmap 或后续增强方向说明，不能写成已完成能力。

如果用户提问超出当前索引资料，例如作者手机号、未来线上用户量、真实公司内部数据，系统应当拒答或提示资料不足。Day 20 的 expected_answerable 和 out-of-scope 防护就是为了观察这类问题是否被误判为可回答。

## 4. 评测关注点

围绕本篇主题，eval 不应只看答案是否流畅，而要同时看 source hit、keyword hit、is_answerable 和 expected_answerable。answerable_accuracy 衡量的是系统层可回答性判断是否符合人工标注，不代表 LLM 回答准确率。真实 DeepSeek review 也只是小样本人工观察，不能包装成生产指标。

当 source 命中不稳定时，要记录 bad case。例如接口字段混淆、项目文档与 RAG 工程文档相互干扰、demo corpus 问题命中 RAGHub 项目说明等，都应被视为索引语料扩展后的正常风险，而不是简单删除问题。

## 5. 面试表达

面试中可以这样解释：我没有一开始就引入复杂基础设施，而是先把文档读取、chunk、embedding、检索、API、引用、拒答和 eval 串成闭环。随后逐步扩展索引语料，让系统面对更接近真实知识库的问题。这个过程暴露了 source 竞争和检索粒度问题，也说明 RAG 工程需要持续 eval 和 bad case 复盘。

## 6. 后续改进

后续可以根据 eval 结果决定是否调整 chunk_size、增加 Markdown 标题感知切块、引入 rerank 或抽象 vector store interface。如果接入 Qdrant、pgvector 或 hybrid search，也应先用小样本 eval 验证收益，再把它写成已完成能力。当前阶段的重点仍然是可解释、可复现和适合求职展示的工程闭环。
