# Week 2 - 文档导入阶段

## 本周目标

本周目标是进入 RAGHub 的文档导入阶段，先完成 TXT 和 PDF 两类文档的最小读取能力，为后续统一 Document 对象、文本切块和检索模块打基础。

## Day 4 - TXT Loader 最小闭环

### 今日目标

完成 TXT 文档导入的最小正向路径：给定一个 `.txt` 文件路径，程序可以成功读取文件内容，并通过 pytest 测试验证。

### 今日完成

- 新建 `app/loaders/` 目录，作为文档加载模块入口。
- 新建 `data/raw/sample.txt`，作为 TXT loader 的最小样本文档。
- 新建 `app/loaders/txt_loader.py`。
- 实现 `load_txt(path: str) -> str`，用于读取 TXT 文件内容。
- 新建 `tests/test_txt_loader.py`。
- 编写 TXT loader 最小测试，验证：
  - 能成功读取样本文档
  - 返回内容是字符串
  - 返回内容包含 `RAGHub` 和 `document loading`
- 运行 `python -m pytest`，结果为 `3 passed`。

### 当前边界

今天只完成 TXT 文件读取，不进入以下内容：

- PDF loader
- DOCX loader
- Document 对象
- 文本切块
- 批量导入
- 编码自动识别
- embedding
- 向量库
- `/chat`

### 当前理解

TXT loader 是 RAGHub 输入链路的第一步。  
它的作用不是完成 RAG，而是先验证系统可以从本地文档中读取原始文本。后续 PDF 导入、统一文档对象和文本切块都会建立在这个输入链路基础上。