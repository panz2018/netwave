# Tasks

## 1. wasm 壳 functions 满覆盖（red 先于 green）

- [ ] 1.1 先在 `typescript/test/wasm/touchstone.test.ts` 加 `fromUrl` 成功路径失败用例：
      用 `vi.stubGlobal('fetch', ...)`（裁决 `stub-global-fetch`）stub 返回 `new Response(S1P)`，
      断言 `fromUrl` resolve 并解析出预期值；保留现有 reject 用例。验证：补阈值前裸跑
      `pnpm -C typescript test:wasm` 仍因 `functions` 未卡而绿，但报告 functions 应为 57/57
      （成功回调已被新用例覆盖）。
- [ ] 1.2 给 `typescript/vitest.wasm.config.ts` 的 `thresholds` 补 `functions: 100`
      （裁决 `wasm-functions-threshold`）。验证：`pnpm -C typescript test:wasm` exit 0；
      若 1.1 缺失则此步应红（red 先于 green 成立）。
- [ ] 1.3 跑 `pnpm -C typescript test:wasm` 实证 functions 翻满、阈值过（裁决
      `verify-functions`），记录 functions 实际值（应为 57/57）。

## 2. 全项目 wasm 测试根聚合入口

- [ ] 2.1 新建 `scripts/run/test_wasm.sh`（裁决 `root-test-wasm-entry`）：
      `set -euo pipefail`，探测 `wasm-pack`/`wasm-opt`/`wasm32-unknown-unknown`/chromium
      缺失即打印安装命令退出、不自动装（裁决 `probe-not-install`），再依次 `build:wasm`、
      `pnpm -C typescript test:wasm`、`pnpm -C typescript test:browser`。验证：缺工具时
      非零退出且 stderr 含安装命令；工具齐备时 exit 0。
- [ ] 2.2 根 `package.json` 加 `"test:wasm": "bash scripts/run/test_wasm.sh"` 并纳入
      `test` 聚合链（裁决 `test-wasm-in-aggregate`）。验证：`pnpm test:wasm` 可单跑；
      `pnpm test` 聚合含该入口。
- [ ] 2.3 确认 `scripts/run/test_ts.sh` 不动：保留 build:wasm + test:wasm 的 node 版本轴
      验证（裁决 `keep-node-axis-wasm`），build:wasm 与 test_wasm.sh 各自幂等（裁决
      `build-wasm-idempotent`）。验证：`pnpm test:ts` 仍 exit 0，两脚本各含 build:wasm。
- [ ] 2.4 改 `.github/workflows/ci.yml` wasm job：测试步骤收成一行
      `bash scripts/run/test_wasm.sh`，前置 install 步（binaryen/wasm-pack/pnpm/playwright
      chromium）保留（裁决 `ci-wasm-job-one-line`）。验证：`python3 scripts/check_ci.py`
      exit 0（根 `test:wasm` 的脚本调用出现在 ci.yml）。

## 3. 文档与波及面同步

- [ ] 3.1 把 `fromUrl` mock 方案与 wasm 壳 functions 补卡结论回写
      `Plan/覆盖率统一-2026-11-12.md` 的「wasm 壳 functions 阈值是否补卡」节，标注已落地。
- [ ] 3.2 改任何 `.md` 后跑 `pnpm check:md` exit 0。

## 4. 集成验证与收尾

- [ ] 4.1 跑 `pnpm check` exit 0（含 `check:md`、`check_ci.py` 等元闸门）。
- [ ] 4.2 跑 `pnpm test` exit 0（全量含 `test:wasm` 浏览器套件与 `test:cross` 四端对拍）。
- [ ] 4.3 收尾删除 `Plan/` 中本 change 已完成章节（锚点 `Plan/`），删后跑 `pnpm check:md`。
- [ ] 4.4 扫 `openspec/specs/` 全目录做更新/新增/退役三态时效检查并留痕（锚点 `三态时效`）。
- [ ] 4.5 按 governance spec「元规则 review 三轴」审实现 diff，diff 文件集逐文件对上 tasks.md，硬伤清零（锚点 `三轴`）。
- [ ] 4.6 对触碰文件全文只读体检（health-check spec apply 态），发现附文件+行号落 `Plan/` 等点名（锚点 `体检`）。
- [ ] 4.7 复查 apply 中途拍板决定已追加进 proposal.md `## 已定裁决` 并补任务行（锚点 `迟到追加`），每个关键词载体任务已打勾。
- [ ] 4.8 跑 `pnpm check:outdated` 并按 dependency-upgrade spec 消化所报 LAG，复跑至
      退出码 0（SUMMARY 归零）（锚点 `check:outdated`）。
- [x] 4.9 归档态 health-check 体检一次性跳过（裁决 `skip-archive-health-check`，仅归档态；apply 态体检见 4.6 照常做）——跳过 2026-11-19。
