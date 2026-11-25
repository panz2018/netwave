# Tasks

## 1. T1 typescript wasm 残留清理

- [ ] 1.1 `typescript/.gitignore` 删除 `target-wasm/`、`target-wasm-cov/` 两条死规则及其注释
- [ ] 1.2 本地删除未跟踪死目录 `typescript/target-wasm/`、`typescript/target-wasm-cov/`（不进 git）
- [ ] 1.3 `提交粒度`：T1 独立成一笔 commit（与其余文件零重叠）

## 2. T2+T3 两脚本搬迁与引用面同步

- [ ] 2.1 `git mv scripts/install_wasi_sdk.sh browser/scripts/install_wasi_sdk.sh`（脚本自身零改动）
- [ ] 2.2 `git mv scripts/install_wasm_bindgen_cli.sh browser/scripts/install_wasm_bindgen_cli.sh`
- [ ] 2.3 `Cargo.lock修正`：`browser/scripts/install_wasm_bindgen_cli.sh` 读根 lockfile 的相对路径 `../Cargo.lock` → `../../Cargo.lock`
- [ ] 2.4 验证 `Cargo.lock修正`：跑 `bash browser/scripts/install_wasm_bindgen_cli.sh` 至版本解析段，确认解析出的 wasm-bindgen 版本非空（不发起真实安装即止）
- [ ] 2.5 `browser/scripts/test.sh` L66/L70 探测提示命令路径加 `browser/` 前缀
- [ ] 2.6 `.github/workflows/ci.yml` L161/L162 browser job 安装步命令加 `browser/` 前缀
- [ ] 2.7 `README承接`：新建 `browser/README.md`（英文），记录 browser 包常用命令并承接两脚本说明
- [ ] 2.8 `README承接`：`scripts/README.md` 删除两脚本对应表格行
- [ ] 2.9 `搬迁范围`：核对全仓无残留旧路径引用（grep `scripts/install_wasi_sdk.sh`、`scripts/install_wasm_bindgen_cli.sh` 仅剩 archive/）
- [ ] 2.10 `提交粒度`：T2+T3（含 README、spec delta 同步）合并成一笔 commit，避免半搬中间态

## 3. spec delta 与闸门

- [ ] 3.1 `change承载`：确认 ci-matrix delta 三条 requirement 路径字符串已更新，跑 `openspec validate relocate-browser-install-scripts --strict` 绿
- [ ] 3.2 跑 `pnpm check:md`（全 .md 校验，退出码 0）
- [ ] 3.3 跑 `pnpm check`（全量静态闸门，退出码 0）

## 4. 收尾打勾

- [ ] 4.1 `Plan/`：删除 `Plan/browser资产彻底归位.md` 中本批已完成章节（§2 两脚本搬迁、§3 typescript 残留清理），只留未执行项（§4 wiring、§6 改名、§8 全仓扫描），删后跑 `pnpm check:md`
- [ ] 4.2 `三态时效`：扫 `openspec/specs/` 全目录，对照本批改动出「更新/新增/退役」三态时效结论留痕（预期：ci-matrix 已随 delta 更新，无新增/退役）
- [ ] 4.3 `pnpm test`：apply 全部任务完成后、三轴 review 之前 MUST `pnpm test` 全绿
- [ ] 4.4 `三轴`：按 governance spec「元规则 review 三轴」对照本 change 工件审实现 diff，diff 文件集逐文件对上 tasks.md，硬伤清零才准入后续
- [ ] 4.5 `体检`：三轴 review 之后、check:outdated 之前，对被触碰文件全文只读体检（health-check spec apply 态），发现附文件+行号+证据落 Plan/ 等点名，不阻塞
- [ ] 4.6 `迟到追加`：apply 中途拍板的决定当场追加进 proposal.md `## 已定裁决` 段并补对应任务行，收尾复查每个关键词载体任务已打勾
- [ ] 4.7 `check:outdated`：最后一项跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾体检与升级预授权」消化所报 LAG，消化后复跑至退出码 0（SUMMARY 归零）才算完成
