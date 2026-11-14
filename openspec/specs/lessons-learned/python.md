# LL ledger — scope: python

## Entries

### LL-014 pyo3 链接三件套

- 犯过：VS Code 外构建 pyo3 找不到解释器
- 规则：`VIRTUAL_ENV`/`PYO3_PYTHON`/`LD_LIBRARY_PATH` 指向 uv 管理的解释器；
  `.vscode/settings.json` 编辑器内自动注入
- 复发检测：可门禁化——CI/脚本显式导出三件套后构建

### LL-016 零拷贝 base-object 绑定与打包

- 犯过：rust-numpy 0.25 无 `from_borrowed_data`；pyo3↔numpy 混版触发
  `links=python` 冲突；maturin 默认不打包 `.pyi`
- 规则：`#[pyclass(frozen)]` Owner 持 `Array3` +
  `PyArray3::borrow_from_array(&owner.get().data, owner.clone().into_any())`，
  base object 保生命周期；pyo3 与 numpy 同 major 配对；maturin 配置
  `include` 显式打包 `netwave.pyi`；`[lib]` 段 `name = "netwave"` 即
  import 名；`crate-type = ["cdylib"]` 避 E0464 rlib 同名冲突
- 复发检测：`test_from_data_s_view_is_zero_copy` 断言 `owndata is False`；
  `pnpm check:cross`

### LL-023 改 core 后先 maturin develop

- 犯过：直接 pytest 测到陈旧 .so；uv cache + target/release 双缓存致 .so
  md5 新旧横跳；`uv run maturin develop` 装对新产物后，`uv run pytest` 的
  隐式 sync 又用缓存旧 wheel 覆盖回旧的（症状：maturin 报 Installed、
  site-packages/.so 却恒为旧大小与旧符号数）
- 规则：改 core 后先 `uv run --no-sync maturin develop`，再 `uv run --no-sync pytest`；`--no-sync` 阻断隐式 sync 回退
- 缓存异常时全清重建：`rm -rf python/target`、`cargo clean -p netwave -p netwave-python`、`uv cache clean`；md5/大小对比 venv/.so vs target/debug vs target/release 定位陈旧产物（maturin wheel 走 release profile，debug 对不代表 release 对）
- 复发检测：可门禁化——对拍前强制重建步骤；诊断口诀 `grep -ac <新符号> .so`

### LL-069 uv 删依赖后旧 .venv 残留旧二进制

- 犯过：`python/pyproject.toml` 删 ruff 并 `uv lock` 后，
  `uv run --project python ruff` 仍报可用——lock 已无 ruff，旧 `.venv/bin/ruff`
  还在（uv 默认不清理既有 venv 的多余包）
- 规则：判断依赖是否移除以 `uv.lock` 为准，不信旧 venv；本地要清干净用
  `uv sync --exact`，CI 新建 venv 天然干净
- 附带：根目录 `uv run` 时若 shell 激活了 `python/.venv`，uv 警告
  `VIRTUAL_ENV ... ignored` 属正常（就近工程解析），不是错误

### LL-077 同秒等长还原源文件后 pytest 跑陈旧字节码

- 犯过：反向验证脚本改坏 `scripts/versions/` 源码跑红后同秒写回原文
  （字节数相同），随后 pytest 报 8 例失败——`__pycache__` 按
  mtime+size 判缓存有效，源码实际已换但缓存未失效，跑的是改坏时的旧字节码
- 规则：任何脚本化“改源码→跑测试→还原”流程，还原后必须清
  `__pycache__`（或给 pytest 加 `PYTHONDONTWRITEBYTECODE=1`）再复跑；
  症状口诀：git diff 干净但测试红 = 先想陈旧字节码
- 复发检测：反向验证类脚本内置 `find … -name __pycache__ -exec rm -rf`；
  暂不可 CI 门禁化（仅影响本地验证流程）

### LL-078 测试离线防护点在 socket.getaddrinfo 非 socket.socket

- 犯过：`scripts/tests/conftest.py` 首版 autouse fixture patch
  `socket.socket`，smoke 用例仍失败——urllib 经
  `socket.create_connection` 内部直接引用类，patch 模块属性拦不住
