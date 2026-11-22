# Tasks

## 1. 文档修复（载体：`三项全修`）

- [ ] 1.1 `三项全修`之体检发现 1：改写 `openspec/specs/lessons-learned/docs.md`
      LL-106「复发检测」段为「已落闸门 `check_comments.py`」，删对已删除 Plan
      文件的断链指针；INDEX.md 摘要行同步核对
- [ ] 1.2 `三项全修`之体检发现 2：`scripts/README.md` Scripts 表补录
      `run/test_wasm.sh`、`run/test_cross.sh`、`install_wasi_sdk.sh`、
      `install_wasm_bindgen_cli.sh` 四行
- [ ] 1.3 `三项全修`之体检发现 3：`CONTRIBUTING.md` Quick start 补
      `pnpm test:wasm` 一行（薄调用 `scripts/run/test_wasm.sh`）
- [ ] 1.4 改后跑 `pnpm check:md` 与 `pnpm check:meta` 至退出码 0

## 2. Plan/ 与归档形态（载体：`修完即删Plan体检报告`、`skip-specs文档形态`、`新开change-fix-stale-doc-facts`）

- [ ] 2.1 `修完即删Plan体检报告`：删除 `Plan/体检发现-2026-11-22.md`
      （结论已被本 change 吸收，`Plan/` 不留存），删后跑 `pnpm check:md`
- [ ] 2.2 `skip-specs文档形态`：核对 `.openspec.yaml` 已设 `skip_specs: true`，
      `openspec validate fix-stale-doc-facts --strict` 通过；归档走
      doc-only 路径不建 specs delta
- [ ] 2.3 `新开change-fix-stale-doc-facts`：proposal.md `## 已定裁决` 四条
      与本文件载体任务行逐一对应，复查无遗漏

## 3. 收尾闸门

- [ ] 3.1 `三态时效`：apply 完成前扫 `openspec/specs/` 全目录出
      「更新/新增/退役」结论留痕本文件（预期：仅 lessons-learned 分片更新，无新增/退役）
- [ ] 3.2 apply 全部任务完成后跑 `pnpm test` 全绿（先于 review 排除断裂）
- [ ] 3.3 按 governance spec「元规则 `三轴` review」对照本 change 工件审
      diff，逐文件对上本 tasks.md，硬伤清零才准入后续
- [ ] 3.4 三轴 review 后对被触碰文件做全文只读 `体检`（health-check apply 态：
      语义考古维 + 四维），发现落 `Plan/` 新文件等点名，不阻塞
- [ ] 3.5 `迟到追加`：apply 中途拍板的决定当场追加进 proposal.md
      `## 已定裁决` 并补任务行，收尾复查每个关键词载体任务已打勾
- [ ] 3.6 最后一项：跑 `pnpm check:outdated` 并按 dependency-upgrade spec
      消化所报 LAG（升级 + 全闸门 + 四端对拍），消化后复跑至退出码 0
