# RAGHub Embedding Baseline 准备说明

## 1. 下一阶段目标

Week 2 已完成文档导入与预处理链路：

```text
原始 TXT / PDF
→ loader
→ Document
→ chunk
→ chunks_preview.jsonl
```

下一阶段的目标是进入 embedding 最小化实现，将 chunk 文本转换为向量表示，为后续向量检索做准备。

当前下一阶段的核心问题不是直接接入完整向量库，而是先解决：

```text
chunk 文本
→ embedding 模型
→ 向量结果
```

也就是说，Day 10 开始应优先验证“能不能把 chunk 变成向量”。

## 2. Embedding 选型标准

后续选择 embedding 模型或方案时，优先考虑以下标准。

### 2.1 中文支持

RAGHub 后续可能处理中文资料、课程文档、项目文档和论文材料，因此 embedding 模型需要具备较好的中文语义表示能力。

### 2.2 易于本地调用

当前项目以本地工程实践为主，因此优先选择容易在本地 Python 环境中调用的方案。

需要考虑：

- 安装是否复杂
- 调用代码是否清晰
- 是否方便写测试
- 是否适合放进当前 FastAPI / RAGHub 工程结构

### 2.3 与后续检索兼容

embedding 输出应能方便接入后续检索模块。

至少需要明确：

- 输入是文本字符串
- 输出是向量列表
- 多个 chunk 可以批量生成向量
- 后续可以和向量库或相似度计算结合

### 2.4 速度和资源要求可接受

当前阶段不追求复杂方案，应优先选择资源占用可控、运行稳定、适合学习和项目展示的方案。

需要考虑：

- 本地机器是否能运行
- 推理速度是否可接受
- 是否适合小规模 demo
- 是否方便后续迁移或替换

## 3. Day 10 最小验证目标

Day 10 不应该直接做完整向量库或检索接口。

更合适的最小目标是：

```text
读取 chunks_preview.jsonl
→ 取出 chunk content
→ 调用 embedding 方法
→ 得到向量
→ 打印向量维度和样例数量
```

最低验证内容：

- 能读取 `data/processed/chunks_preview.jsonl`
- 能提取 `content`
- 能对若干 chunk 生成 embedding
- 能打印向量数量
- 能打印单个向量维度

## 4. 当前暂不做内容

当前阶段暂不进入：

- FAISS
- BM25
- 向量库持久化
- `/retrieve`
- `/chat`
- RAG 问答接口
- 复杂评测指标
- 多模型对比

这些内容应在 embedding 最小验证通过后再逐步展开。

## 5. 当前阶段边界

Day 9 只负责确定 embedding 阶段的入口和选型标准。

当前不急着确定最终模型，也不急着写 embedding 代码。

下一步应优先完成：

```text
chunk 文本
→ 向量
```

这条最小路径，再考虑向量存储、相似度检索和问答接口。