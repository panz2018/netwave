# Tasks

> 本 change 为命令更名 + 死引用清理 + 删冗余测试/已吸收 Plan，无新增数值实现，
> 故「red 先于 green」与「cross-binding 对拍」两条规则无适用任务（不触碰任何
> 数值实现或跨端 API）。验证一律引用根聚合入口，不手抄 CI 内联参数。

## 1. build:browser→build 命令更名

- [ ] 1.1 落实 `build改名`：`browser/package.json` scripts 定义 `build:browser`→`build`
      （与现有 test/typecheck/gen:constants/test:unit/test:e2e 无脚本名冲突，已实测）。
      验证：`pnpm -C browser build` exit 0。
- [ ] 1.2 同步调用方命令名：`browser/scripts/test.sh`、`scripts/run/test_ts.sh`
      （注释+调用）、`typescript/scripts/merge_browser.mjs`（报错提示）、
      `typescript/scripts/check_dts_any.mjs`（注释）。验证：`pnpm test:ts` exit 0。
- [ ] 1.3 同步文档/CI 命令名：`.github/workflows/ci.yml`（步骤名+注释）、
      `browser/README.md`、`typescript/README.md`、`CONTRIBUTING.md`、
      `browser/.gitignore`（注释）、`browser/Cargo.toml`（注释）。
      验证：`pnpm check:md` exit 0。

## 2. 死引用清理（命令名 build:wasm）

- [ ] 2.1 落实 `死引用两类一起清`（命令名维）：活文件注释里的旧命令名 `build:wasm`
      同步为现名——`browser/src/lib.rs`、`typescript/scripts/check_dts_any.mjs`。
      验证：grep `build:wasm` 活文件零命中（排除 target*/dist/node_modules/.venv/archive）。
- [ ] 2.2 落实 `死引用两类一起清`（账本维）：账本规则正文里的 `build:wasm` 同步为
      现名——`openspec/specs/lessons-learned/ci.md`、`core.md`、`INDEX.md`（LL-034）、
      `typescript.md`。验证：`pnpm check:md` exit 0。

## 3. 死引用清理（job 名 wasm job）

- [ ] 3.1 落实 `死引用两类一起清`（job 名维）：散文里的旧 job 名 "wasm job" 同步为
      browser——`.github/workflows/ci.yml`（顺序注释 docs->rust->wasm、rust/browser/
      node job 交叉引用「see wasm job」「The wasm job owns」）、`browser/scripts/test.sh`
      探测注释。验证：grep `wasm job` 活文件零命中（排除 archive）。
- [ ] 3.2 落实 `scenario标题经agent-driven sync直改主spec`：openspec delta 无 scenario
      改名机制（MODIFIED 删旧触发 scenario-loss ERROR、REMOVED+ADDED 同名被拒、
      RENAMED 只改 requirement 名，实证 openspec 2.2.0 validator.ts）。netwave 归档走
      agent-driven sync（直接编辑主 spec），故 scenario 标题「ci.yml wasm job 不再
      内联测试命令」→「ci.yml browser job 不再内联测试命令」在 apply 态 sync 时直接
      编辑主 spec `openspec/specs/ci-matrix/spec.md`，delta 不碰该 requirement。
      验证：sync 后 grep 主 spec `wasm job` 零命中、`openspec validate --strict` exit 0。

## 4. 删冗余测试与已吸收 Plan

- [ ] 4.1 落实 `删wiring测试不搬家`：删除 `scripts/tests/test_test_browser_wiring.py`
      （镜像税 + dist 纯净断言在 lint job 永远 skip + gate 行由 coverage_gate.py
      自身与 review 覆盖）。验证：`pnpm check:py` exit 0（根 pytest 收集不含该文件）。
- [ ] 4.2 落实 `spec产物纯净scenario不动`：确认 `workspace-layout`「browser 发布产物
      不含测试代码」scenario 未被改动（由 publish_shell.mjs 构建时闸门满足）。
      验证：`pnpm -C browser build` 后 grep dist worker 零命中覆盖率符号。
- [ ] 4.3 落实 `根pytest地板不受影响`：实测删测试后根 pytest 覆盖率地板不变
      （pyproject coverage source 不含测试文件）。验证：`pnpm check:py` exit 0。
- [ ] 4.4 落实 `删已吸收Plan`：删除 `Plan/browser资产彻底归位.md`（全部裁决已被本
      change 吸收）。验证：`pnpm check:md` exit 0。

## 5. C 类合法 wasm 引用确认

- [ ] 5.1 落实 `C类wasm保留`：确认 core/oracle/check_verbs/check_vocab*/install 脚本/
      versions 域的 `wasm`（编译目标/绑定端术语）未被改动。验证：grep 这些文件
      `wasm` 引用与改前一致（仅 build:browser→build 命令名相关行除外）。

## 6. 全仓兜底扫描与收尾闸门

- [ ] 6.1 全仓 grep `build:browser`、`build:wasm`、`wasm job` 兜底（排除 target*/
      dist/node_modules/.venv/archive），活文件零残留。验证：三条 grep 均空。
- [ ] 6.1b 落实 `全仓wasm逐条确认`：全仓搜 `wasm`（活文件，排除 target*/dist/
      node_modules/.venv/archive），逐条研究归属并记录：属 browser 死引用的已改完，
      C 类合法术语（编译目标/绑定端）保留不动，确认剩余全部是无法且不应改名的
      合法 wasm。逐条结论落本节完成记录，零漏网才算闭环。验证：人工核对清单无残余死引用。
- [ ] 6.2 `pnpm test` 全绿（三轴 review 之前，含四端对拍，先排除实现断裂）。
- [ ] 6.3 `三轴`：按 governance spec「元规则 review 三轴」（Standards/Spec/Lessons）
      对照本 change 工件审实现 diff，diff 文件集逐文件对上 tasks.md，硬伤清零。
- [ ] 6.4 `体检`：对触碰文件全文只读体检（health-check spec apply 态），发现附
      文件+行号+证据落 Plan/ 等点名，不阻塞。
- [ ] 6.5 `迟到追加`：复查 apply 中途拍板的决定已当场追加进 proposal.md
      `## 已定裁决` 段并补对应任务行，每个关键词载体任务已打勾。
- [ ] 6.6 `Plan/`：确认 Plan/ 中本 change 对应章节已当场删除（4.4 删整文件即满足），
      只留未执行任务。验证：`pnpm check:md` exit 0。
- [ ] 6.7 `三态时效`：扫 openspec/specs/ 全目录，对照本次改动产出更新/新增/退役
      三态时效结论留痕（预期：ci-matrix、workspace-layout 经 delta 更新；账本四文件
      直接改；无新增/退役）。
- [ ] 6.8 `check:outdated`：跑 pnpm check:outdated 并按 dependency-upgrade spec
      「apply 末尾体检与升级预授权」消化所报 LAG（升级+全闸门+四端对拍，含全局
      CLI/直装工具机器级升级；登记回退不阻塞）；消化后复跑至退出码 0（SUMMARY 归零）。
- [ ] 6.9 `跳过归档体检`：本 change 归档阶段跳过 health-check spec 的 archive 态
      只读体检（apply 态体检见 6.4，照常执行不受此裁决影响）。