- 规则：离线咽喉点选 `socket.getaddrinfo`（所有出网 TCP 连接必经域名
  解析）；子进程不走 socket，由测试内替换 `run_cmd` 类 helper 覆盖
- 复发检测：`scripts/tests/test_offline_guard.py` 钉住防护生效（真联网
  尝试必报 `network access forbidden`）

### LL-079 runpy 重执行门面时桩须打在 lib 源头模块

- 实证：受控实验确认——以 `runpy.run_path(facade, run_name="__main__")`
  覆盖门面的 `sys.exit(main())` 守卫行时，若沿用既有门面测试的写法把桩
  打在门面模块（`check_versions.all_laws`），runpy 重新执行门面文件，其
  `from lib.rules import ...` 在 exec 时按 `sys.modules` 重新绑定，取到
  lib 模块的原始函数，门面模块上的 monkeypatch 随重执行被冲掉——实测
  桩注入的违规未生效、真实四律对真仓库跑通、`SystemExit.code` 变 0
- 规则：runpy 类"重执行源文件"的测试，桩打在**源头模块属性**
  （`lib.rules.all_laws`、`lib.latest.run_cmd`）；直调 `main()` 的测试
  桩打在门面模块仍有效——两种缝各自成立，不可混用
- 复发检测：`scripts/tests/versions/test_check_*.py::TestMainGuard` 断言
  守卫退出码，桩绑错模块时 violations 例的 `SystemExit.code` 变 0 即红

### LL-088 abi3-py310 门控掉 `pyo3::buffer`，memoryview 走 `tobytes()`

- 犯过：`from_bytes` 收 buffer 三件套首版 `use pyo3::buffer::PyBuffer` 编译
  失败——`pyo3::buffer` 整模块 `#![cfg(any(not(Py_LIMITED_API), Py_3_11))]`，
  本仓 pyo3 开 `abi3-py310`（Limited API + 3.10）两条件皆不满足；同轮
  连带两错：0.30 的 `PyBytes::as_bytes()` 不收 `Python` 参数、
  `PyBytes::new` 返回 `Bound` 需 `.unbind()` 才配 `Py<PyBytes>` 签名
- 规则：abi3-py310 下 bytes-like 提取只用稳定面——`cast::<PyBytes>()` +
  `as_bytes()`、`cast::<PyByteArray>()` + `to_vec()`、memoryview 经
  `call_method0("tobytes")`；类型门控（cast 失败即拒）天然排除 numpy 数组，
  与"不收 numpy uint8"裁决一致
- 复发检测：`python/tests/test_touchstone_class.py` 的 buffer 三件套用例 +
  numpy 拒绝用例钉住行为；`cargo clippy -p netwave-python` 编译即门禁

### LL-094 改 pytest 全局配置须当轮全量跑并贴语义范围证据

- 犯过：`unify-coverage-gates` 给根 `pyproject.toml` 的 `pythonpath` 补
  `scripts`，当轮只跑 `-k coverage_gate` 过滤用例，未跑全量 pytest，
  也未在改动时刻贴"覆盖率范围未变"的证据；人工质疑"是否把整个 scripts
  纳入覆盖率"时只能事后补跑取证
- 规则：`pythonpath` 只注入 `sys.path`（pytest 源码
  `_pytest/config/__init__.py` "Add paths to sys.path"），覆盖率范围由
  `check:py` 的 `--cov=scripts/versions` 决定，两者不是一回事；改
  `pythonpath`/`testpaths` 等全局测试配置 MUST 当轮跑全量 pytest，
  并贴被统计的文件清单（`--cov-report=term` 输出）证明语义范围如所述
- 两问分开取证："改动没破坏"（全量绿）与"改动语义范围如我所说"
  （文件清单证据），后者不可用前者代替
- 复发检测：暂不可 CI 门禁化（属验证时序纪律）；review Standards 轴
  核对"改全局测试配置的 commit 是否附全量 pytest 文件清单证据"
