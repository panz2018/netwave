# Tasks

> 纯文档迁移：无新数值逻辑，跳过 red/green（简化表"改文档"行）；
> 验收 = 链接校验 + openspec validate + 全仓 grep 零旧引用。

## 1. 迁入 spec

- [ ] 1.1 `openspec/specs/project-governance/spec.md`：按 delta 的 ADDED
      Requirements 建立主 spec（铁律一~七 + 两条元规则 + 修订历史原样迁入）
- [ ] 1.2 `openspec/config.yaml`：context 指针从 `Plan/constitution.md`
      改指 `openspec/specs/project-governance/spec.md`；rules 保留不变
- [ ] 1.3 验证：`openspec validate --specs` 通过（含新能力）

## 2. 全仓引用改写

- [ ] 2.1 顶层文档：`AGENTS.md`（铁律指针 + Plan/ 生命周期条款）、
      `CONTRIBUTING.md`（如有 constitution 引用）改指新位置
- [ ] 2.2 子项目 README：`core/`、`python/`、`typescript/`、`testdata/`、
      `scripts/` 中 `constitution rule N` 措辞改 `governance spec rule N`，
      链接改指 `openspec/specs/project-governance/spec.md`
- [ ] 2.3 代码注释：`core/src/lib.rs`、`core/tests/fill_pattern.rs`、
      `python/tests/test_roundtrip.py` 等英文注释中 constitution 指向改写
      （仅措辞与链接，零逻辑改动）
- [ ] 2.4 `Plan/` 内部：`README.md`、`开发流程.md`、`总体计划.md`、
      `测试规划.md`、`typescript源码化规划.md` 的 constitution 链接改指
      新位置；"迁入 openspec/project.md" 表述改为"已迁入
      openspec/specs/project-governance/"（历史修订记录不改写）

## 3. 删除与终验

- [ ] 3.1 删除 `Plan/constitution.md`；确认无编辑器幽灵回写
      （`git status` 干净）
- [ ] 3.2 验证：`pnpm check:md` 零断链；
      `grep -rn "Plan/constitution" --include="*.md" --include="*.rs" --include="*.py" --include="*.ts" .`
      仅剩归档目录与修订历史命中
- [ ] 3.3 验证：`cargo test --workspace`、`pnpm check:ts`、`pnpm check:py`
      通过（注释改动不破坏编译）
- [ ] 3.4 提交推送，CI 全绿
