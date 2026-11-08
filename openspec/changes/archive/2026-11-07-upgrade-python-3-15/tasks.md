# Tasks

本 change 无新增数值实现（proposal Non-goals：不改数值行为与容差），
故无 red-before-green 新测试；验收靠既有闸门（design Decision 9）。
跨端对拍任务见第 5 组。

## 1. 全局 CLI 与工具链升级（spec「升级流程固定顺序」第 1 步）

- [x] 1.1 node 26.12.1→26.13.0：`nvm install 26.13.0 --reinstall-packages-from=26.12.1`，验证 `openspec`、`markdownlint-cli2`、`pnpm` 在新版本可用（`ls /config/.nvm/versions/node/26.13.0/bin`）。验证: 三条命令均有版本输出。
- [x] 1.2 pnpm 12.5.1→12.18.0（corepack，带 `COREPACK_ENABLE_DOWNLOAD_PROMPT=0`）、uv 0.13.5→0.13.7、rustup 1.29.2→1.29.3、openspec 1.15.0→1.16.1、markdownlint-cli2 0.23.3→0.24.0。验证: 各 `--version` 输出目标版。
      （实测偏离：node 26 已不内置 corepack，pnpm 改经
      `npm install -g --allow-scripts=pnpm pnpm@12.18.0` 安装——npm 新
      allow-scripts 策略会拦 pnpm 的 install.js，不加 `--allow-scripts`
      则二进制不替换、`pnpm -v` 仍旧版；
      仓库内 `pnpm -v` 仍显示 12.5.1 属预期（pnpm 读 `packageManager` 钉版），
      4.3 改钉版后消除。附带：node 自带 npm 11.20.0，`--reinstall-packages-from`
      不迁移手动装的 npm，已另装 npm@12.2.2。两条待 6.4 归账本。）
- [x] 1.3 rustup 升版后补装（spec「工具链升版后补装」Scenario）：确认 `1.99.1` 工具链的 rustfmt/clippy 组件与 `wasm32-unknown-unknown` target 在位，`cargo install --locked cargo-llvm-cov` 重装。验证: `rustup component list --installed`、`rustup target list --installed`、`cargo llvm-cov --version`。
      （实测：rustfmt/clippy 组件、wasm32 target 均在位；cargo-llvm-cov 0.9.1
      已是最新（体检 OK），toolchain pin 未变故无需重编译。）
- [x] 1.4 wasm-pack 0.15.0→0.15.1：重跑 `scripts/install_wasm_pack.sh`。验证: `wasm-pack --version`。
      （实测坑：脚本装 `~/.local/bin`，本机 `~/.cargo/bin` 在 PATH 更前且存
      旧版 0.15.0 遮蔽新版；已删旧版使 0.15.1 生效。待 6.4 归账本。）

## 2. cp315 可装性事实核查（design Risks 前两条的触发点）

- [x] 2.1 `uv python install 3.15` 后，在临时环境确认 numpy 2.5.4 与 maturin 1.16.0 有 cp315 wheel 可装（非源码编译）。装不上 = 阻碍性问题，停止并报告（design Decision 6）。验证: `uv pip install --python 3.15 numpy maturin` 成功且非 sdist 构建。
      （实测：装到 cpython-3.15.2；临时 venv `uv pip install numpy maturin`
      显示 `Downloaded numpy`（非 build）、秒装 numpy==2.5.4 + maturin==1.16.0，
      `import numpy` 通过。cp315 wheel 可用。）
- [x] 2.2 核实 numpy crate 0.30 对 pyo3 的依赖范围（crates.io API 或 `cargo add --dry-run`），确认 pyo3 0.30 + numpy 0.30 可共存。解析不出 = 阻碍性问题，停止并报告。验证: 给出依赖范围原文。
      （实测：crates.io numpy 0.30.0 依赖 `pyo3 ^0.30.0`、
      `pyo3-build-config ^0.30`；pyo3-stub-gen 0.23.2 依赖
      `pyo3 >=0.27,<0.31`。三者同落 pyo3 0.30 线，可共存。）

