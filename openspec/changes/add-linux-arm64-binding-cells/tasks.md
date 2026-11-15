# Tasks

## 1. ci.yml 矩阵加格

- [x] 1.1 `ci.yml` python job `matrix.include` 加
      `{ os: ubuntu-26.04-arm, python-version: "3.15" }`（版本以现有 ubuntu 格
      最新值为准）。验证：`python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))"`
      通过，push 后 `python (ubuntu-26.04-arm, 3.15)` 格出现且 exit 0。
- [x] 1.2 `ci.yml` node job `matrix.include` 加
      `{ os: ubuntu-26.04-arm, node-version: "26" }`（版本以现有 ubuntu 格
      最新 LTS 值为准），自动继承全套步骤（wasm 构建、napi、vitest、
      typecheck、dts 检查、check:cross）。验证：`node (ubuntu-26.04-arm, 26)`
      格出现且 exit 0。
- [x] 1.3 确认新格覆盖率报告不冲突：artifact 名已含 matrix.os（
      `coverage-python-ubuntu-26.04-arm-3.15`、
      `coverage-native-ubuntu-26.04-arm-26`），CI run 产物列表逐格可下载。
- [x] 1.4 删除 `ci.yml` 中因标定机制移除而悬空的历史归因注释
      （`Floor 100: calibration closed` 等三处），改写为当前契约陈述或径直删除。
      验证：`grep -i "calibration" .github/workflows/ci.yml` 无输出。

## 2. spec 同步

- [x] 2.1 `openspec/specs/ci-matrix/spec.md`：按本 change delta 应用
      MODIFIED「语言版本矩阵」（硬件平台轴补 linux-arm64 + Scenario 补断言）与
      REMOVED「覆盖率地板两阶段标定」整条；另直接编辑主 spec 清理悬空措辞——
      Scenario「胶水行未测即红（地板启用后）」标题去括号限定语（铁律七本身
      无行为变更，不入 delta，见 spec delta 内注释）。
      验证：`grep -n "标定\|地板启用后" openspec/specs/ci-matrix/spec.md`
      无输出；`pnpm check:md` 退出码 0。
- [x] 2.2 全仓 grep 悬空引用：
      `grep -rn "两阶段标定\|地板启用后\|标定轮" openspec/specs/ AGENTS.md CONTRIBUTING.md`
      无输出（lessons-learned 账本除外——账本留原文作历史证据）。

## 3. 闸门与对拍

- [x] 3.1 本地闸门：`pnpm check`、`pnpm check:md` 退出码 0；
      `openspec validate add-linux-arm64-binding-cells --strict` 通过。
- [x] 3.2 跨端对拍：push 后 CI 的 `node (ubuntu-26.04-arm, 26)` 格内
      `pnpm check:cross` 通过（aarch64 上三端词汇对拍 + 防同义反复自检），
      `python (ubuntu-26.04-arm, 3.15)` 格 pytest 胶水阅卷 100 通过。
      完成记录：CI run 43666522002 两 arm 格 success（fail-fast: false，
      与 lint 失败无关）。
- [x] 3.3 人工：GitHub 分支保护 required checks 添加
      `python (ubuntu-26.04-arm, 3.15)`、`node (ubuntu-26.04-arm, 26)`；
      核对 required 列表与矩阵格一一对应。

## 4. 收尾

- [x] 4.1 删除 `Plan/linux-arm64绑定格-2026-11-13.md`（结论已吸收进本
      change 工件），删后 `pnpm check:md` 退出码 0。
- [x] 4.2 三轴 review（Standards/Spec/Lessons）：按 governance spec
      「元规则 review 三轴」对照本 change 工件（proposal/specs/design/tasks）
      审实现 diff，硬伤清零。
      完成记录：Standards——ci.yml 加格沿用现有 matrix include 风格，注释
      只留当前契约（calibration 归因已删）；spec 悬空引用清零、Scenario
      同步。Spec——delta（MODIFIED 语言版本矩阵 + REMOVED 标定）与实现逐条
      一致。Lessons——无新错误，无需新增 LL。
- [x] 4.3 三态时效结论留痕：扫描 `openspec/specs/` 全目录，对照本次改动
      记录"更新/新增/退役"结论于本文件完成记录（预期：更新 ci-matrix，
      无新增，无退役；`specs/README.md` 路由表无需变动）。
      完成记录：更新 ci-matrix（硬件平台轴 + 删标定）；无新增能力；无退役
      能力；ci-matrix 已在 `specs/README.md` 路由表，无需变动。
- [x] 4.4 归档说明：本 change 归档时按人工裁决跳过 archive-health-check
      五维体检步骤（仅本 change 一次性豁免，不改 config.yaml 与 spec）。
- [x] 4.5 跑 `pnpm check:outdated` 并按 dependency-upgrade spec
      「apply 末尾体检与升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍，
      含全局 CLI/直装工具的机器级升级；登记回退不阻塞）；消化后复跑
      `pnpm check:outdated` 至退出码 0（SUMMARY 归零）。
      完成记录：消化 4 LAG——playwright/playwright-core 1.65.0→1.65.1、
      pnpm 12.18.0→12.21.0（`packageManager` 钉版 + 全局 CLI）；复跑
      `pnpm check:outdated` SUMMARY 0 LAG；`pnpm check`/`pnpm check:md` 绿；
      四端对拍 `pnpm check:cross` PASS（core==python==node bit-exact，
      wasm within tol，防同义反复自检 3 端检出）。
