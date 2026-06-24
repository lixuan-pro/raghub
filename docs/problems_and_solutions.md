# RAGHub 问题与解决方案复盘

本文档记录 RAGHub 从工程骨架到最小 RAG 闭环过程中遇到的真实问题、处理方式和可复用的工程经验。

## 问题 1：Python / `.venv` 环境损坏

### 背景

Day 12 需要运行 FastAPI 和 pytest，但项目原有 `.venv` 是基于本机旧 Python 3.10 创建的。

### 表现

PowerShell 中找不到 `python` 和 `py`，项目 `.venv` 启动时报错，提示无法使用 `C:\Users\75798\AppData\Local\Programs\Python\Python310\python.exe` 创建进程。

### 原因

旧 `.venv` 记录的 base Python 路径已经不存在。虚拟环境里的 `python.exe` 启动时仍依赖这个 base executable，因此即使 `.venv` 目录还在，也无法正常运行。

### 解决方案

先诊断系统 Python、`py launcher`、PATH 和 `.venv\pyvenv.cfg`，确认不是业务代码问题。随后安装官方 Python 3.11.6，使用 `py -3.11 -m venv .venv` 重建虚拟环境，重新安装 `requirements.txt`，再运行 `python -m pytest` 验证。

### 结果

项目恢复到可用标准命令运行测试的状态，Day 12 和 Day 13 都能通过 `.venv` 中的 Python 运行。

### 学到的工程经验

虚拟环境不是可随意迁移的完整 Python，它会记录创建时的 base interpreter。遇到测试无法启动时，要先区分环境问题和代码问题。

### 面试表达版本

我在项目中遇到过 `.venv` 损坏导致测试无法运行的问题。我的处理方式不是直接改代码，而是先检查 `python/py/pip`、PATH 和 `pyvenv.cfg`，定位到虚拟环境依赖的 base Python 被删除，然后用官方 Python 重新创建 `.venv` 并跑完整测试恢复环境。

## 问题 2：测试中避免加载 embedding 模型

### 背景

向量检索需要调用 sentence-transformers 生成 query embedding，真实运行时会加载本地模型，首次运行还可能访问 Hugging Face 缓存或网络。

### 表现

如果 API 测试直接调用真实检索链路，测试会变慢，并且可能因为模型缓存、网络或机器性能不同而不稳定。

### 原因

API 测试的目标是验证 request/response、schema 校验和路由行为，不应该依赖大模型加载这种外部成本较高的步骤。

### 解决方案

在 `tests/test_retrieve_api.py` 和 `tests/test_chat_api.py` 中使用 `monkeypatch` 替换 service 层的检索函数，让测试直接返回固定 chunks。

### 结果

API 测试保持快速稳定，完整测试从 Day 13 起能在 1 秒左右完成，同时 demo 和 eval 脚本仍然保留真实检索链路。

### 学到的工程经验

测试要按层次隔离外部依赖。API 层测试关注接口契约，检索质量验证应放到 eval 或集成脚本里。

### 面试表达版本

我在 RAG 项目中把 API 测试和 embedding 模型加载解耦了。接口测试用 monkeypatch 固定检索结果，保证 CI 和本地测试稳定；真实模型链路放在 demo 和 eval 中验证。

## 问题 3：为什么 `/retrieve` 和 `/chat` 分层设计

### 背景

Day 12 实现 `/retrieve`，Day 13 实现 `/chat`。两者都需要使用检索结果，但职责不同。

### 表现

如果把检索、prompt 构造和回答生成都写在 router 里，代码会很快变成难以测试和替换的混合逻辑。

### 原因

`/retrieve` 是召回接口，核心是 query 到 chunks；`/chat` 是 RAG 问答接口，核心是 query 到 answer，同时保留 retrieved chunks。它们应该共享检索能力，但不应该互相耦合在路由实现里。

### 解决方案

将检索封装到 `retrieve_service.py`，将 RAG 编排封装到 `rag_service.py`，router 只负责接收请求和返回 response。Prompt 和 mock LLM 也拆到独立模块。

### 结果

`/chat` 可以复用 Day 12 的检索服务，同时测试可以针对 service 做替换。后续接入真实 LLM 或更换检索后端时，不需要大改 API router。

### 学到的工程经验

RAG 系统要把检索、prompt、生成和 API 层拆开。这样每一层都可以独立测试、替换和演进。

### 面试表达版本

我没有把 RAG 逻辑直接写进 FastAPI router，而是把 `/retrieve` 做成检索服务，把 `/chat` 做成 RAG 编排服务。这样后续替换向量库或接入真实 LLM 时，只需要替换 service/provider，不破坏 API 层。

## 问题 4：为什么 Day 13 先用 mock LLM

### 背景

Day 13 的目标是打通最小 RAG 闭环，而不是接入生产级大模型。

### 表现

如果一开始接外部 LLM，会引入 API key、网络、费用、限流、模型差异和测试不稳定等问题。

### 原因

在检索链路、schema、prompt 和 response 结构还在演进时，真实 LLM 不是最小必要依赖。先用 mock LLM 可以验证系统边界和数据流。

### 解决方案

新增 `app/llm/mock_client.py`，根据 retrieved chunks 返回可测试的占位回答。没有有效 chunks 时返回“资料不足，无法基于当前文档回答”。

### 结果

