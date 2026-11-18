# Tasks

## 1. 接线冒烟测先行（red）

- [ ] 1.1 在 `scripts/tests/` 增用例：断言根 `package.json` 含 `test:py` 且
  ci.yml python job 调用 `scripts/run/test_py.sh`、`test_rs.sh` 后置块以
  `clean_stray_profraw.py` 开头——此时脚本未建，用例先失败（red 先于 green）
- [ ] 1.2 跑 `uv run pytest scripts/tests`，确认 1.1 用例因入口缺失而红

## 2. 建 python 测试脚本

- [ ] 2.1 建 `scripts/run/test_py.sh`，`set -euo pipefail`（`严格失败语义`），
  开头探测 `cargo-llvm-cov` 与 `uv`，缺则打印安装命令并非零退出、不自动装、
  不新建 `install_uv.sh`（`缺工具报错不自动装`）
- [ ] 2.2 脚本前置块：`clean_stray_profraw.py` → `cargo llvm-cov show-env
  --sh --no-cfg-coverage` → `cargo llvm-cov clean --workspace`
  （`清理用clean-workspace`、`前后各一次清理`）
- [ ] 2.3 `uv子shell写法`、`脚本承载命令`：脚本主体 `mkdir -p coverage` →
  `(cd python && uv sync && uv run maturin develop)` → `(cd python && uv run
  pytest)` → `cargo llvm-cov report --codecov --output-path
  coverage/coverage-python.json --ignore-filename-regex '[\\/]core[\\/]'` →
  `python3 scripts/coverage_gate.py coverage/coverage-python.json 100`
- [ ] 2.4 脚本后置块：`clean_stray_profraw.py` → `cargo llvm-cov clean
  --workspace`，drain 顶最前（`后置drain先于clean`、`前后各一次清理`）
- [ ] 2.5 根 `package.json` 加 `"test:py": "bash scripts/run/test_py.sh"`，
  范围仅此一个入口（`范围只建test-py`、`脚本承载命令`）

## 3. rust 脚本后置换序

- [ ] 3.1 `scripts/run/test_rs.sh` 后置块改为 `clean_stray_profraw.py` →
  `rm -rf target/llvm-cov-target`，与 `test_py.sh` 后置结构一致（`rs同步换序`、
  `后置drain先于clean`）

## 4. CI 塌步

- [ ] 4.1 ci.yml python job：删前后两道独立 drain 步骤，清扫改由脚本内置
  （`drain入脚本`）
- [ ] 4.2 ci.yml python job：内联大步骤塌为 `bash scripts/run/test_py.sh`
  （保留 `shell: bash`），upload-artifact 步骤保留（`ci塌步调脚本`）

## 5. 本地验收（green）

- [ ] 5.1 本地 `pnpm test:py` 全绿且产出 `coverage/coverage-python.json` 经
  `coverage_gate.py` 阅卷 100（`验收三判据`）
- [ ] 5.2 `python/src/` 人为加一行未测胶水产码 → `pnpm test:py` 报红，验后还原
  （`验收三判据`）
- [ ] 5.3 人为放 `stray.profraw` → `pnpm test:py` 报红并删除，验后确认工作区干净
  （`验收三判据`）
- [ ] 5.4 重跑 `pnpm test:rs` 全绿 + 放 stray.profraw 仍报红，确认换序无回归
  （`rs同步换序`）
- [ ] 5.5 重跑第 1 组冒烟测转绿（green）

## 6. 文档与 spec 同步

- [ ] 6.1 同步 ci-matrix spec：python 清扫归 `test_py.sh`、后置 `drain → clean`
  顺序、新增「python 测试入口本地与 CI 同脚本」Requirement（`文档spec同步`）
- [ ] 6.2 同步 `scripts/README.md`（补 `run/test_py.sh` 条目）与
  `CONTRIBUTING.md`（本地入口表补 `pnpm test:py` + 快循环出口
  `(cd python && uv run pytest)`）（`文档spec同步`）
- [ ] 6.3 本 change 不扩范围：`check_ci.py` 根级接线闸门升级（T4）、
  `check:cross` 改名（决策二）留痕不实现（`不扩范围`）
- [ ] 6.4 删除 `Plan/闸门重排-2026-11-12.md` 中 `test:py` 已定案章节，
  只留未执行任务（锚点 `Plan/`）
- [ ] 6.5 跑 `pnpm check:md` 至退出码 0（`文档spec同步`）

## 7. 收尾体检与对账

- [ ] 7.1 扫 `openspec/specs/` 全目录，产出本次改动"更新/新增/退役"三态时效
  结论留痕本文件（锚点 `三态时效`）
- [ ] 7.2 按 governance spec「元规则 review 三轴」（Standards/Spec/Lessons）
  对照本 change 工件审实现 diff，逐文件对上 tasks.md，硬伤清零（锚点 `三轴`）
- [ ] 7.3 对触碰文件全文只读体检（health-check spec apply 态：语义考古维 +
  四维），发现附文件+行号+证据落 `Plan/` 点名，不阻塞（锚点 `体检`）
- [ ] 7.4 `迟到追加`：复查 apply 中途拍板的决定已当场追加进 `proposal.md` 的
  `## 已定裁决` 段并补对应任务行，每个关键词载体任务已打勾（锚点 `迟到追加`）
- [ ] 7.5 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾体检
  与升级预授权」消化所报 LAG，消化后复跑至退出码 0（SUMMARY 归零）（锚点
  `check:outdated`）
