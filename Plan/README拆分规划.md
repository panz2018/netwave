# README 拆分规划（待执行）

原则：**文档按"读者何时需要"分层**。稳定、跨项目的决策留 `Plan/` +
`AGENTS.md`；某绑定的构建命令、踩坑、FFI 细节放各子项目 `README.md`，
顶层只留指针。全部落地且 Plan 瘦身完成后**删除本文件**
（见 [README.md](README.md) 生命周期）。

## 新建 README 清单

### 根 `README.md`

- 项目是什么：网络散射参数（S 参数）计算库，Rust core +
  Python/Node/WASM 三绑定，对标 skrf（从
  [总体计划·项目定位](总体计划.md#项目定位) 压缩为一段）
- 仓库结构图：`core/ python/ typescript/ testdata/ scripts/ Plan/ openspec/`
  各一行说明
- 快速上手（顶层命令，每条一行）：`pnpm install`、
  `cargo test --workspace`、`pnpm -C typescript build:native`、
  `pnpm -C typescript build:wasm`、`python3 scripts/cross_compare.py .cross-tmp`
- workspace 覆盖率门禁（自 core README 迁入）：
  `cargo llvm-cov --workspace --fail-under-lines 100`
  `--ignore-filename-regex '(python|typescript/(native|wasm))/src/lib\.rs'`
- 环境坑：uv venv + `LD_LIBRARY_PATH`/`PYO3_PYTHON`/`VIRTUAL_ENV` 三件套；
  corepack `COREPACK_ENABLE_DOWNLOAD_PROMPT=0`；沙箱 cwd 漂移用绝对路径
- 文档地图：铁律 → [constitution.md](constitution.md)、
  流程 → [开发流程.md](开发流程.md)、各端细节 → 各子 README
- 链接校验纪律：改任何 md 后跑 `markdownlint-cli2` + `check_links.py`

### `python/README.md`

- 目的：numpy 零拷贝视图绑定（pyo3 + numpy crate）
- 命令：`uv sync --project python`、`uv run maturin develop`（改 core 后必跑）、
  `uv run pytest`、`scripts/dump_py.py`
- 实现细节：`crate-type = ["cdylib"]` 防 E0464 的机制展开；
  `read_element` 返回 `(float, float)`；`netwave.pyi` stub 随 wheel 发布；
  `python_relative: 0.0` 逐 bit 容差依据
- 注意：`[lib] name = "netwave"` 与 core 同名是故意的（import 名）

### `typescript/README.md`（覆盖 native + wasm，不单独建子 crate README）

- 目的：单包双发布——node 走 napi 原生、browser 走 wasm，
  `exports` 条件分发
- 命令：`build:native`（napi esm + commonjs 两遍 + `publish_shell.mjs`）、
  `build:wasm`（web target + `CARGO_TARGET_DIR=../target-wasm`）、
  `test:native` / `test:wasm`（两套 vitest config，100% 阈值）
- 实现细节（坑最密集）：napi 零拷贝 Buffer 与 capacity 陷阱、CLI 旗标漂移、
  wasm web-target 选型、`{module_or_path: bytes}` init 形态、
  wasm-opt 用 `scripts/install_binaryen.sh` 动态装 GitHub latest
  （不钉版本；wasm-pack 内置的钉在老版 117 必须 PATH 覆盖）、
  worker 内存不可 transfer、壳文件体系与 `publish_shell.mjs` 重写规则
  （逐条见 [阶段0复盘回写.md](阶段0复盘回写.md)）
- 注意：JSON 丢负零 → 对拍 dump 用 `.bin`

### `testdata/README.md`（短）

- `manifest.json` 契约字段说明（`core_tol.relative`、`python_relative`）、
  `.bin` 格式（little-endian f64）、谁生成谁消费

### `scripts/README.md`（短）

- 每个脚本一行：用途 + 调用方式（`cross_compare.py <dir> [--tamper=<end>]`
  的 tamper 语义、`bench_gate.py` 阈值来源、`install_binaryen.sh`
  动态安装 wasm-opt 最新版——本地与 CI 共用）

## Plan/ 瘦身对照

| Plan 文档 | 拆走 | 保留 |
|---|---|---|
| [开发流程.md](开发流程.md) | 工具链状态表里的绑定级细节（napi 旗标、wasm-pack 参数、E0464、corepack 交互坑）→ 各 README；技能地图每行加"细节见 X README"指针 | 核心循环、复盘三问、何时简化、技能×阶段表 |
| [总体计划.md](总体计划.md) | `Python 环境管理：uv`、`Node.js 包管理：pnpm` 的操作细节 → 对应 README（留一句决策+指针）；`目录名与发布名解耦` 的 npm 包名映射表 → `typescript/README.md` | 项目定位、语言选型理由、数据布局决策、Monorepo 结构、路线图、License 策略 |
| [测试规划.md](测试规划.md) | `三端 runner` 的各端调用命令 → 各 README；覆盖率工具的具体命令行 → core/typescript README | 测试分层、golden 契约、manifest schema、容差标准、cross-binding 规则 |
| [功能覆盖规划.md](功能覆盖规划.md) | 基本不拆（纯范围规划，无命令细节） | 全部 |

## 红线

cross-binding 对拍的**规则**（原生逐 bit、wasm 容差、篡改自检）留在
[测试规划.md](测试规划.md) 单点定义——跨项目契约，散进 README 会漂移；
README 只放"怎么跑"并链回去。

## 落地顺序

1. 根 `README.md`
2. `typescript/README.md`（含 native/wasm 分节）
3. ~~`python/README.md`~~ ✅（2026-09-25）
4. ~~`testdata/README.md`~~ ✅（2026-09-25）~~`scripts/README.md`~~ ✅（2026-09-25）
5. 瘦身 Plan 三文档并加指针
6. `npx markdownlint-cli2 "**/*.md"` + `python3 scripts/check_links.py` 全绿收尾
