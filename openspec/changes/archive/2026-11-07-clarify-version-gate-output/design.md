# Design

## Context

See proposal.md - Why. 现状输出（实测 2026-11-06）：

- 闸门通过行：`version laws OK: 4 workspace members consistent (rust-version 1.99, pin 1.99.1)`
- 体检 python 行：`python pin python/.python-version 3.14     latest stable minor: 3.15 LAG`
  （长路径溢出错位）
- 段 2/3 比较行无状态标记；段 4 已有 `OK`/`LAG`/`REF`
- 四律真实覆盖面：律1=4 members、律2=2 pyproject、律3=1 package.json、
  律4=2 `.python-version`（CI cells 3.10/3.14）

约束：摘要行措辞是 `split-version-gates` 定的输出契约，改措辞即本 change；
`test_check_versions.py` 以 monkeypatch 假摘要测门面，不受措辞影响。

## Goals / Non-Goals

**Goals:**

- versions 域输出零黑话、四律覆盖面一眼可见、落后状态一眼可见。
- 每处措辞有测试锁定（TDD 先 red）。

**Non-Goals:**

- 见 proposal.md Non-goals；设计层追加：不改 `summary()` 的函数签名与
  `all_laws()` 结构（计数从 `lib/repository.py` 现成函数取，不新增扫描逻辑）。

## Decisions

1. **摘要行措辞定稿**（人工裁决，四律并列一行）：
   `version laws OK: rust {n} members (rust-version {v}, toolchain {c}), python {n} projects, pnpm {n} manifests, ci {n} python-version files`
   计数=各律检查到的文件数：律1 `rust_versions`，律2 `find_files` 配合
   `is_python_project`，律3 `find_package_managers`，律4 `find_python_versions`。
   备选"只报总数 4 laws checked"被否——信息倒退；备选 `ci n pins` 被否——
   pins 仍是黑话。
2. **python 行格式**：`python-version {path:24s} {cur:8s} -> latest stable {latest:8s} {mark}`
   ——字段名照抄 `.python-version`（AGENTS.md 与被检字段同名可追溯），`->` 表
   当前→最新，列宽 24 容纳 `python/.python-version` 不溢出。WARN 降级行同步：
   `python-version files: WARN ({e})`。
3. **段 2/3 补标记**：所有比较行尾部 `OK`/`LAG`，复用 `is_outdated`；
   取数口径先剥壳——`clean_version()` 剥工具名前缀（uv、rustc、rustup、
   wasm-pack、wasm-opt version、markdownlint-cli2）与 `(arch...)` 括号后缀，
   `latest` 侧剥 `v` 前缀。
   比较失败（剥壳后仍不可解析）降级 `?`，不误报 LAG。备选"段 2/3 不动"被否——
   spec「一条命令看全貌」已要求输出是否落后。
4. **README 不补示例输出行**（人工裁决：使用方法够用、输出细节易变）；仅核对
   既有描述（`WARN` 降级、退出码）不变旧。
5. **skip_specs 纯执行**：段 2/3 标记=履行现有 spec 条款；摘要格式不进 spec
   （易变细节，测试即契约）。

## Risks / Trade-offs

- [剥壳正则漏了某工具的输出形状] → 解析失败降级 `?` 标记而非误判 LAG/OK；
  夹具覆盖 uv/rustc/rustup/wasm-opt/markdownlint 五种实测形状。
- [改措辞破坏未知消费者] → 全仓 grep `version laws OK` 仅测试与文档命中，
  CI 不解析该字符串；体检输出 informational 无消费者。
- [段 2/3 标记让报告变长] → 每行只增 4 字符，可忽略。

## Migration Plan

TDD：先改 `test_rules.py` 摘要逐字断言与 `test_check_outdated.py` 新格式断言
（red），再改实现（green）。回滚 = `git revert`（无数据/配置迁移）。
