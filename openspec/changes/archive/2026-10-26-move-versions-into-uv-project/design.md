# Design

## Context

`scripts/` 平铺 13 个 py 闸门 + 2 个 sh + `versions.json`。版本治理三件套
（登记表 + 离线对账闸门 + 联网体检）即将继续长功能（配对校验、补 reader），
平铺会加速膨胀。门禁脚本现寄居 `python/` uv 环境（`check:py` 经
`--project python` 跑 ruff），工具依赖无独立声明。仓库根已有
`Cargo.toml`（cargo workspace 根）与 `package.json`（pnpm workspace 根，
private）两个语言根，Python 缺位。`python/` 是发布物，其 uv 工程
（numpy/maturin/pyo3）必须保持独立。

## Goals / Non-Goals

**Goals:**

- 根级 uv 工具工程：治理脚本的依赖声明、锁定、运行环境统一可控。
- 版本域收进 `scripts/versions/`：门面在域根、数据进 `lib/`，目录即语义。
- 搬家零行为变化：两脚本逻辑原样，仅路径常量适配；旧新输出一致为验收。
- 波及面（package.json / ci.yml / spec / README / AGENTS / CONTRIBUTING /
  Plan）一次改全。

**Non-Goals：**

见 proposal.md Non-goals（不拆模块、不加测试、不做 pairs、不动其余闸门、
不碰 python/ 工程本体除删 ruff）。

## Decisions

- **uv 工程放仓库根而非 `scripts/`**：根 = 每语言 workspace 根的既有模式
  （Cargo.toml/package.json 并列）；`uv run` 自 cwd 向上解析最近工程，
  任何目录一条命令可用，无需 `--project` 后缀；oracle 阅卷脚本等将来
  共用同一环境。备选"scripts/ 建工程"被否：命令永远带 `--project scripts`，
  且其他目录（oracle）复用要跨工程引用，别扭。
- **根工程不声明 `[tool.uv.workspace]`**：uv workspace 会把 `python/` 吸入
  统一 lock，破坏发布物依赖独立性；嵌套目录不声明成员即互不干扰（uv 就近
  解析）。
- **登记表改名 `registry.json` 并入 `lib/`**：目录已名 `versions`，文件再名
  versions.json 撞名；数据跟着读它的代码走（`Path(__file__)` 定位，不依赖
  cwd）。spec 路径表述本就要出 delta，改名成本已被吸收。
- **门面直接文件执行，不建 `__init__.py`**：第一步不拆分，模块导入机制
  （`python -m versions.check_versions`）留到拆分 change；空壳 `__init__.py`
  是提前引入第二步的抽象。跑法：`uv run python scripts/versions/check_versions.py`。
- **ruff 归根环境统一**：根 `ruff.toml` 本就是全仓配置，ruff 进根 dev 组后
  `check:py` 一条命令跑 python/ + scripts/；`python/` dev 组删 ruff，消除
  同一工具两处钉版的漂移面。pytest 留 `python/`（需 numpy+扩展），根环境
  pytest 供 scripts 侧后续测试用。
- **自登记三条**：`root-python`（`.python-version`，paired_with
  `python-runtime`，值同 3.14，现有泛查要求其在 CI 矩阵——已成立）、
  `root-requires`（根 pyproject `requires-python`，paired_with
  `root-python`）、`root-uv-lock`（`uv.lock`，paired_with `root-python`）。
  发现式扫描会扫到根 pin，不登记即 FAIL——闸门自食其果是特性不是负担。
- **CI lint job 加 `uv sync --locked`**：既预建环境又断言根 lock 与
  pyproject 一致（lock 漂移当场红），与 python job 的 `uv sync` 模式对称。

## Risks / Trade-offs

- **根目录文件数 +3**：根已有 Cargo.toml/package.json/pnpm-lock/
  rust-toolchain.toml 等清单，模式一致不突兀；接受。
- **搬家 change 波及面宽**（package.json、ci.yml、3 spec、多 README）：
  全部列入 tasks 逐项打勾 + `pnpm check` 全绿兜底；漏改即红，不存在
  静默通道。
- **`upgrade-python-3-15`（暂停中）内旧路径暂不更新**：其恢复时 tasks
  本就要按当时状态重写，现在改是给将废弃文本续命；已在 Plan 文档登记
  恢复时的同步项。
- **本地未 `uv sync` 时 `pnpm check:meta` 首跑变慢**（建根 .venv 一次性
  成本）：与 python/ 工程既有体验一致，接受。
