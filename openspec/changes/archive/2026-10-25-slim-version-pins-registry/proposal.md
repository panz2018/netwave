# Proposal

## Why

登记表现存两处手抄的"闸门本就能扫描发现的位置清单"：`rust-msrv` 的四个
`Cargo.toml` 路径与 `ci-actions` 的六条 `watch`。闸门对 `rust-version` 与
workflow `uses:` 行的核对早已是发现式扫描，json 再抄一份 = 第二真相源——
改一处忘另一处必漂移，新增子项目还得手动同步清单。

同时纯发现扫描有个盲区：扫描只看得见"带字段的文件"，某成员删掉
`rust-version` 后该 MSRV 钉静默蒸发、闸门全绿。本 change 把位置交给发现规则、
登记表只留扫描给不了的知识（升级方法、配对、machine 钉），并以 workspace
成员清单为权威堵住逃逸盲区。

## What Changes

- `scripts/version_pins.json`：
  - `rust-msrv.pin_location` 由四文件列表改为哨兵值
    `"discovered:workspace-members"`（位置由闸门发现规则提供）；
    `upgrade_method` 措辞 "all four equal" → "all workspace members equal"。
  - `ci-actions` 条目删 `watch` 列表；`upgrade_method` 删
    "every uses: line must appear in watch" 半句（action 新旧检测已由
    `check_outdated.py` 直接扫 `uses:` 行覆盖）。
- `scripts/check_version_pins.py`：
  - 位置存在性检查跳过 `machine:` 与 `discovered:` 前缀；
  - MSRV 检查重写：根 `Cargo.toml` 的 `members` 清单为权威——每个成员的
    `Cargo.toml` MUST 带 `rust-version`，全部相等且 ≤ toolchain pin
    （堵"删字段逃逸"盲区）；
  - ci-actions watch 双向核对整段删除，剩余检查重编号为连续序号；
  - 模块 docstring 重写为新检查清单；每段检查顶部一句大白话目的注释。
- `openspec/specs/dependency-upgrade/spec.md`（delta，见
  [specs/dependency-upgrade/spec.md](specs/dependency-upgrade/spec.md)）：
  钉版位置补 `discovered:` 形态；"四处" 措辞改"全部 workspace 成员"；
  新增"成员丢 MSRV 钉静默逃逸"场景。
- `Plan/测试规划.md`：登记表瘦身小节改写为已拍板结论 + 指向本 change；
  落地形态段改为瘦身独立先行、其余三问留待议。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `dependency-upgrade`：钉版位置新增 `discovered:` 发现规则形态；MSRV
  一致性规则从"四处彼此一致"升级为"全部 workspace 成员必须携带且彼此一致"。

## Impact

- 工具：`scripts/version_pins.json`、`scripts/check_version_pins.py`
  （仍纯标准库，无新依赖）。
- 文档：`openspec/specs/dependency-upgrade/spec.md`（随归档 sync）、
  `Plan/测试规划.md`。
- CI：无改动——`check:meta` 已接闸门，命令不变。
- 不碰 core 数值代码、API、容差 manifest；属 governance 类变更。

## Non-goals

- 不做过期检查 CI 门禁、bug 版本黑名单（`blocked`）、配对版本约束
  （`constraint`）——三问留在
  [测试规划·待议](../../../../Plan/测试规划.md#待议过期检查门禁化--配对版本校验)
  将来另议。
- 不删 `ci-actions` 条目本身——它还扛 action 升级方法的程序性知识。
- 不删 `verified` 字段——配对验证证据随条目入库。
- 不改单文件 `pin_location`——它是条目↔文件的身份映射，未登记检测的地基。
- 不改 `check_outdated.py`——它本就直接扫 `uses:` 行，不依赖 watch。
