# Tasks

## 1 安装脚本

- [ ] 1.1 新增 `scripts/install_cargo_llvm_cov.sh`：照 `install_wasm_pack.sh`
      套路（latest tag 查询 + `GITHUB_TOKEN` 防限流、`case "$os:$arch"` 五格
      musl/darwin/windows-msvc、下载重试、装到 `~/.local/bin`、本 shell PATH
      export、`GITHUB_PATH` 追加含 cygpath 转换）。差异点：tar 顶层为裸二进制
      无包裹目录，解包直接 `-C "$bindir"` + `chmod +x "$bindir"/cargo-llvm-cov*`
      （通配覆盖 `.exe`）。验证：`bash -n` 语法过。
- [ ] 1.2 脚本末尾 LL-085 遮蔽处理 + 冒烟：`which cargo-llvm-cov` 命中非
      `~/.local/bin` 且遮蔽位在 `~/.cargo/bin` 时删除旧二进制并复验；
      `cargo llvm-cov --version` 打印版本才算成功。
      验证：本机 `bash scripts/install_cargo_llvm_cov.sh` 跑通，
      `which cargo-llvm-cov` 指向 `~/.local/bin`，`cargo llvm-cov --version`
      输出最新 tag。

## 2 CI 接线

- [ ] 2.1 `ci.yml` rust job：新增独立安装步骤（无 `if`，四平台每格跑，
      `env: GITHUB_TOKEN`，置于覆盖率步骤之前），覆盖率步骤内
      `cargo install cargo-llvm-cov --locked` 删除；覆盖率步骤保留
      `if: matrix.target == 'linux-x64'`，命令字面
      （`cargo llvm-cov -p netwave --codecov --output-path codecov.json` +
      `coverage_gate.py 100`）不动。验证：`python3 scripts/check_ci.py` 绿、
      YAML 解析过。

## 3 文档同步（LL-034）

- [ ] 3.1 `scripts/README.md` 脚本表新增 `install_cargo_llvm_cov.sh` 行
      （英文，口径同 wasm-pack 行：latest 直装、本地与 CI 共用）。
- [ ] 3.2 `Plan/闸门重排-2026-11-12.md` 决策四：缺 cargo-llvm-cov 的报错
      提示文案由 `cargo install cargo-llvm-cov --locked` 改指
      `scripts/install_cargo_llvm_cov.sh`。
- [ ] 3.3 本机跑 `python3 scripts/versions/check_outdated.py`，确认第 3 节
      cargo-llvm-cov 行命中新装版本且无 LAG。
- [ ] 3.4 `pnpm check:md` 绿。

## 4 收尾

- [ ] 4.1 三轴 review（Standards/Spec/Lessons）：按 governance spec
      「元规则 review 三轴」对照本 change 工件（proposal/specs/design/tasks）
      审实现 diff，硬伤清零。
- [ ] 4.2 apply 完成前扫 `openspec/specs/` 全目录，产出三态时效结论
      （更新/新增/退役）留痕本文件完成记录。
      注：归档阶段经人工点名豁免（2026-11-13），本 change 归档时跳过
      archive-health-check spec 的五维只读体检；归档前 Plan/ 瘦身与三态时效
      检查照常执行。
- [ ] 4.3 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾
      体检与升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍；登记回退
      不阻塞）；消化后复跑至退出码 0（SUMMARY 归零）。
