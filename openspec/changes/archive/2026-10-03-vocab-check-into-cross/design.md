# Design

## Context

见 proposal.md - Why。当前状态：`vocabulary-consistency.test.ts` 用 vitest 读
三份生成产物（node `.d.mts`、wasm `.d.ts`、python `.pyi`），用正则从各产物的
enum/class 块提取成员名并断言相等；node job 为喂给它而单开 `stub_gen` 步骤。
既有 `scripts/check_vocab.py` 是同族先例——纯标准库 grep 闸门，经
`check:meta` 入门禁，扫描绑定源码禁手抄词汇。

约束：`check_ci.py` 只强制 `typescript/package.json` 的 `test:*` 脚本进 CI；
`check:*` 脚本不在其管辖。`test:native` 覆盖率门槛 100% 须维持。

## Goals / Non-Goals

**Goals:**

- 跨端词汇一致性检查落在"本就已构建 python"的集成步骤，node 测试段零 python 依赖。
- 检查逻辑与 `check_vocab.py` 同族：纯标准库、独立可跑、失败 exit 1。
- 成员提取语义与原 vitest 版等价（同一套正则规则，避免移植引入假绿/假红）。

**Non-Goals:**

- 不改产物生成方式（stub_gen / napi / wasm-pack 不变）。
- 不改数值对拍（`cross_compare.py` 不碰）。

## Decisions

**决策一：脚本化而非保留 vitest。**
把断言从 vitest 测试改为 `scripts/check_vocab_types.py`。理由：该检查读的是
构建产物、不依赖 JS/Python 运行时，本质是构建后静态校验，与 `check_vocab.py`
同类；放 `scripts/` 可被任意 job 直接调用，无需 vitest 配置与覆盖率上下文。
备选（保留 vitest、仅把测试文件挪到独立 `test:cross` 脚本）被否：仍需 node job
跑 python 产物，且 `check_ci.py` 会强制新 `test:*` 进 CI，反而增加耦合面。

**决策二：成员提取逻辑逐条移植原 vitest 正则。**
原测试的 `tsMembers`（`enum FrequencyUnit` 花括号块内 `Name =` 行）、
`pyMembers`（`class FrequencyUnit` 下 4 空格缩进 `Name = ...` 行、遇 dedent 停）
已在 CI 验证正确，移植为 Python 时保持同一匹配规则与注释剥离，不重写解析器。
真值来源仍是三份生成产物本身（零手抄词汇，符合 frequency-unit spec）。

**决策三：并入 `check:cross` 步骤而非新开步骤。**
node job 末尾 `check:cross` 步骤已 `uv sync --project python` +
`maturin develop`（python 在此构建是数值对拍的自然需要）。在同一 bash 块内
追加 `stub_gen` 生成 `.pyi` + `python3 scripts/check_vocab_types.py`，python
依赖被限制在"本就需要 python"的步骤内，node 测试段（`test:native`）回归纯 node。
备选（新开独立步骤）被否：那正是当前被质疑的形态，只是换了位置。

## Risks / Trade-offs

- [移植正则与原 vitest 版行为漂移] → 任务含"对同一组产物，脚本结果须与原
  vitest 断言一致"的对拍验证；正则原样复制不重写。
- [`check:vocab-types` 未进任何 CI 步骤 = 假闸门（违 LL-037 同类）] → 任务
  含"grep ci.yml 确认 `check:vocab-types` 被调用"；本地模拟 node job 全序列。
- [`test:native` 移出该测试后 native 覆盖率跌破 100%] → 任务含"重跑
  `test:native --coverage` 确认仍 100%"；该测试读文件不产码，移出通常不影响
  壳层产码覆盖，但须实测。
