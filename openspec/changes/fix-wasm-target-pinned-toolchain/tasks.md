# Tasks

## 1. CI 工具链安装修复

- [x] 1.1 `.github/workflows/ci.yml` wasm job：dtolnay 步骤后新增一步裸命令
      `rustup target add wasm32-unknown-unknown`（载体：`CI补装target`）
- [x] 1.2 该步加注释说明 rust-toolchain.toml 覆盖活动工具链、dtolnay 只装 @stable，
      镜像 lint job「components for the pinned toolchain」写法；dtolnay `target:`
      输入保留不动（载体：`保留dtolnay输入`）

## 2. 脚本探测注释

- [x] 2.1 `scripts/run/test_wasm.sh` target 探测块上方补注释：点明
      `rustup target list --installed` 跟随 rust-toolchain.toml override 查的是
      激活工具链，前提是 CI 已把 target 装进激活工具链（载体：`探测注释`）

## 3. 账本泛化

- [x] 3.1 `openspec/specs/lessons-learned/ci.md` LL-041：正文与复发检测从
      component 泛化到 target+component，写明 `rustup ... list` 探测跟随 override
      （载体：`LL-041泛化`）
- [x] 3.2 `openspec/specs/lessons-learned/INDEX.md` LL-041 行标题同步泛化措辞
      （载体：`LL-041泛化`）

## 4. 验证闸门

- [x] 4.1 本地复跑 `bash scripts/run/test_wasm.sh` 全绿（探测通过、build+node
      wasm+browser 三段跑通）
- [x] 4.2 `pnpm check` 全绿（含 check:md、check_ci.py 接线闸门）
- [x] 4.3 ci-matrix spec 不补 scenario，本 change skip_specs（载体：`spec不动`）

## 5. 收尾对账

- [x] 5.1 Plan/ 无本 change 对应章节需删除（本次结论源自 CI 失败根因，Plan/
      无残留草案）——已查，无适用文件（锚点 `Plan/`）
- [x] 5.2 扫 openspec/specs/ 出三态时效结论：ci-matrix 无改（实现 bug 非契约）、
      lessons-learned LL-041 更新、无退役（锚点 `三态时效`）
- [x] 5.3 `pnpm test` 全绿（先于 review，排除实现断裂）
- [x] 5.4 按 governance spec「元规则 review 三轴」（Standards/Spec/Lessons）
      对照本 change 工件审实现 diff，逐文件对上 tasks.md，硬伤清零（锚点 `三轴`）
- [x] 5.5 被触碰文件全文只读体检（health-check apply 态：语义考古维+四维），
      发现附文件+行号+证据落 Plan/ 等点名（锚点 `体检`）——已查，无适用发现
- [x] 5.6 archive 阶段跳过 archive 态全项目存量体检——人工点名一次性，
      不豁免后续 change（载体：`体检一次性跳过`）
- [x] 5.7 迟到追加核对：本 change 工件与实现 diff 无未捕获的拍板/追加决定，
      已定裁决逐条对上载体任务（锚点 `迟到追加`）
- [x] 5.8 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾体检
      与升级预授权」消化所报 LAG（升级+全闸门+四端对拍），复跑至退出码 0
      SUMMARY 归零（锚点 `check:outdated`）——已消化 cc/pyo3-stub-gen/
      pyo3-stub-gen-derive + markdownlint-cli2（仓内 devDep+全局），SUMMARY 0 LAG
