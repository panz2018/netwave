# Tasks

本 change 无 core 数值实现（铁律二 red/green 循环不适用）；闸门脚本按
"先构造已知漂移输入、看闸门变红，再让它变绿"的等价 red-first 执行。

## 1. RED：钉死新闸门必须抓住的失败形态

- [x] 1.1 临时删 `typescript/wasm/Cargo.toml` 的 `rust-version`，跑
      `python3 scripts/check_version_pins.py`，记录旧闸门的 FAIL 输出——
      这是新 MSRV 检查必须等价复现的能力（缺字段即 FAIL）。验证后恢复。
- [x] 1.2 临时新建一个带 `rust-version` 的 throwaway 子项目 Cargo.toml，
      确认闸门因"钉版点未登记"FAIL。验证后删除 throwaway。

## 2. GREEN：登记表瘦身

- [x] 2.1 `scripts/version_pins.json`：`rust-msrv.pin_location` 改为
      `"discovered:workspace-members"`，`upgrade_method` 的 "all four
      equal" → "all workspace members equal"；`ci-actions` 删 `watch`
      列表与 `upgrade_method` 的 "every uses: line must appear in watch"
      半句。其余条目零改动。验证：json 解析成功、`git diff` 仅命中这两条。

## 3. GREEN：闸门改造

- [x] 3.1 `scripts/check_version_pins.py`：位置存在性检查跳过 `machine:`
      与 `discovered:` 前缀；MSRV 检查重写为 members 权威（根 `Cargo.toml`
      `members` 每个成员必须带 `rust-version`、全部相等、≤ pin）；
      ci-actions watch 双向核对整段删除，剩余检查重编号连续；模块 docstring
      重写为新检查清单，每段检查顶部一句大白话目的注释（只写当前契约事实，
      不留考古叙述）。
      验证：1.1、1.2 的漂移输入变红、现状全绿。

## 4. 验收

- [x] 4.1 `pnpm check:meta` 全绿；复跑两条破坏测试（删某成员
      `rust-version` → FAIL；throwaway 未登记成员带 `rust-version` → FAIL），
      验证后恢复并确认复绿。
- [x] 4.2 `pnpm check:md` 全绿（覆盖第 5 节的 Plan/ 改动）。

## 5. Plan 收口

- [x] 5.1 `Plan/测试规划.md`：登记表瘦身小节改写为已拍板结论 + 指向本
      change；落地形态段改为"登记表瘦身独立先行，过期检查门禁化、bug 版本
      黑名单、配对版本约束三问留待议"。验证：`pnpm check:md` 全绿。
