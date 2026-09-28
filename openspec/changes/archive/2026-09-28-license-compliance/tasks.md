# Tasks

## 1. LICENSE 文件与元数据

- [x] 1.1 根新增 `LICENSE-MIT`（MIT 全文，`Copyright (c) 2026 panz2018`）
      与 `LICENSE-APACHE`（Apache-2.0 全文）
- [x] 1.2 补齐 license 字段为 `MIT OR Apache-2.0`：`core/Cargo.toml`、
      `python/Cargo.toml`、`typescript/native/Cargo.toml`、
      `typescript/wasm/Cargo.toml`、`python/pyproject.toml`；
      `typescript/package.json` 由纯 MIT 改为双许可
- [x] 1.3 各 `Cargo.toml` 补 license-files 指向两份 LICENSE
      （workspace 根许可继承验证）

## 2. 门禁

- [x] 2.1 新增 `scripts/check_license.py`（纯标准库）：校验六处元数据
      license 字段与根声明一致；先写会失败的用例（red：临时改 package.json
      为 MIT 应报 LICENSE DRIFT）再实现（green）
- [x] 2.2 根 `package.json` 加 `check:meta` 并纳入 `check` 聚合；
      `pnpm check` 全绿

## 3. 文档

- [x] 3.1 README `## License` 节改写：双许可 + AS IS 人话版 +
      `## References` 节（scikit-rf/SignalIntegrity/Touchstone spec/书
      四条 URL+DOI，含 Touchstone® 商标声明行）
- [x] 3.2 `testdata/LICENSE-NOTES.md` 占位改为登记模板表
      （文件 | 来源 URL | 上游版本 | copied/generated | 许可）+ demo
      数据自产规则
- [x] 3.3 AGENTS.md 加一行指针：参考第三方前先查账本许可表

## 4. 账本

- [x] 4.1 lessons-learned docs 分片新增 LL：第三方许可表（四源 URL）+
      GPL 红线（SignalIntegrity 禁抄代码）；INDEX.md 同步

## 5. 验证

- [x] 5.1 `openspec validate license-compliance` 通过
- [x] 5.2 `pnpm check:md` + `pnpm check` 全绿；提交
