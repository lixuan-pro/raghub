# RAGHub

本项目是一个面向本地文档的检索增强问答系统，目标是逐步完成文档导入、切块、检索、生成与评测全链路。

## Current Progress
- 初始化 FastAPI 项目骨架
- 提供 /health 与 /version 接口
- 增加最小配置文件
- 编写首个接口测试

## Run
```bash
uvicorn app.main:app --reload
```

## Test
```bash
pytest
```

## Project Structure
```text
raghub/
├─ app/
├─ docs/
├─ tests/
├─ .env.example
├─ README.md
└─ requirements.txt
```