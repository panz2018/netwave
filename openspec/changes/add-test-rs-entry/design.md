# Design

## Context

见 proposal.md - Why。当前状态：rust 覆盖率链内联在 ci.yml rust job（llvm-cov +
gate + build 看门闸一段、前后两道 drain bash 块各一段）；profraw 清扫有四份
实现——`scripts/tests/conftest.py`、`python/conftest.py`（各带本地
`drain_stray_profraw` 副本）、`typescript/test/global-drain-profraw.ts`、
ci.yml 内联 ×4。剪枝清单 `SKIP_DIRS` 已在
`scripts/versions/lib/repository.py`（根 conftest 经 `lib.repository` import，
`python/conftest.py` 经 sys.path 注入 import）。

约束：`python/conftest.py` 运行在 Python 3.10 底线解释器上，共享库函数 MUST
只用 3.10 可用标准库（`pathlib` 足够；禁 `tomllib` 于该路径，现有模块已按此
组织）；ci.yml rust job 无 pnpm/Node 环境（裁决 `ci直调脚本不补pnpm`）；
注释卫生由 `scripts/check_comments.py` 执法，新代码注释只写当前契约事实。

## Goals / Non-Goals

**Goals:**

- rust 测试链本地/CI 物理同源：一个脚本文件，参数只定义一处。
- profraw 清扫收敛为一份实现，四端消费。
- 新增入口即接进 CI 并被 `pnpm check:meta` 生态覆盖（接线机器检查的根级
  升级归 Plan T4，本 change 只保证人工核对通过）。

**Non-Goals:**

- 不改覆盖率地板、豁免模式、报告命名（铁律七口径不动）。
- 不动 CI job 拓扑（语言 × 平台矩阵保持）。
- 不建其余 `test:*` 入口。

## Decisions

1. **命令载体 = `scripts/run/test_rs.sh`（bash），清扫实现 = Python**。
   cargo/show-env 链是 shell 的活（`eval "$(cargo llvm-cov show-env …)"`），
   但清扫需要复用 `SKIP_DIRS`——bash 只能硬编码复制剪枝清单，正是参数漂移
   病根；Python 与 `SKIP_DIRS` 同库直接 import。CI runner-images 官方 README
   实证 Python 四平台预装（proposal Prior art），裸 `python3` 零依赖可跑。
   备选"全 bash"被否（复制 SKIP_DIRS）；"全 Node"被否（rust job 无 Node，
   治理层惯例是 Python）。
2. **`drain_stray_profraw` 函数进 `scripts/versions/lib/repository.py`**，
   与 `SKIP_DIRS` 同家：两个 conftest 已在 import 该模块，零新增路径魔法。
   `scripts/run/clean_stray_profraw.py` 是薄 CLI 壳（import + main + 报错
   文案），供 ci.yml 与 `test_rs.sh` 消费。备选"函数放 `scripts/run/` 壳内"
   被否（conftest 需再注入 sys.path）。
3. **ci.yml rust job 塌为一步** `bash scripts/run/test_rs.sh`：脚本内置
   pre/post 清扫，等价原三道步骤。python / node job 的四道 drain 块改调
   `python3 scripts/run/clean_stray_profraw.py`（其测试尚未脚本化，清扫
   留在步骤层）。备选"rust job 补 pnpm 写 `pnpm test:rs`"被否（每格多装
   Node，同口径的本质是同一脚本而非同一前缀）。
4. **vitest 端改 shell out**：`typescript/test/global-drain-profraw.ts` 改为
   `spawnSync("python3", ["scripts/run/clean_stray_profraw.py"])`（cwd=仓库根），
   删除 TS 内复制的遍历逻辑。代价：Windows 本地跑 `test:wasm` 需装有
   python3（CI windows 格预装；本地未验证，README 写明前置）。备选"TS 保留
   第四份实现"被否（裁决 `清扫唯一实现python`：分叉风险大于个别平台便利）。
5. **工具探测位置 = `test_rs.sh` 开头**：`command -v cargo-llvm-cov` 失败即
   stderr 打印 `bash scripts/install_cargo_llvm_cov.sh` 并 exit 1，不自动装
   （机器副作用归人工，CI 自带安装步骤）。

## Risks / Trade-offs

- [本地首跑 `pnpm test:rs` 含编译看门闸，绑定 crate 编译数分钟] → 脚本
  echo 阶段标题使等待可见；sccache/增量编译摊薄后续轮次。
- [vitest shell out python3 在 Windows 本地缺 Python 时 `test:wasm` 报错] →
  报错文案指名"install python3"；CI windows 格预装不受影响；「未验证」标注
  写入 `scripts/README.md`。
- [conftest 改 import 后若 `lib.repository` 路径注入失败，pytest 收集期崩] →
  两个 conftest 沿用现有 sys.path 注入方式（python/conftest.py 已有先例），
  单测 `test_drain_profraw.py` 在 CI 的 `pnpm check:py` 中兜底。
- [根级 `test:rs` 暂不被 `check_ci.py` 机器核对（T4 未落地前）] → 本 change
  tasks 含人工核对项；T4 落地后自动覆盖，风险窗口 = 一个 change 周期。

## Migration Plan

一次性切换：脚本与唯一实现先落地并通过本地 `pnpm test:rs`，同轮删除四份旧
实现与 ci.yml 内联块（不留双轨）。回滚 = revert 单 commit，ci.yml 恢复内联
即回到旧口径。

## Open Questions

- 无。
