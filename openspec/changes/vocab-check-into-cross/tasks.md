# Tasks

## 1. 词汇类型检查脚本（先绊红，再绊绿）

- [ ] 1.1 写 `scripts/check_vocab_types.py`（纯标准库）：逐条移植原
      `vocabulary-consistency.test.ts` 的 `tsMembers`/`pyMembers`/`stripComments`
      正则，读三份生成产物（`typescript/dist/index.node.generated.d.mts`、
      `typescript/dist/wasm-web/netwave_wasm.d.ts`、`python/netwave/_netwave.pyi`），
      断言三者成员集合相等且等于 `{Hz,kHz,MHz,GHz,THz}`，不等 exit 1。
      验证：对当前正确产物跑 exit 0；临时手改一份产物的成员名（如 `kHz`→`kHZ`）
      跑须 exit 1（绊红证明非空断言），改回 exit 0。
- [ ] 1.2 根 `package.json` 加 `check:vocab-types` 脚本调该脚本。
      验证：`pnpm check:vocab-types` exit 0。

## 2. CI 重排（node 测试段去 python 依赖）

- [ ] 2.1 删 `typescript/test/native/vocabulary-consistency.test.ts`。
      验证：`pnpm -C typescript test:native --coverage` 仍 exit 0 且覆盖率 100%
      （确认移出该测试未使 native 壳层产码覆盖跌破门槛）。
- [ ] 2.2 改 `.github/workflows/ci.yml` node job：删独立 "generate python
      stub" 步骤；在末尾 `check:cross` 集成步骤的 bash 块内、`maturin develop`
      之后追加 `cargo run --features stub-gen --bin stub_gen`（生成 `.pyi`）与
      `pnpm check:vocab-types`。验证：本地按 node job 全序列模拟——先
      `rm python/netwave/_netwave.pyi`，再依次跑 build:wasm、build:native、
      `uv sync`+`maturin develop`+`stub_gen`+`check:vocab-types`+`check:cross`，
      全 exit 0（LL-047：模拟前删该 job 不该有的产物，别信脏工作树）。
- [ ] 2.3 确认 `check:vocab-types` 已进 CI 且 `check_ci.py` 仍绿。
      验证：`grep -q 'check:vocab-types' .github/workflows/ci.yml` 命中；
      `python3 scripts/check_ci.py` exit 0（`test:native` 仍在 CI）。

## 3. 账本与全量门禁

- [ ] 3.1 更新 LL-047（ci.md + INDEX.md）：补"跨端一致性检查归集成步骤
      （本已构建该端产物处），勿下沉进单端测试段并为此单开跨语言步骤"。
      验证：`pnpm check:md` exit 0。
- [ ] 3.2 全量门禁。验证：`pnpm check` exit 0。
