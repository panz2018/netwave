# Tasks

## 1 安装脚本

- [x] 1.1 新增 `scripts/install_cargo_llvm_cov.sh`：照 `install_wasm_pack.sh`
      套路（latest tag 查询 + `GITHUB_TOKEN` 防限流、`case "$os:$arch"` 五格
      musl/darwin/windows-msvc、下载重试、装到 `~/.local/bin`、本 shell PATH
      export、`GITHUB_PATH` 追加含 cygpath 转换）。差异点：tar 顶层为裸二进制
      无包裹目录，解包直接 `-C "$bindir"` + `chmod +x "$bindir"/cargo-llvm-cov*`
      （通配覆盖 `.exe`）。验证：`bash -n` 语法过。
- [x] 1.2 脚本末尾 LL-085 遮蔽处理 + 冒烟：`which cargo-llvm-cov` 命中非
      `~/.local/bin` 且遮蔽位在 `~/.cargo/bin` 时删除旧二进制并复验；
      `cargo llvm-cov --version` 打印版本才算成功。
      验证：本机 `bash scripts/install_cargo_llvm_cov.sh` 跑通，
      `which cargo-llvm-cov` 指向 `~/.local/bin`，`cargo llvm-cov --version`
      输出最新 tag。

## 2 CI 接线

- [x] 2.1 `ci.yml` rust job：新增独立安装步骤（无 `if`，四平台每格跑，
      `env: GITHUB_TOKEN`，置于覆盖率步骤之前），覆盖率步骤内
      `cargo install cargo-llvm-cov --locked` 删除；覆盖率步骤保留
      `if: matrix.target == 'linux-x64'`，命令字面
      （`cargo llvm-cov -p netwave --codecov --output-path codecov.json` +
      `coverage_gate.py 100`）不动。验证：`python3 scripts/check_ci.py` 绿、
      YAML 解析过。

## 3 文档同步（LL-034）

- [x] 3.1 `scripts/README.md` 脚本表新增 `install_cargo_llvm_cov.sh` 行
      （英文，口径同 wasm-pack 行：latest 直装、本地与 CI 共用）。
- [x] 3.2 `Plan/闸门重排-2026-11-12.md` 决策四：缺 cargo-llvm-cov 的报错
      提示文案由 `cargo install cargo-llvm-cov --locked` 改指
      `scripts/install_cargo_llvm_cov.sh`。
- [x] 3.3 本机跑 `python3 scripts/versions/check_outdated.py`，确认第 3 节
      cargo-llvm-cov 行命中新装版本且无 LAG。
- [x] 3.4 `pnpm check:md` 绿。

## 4 收尾

- [x] 4.1 三轴 review（Standards/Spec/Lessons）：按 governance spec
      「元规则 review 三轴」对照本 change 工件（proposal/specs/design/tasks）
      审实现 diff，硬伤清零。
      结论：Standards——铁律七命令字面未动，脚本与同类模板风格一致，
      review 中补可执行位（chmod +x）；Spec——delta 两 Scenario 与实现一致
      （安装已改直装、不随工具链重装）；Lessons——LL-085 遮蔽处理已落脚本
      并本机验证，LL-011（GITHUB_PATH/cygpath、安装独立 step）遵守，
      LL-057 口径不动，LL-034 波及面（README/决策四/Plan）已同步。硬伤 0。
- [x] 4.2 apply 完成前扫 `openspec/specs/` 全目录，产出三态时效结论
      （更新/新增/退役）留痕本文件完成记录。
      三态结论：更新＝dependency-upgrade（本 change delta 已覆盖）；
      ci-matrix 铁律七命令字面未动无需改；其余 12 个 spec 与本 change 无关。
      新增＝无；退役＝无；LL-085 复用不新增条目。
      注：归档阶段经人工点名豁免（2026-11-13），本 change 归档时跳过
      archive-health-check spec 的五维只读体检；归档前 Plan/ 瘦身与三态时效
      检查照常执行。
- [x] 4.3 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾
      体检与升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍；登记回退
      不阻塞）；消化后复跑至退出码 0（SUMMARY 归零）。
      消化记录：biome 2.6.7、markdownlint-cli2 0.24.1（仓库+全局）、
      prettier 3.10.1、cc 1.11.2、rustls-webpki 0.103.17、coverage 7.17.3、
      ruff 0.17.5、uv 0.13.8（self update）；`pnpm check` 全绿、
      `pnpm check:cross` 四端对拍通过、复跑 SUMMARY: 0 LAG。
