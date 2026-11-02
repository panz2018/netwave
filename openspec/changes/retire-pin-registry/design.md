# Design

## Context

见 `proposal.md` — Why。补充源码事实基线（均已核实，出处为文件+行号）：

- `check_versions.py` 的 check #3（MSRV，`:232`）、#4（packageManager，
  `:257`）、#5（`.python-version` ∈ CI 矩阵，`:267`）直读仓库文件，
  不消费登记表任何字段；`current_values()`（`:112`）唯一消费者是
  check #1b（blocked 黑名单，`:205`）。
- `check_outdated.py` 的 blocked 消费链（`load_blocked` `:67`、
  `blocked_target` `:134`、`PROBE_TO_ENTRY` `:46`）因 `blocked` 0 条数据
  而恒为直通。
- `registry.json`：31 条 pin、13 类；`oracle-env` 空类；`ci-actions`
  类名与唯一条目名同名；`machine:` 前缀 9 条被离线闸门两处显式跳过
  （`check_versions.py:121`、`:228`）。
- 全仓 manifest 实测：`Cargo.toml` ×5、`package.json` ×2（仅根有
  `packageManager`）、`pyproject.toml` ×2（均有 `requires-python` +
  同目录 `.python-version`）、`.python-version` ×2、`rust-toolchain.toml` ×1。

## Goals / Non-Goals

**Goals:**

- 登记表退役后，今天生效的全部机器判定（MSRV、packageManager、
  `.python-version` ∈ 矩阵）一条不少——保护网零空窗。
- spec、程序、仓库文件三层职责各归其位：spec=契约、程序=规则执行、
  钉版文件=数值真相源。
- 波及面一次改全（代码、spec delta、文档指针、Plan 收尾）。

**Non-Goals:**

- 设计层面的补充边界：不为四律引入任何配置机制（规则开关、豁免参数、
  目录排除列表）——全仓现状无豁免需求，出现时再开 change；
  其余同 `proposal.md` Non-goals。

## Decisions

### D1 四律写死在 `check_versions.py`，不做数据驱动

规则是"每个同型 manifest 必须满足"的通用律，不是实例数据。数据驱动
需发明选择器+约束词 mini-DSL，且 spec 还得再描述 DSL 语义，复杂度净增；
全仓其他闸门（`check_vocab.py`、`check_else.py`、`check_license.py`）
均为"代码硬编码 + spec 描述"，版本域不例外。备选（JSON 规则表）否决。
pairs 的 JSON 化是**实例数据**（同形状、逐条追加），与本决策不冲突，
已作为待触发项留 `Plan/软件升级.md`。

### D2 保留 check #3/#4/#5 原实现，四律中新增的第 2 律是新代码

现有三条检查行为不变（回归基线 = 改动前后输出逐行一致）；新增的
`pyproject.toml` → `requires-python` + 同目录 `.python-version` 律是唯一
新判定逻辑，按 TDD 先写失败夹具（tmp 目录造缺 `.python-version` 的
`pyproject.toml`），再实现使其通过。

### D3 `check_outdated.py` 删 blocked 链而非留空转

`load_blocked`/`blocked_target`/`PROBE_TO_ENTRY`/`BlockedMap` 全删，
体检报告直接取最新稳定版为 target。备选（留最小实现等 blocked）否决：
零数据机制即死代码，且旧代码兼容的是已废的登记表格式，重写反而更薄。
探针集（node/npm/pnpm/uv/rustup/openspec/markdownlint-cli2/wasm-pack/
binaryen/cargo-llvm-cov）保留为程序常量 `PROBES`，spec 只写类别不列名字。

### D4 `registry.json` 直接删除，不留空壳

`git rm scripts/versions/lib/registry.json`，`lib/` 目录随之消失
（其中仅此一文件）。备选（留 `{"blocked":[],"pairs":[]}` 占位）否决：
仓库先例 `api-contract/spec.md:200`（从未实现的入口从契约删除）、
`lessons-learned/spec.md:125`（禁占位行）确立"不留空挂"原则。

### D5 单 change 完成（不拆两步）

原"两步走"的第二步（拆包+改名）因 pins/categories 退役而空心化，
剩余内容与第一步同属"登记表退役"一个自洽单元；合并后回滚单位明确
（revert 一笔即恢复旧状）。

### D6 文档指针统一改法

所有"登记表/唯一真相源/registry.json"字样按语义分两类改：
声称真相源的 → "钉版文件本身 + 规则闸门"（`AGENTS.md:104`、
`CONTRIBUTING.md:79/89/91`、`specs/README.md` 路由摘要、
`scripts/README.md:19`）；引用具体数值的 → 文件路径指针
（`ci-matrix/spec.md:51-52/63-64/70`，已入 delta）。
`scripts/versions/README.md` 整篇重写：域使命改为"版本一致性规则闸门 +
联网体检"。

## Risks / Trade-offs

- [删 check #6 后"新子工程漏管版本"保护变弱] → 四律按 manifest 类型
  全覆盖（Cargo/pyproject/package.json/.python-version），并以正反夹具
  当场自证；漏网形态（如全新工具类型的钉版）接受人工 review 兜底。
- [blocked 义务暂无机制承接] → spec 触发式条款把义务转为"降级 + 立
  Plan + 强制开 change"三步人工流程，语义不丢，机制晚到。
- [机器工具（cargo-llvm-cov 等）不再登记，升级漏装风险] → 操作提示已在
  spec「升级流程固定顺序·工具链升版后补装」Scenario，体检仍探测其版本。
- [单 change 体积大] → 任务按"先删后改指针"排序，每步跑
  `pnpm check:meta` 局部验证；回滚为单 revert。

## Migration Plan

1. 留回归基线：`uv run python scripts/versions/check_versions.py` 与
   `check_outdated.py` 当前输出存档 `/tmp/`。
2. 改 `check_versions.py`（删登记表检查、加第 2 律、TDD 夹具）→
   输出与基线一致（除新增律外零差异）。
3. 改 `check_outdated.py`（删 blocked 链）→ 联网输出与基线一致
   （blocked 段本为空）。
4. `git rm registry.json` → 再跑两闸门确认绿。
5. 应用 spec delta（archive 时由 openspec 完成主 spec 更新）。
6. 文档指针同步 + Plan 收尾 + `pnpm check:md`。
7. 全仓 grep `registry.json` 收口（archive 目录除外清零）。

回滚：revert 本 change 提交即恢复登记表与旧闸门；spec 主文件在归档前
不受影响，归档后回滚走 governance「冻结非不可变」修正协议。

## Open Questions

（无——格式细节属 blocked/pairs 触发时的 change，不在本 change 范围。）
