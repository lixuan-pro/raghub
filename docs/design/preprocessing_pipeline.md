# RAGHub 文档导入与预处理链路设计说明

## 1. 当前输入支持范围

Week 2 当前支持两类本地文档输入：

- TXT 文档：通过 `load_txt_documents()` 读取
- PDF 文档：通过 `load_pdf_documents()` 按页读取

当前输入样例包括：

- `data/raw/sample.txt`
- `data/raw/sample.pdf`

当前暂不支持：

- DOCX
- 扫描版 PDF / OCR
- 图片内容识别
- 复杂表格解析

## 2. 为什么先统一成 Document

TXT 和 PDF 的原始读取结果不同：

- TXT 原始读取结果是 `str`
- PDF 原始读取结果是 `list[str]`

如果直接进入后续处理，切块模块就需要分别处理 TXT 和 PDF，代码会出现分支。

因此 Week 2 先设计了最小版 `Document` 对象，用于统一不同来源的文档内容。

当前 `Document` 字段包括：

- `content`：文档内容
- `source`：来源文件路径
- `file_type`：文件类型，例如 `txt` 或 `pdf`
- `page`：页码，TXT 当前为 `None`，PDF 从第 1 页开始记录

统一后的主链路是：

```text
TXT / PDF
→ loader
→ list[Document]
```

这样后续切块模块只需要处理 `list[Document]`，不用关心原始文件格式。

## 3. 为什么切块先用固定长度 + overlap

Week 2 当前采用最小切块策略：

- 按字符长度切块
- 支持 overlap
- 切块后仍然输出 `list[Document]`
- 保留原始 `source`、`file_type` 和 `page`

当前没有直接使用 token 切块、语义切块或中文分词切块。

原因是当前阶段目标不是追求最优切块策略，而是先跑通稳定的预处理主链路：

```text
Document 列表
→ 固定长度 + overlap 切块
→ chunk 后的 Document 列表
```

固定长度 + overlap 的好处是：

- 实现简单
- 行为可预测
- 方便测试
- 能为后续 embedding 和检索提供最小可用输入

更复杂的切块策略会放到后续优化阶段。

## 4. 当前输出产物

Week 2 当前输出产物为：

```text
data/processed/chunks_preview.jsonl
```

该文件由脚本生成：

```bash
python scripts/build_chunks_demo.py
```

脚本流程：

```text
data/raw/sample.txt
data/raw/sample.pdf
→ load_txt_documents()
→ load_pdf_documents()
→ 合并为 list[Document]
→ chunk_documents()
→ 写入 data/processed/chunks_preview.jsonl
```

当前 `chunks_preview.jsonl` 每行包含：

- `content`
- `source`
- `file_type`
- `page`

示例：

```json
{"content": "RAGHub is a local document question answering proj", "source": "data/raw/sample.txt", "file_type": "txt", "page": null}
```

该文件当前用于预览文档导入与切块结果，不作为最终向量索引格式。

## 5. 当前阶段边界

Week 2 当前已经完成：

- TXT 最小读取
- PDF 最小读取
- 最小版 `Document` 对象
- 固定长度 + overlap 文本切块
- 预处理结果 JSONL 落盘
- Week 2 最小评测占位

当前暂未进入：

- chunk_id
- metadata 扩展
- embedding
- 向量库
- BM25
- `/retrieve`
- `/chat`

下一阶段将围绕 embedding 最小化实现展开。