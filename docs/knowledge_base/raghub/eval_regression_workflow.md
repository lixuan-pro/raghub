# Eval 回归工作流

## 1. 背景

RAGHub 每次扩展语料后都需要运行 eval 回归。回归不是为了追求单一高分，而是为了观察 source_hit、keyword_hit、answerability_judgment_accuracy 和 out_of_corpus_rejected 是否出现异常变化。若 source_hit 下降，需要检查新增文档是否与原问题产生竞争；若 keyword_hit 下降，需要检查 expected_keywords 是否仍合理；若 out-of-corpus 被误判为可回答，需要更新 no-answer 或 bad case。这个流程让项目从单次 demo 变成可持续复盘的工程样例。

## 2. 执行方式

RAGHub 每次扩展语料后都需要运行 eval 回归。回归不是为了追求单一高分，而是为了观察 source_hit、keyword_hit、answerability_judgment_accuracy 和 out_of_corpus_rejected 是否出现异常变化。若 source_hit 下降，需要检查新增文档是否与原问题产生竞争；若 keyword_hit 下降，需要检查 expected_keywords 是否仍合理；若 out-of-corpus 被误判为可回答，需要更新 no-answer 或 bad case。这个流程让项目从单次 demo 变成可持续复盘的工程样例。

## 3. 风险边界

RAGHub 每次扩展语料后都需要运行 eval 回归。回归不是为了追求单一高分，而是为了观察 source_hit、keyword_hit、answerability_judgment_accuracy 和 out_of_corpus_rejected 是否出现异常变化。若 source_hit 下降，需要检查新增文档是否与原问题产生竞争；若 keyword_hit 下降，需要检查 expected_keywords 是否仍合理；若 out-of-corpus 被误判为可回答，需要更新 no-answer 或 bad case。这个流程让项目从单次 demo 变成可持续复盘的工程样例。

## 4. 面试表达

RAGHub 每次扩展语料后都需要运行 eval 回归。回归不是为了追求单一高分，而是为了观察 source_hit、keyword_hit、answerability_judgment_accuracy 和 out_of_corpus_rejected 是否出现异常变化。若 source_hit 下降，需要检查新增文档是否与原问题产生竞争；若 keyword_hit 下降，需要检查 expected_keywords 是否仍合理；若 out-of-corpus 被误判为可回答，需要更新 no-answer 或 bad case。这个流程让项目从单次 demo 变成可持续复盘的工程样例。
