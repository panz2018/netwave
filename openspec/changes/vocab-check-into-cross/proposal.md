# Proposal

## Why

`vocabulary-consistency.test.ts`（跨端词汇一致性绊线）物理上放在
`typescript/test/native/`，被 node job 的 `test:native` 跑，却读取三份生成类型
产物（node `.d.mts`、wasm `.d.ts`、python `.pyi`）。为让它在 node job 通过，
上一次修复（`ceeac5e`）在 node job 里塞了一个独立的 `stub_gen` 步骤——于是
node 的**测试段**凭空依赖了 python 构建，职责错位（用户质疑："node 的章节跟
python 有啥关系"）。

跨端一致性检查的自然归属是 node job 末尾**本就已构建 python** 的集成步骤
（`check:cross`：`uv sync` + `maturin develop` + 三端 dump 对拍），而非 node
的 vitest 测试段。

## What Changes

- 把 `vocabulary-consistency.test.ts` 的词汇一致性断言从 vitest 测试改写为
  纯标准库脚本 `scripts/check_vocab_types.py`（与既有 `check_vocab.py` grep
  闸门同族），读取同样三份生成产物、断言成员集合相等。
- 删除 `typescript/test/native/vocabulary-consistency.test.ts`（其职责由上述
  脚本承接）。
- 根 `package.json` 新增 `check:vocab-types` 脚本。
- node job：删除独立的 "generate python stub" 步骤；把 `stub_gen` 生成与
  `check:vocab-types` 调用并入末尾的 `check:cross` 集成步骤（该步骤本已
  `uv sync` + `maturin develop`，python 在此构建是自然归属）。
- `test:native` 回归纯 node：不再读取任何 python 产物。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无——CI 捕获跨端词汇漂移的可观测行为不变，仅检查所在 job/步骤迁移；
`frequency-unit` spec 的"三端成员集合相等 / 任一构建产物过期即 CI 红"契约
保持成立，`ci-matrix` spec 无涉及该检查归属的要求。故 `skip_specs: true`。）

## Non-goals

- 不改词汇单源机制本身（core enum 反射 + 构建期生成物不变）。
- 不改 `check:cross` 的数值对拍逻辑（仅在同一 CI 步骤内追加词汇类型检查）。
- 不新增 CI job、不动矩阵格、不关任何闸门（铁律：修归属而非跳闸门）。
- 不改覆盖率门槛（`test:native` 移出该测试后仍须 100%，靠其余 native 测试维持）。

## Impact

- `.github/workflows/ci.yml`：node job 步骤重排（删独立 stub_gen 步骤，
  集成步骤内加 stub_gen + check:vocab-types）。
- `typescript/test/native/vocabulary-consistency.test.ts`：删除。
- `scripts/check_vocab_types.py`：新增（纯标准库）。
- `package.json`（根）：新增 `check:vocab-types`。
- `scripts/check_ci.py`：无需改——它只强制 `test:*` 脚本进 CI，
  `check:vocab-types` 是 `check:*` 不在其管辖；`test:native` 仍在 CI。
- lessons-learned LL-047：补记"跨端检查归集成步骤，勿下沉进单端测试段"。
