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
