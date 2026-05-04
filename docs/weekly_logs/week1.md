---

## Day 2 - 配置、日志与基础测试增强

### 今日目标

将 Day 1 的最小可运行骨架进一步整理成更稳定的工程基础，重点补齐配置管理、日志模块、基础测试、README 和 develop 分支流程。

### 完成内容

- 从 `main` 创建并推送 `develop` 分支，作为后续日常开发分支。
- 扩展 `.env.example`，增加 `DEBUG`、`HOST`、`PORT`、`LOG_LEVEL` 等配置项。
- 扩展 `app/core/config.py`，将项目配置集中管理。
- 新增 `app/core/logger.py` 日志模块，实现控制台日志输出。
- 在 `app/main.py` 中使用 FastAPI `lifespan` 接入启动日志。
- 用 `lifespan` 替代旧的 `@app.on_event("startup")` 写法，清除 deprecated warning。
- 补充 `/version` 接口测试。
- 更新 `README.md`，补充项目结构、配置、运行方式、测试方式和 Roadmap。
- 运行 `python -m pytest`，当前结果为 `2 passed`。
- Day 2 代码改动已提交并推送到 `develop` 分支。

### 当前理解

Day 2 仍然属于 Week 1 工程基础设施阶段，不进入 RAG 业务功能。配置和日志不是直接的 RAG 功能，但它们会支撑后续文档导入、切块、检索和问答接口的稳定开发。

### 测试结果

命令：`python -m pytest`

结果：`2 passed`

### 简历素材草稿

从 0 搭建 RAGHub 的 FastAPI 后端工程骨架，完成配置管理、日志模块、基础接口测试与 GitHub 分支管理，建立可运行、可测试、可持续扩展的项目基础。

### 下一步

- 建立 `docs/thesis/` 占位文件。
- 建立 `eval/queries.jsonl` 占位文件。
- 最后运行一次 `python -m pytest`。
- 完成 Week 1 收口提交并推送到 `develop` 分支。


