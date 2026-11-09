# Tasks

## 1. biome 认领 YAML

- [ ] 1.1 改 `biome.jsonc`：从 `files.includes` 移除 `!**/*.yaml` 与
      `!**/*.yml` 两条（保留 `!**/pnpm-lock.yaml` 及生成物目录排除），
      不加 `yaml.formatter.quoteStyle`（用 biome 默认 double）。
      验证: `pnpm check:ts` 退出码 0（dry-run 基线为 41 文件零改动）。
- [ ] 1.2 改写 `biome.jsonc` 顶部注释：删除"YAML 由 pnpm 约定（单引号）"
      这一过时事实，改为记录现行归属（md=markdownlint+Prettier、
      yaml/js/ts/json=biome）与 md 排除理由（biome md 格式化官方自报约
      92% 兼容 Prettier、lint 规则仍在 Nursery）。
      验证: 注释无与 1.1 矛盾之处，`pnpm check:ts` 仍绿。
- [ ] 1.3 跑 `pnpm fix:ts` 后 `git diff` 核对 YAML 实际改动面，
      逐文件确认无非预期重排（重点看 `.github/workflows/ci.yml` 的矩阵
      表达式与长字符串）。验证: diff 为空或仅含可解释的改动；出现非预期
      重排即停下汇报，不自行放行。

## 2. 归属不变式成文与编辑器对齐

- [ ] 2.1 将本 change 的 `specs/ci-matrix/spec.md` delta（Requirement
      「格式化归属单一来源」）同步进 `openspec/specs/ci-matrix/spec.md`。
      验证: 主 spec 含该 Requirement 及其三个 Scenario，
      `openspec validate adopt-biome-yaml-formatting` 通过。
- [ ] 2.2 `.vscode/extensions.json` 的 recommendations 补 `biomejs.biome`，
      注释说明其为 js/ts/json/yaml 的格式化与 lint 扩展（对齐闸门层）。
      验证: JSON 可解析，`pnpm check:ts` 绿（该文件在 biome 管辖内）。
- [ ] 2.3 删除 `Plan/biome多文件格式化.md`（结论已吸收进 spec 与配置）。
      验证: `grep -c biome Plan/*.md` 无残留待议条目，`pnpm check:md` 绿。

## 3. 闸门与时效收口

- [ ] 3.1 跑全量闸门 `pnpm check`（md + ts + rs + py + meta）。
      验证: 退出码 0；`check:ts` 覆盖面含 YAML、`check:md` 行为不变。
- [ ] 3.2 扫 `openspec/specs/` 全目录出三态时效结论（更新/新增/退役），
      记在本项完成记录：预期为 ci-matrix 更新、无新增目录、无退役，
      `openspec/specs/README.md` 路由表无需结构改动。
      验证: 结论与本 change 影响面一致，无 spec 需改而未改。
- [ ] 3.3 跑 `pnpm check:outdated` 并按 dependency-upgrade spec
      「apply 末尾体检与升级预授权」消化所报 LAG（升级 + 全闸门 +
      四端对拍，含全局 CLI/直装工具的机器级升级；上游 bug/不兼容登记
      回退不阻塞；仅设计级适配、restrictions.json 破损、流程走不通才停下
      报告；下限变更等人工发起）。消化完成后复跑 `pnpm check:outdated`
      至退出码 0（SUMMARY 归零）。验证: 复跑退出码 0。