## 3. Python 绑定升级与适配

- [x] 3.1 `python/Cargo.toml`：pyo3 0.29→0.30（`abi3-py310` feature 不动）、numpy 0.29→0.30、pyo3-stub-gen 0.23→0.23.2。验证: `cargo tree -p netwave-python` 中 pyo3 与 numpy 同 0.30 线且无重复版本。
      （实测补充：`core/Cargo.toml` 的可选 pyo3 必须同步 0.29→0.30——pyo3 用
      `links = "pyo3-python"`，全 workspace 只容一个版本，不同步则
      `cargo update` 报 links 冲突（core 注释本就规定二者同 minor）。
      stub-gen 保持 `0.23` caret 声明，lock 解析到 0.23.2。验证：lock 中
      pyo3 0.30.1（唯一）/ numpy 0.30.0 / pyo3-stub-gen 0.23.2，
      `cargo tree -p netwave-python` 三者同线复用。）
- [x] 3.2 以编译报错驱动适配 pyo3 0.30 breaking changes（`FromPyObject` 默认不再生成、abi3 feature 逻辑、`PyBuffer` 弃用方法等；已扫 `python/src/lib.rs` 仅用 pyclass/pymethods + stub-gen）。工作量大小不构成停止理由；仅确认上游 bug 或真不兼容时报告。验证: `cargo build -p netwave-python` 通过、`clippy` 无新告警。
      （实测：唯一 breaking 命中 = `core/src/frequency.rs` 两处
      `pyclass(skip_from_py_object)`——0.30 起该选项默认启用且将移除，
      删显式选项即消除弃用告警，行为不变（仍不生成 FromPyObject，
      契约由注释保留）。普通与 `--features stub-gen` 两条编译路径均通过，
      `cargo clippy` exit 0；残留仅既有 license-file manifest 告警，与本升级无关。）
- [x] 3.3 `python/` 下 `maturin develop` 后用 pytest 跑全量（3.15 解释器）。验证: pytest 全绿、覆盖率仍达铁律七阈值。
      （实测：本地 venv 以 `uv venv --python 3.15 --clear` 重建（`.venv` 属
      gitignore 产物），钉版文件未动、以 `UV_PYTHON=3.15` 覆盖；
      `maturin develop` 出 abi3≥3.10 wheel，
      `pytest --cov=netwave --cov-fail-under=100` 于 Python 3.15.2：
      47 passed、覆盖率 100%。）
- [x] 3.4 依赖刷新：`uv lock --upgrade --project python` 与根工程 `uv lock --upgrade`（maturin 1.16、pytest 9.2、numpy 2.5.4、pluggy/coverage 随动）。验证: lock diff 仅含预期包，无 JS/cargo 传递依赖混入。
      （实测：python/uv.lock → coverage 7.17.2、maturin 1.16.0、numpy 2.5.4、
      pluggy 1.7.0、pytest 9.2.0；根 uv.lock → coverage 7.17.2、pytest 9.2.0、
      ruff 0.17.4。全部 Python 包，无 JS/cargo 混入。）

## 4. 钉版点改齐（集中一笔 commit）

- [x] 4.1 `python/.python-version` 与根 `.python-version`：3.14→3.15。
- [x] 4.2 `.github/workflows/ci.yml`：python 矩阵最新格 3.14→3.15（3.10 底线格不变，不留 3.14 过渡格）。验证: `python3 scripts/versions/check_versions.py` 矩阵覆盖律通过。
      （实测：三格 3.14→3.15，3.10 底线格不动；矩阵块自带注释
      "latest (3.14)" 同步改 3.15（本文件既有风格，注释硬编码版本号）；
      grep 全文件无 3.14 残留；`check_versions.py` 四律 OK。）
