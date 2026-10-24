# Design

## Context

See proposal.md - Why. 前置：`add-dependency-upgrade-spec` 已落地（登记表、
闸门、体检命令、选线/流程规则）。当前 Python 侧：`python/.python-version`
钉 3.14、`requires-python >= 3.10`、pyo3 0.29（abi3-py310）+ numpy 0.29 +
pyo3-stub-gen 0.23；CI python job 跑 3.10 + 3.14 两格。

## Goals / Non-Goals

**Goals:**

- Python 3.15 + pyo3 0.30 迁移一次到位，四端对拍数值不变。
- 作为 `dependency-upgrade` spec 升级流程的首次实战：流程走不通之处当轮回写
  spec/账本（该 spec 的经验回写 Requirement）。

**Non-Goals:**

- 见 proposal Non-goals（底线、abi3、新特性采纳均不动）。

## Decisions

- **pyo3 与 numpy 同 major 联动**（0.29→0.30 成对升，AGENTS.md 配对规则；
  pyo3-stub-gen 升至声明兼容 pyo3 0.30 的版本，实施时以 crates.io 元数据为准）。
- **breaking changes 以编译报错驱动逐项处理**，不预防性重写：已知大头是
  `#[pyclass]` 默认不再生成 `FromPyObject`（netwave 若依赖该 derive 则显式加
  `#[derive(FromPyObject)]` 或改用 `Bound` 转换）、abi3 feature 选择逻辑变更、
  `PyBuffer::as_slice` 系列弃用（零拷贝路径若用到则改 `as_bytes`/指针系）。
- **先本地 3.15 环境验证再动 CI**：`uv python install 3.15` +
  `uv sync --project python` + `maturin develop` + pytest 全绿后，才改
  `.python-version` 与 CI 矩阵（LL-004：禁止 push-and-pray）。
- **oracle uv 环境同 change 重建**：golden 生成侧 skrf 在 3.15 下重锁，
  golden 数值与 3.14 结果对拍应 bit 级一致（同 skrf 版本仅换 minor）。

## Risks / Trade-offs

- [pyo3 0.30 迁移面比预期大（stub-gen 链）] → 编译报错驱动 + 分步提交；
  若 stub-gen 无兼容版本，回退策略=暂缓 stub 功能并记账本（不阻塞主迁移）。
- [abi3-py310 wheel 在 3.15 解释器上的行为差异] → pytest + check:cross
  在 3.15 下全跑，数值契约由 manifest 容差守护。
- [uv 托管的 3.15 与 CI runner 可用性时间差] → CI 改用 `uv python install 3.15`
  显式安装，不依赖 runner 预装。

## Migration Plan

1. 全局 CLI 体检（uv 是否落后稳定线，落后先升）。
2. 本地：uv 装 3.15 → 升 pyo3/numpy/stub-gen → 编译报错逐项适配 →
   maturin develop → pytest 全绿。
3. 依赖刷新：`uv lock --upgrade --project python`、oracle uv.lock 重建。
4. 配置：`.python-version`、CI python 矩阵 3.14→3.15、登记表更新。
5. 全闸门 + 四端对拍 + grep 3.14 残留。
   回滚：git revert（版本钉全部在清单/登记表，revert 即回 3.14）。

## Open Questions

- 无（stub-gen 兼容版本在实施 step 2 用 crates.io 元数据确定，不影响计划结构）。
