# Design

## Context

See proposal.md - Why. 现状：`rust-msrv` 条目手抄四个 `Cargo.toml` 路径、
`ci-actions` 条目手抄六条 `watch`；闸门（`scripts/check_version_pins.py`）
的 MSRV 一致性与未登记检测已是发现式扫描，watch 双向核对完全依赖手抄清单。
根 `Cargo.toml` 的 `members = ["core", "python", "typescript/native",
"typescript/wasm"]` 是成员清单的仓库内权威来源。

## Goals / Non-Goals

**Goals:**

- 登记表只存扫描发现不了的知识：升级方法、配对、machine 钉、条目身份；
  位置清单类冗余清零。
- MSRV 对账以 workspace 成员清单为权威：带字段的一致、缺字段的逃逸、
  新成员的纳入，三种形态全覆盖。
- 闸门代码注释达到"一句大白话看懂这段拦什么"的标准。

**Non-Goals:**

- 不动过期体检命令、不引入 `blocked`/`constraint` 字段（另议）。
- 不改 `check:meta` 接线与 CI 结构。

## Decisions

- **`discovered:` 为通用前缀机制（非 msrv 特判）**：`pin_location` 值三形态
  ——文件路径、`machine:`（机器环境钉）、`discovered:`（发现规则）；前缀后是
  规则名，规则名→扫描函数的映射表在闸门脚本内。与 `machine:` 同构，位置语义
  显式写在 json 值里，比藏在脚本的类别判断诚实。备选"category == msrv 特判"
  否决：把定位规则藏进脚本，json 读者看不见条目靠什么定位。
- **哨兵名取 `discovered:workspace-members`（非 `discovered:rust-version`）**：
  权威来源是根 `Cargo.toml` 的 `members` 清单，不是"扫谁带字段"——后者正是
  逃逸盲区的来源，名字即规则。
- **MSRV 检查以 members 为权威重写**：每个成员 MUST 携带 `rust-version`
  （缺 = FAIL）、全部相等、全部 ≤ pin major.minor。一条规则同时替代旧检查 3
  的"登记表列表反向核对"与未登记检测对 msrv 的覆盖，且比现状更强：旧机制下
  json 列表漏登记的新 crate 缺 `rust-version` 反而查不到。
- **ci-actions watch 双向核对整段删除**：watch 没了对照物，保留空壳检查只
  增加噪音；action 的新旧检测由 `check_outdated.py` 直接扫 `uses:` 行完成
  （已实现，零依赖 watch）。`ci-actions` 条目保留——`upgrade_method` 里
  "routine bump、major-only tag 只比 major"是扫描给不了的判断标准。
- **`verified` 字段保留**：配对验证证据随条目入库，与将来 `blocked` 的
  issue 链接同性质；赶回散文违背登记表消灭散落副本的初衷。
- **注释标准**：模块 docstring = 新检查清单逐条一句话；每段检查顶部一句
  大白话目的（例：`# MSRV: every workspace member must pin rust-version
  (missing = FAIL, so deleting the field cannot silently escape)`）。
  只写当前契约事实，不写"以前有 watch"式考古，追溯靠 git log。

## Risks / Trade-offs

- [哨兵前缀是新增约定，读者需知道语义] → spec 场景已写明三种位置形态；
  闸门 docstring 同步列出前缀含义。
- [members 清单若被手改短（删成员）] → 成员删除本身必现于 diff 且 cargo
  构建当场失败，属 code review + 构建闸门双拦，不在本闸门重复设防。
- [删 watch 后"登记表列 action"能力消失] → 可接受：action 清单的真相源
  本就是 workflow 文件，登记表只留升级方法。

## Migration Plan

1. 先构造两类漂移输入定基线（成员缺 `rust-version`、新成员未登记），
   确认旧闸门变红形态。
2. 改 json（哨兵 + 删 watch）+ 改闸门（前缀跳过、MSRV 重写、删 watch 核对、
   重编号、注释重写），同一笔提交内完成，避免中间态红。
3. `pnpm check:meta` 全绿 + 两条破坏测试复验；Plan/ 收口。

回滚：单 change 单提交，`git revert` 即整体回退。