- [x] 4.3 根 `package.json`：`packageManager`→`pnpm@12.18.0`，`pnpm install` 刷新 `pnpm-lock.yaml`（仅 pnpm 元数据变化，不刷依赖版本）。验证: `pnpm -v` 与 `packageManager` 一致。
      （实测：lock diff 62/62 行仅 `pnpm` 与 `@pnpm/exe.*` 平台二进制
      12.5.1→12.18.0，无其他依赖版本混入；仓库内 `pnpm -v` 现读
      packageManager = 12.18.0，1.2 记录的旧版遮蔽消除。）
- [x] 4.4 `python/Cargo.lock` 随 3.1 更新入库。验证: `git status` 钉版文件集合 = design Migration 第 5 步所列，无遗漏。
      （实测：本 workspace 单一根 `Cargo.lock`，无独立 `python/Cargo.lock`，
      已在 3.1 更新到 pyo3 0.30.1。钉版文件集合核对完整——版本声明
      `.python-version`×2 / `ci.yml` / `package.json` / `python/Cargo.toml` /
      `core/Cargo.toml`，lockfile `Cargo.lock` / `python/uv.lock` / `uv.lock` /
      `pnpm-lock.yaml`；`core/src/frequency.rs` 属代码适配非钉版，另笔。无遗漏。）

## 5. 全闸门与跨端对拍

- [x] 5.1 清脏工作树：删 `python/netwave/_netwave.pyi`、`python/netwave/*.so`、`typescript/dist/` 等历史生成物（LL-047）。验证: `git status --ignored` 确认产物已清。
      （实测：删 `.pyi`/`.so`/`typescript/dist/`/`oracle/tmp/`（gitignored
      对拍输出，dump 脚本自建），与 CI fresh checkout 一致。）
- [x] 5.2 按序重建各端产物（maturin develop → stub_gen → napi build → wasm build）。验证: 三端类型产物齐备。
      （实测：按 CI 集成 job 顺序 build:wasm → build:native（tsdown dts
      解析到 wasm glue，LL-034）→ maturin develop（abi3≥3.10 .so）→
      stub_gen（导出 uv libpython LIBDIR，Python 3.15.2）；三端类型产物
      `dist/wasm-web/netwave_wasm.d.ts`、`dist/index.node.generated.d.mts`、
      `netwave/_netwave.pyi` 齐备。）
- [x] 5.3 cross-binding 跨绑定对拍：`pnpm check:cross` 全绿（四端数值一致、容差不变、`check_vocab_types.py` 三端成员集合互等）。验证: 退出码 0，manifest 容差 key 零改动。
      （实测：FREQ/TOUCHSTONE 对拍 core==python==node bit-exact、wasm
      within tol；反同义反复自检 python/node/wasm 三端注入均检出；
      `check_vocab_types.py` FrequencyUnit/WavelengthUnit 三端产物成员互等；
      `check_verbs.py` 通过。manifest.json 未改动，容差不变。）
- [x] 5.4 `pnpm check` 全绿（含 `check:md`、`check:meta` 四律、`check:py`）。验证: 退出码 0。
      （实测：`pnpm check` exit=0——check:md（363 files OK）、check:ts、
      check:rs（clippy -D warnings 通过，佐证 frequency.rs 适配干净）、
      check:py（161 passed、覆盖率 100%）、check:meta（license/ci/vocab/
      comments/proposal/version laws/else 全 OK）。中途踩坑：补充说明里
      反引号跨行触发 check_md OPEN CODE SPAN，已改自闭合。待 6.4 归账本。）

## 6. 文档同步与收尾

- [x] 6.1 grep 全仓 `3.14` 残留清除（散文不复制数字，按 spec「散文不复制版本号」以文件指针措辞）。验证: `grep -rn '3\.14' --exclude-dir=target --exclude-dir=node_modules .` 无本升级相关残留。
      （实测：唯一真残留 = `.vscode/settings.json` 的 `LD_LIBRARY_PATH`
      硬编码本地 `cpython-3.14` libpython 目录（pyright/rust-analyzer 用），
      已改 `cpython-3.15`。其余 `3.14` 逐类甄别均非残留：Cargo.lock
      `errno 0.3.14`/`napi 3.14.2`、pnpm-lock `typanion@3.14.0` 是无关包版本；
      lessons-learned/typescript.md 的 napi 3.13→3.14 是冻结账本历史；
      scripts/tests 的 "3.14" 是测试夹具样本值；根 `pyproject.toml`/`uv.lock`
      的 `requires-python >=3.14` 是治理工具工程底线（floor ≤ pin 合法，
      "不抬底线"属已定 Non-goal，不动）；Plan/软件升级.md 由 6.2 删除。）
