# RAGHub Problems and Solutions

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
