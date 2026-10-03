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
- 复发检测：`test_fill_pattern_view_zero_copy` 断言 `owndata is False`；
  `pnpm check:cross`

### LL-023 改 core 后先 maturin develop

- 犯过：直接 pytest 测到陈旧 .so；uv cache + target/release 双缓存致 .so
  md5 新旧横跳；`uv run maturin develop` 装对新产物后，`uv run pytest` 的
  隐式 sync 又用缓存旧 wheel 覆盖回旧的（症状：maturin 报 Installed、
  site-packages/.so 却恒为旧大小与旧符号数）
- 规则：改 core 后先 `uv run --no-sync maturin develop`，再 `uv run --no-sync pytest`；`--no-sync` 阻断隐式 sync 回退
- 缓存异常时全清重建：`rm -rf python/target`、`cargo clean -p netwave -p netwave-python`、`uv cache clean`；md5/大小对比 venv/.so vs target/debug vs target/release 定位陈旧产物（maturin wheel 走 release profile，debug 对不代表 release 对）
- 复发检测：可门禁化——对拍前强制重建步骤；诊断口诀 `grep -ac <新符号> .so`
