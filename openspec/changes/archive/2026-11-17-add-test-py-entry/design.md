# Design

## Context

`test:rs` 已确立"脚本承载命令、本地与 CI 同一文件"模式（change
`add-test-rs-entry`）。`test:py` 套用同模式，但 python 胶水覆盖率链与 rust core
链有两处结构差异，需在此记录取舍，避免实现时误抄 `test_rs.sh`。

## Decision 1: 插桩清理用 `clean --workspace`，不用 `rm -rf llvm-cov-target`

`test_rs.sh` 用 `rm -rf target/llvm-cov-target` 是因为 `cargo llvm-cov`（自带
子命令）把插桩产物建进 `target/llvm-cov-target/`，而 `cargo llvm-cov clean` 在
`CACHEDIR.TAG` 缺失时静默 no-op（LL-101）。

python 链不同：它走 `cargo llvm-cov show-env` 导出 `RUSTFLAGS` 后用普通
`maturin develop` 编译，插桩对象落 **host `target/debug`**（ci-matrix spec
「覆盖率门槛生效」实证"maturin 不带 `--target`，对象落 host `target/debug`"），
`rm -rf target/llvm-cov-target` 打不中它。故 `test_py.sh` 用
`cargo llvm-cov clean --workspace`——它正是清理 workspace 内影响覆盖率结果的
产物（含 profraw 与清单），是 python 链适用的命令。

风险与缓解：`clean --workspace` 是否也受 LL-101 式静默 no-op 影响**未实证**；
缓解因素是 `show-env` 改 `RUSTFLAGS` 会强制 cargo 重编，旧二进制残留概率低于
rust 链。验收判据②（加未测胶水行必报红）间接覆盖"旧产物污染致假绿"——若污染
发生，新行仍会缺命中报红，不会静默放行。

## Decision 2: 后置清理块统一 `drain → clean`

后置块含两件事：散落 profraw 清扫（`clean_stray_profraw.py`，带"断链当轮即红"
检测职责）与插桩清理（`clean --workspace` / `rm -rf`）。二者作用集互斥——
`drain_stray_profraw` 的 `SKIP_DIRS` 含 `target`（见
`scripts/versions/lib/repository.py`）只删 `target/` 外，插桩清理只清 `target/`
内——换序不互相破坏。

把 drain 顶到后置块最前是防御性排序：日后若有人向后置块追加命令，drain 不会
被挤到末尾而失去"当场检测"的时机。`test_rs.sh` 后置块同步从
`rm -rf → drain` 改为 `drain → rm -rf`，两脚本后置结构一致。

## Decision 3: 缺工具探测不新建 `install_uv.sh`

`cargo-llvm-cov` 复用现成 `scripts/install_cargo_llvm_cov.sh` 作提示。uv 无对应
安装脚本——CI 由 `astral-sh/setup-uv` 负责，本地缺 uv 属开发环境前置，脚本仅
打印官方安装命令（`curl -LsSf https://astral.sh/uv/install.sh | sh`）并非零
退出。为一次性提示新建 `install_uv.sh` 违反最小改动，不做。

## Decision 4: 不改「覆盖率门槛生效（铁律七）」Requirement

ci.yml python job 塌为 `bash scripts/run/test_py.sh` 后，"show-env、clean、
build、test、report MUST 同一 step"的约束天然满足（脚本调用即单个 step，环境
变量在脚本进程内跨行存活）。铁律七口径（地板 100、豁免规则、报告命名）不变，
仅执行载体变化，故不 MODIFIED 该长 Requirement；脚本承载这一新事实由本 change
新增的「python 测试入口本地与 CI 同脚本」Requirement 表达。

## Migration

无数据迁移。落地顺序：先建 `test_py.sh` 并本地跑绿，再改 ci.yml 塌步，最后同步
spec 与文档；`test_rs.sh` 换序独立可验证（重跑 `test:rs` 仍全绿 + 放 stray
profraw 仍报红）。
