# Tasks

> **⏸ 暂停实施（勿 apply）**：本 change 是升级流程的首次实战，但升级所依赖的
> 治理机制尚未拍板，机制没搞定就无法有效执行升级：
>
> 1. **过期检查门禁化**——哪些该升、哪些不该升尚无机器判定（选线判断仍靠人工，
>    无法在闸门里区分"例行刷新"与"须走 change 的结构升级"）；
> 2. **登记表分工**——`versions.json` 与发现式扫描的边界未确认，登记表如何
>    使用未定案；
> 3. **`paired_with` 版本相容校验**——当前闸门只验配对名存在、不验版本相容，
>    拦不住 pyo3↔numpy 这类配对漂移，升级联动无兜底。
>
> 三项见 [Plan/测试规划.md 待议节](../../../Plan/测试规划.md#待议过期检查门禁化--配对版本校验)，
> 须先专门拍板并落成机制（闸门规则/登记表字段），再恢复本 change。
> 另：tasks 3.1 / 4.1 假设 oracle uv 环境已存在可"重建"，实际尚未建成，
> 恢复时一并修正。

前置：`add-dependency-upgrade-spec` 已归档（登记表/闸门/体检命令/流程规则就位）。
本 change 是该 spec 升级流程的首次实战，流程走不通之处当轮回写 spec 或账本。

## 1. 体检与运行时准备

- [ ] 1.1 跑 `pnpm check:outdated`，全局 CLI（uv 等）落后 LTS/稳定线的先升级。
      验证：uv 版本为最新稳定版。
- [ ] 1.2 `uv python install 3.15`，本地可用 3.15 解释器。
      验证：`uv run --project python python --version` 输出 3.15.x（先改
      `.python-version` 或显式 `--python 3.15`）。

## 2. pyo3 0.30 配对迁移

- [ ] 2.1 `python/Cargo.toml`：pyo3 0.29→0.30、numpy 0.29→0.30、
      pyo3-stub-gen 升至兼容 pyo3 0.30 的版本（crates.io 元数据核实配对）。
      验证：`cargo check -p netwave-python` 通过或产出完整报错清单。
- [ ] 2.2 按编译报错逐项适配 `python/src/lib.rs`（`FromPyObject` 默认不再生成、
      abi3 feature 逻辑、`PyBuffer` 弃用方法等）。验证：
      `cargo check --workspace` 与 `pnpm check:rs` 全绿。
- [ ] 2.3 `uv sync --project python` + `maturin develop` + pytest 全绿
      （3.15 环境；pyo3 venv 三件套环境变量按账本 LL-014）。
      验证：pytest 全绿且 `netwave/_netwave.pyi` stub 再生成无 diff 异常。

## 3. oracle 与依赖刷新

- [ ] 3.1 oracle uv 环境在 3.15 下重建 lock（skrf 2.2 支持 3.15），
      golden 生成链在 3.15 下跑通。验证：golden 数值与 3.14 结果 bit 级一致
      （同 skrf 版本仅换 minor）。
- [ ] 3.2 `uv lock --upgrade --project python` 例行刷新 dev 组
      （maturin/pytest/ruff）。验证：`pnpm check:py` 全绿。

## 4. 配置与文档同步

- [ ] 4.1 `python/.python-version` 改 3.15；`scripts/versions.json` 更新
      Python 相关条目（运行时、矩阵、oracle 环境）。验证：
      `python3 scripts/check_versions.py` 全绿。
- [ ] 4.2 `.github/workflows/ci.yml` python 矩阵最新格 3.14→3.15（底线 3.10
      不变；runner 无预装则显式 `uv python install 3.15`）。验证：
      本地按 LL-004 模拟两格命令均通过。
- [ ] 4.3 grep 全仓 `3\.14` 残留并清除（登记表/lockfile/归档除外）；
      `pnpm check:md` 全绿。

## 5. 收尾验收

- [ ] 5.1 `pnpm check` 全绿 + `pnpm check:cross` 四端对拍通过（数值契约不变，
      铁律三容差不变）。
- [ ] 5.2 retro：pyo3 0.30 迁移坑与流程摩擦点回写 lessons-learned
      （python scope 分片 + INDEX）；登记表/流程 spec 漏项当轮补全。

## Workflow follow-up

- 用户确认后走 apply；完成并 review 后 `/opsx:archive`（skip_specs 无 sync）。
- 提交分组由人工确认后执行（agent 不主动 commit）。
