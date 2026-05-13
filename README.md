# RAGHub

RAGHub 是一个面向本地文档的检索增强问答系统，目标是逐步完成文档导入、文本切块、检索召回、问答生成与评测展示的完整链路。

当前项目已完成 Week 1 工程骨架收口，并进入 Week 2：文档导入阶段。

## Current Stage

当前阶段目标是从最小输入链路开始，先完成本地 TXT 文档读取能力。

当前已经完成：

- FastAPI 后端工程骨架
- 基础配置与日志模块
- `/health` 和 `/version` 基础接口
- pytest 基础测试
- Week 1 周志、论文占位、评测占位和项目讲解稿
- TXT loader 最小版

当前暂不进入 PDF loader、DOCX loader、统一 Document 对象、文本切块、向量检索和 `/chat` 问答接口。

## Features

当前已完成：

- FastAPI 最小后端服务
- `/health` 健康检查接口
- `/version` 版本信息接口
- `.env.example` 配置模板
- `app/core/config.py` 配置模块
- `app/core/logger.py` 日志模块
- FastAPI lifespan 启动日志
- pytest 基础接口测试
- `app/loaders/txt_loader.py` TXT 文档读取模块
- `data/raw/sample.txt` 最小样本文档
- `tests/test_txt_loader.py` TXT loader 测试
- README 与周志
- 论文材料占位目录 `docs/thesis/`
- 评测样例占位文件 `eval/queries.jsonl`
- GitHub main / develop 分支管理

## Project Structure

```text
raghub/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ core/
│  │  ├─ __init__.py
│  │  ├─ config.py
│  │  └─ logger.py
│  └─ loaders/
│     ├─ __init__.py
│     └─ txt_loader.py
├─ data/
│  └─ raw/
│     └─ sample.txt
├─ tests/
│  ├─ test_health.py
│  └─ test_txt_loader.py
├─ docs/
│  ├─ weekly_logs/
│  │  ├─ week1.md
│  │  └─ week2.md
│  ├─ thesis/
│  │  └─ README.md
│  └─ project_explanation_week1.md
├─ eval/
│  └─ queries.jsonl
├─ .env.example
├─ .gitignore
├─ README.md
└─ requirements.txt
```

## Environment

建议使用 Python 3.10+。

安装依赖：

```bash
pip install -r requirements.txt
```

## Configuration

项目使用 `.env.example` 作为配置模板。

当前配置项：

```env
APP_NAME=RAGHub
APP_VERSION=0.1.0
DEBUG=true
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=INFO
```

如需本地自定义配置，可复制一份 `.env`：

```bash
copy .env.example .env
```

`.env` 不应提交到 GitHub。

## Run

启动服务：

```bash
uvicorn app.main:app --reload
```

访问接口：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/version
```

预期结果：

```json
{"status":"ok"}
```

```json
{"version":"0.1.0"}
```

## TXT Loader

当前已实现最小 TXT 文档读取函数：

```python
from app.loaders.txt_loader import load_txt

content = load_txt("data/raw/sample.txt")
print(content)
```

当前 TXT loader 只负责读取本地 `.txt` 文件并返回字符串内容。

暂不处理：

- metadata
- Document 对象
- 批量导入
- 编码自动识别
- 文本切块

## Test

运行测试：

```bash
python -m pytest
```

当前测试内容：

- `/health` 状态码和返回内容
- `/version` 状态码和版本字段
- TXT loader 能读取 `data/raw/sample.txt`
- TXT loader 返回内容为字符串
- TXT loader 返回内容包含指定关键词

当前测试结果：

```text
3 passed
```

## Roadmap

接下来计划：

1. Week 1：工程骨架与基础设施【已完成】
   - FastAPI 最小服务
   - `/health` 和 `/version`
   - 配置模块
   - 日志模块
   - pytest 基础测试
   - README、周志、论文占位、评测占位和讲解稿

2. Week 2：文档导入【进行中】
   - TXT loader 最小版【已完成】
   - PDF loader
   - 统一 Document 对象
   - 文本切块

3. 后续逐步实现
   - 向量检索
   - RAG 问答接口
   - 评测与展示