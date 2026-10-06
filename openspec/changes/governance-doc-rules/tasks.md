# Tasks: governance-doc-rules

## 1. 应用 delta 至主 spec

- [x] 1.1 sync：「教学式文档与类型标注」修订版（去绝对路径、补引用格式与
      指针）写入 `openspec/specs/project-governance/spec.md`
- [x] 1.2 sync：新增元规则「注释只写当前事实」
- [x] 1.3 验证 sync 无重复需求块（LL-028）

## 2. 门禁脚本

- [x] 2.1 新建 `scripts/check_comments.py`：动态改动名名单（changes +
      archive 目录名剥日期前缀，减去活 spec 能力名）+ 硬编码阶段词
      （`stage [0-9]`/`phase-[0-9]`/`skeleton`/`arrives with`）；扫
      `.rs`/`.py`/`.ts` 注释与 `openspec/specs/**/*.md`；豁免治理 spec 本文、
      账本、archive、`node_modules`/`target`/`dist`/`.venv`
- [x] 2.2 根 `package.json` `check:meta` 挂入 `scripts/check_comments.py`
- [x] 2.3 反向验证（LL-004）：临时注入含改动名注释 → 门禁红；删除 → 绿
- [x] 2.4 存量修复：`core/tests/frequency_memory.rs` 首行 `skeleton` 改写
      为当前事实描述

## 3. CONTRIBUTING.md

- [x] 3.1 文件末尾新增「Local reference mirrors (this machine only)」节
      （英文）：4 真参考表（两书 + scikit-rf + SignalIntegrity，含许可红线）+
      换机 `ls` 自检指引
- [x] 3.2 其下 `###` 子段「Predecessor project (not a reference)」标注
      RF-Touchstone（`/config/GitHub/RF-Touchstone/`，MIT，panz2018）

## 4. AGENTS.md

- [x] 4.1 「语言」节补一行：向用户提问与解释先大白话再术语，禁堆术语
- [x] 4.2 「通用原则」节末新增 `### 对话效率`：实证 / 全景表 / 查现成 /
      会话卫生四条单行要点

## 5. 闸门

- [x] 5.1 `pnpm check:md` 退出码 0
- [x] 5.2 `pnpm check:meta` 退出码 0（含新门禁）
- [x] 5.3 `openspec validate` 通过

## 6. Plan/ 瘦身（archive 时）

- [x] 6.1 删除 `Plan/频率类设计.md`「教学式文档元规则补充」「对话效率
      准则」全节与「实现清单」`governance-doc-rules` 相关条目
- [x] 6.2 新立 `Plan/文档卫生清理.md`：主 spec「阶段 N」存量 15 处清理
      任务（LL-032 存量）