项目在不依赖外部 LLM 的情况下完成了 `/chat` 闭环，测试可控，后续可以替换为 DeepSeek 或 OpenAI adapter。

### 学到的工程经验

做复杂系统时，先用 mock 打通接口和数据流，再替换真实 provider，可以降低调试成本和不确定性。

### 面试表达版本

我在 RAG 项目里先用了 mock LLM，而不是直接接大模型 API。这样可以先稳定 schema、prompt 和检索结果组织，避免 API key、网络和费用影响主链路开发。

## 问题 5：为什么当前先用内存向量检索而不是向量数据库

### 背景

RAGHub 早期数据集只有 sample TXT/PDF 生成的少量 chunks，目标是学习和展示完整 RAG 主链路。

### 表现

直接引入 Qdrant、Milvus 或 pgvector 会增加部署、数据导入、索引维护和测试复杂度。

### 原因

当前阶段真正需要验证的是文档导入、chunk、embedding、相似度排序、API 封装和 eval 流程。内存版 numpy 矩阵已经足够承载这些目标。

### 解决方案

先将 embeddings 存为 `data/processed/chunk_embeddings.npy`，chunks 存为 `chunks_preview.jsonl`，用 numpy cosine similarity 完成 top-k 检索。

### 结果

项目快速完成了从文档到 `/retrieve`、`/chat`、eval 的闭环，同时 README 中明确说明当前不是生产级向量数据库系统。

### 学到的工程经验

技术选型要服务当前阶段目标。早期先用简单可控的实现验证主链路，等数据规模和查询需求上来后再引入向量数据库。

### 面试表达版本

我没有一开始就引入向量数据库，而是先用 numpy 内存检索打通 RAG 主链路。这样能更快验证 chunk、embedding、召回和 API 设计，后续再替换为 Qdrant 或 pgvector。

## 问题 6：source competition 导致 exact source hit 不高

### 背景

索引扩展到 254 chunks 后，README、scope 文档、eval/review 文档、bad case 文档、RAG 工程知识库和 demo corpus 都进入同一个检索空间。

### 现象

Eval-100 中 exact source hit 不高，default `/chat` 的 `exact_source_hit_rate=0.5909`，retrieval-only vector 为 `0.5909`，hybrid 仍为 `0.5909`，hybrid_rerank 为 `0.6023`。

### 定位

问题主要来自语义相关文档竞争。比如 eval/review/bad_case 文档会复述 README 或设计文档中的能力边界，导致 top-k 命中语义相近但不是最直接 expected_source 的片段。

### 尝试

本轮比较了 BM25、hybrid 和 hybrid_rerank，并把指标拆成 exact / acceptable / source_group / keyword / MRR@k / Recall@k，而不是只看单一 source hit。

### 结果

hybrid 对 acceptable/source_group/keyword 有轻微提升：acceptable 从 vector `0.7955` 到 hybrid `0.8068`，source_group 从 `0.9091` 到 `0.9205`，keyword 从 `0.6391` 到 `0.6805`。但 exact 提升有限，hybrid 与 vector 同为 `0.5909`。

### 结论

不默认启用 hybrid。当前问题不是继续调 fusion 权重就能稳定解决，默认 vector 更简单、可解释，也避免改变既有 `/retrieve` 和 `/chat` 行为。

### 后续

优先考虑 source_type filter、heading-aware chunk、metadata filter 和 answer-level source selection，而不是继续调 hybrid 参数。

### 工程结论

该 case 说明，语料扩展后问题不只是“是否能召回资料”，还包括“是否命中最直接来源”。当前处理方式是把命中拆成 exact、acceptable 和 source_group 三层，验证 hybrid 是否改善最直接来源。结果显示 hybrid 有轻微 coverage 收益，但 exact 改善有限，因此不设为默认。

## 问题 7：Eval-100 no-answer 失败

### 背景

原来的 eval 只有 20 条，out-of-corpus 样本较少。Eval-100 扩展到 100 条后，单独保留 12 条 out-of-corpus 风险问题。

### 现象

修复前 default `/chat` 的 `out_of_corpus_rejected` 只有 4/12，`answerability_accuracy=0.91`。

### 定位

复杂越界意图没有被原规则覆盖，尤其是真实 API key/token、未来预测、内部业务数据、医疗诊断和未发布信息。仅靠少量关键词不足以覆盖这些问题。

### 修复

新增 `classify_out_of_scope_query()`，把明显越界问题归类为作者隐私、个人/密钥信息、未来预测、实时外部事实、内部业务数据、不受支持的外部知识等类型，并在 `assess_answerability()` 中优先执行该 guard。

### 结果

修复后 out-of-corpus 拒答为 12/12，`answerability_accuracy=0.99`，`expected_answerable_accept_rate=0.9886`，`expected_unanswerable_reject_rate=1.00`。

### 边界

这是规则化 guard，不是完整意图识别器，也不是生产级安全系统。它适合当前项目的明显越界问题防护，但不能替代权限、审计、内容安全和更系统的 answerability judge。

### 工程结论

该 case 说明，Eval-100 能暴露 20 条小样本不容易覆盖的 no-answer 漏拒。修复方式是将明显越界意图收敛为通用分类 guard，并用同一批数据验证 4/12 到 12/12 的闭环。这体现的是评测驱动的工程修复，而不是继续堆功能。
