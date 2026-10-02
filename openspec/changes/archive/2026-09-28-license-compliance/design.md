# Design

## 许可选型结论（已拍板）

MIT OR Apache-2.0 双许可，使用者任选一侧。理由：Rust 数值库生态事实
标准（serde/tokio/rayon/pyo3 同款）；Apache-2.0 §3 明示专利授权覆盖 RF
算法领域风险，MIT 侧给嫌条款长的下游零负担；两侧对 scikit-rf BSD-3
数据全兼容。免责（AS IS）由两份许可自带，README 补一句人话版。

## 三层归位

| 内容                                  | 层              | 落点                          |
| ------------------------------------- | --------------- | ----------------------------- |
| 知识产权合规原则                      | 宪法            | governance 元规则（本次新增） |
| 参考第三方前查许可表                  | 行为准则        | AGENTS.md 一行指针            |
| 第三方许可表（URL）+ GPL 红线         | 事件级事实      | lessons-learned docs 分片 LL  |
| 许可落地细节（文件/元数据/登记/门禁） | capability spec | `license-compliance`          |

## check_license.py 设计

纯标准库（与 check_md.py 同风格）：读根声明常量 `MIT OR Apache-2.0`，
逐一比对 4×`Cargo.toml`（正则匹配 license 行）、`typescript/package.json`
与 `python/pyproject.toml`（JSON/TOML 字符串字段）；漂移打印
`LICENSE DRIFT <file>: <found>` 并退出 1。并入根 `package.json`
`check:meta` 脚本，`pnpm check` 聚合调用。

## 版权人

`Copyright (c) 2026 panz2018`（GitHub handle，法律有效；与老项目
RF-Touchstone 署名一致；用户确认无职务发明冲突）。

## 门禁分期

本次仅元数据一致性（阶段 0 无实质借鉴代码）；GPL 特征头扫描、
rustdoc 出处覆盖率检查留待阶段 1/2 有真实代码后另行立项（Non-goals）。
