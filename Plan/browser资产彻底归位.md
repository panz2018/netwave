# browser 资产彻底归位（待拍板）

判据：删掉 `browser/` 子项目后必须跟着删的文件，就是 browser 的资产，不该散落在
仓库各处。按此判据扫 `scripts/`，发现三类该搬未搬 + 一类共享须留；另含一项
browser 包内命令更名（`build:browser`→`build`）。

## 1. 判据扫描结果

| 文件                                        | 删 browser 后是否必须删                                | 处置                |
| ------------------------------------------- | ------------------------------------------------------ | ------------------- |
| `scripts/tests/test_test_browser_wiring.py` | 是（测 `browser/scripts/test.sh` + worker 产物纯净度） | 搬进 browser        |
| `scripts/install_wasi_sdk.sh`               | 是（ci.yml 仅 browser job 引用，实证 161 行）          | 搬进 browser        |
| `scripts/install_wasm_bindgen_cli.sh`       | 是（ci.yml 仅 browser job 引用，实证 162 行）          | 搬进 browser        |
| `scripts/install_wasm_pack.sh`              | 否（node `test_ts.sh` 也用）                           | 共享，留 `scripts/` |
| `scripts/install_binaryen.sh`               | 否（node `test_ts.sh` 也用）                           | 共享，留 `scripts/` |
| `scripts/coverage_gate.py`                  | 否（rs/py/ts/browser 四端都用）                        | 共享，留 `scripts/` |
| `scripts/run/clean_stray_profraw.py`        | 否（四端都用）                                         | 共享，留 `scripts/` |

## 2. 待搬清单（三项）

- `scripts/install_wasi_sdk.sh` → `browser/scripts/install_wasi_sdk.sh`
  - 波及：`browser/scripts/test.sh` 探测提示路径、`ci.yml` browser job 安装步。
- `scripts/install_wasm_bindgen_cli.sh` → `browser/scripts/install_wasm_bindgen_cli.sh`
  - 波及：同上。
- `scripts/tests/test_test_browser_wiring.py` → browser 内（见第 3 节，含改名与
  语言选择）。

## 3. wiring 测试的归属与形态（核心待拍板）

现状：`scripts/tests/test_test_browser_wiring.py` 是 Python，由根 pytest
（`testpaths = ["scripts/tests"]`）跑，读 `browser/scripts/test.sh` 文本、
`.github/workflows/ci.yml` 文本、grep `browser/dist/netwave.worker.js`，断言覆盖率
链接线齐全 + 发布产物纯净。

按判据它是 browser 的，应进 `browser/`。两个待拍板点：

- **改名**：`test_test_browser_wiring.py` 双 `test_` 拗口且指向已不存在的旧脚本名。
  候选 `browser_chain.test.ts`（进 vitest）或 `test_browser_chain.py`（留 pytest）。
- **语言/runner**：改成 TS 进 `browser/test/`（vitest）还是留 Python？
  - 改 TS 的代价（事实，非借口）：browser 包的测试将读仓库根 `.github/workflows/ci.yml`
    ——按判据可接受（删 browser 时该 ci.yml job 同删、断言同死），但 browser 测试
    从此依赖仓库根 CI 结构。
  - 留 Python 的代价：违背"browser 资产归位"判据，且与 `scripts/tests/` 的
    CI-接线闸门家族（`test_check_ci.py`、`test_test_py_wiring.py`）混在一起。
  - 倾向：改 TS 进 `browser/test/`，把"读 ci.yml 接线"那部分断言一并迁入——
    browser 自包含优先于"家族聚合"。

## 4. 不在本 Plan 范围（共享，明确留下）

`coverage_gate.py`、`clean_stray_profraw.py`、`install_wasm_pack.sh`、
`install_binaryen.sh`——多端共用，搬进 browser 反而让 node/python/rust 链依赖
browser 包，制造反向耦合。

## 5. build:browser 命令更名（待拍板）

`browser/package.json` 的 `build:browser` 是历史遗留名——该命令原住 `typescript/`
包，与 `build:native` 当邻居才需后缀区分；现独立成 `browser/` 包后全包只有这一个
build 命令，再叫 `build:browser` 即"在 browser 包里构建 browser"，重复。改 `build`
后调用方读作 `pnpm -C browser build`，更干净。

改名波及面（当前名 `build:browser`，归档目录 `openspec/changes/archive/**` 不动）：

| 文件                                        | 位置         | 改什么                           |
| ------------------------------------------- | ------------ | -------------------------------- |
| `browser/package.json`                      | L21          | 定义 `build:browser` → `build`   |
| `browser/scripts/test.sh`                   | L80          | 调用命令名                       |
| `scripts/run/test_ts.sh`                    | L33,38       | 注释 + 调用命令名                |
| `scripts/tests/test_test_browser_wiring.py` | L36          | skip 提示里的命令名              |
| `typescript/scripts/merge_browser.mjs`      | L15          | 报错提示里的命令名               |
| `typescript/scripts/check_dts_any.mjs`      | L4           | 注释里的命令名（兼死引用，见下） |
| `typescript/README.md`                      | L63          | 命令名                           |
| `CONTRIBUTING.md`                           | L69          | 命令名                           |
| `.github/workflows/ci.yml`                  | L163,166     | 步骤名 + 注释里的命令名          |
| `browser/.gitignore`                        | L7           | 注释里的命令名                   |
| `browser/Cargo.toml`                        | L28          | 注释里的命令名                   |
| `openspec/specs/ci-matrix/spec.md`          | L124,403,470 | 命令名                           |
| `openspec/specs/workspace-layout/spec.md`   | L78          | 命令名                           |

同批清理的死引用（上一轮 `build:wasm`→`build:browser` 未改净的残留，活文件里的
死事实）：

- `browser/src/lib.rs` L16、L70：注释仍写 `build:wasm`。
- `typescript/scripts/check_dts_any.mjs` L4：注释写 `build:wasm + build:native`。
- 账本 `openspec/specs/lessons-learned/`（ci.md、core.md、INDEX.md LL-034、
  typescript.md）：规则正文仍用 `build:wasm` 描述当前 CI 顺序，须同步为现名。

## 6. 落地前置

- 单开 change（不在已归档/收尾的 `extract-browser-test-chain` 里塞）。
- 搬安装脚本需同步 `browser/scripts/test.sh` 探测提示与 `ci.yml` browser job。
- wiring 测试若改 TS，需给 `browser/test/` 配 vitest include，并确认根 pytest
  覆盖率地板不受影响（该文件从 `scripts/tests/` 移出后，根 coverage source 不再含它）。
- `build:browser`→`build` 改名波及 spec/CI/注释，须同步改全并跑 `pnpm check:md`、
  `pnpm check`；账本死引用同步属 LL-034 波及面。