- [x] 6.2 `Plan/软件升级.md`：删除「Python 3.15 + pyo3 0.30 升级」整节与落地形态汇总中的对应行（apply 钩子：结论入本 change）。删后跑 `pnpm check:md`。验证: 退出码 0。
      （实测：删「Python 3.15 + pyo3 0.30 升级」整节；头部状态行
      同步去掉"Python 3.15 升级=暂缓待机制拍板"；落地形态汇总本无
      Python 行无需改。保留「过期检查门禁化」节里"Python 3.15 发布当天
      全红"的假设例句（属另一待拍板项论据，非本升级残留）。
      `pnpm check:md` 退出码 0。）
- [x] 6.3 扫 `openspec/specs/` 全目录做三态时效检查（更新/新增/退役），结论写进本文件完成记录。验证: 结论清单存在。
      （三态结论：更新=无——ci-matrix / workspace-layout /
      dependency-upgrade 均以文件指针与"最新稳定版"措辞表述、不硬编码
      版本号（grep specs 无 3.14/3.15），本次升级不触发 spec 改动；
      新增=无——无新契约；退役=无。specs/README.md 路由表无需改
      （无 spec 增删）。与 proposal `skip_specs` 判定一致。）
- [x] 6.4 retro：本次踩坑按性质归位——版本级 bug 进 `Plan/` blocked 计划（若出现），非版本性坑进 `openspec/specs/lessons-learned/` 对应分片 + INDEX。验证: 账本有对应条目或明确记「无新坑」。
      （版本级 bug：无——pyo3 0.30 / numpy 0.30 / cp315 wheel 均正常，
      无上游 bug、无降级，故无 blocked/Plan 条目。非版本性坑：登记
      LL-084（本机 node 26 无 corepack + npm allow-scripts 静默拦 pnpm
      二进制替换）、LL-085（`~/.cargo/bin` 遮蔽 `~/.local/bin` 直装工具
      旧版），均入 ci.md + INDEX。第三处反引号跨行由 `check_md.py`
      门禁当场拦（已有门禁不重复登记，最小规则原则）。）
- [x] 6.5 闸门全绿后输出「分组→文件→commit 标题」全景表等人工点名（钉版一笔、代码适配一笔、文档一笔），不自行 `git commit`。验证: 全景表已给出且未提交。
      （全景表见对话；`pnpm check` exit=0 后给出，未执行任何 commit。）

## Workflow follow-up

- 本 change 归档前：确认 Plan/ 相关条目已清空（6.2）、specs 三态结论已留痕（6.3）。
- 归档后另开例行刷新普通 PR：JS（vitest/playwright/biome/tsdown/@napi-rs/cli 等）
  与 cargo 传递依赖刷新（design Decision 4）。

## 完成记录

- 5.3 四端对拍：FREQ/TOUCHSTONE core==python==node bit-exact、wasm within
  tol；反同义反复自检 python/node/wasm 三端注入均检出；词汇类型三端互等；
  动词闸门通过；manifest 容差零改动。
- 5.4 `pnpm check` exit=0（md/ts/rs/py/meta 全绿；check:py 161 passed
  覆盖率 100%；check:rs clippy -D warnings 通过）。
- 6.3 specs 三态：更新/新增/退役均为无（spec 版本无关，见 6.3）。
- 6.4 账本：无版本级 bug（无 blocked）；非版本性坑 LL-084、LL-085
  入 ci.md + INDEX。
- 6.5 提交全景表：见对话（钉版一笔 / 代码适配一笔 / 文档一笔），
  等人工点名，未自行 commit。
