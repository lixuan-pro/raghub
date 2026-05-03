# RAGHub

RAGHub 是一个面向本地文档的检索增强问答系统，目标是逐步完成文档导入、文本切块、检索召回、问答生成与评测展示的完整链路。

当前项目处于 Week 1：工程骨架与基础设施阶段。

## Current Stage

当前阶段目标是先搭建一个稳定的 FastAPI 后端工程骨架，做到：

- 服务可以启动
- 基础接口可以访问
- 配置可以集中管理
- 日志可以正常输出
- 测试可以自动运行
- 代码可以提交到 GitHub

当前暂不进入 TXT/PDF 文档导入、文本切块、向量检索和 `/chat` 问答接口。

## Features

当前已完成：

- FastAPI 最小后端服务
- `/health` 健康检查接口
- `/version` 版本信息接口
- `.env.example` 配置模板
- `app/core/config.py` 配置模块
- `app/core/logger.py` 日志模块
- pytest 基础接口测试
- README 与周志初始化
- GitHub main / develop 分支管理

## Project Structure

```text
raghub/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  └─ core/
│     ├─ __init__.py
│     ├─ config.py
│     └─ logger.py
├─ tests/
│  └─ test_health.py
├─ docs/
│  └─ weekly_logs/
│     └─ week1.md
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

## Test

运行测试：

```bash
python -m pytest
```

当前测试内容：

- `/health` 状态码和返回内容
- `/version` 状态码和版本字段

## Roadmap

接下来计划：

1. 完善 Week 1 基础设施
   - 日志模块
   - 配置模块
   - README
   - 基础测试
2. Week 2 进入文档导入
   - TXT loader
   - PDF loader
   - 统一 Document 对象
3. 后续逐步实现
   - 文本切块
   - 向量检索
   - RAG 问答接口
   - 评测与展示