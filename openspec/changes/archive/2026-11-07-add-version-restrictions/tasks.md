# Tasks

## 1. 限制记录读取与判定（TDD 先 red）

- [x] 1.1 先写失败测试 `scripts/tests/versions/lib/test_restrictions.py`：断言
      `load_restrictions` 对"文件不存在"返回空记录、对四类不合契约输入（非法 JSON、
      缺 `reason`、缺 `combos`、包名缺生态前缀）抛 `RestrictionFormatError`，
      验证 `uv run pytest scripts/tests/versions/lib/test_restrictions.py` 因模块不存在
      而 red
- [x] 1.2 实现 `scripts/versions/lib/restrictions.py` 的 `load_restrictions(root)`
      与 `RestrictionFormatError`，使 1.1 全绿（验证：同命令通过；文件不存在返回 `[]`）
- [x] 1.3 补失败测试：`is_restricted(combo, restrictions)` 全等命中（当前锁定版本
      同时等于组合内每个包版本才算命中）、同记录多组合"或"、
      **未实测交叉组合判为放行**（登记 `TS7.0.0×tsdown0.23.0` 与
      `TS7.0.1×tsdown0.23.1` 时，`TS7.0.0×tsdown0.23.1` 必须判 False），
      再实现使其 green
- [x] 1.4 补失败测试：`pick_unrestricted(package, candidates, peers, restrictions)`
      在候选含已登记版本时返回"与对端搭配后未登记的最高可用版本"（方向不预设：
      最新稳定版未命中即返回最新），全候选命中时返回 `None`，再实现使其 green
- [x] 1.5 补失败测试：包名生态前缀定位锁定版本——`npm:` 从 `pnpm-lock.yaml`
      提取 `name@version` 键、`cargo:` 与 `pypi:` 从 `Cargo.lock` / `uv.lock` 的
      `[[package]]` 读取（夹具用临时目录构造 lockfile），记录引用的包在仓库不存在时
      该条判为不命中且不报错、记录保留，再实现使其 green
- [x] 1.6 跑 `uv run pytest --cov=scripts/versions --cov-report=term` 加
      `--cov-fail-under=100`，确认 `lib/restrictions.py` 覆盖率 100%（铁律七），
      缺口补测试至绿

## 2. 体检消费与退出码语义

- [x] 2.1 先写失败测试 `scripts/tests/versions/test_check_outdated.py`：断言
      target 计算调用 `pick_unrestricted`，命中已登记组合时输出含
      `SKIP <id/原因>` 且 target 不是被登记的版本；未命中时 target 仍是最新稳定版
      （验证：`uv run pytest scripts/tests/versions/test_check_outdated.py` red）
- [x] 2.2 改 `scripts/versions/check_outdated.py`：项目依赖段接入
      `lib/restrictions.py`，逐包 target 按 2.1 语义输出（只调整本行包，对端不动），
      使 2.1 green
- [x] 2.3 先写失败测试：断言网络段失败时 `main()` 返回非零、且其余段仍产出报 告；
      断言脚本不再存在"恒返回 0"路径
- [x] 2.4 改 `check_outdated.py` 退出码：网络失败段记录失败并继续其余段，
      末尾返回非零；更新文件 docstring 删除"Exit code: always 0"措辞，使 2.3 green
- [x] 2.5 核对 `scripts/check_ci.py` 与 `.github/workflows/ci.yml`：确认
      `check:outdated` 未被任何 PR 门禁调用，且无残留"退出码恒 0"断言或注释
      （验证：`python3 scripts/check_ci.py` 退出 0，`grep -rn "always 0" scripts/`
      零命中）
- [x] 2.6 人工跑 `pnpm check:outdated` 一次，确认四段照常输出、限制记录被消费、
      无网络时以非零退出并点名失败服务（验证：观察输出与 `echo $?`）

## 3. 实测 typescript × tsdown 并登记首批记录

- [x] 3.1 用 `pnpm -C typescript build:shells` 逐个实测 typescript 与 tsdown 各
      候选版本，记录每个组合的通过/失败结论（验证：每个组合有明确命令与退出码留痕）
      **实测结论（改判）**：原任务写"实测 `typescript@7.0.0`"前提不成立——npm
      registry 从未发布 `typescript@7.0.0`/`7.0.1`（`npm view typescript@7.0.0` → 404，
      7.x 稳定线仅有 7.0.2）。改测现网实有版本：TS 7.0.2 × tsdown
      {0.23.0,0.23.1,0.23.2,0.23.3,0.23.4,0.23.5,0.23.7} 全部 rc=0（日志
      /tmp/build_*.log）。git 可核时间线：失败时点（`3c6c438`，2026-09-29）与
      复测绿时点（`091fd3a`，2026-10-01）锁定的是同一版本对 TS 7.0.2 × tsdown
      0.23.0，根因是当时项目侧 dts 管线（壳尚为手写 JS、走实验路径），非坏版本对
- [x] 3.2 创建 `scripts/versions/restrictions.json`：3.1 实测无失败组合，故以空清单
      `{"restrictions": []}` 落地（验证：`load_restrictions` 对仓库根读出 `[]`，
      与失败组合数 0 一致）
- [x] 3.3 `typescript/package.json` 的 `tsdown` 版本要求**无需收紧**：3.1 实测无失败
      组合、无已登记版本，按 spec「只登记实测失败的具体版本组合」与 LL-081
      「禁加未实测限制」，保持 `^0.23.0` 不动（验证：无登记即无收紧需求，
      `pnpm check` 全绿）
- [x] 3.4 跑 `pnpm check` 全绿 + `pnpm check:cross` 四端对拍（容差不变），
      确认登记未破坏构建与数值行为（验证：两命令退出码均 0，四端
      bit-exact / wasm within tol；因无失败组合，本轮无收紧范围改动）

## 4. 文档与波及面同步

- [x] 4.1 `scripts/versions/README.md` 补「登记一条版本限制」小节：跑哪条命令确认
      失败、往 `restrictions.json` 加什么格式（含 `reason` + `combos` 示例）、
      包名必须带生态前缀、只写实测版本禁写范围、同轮如何收紧钉版文件；
      验证：新人照文档能独立登记一条并让体检输出 SKIP
- [x] 4.2 `Plan/软件升级.md` 删除「blocked 落地」「pairs JSON 化」两节与
      「落地形态汇总」中对应条目（机制已落地，结论入主 spec 与数据文件），
      「过期检查门禁化」节 blocked 措辞改指 `restrictions.json`，
      「Python 3.15 升级」节删去"blocked 未实施"暂缓理由与前置
      （验证：`grep -rn "blocked" Plan/` 零命中）
- [x] 4.3 登记 lessons-learned 两条并更新 INDEX：无官方文档且无本仓实测的
      "必须配套升级"规矩属凭空生成、一律删除（workflow 分片）；收紧依赖范围只抬下界、
      禁止新增未实测上界（ci 或 workflow 分片）（验证：
      `openspec/specs/lessons-learned/INDEX.md` 出现两条新编号）
- [x] 4.4 跑 `pnpm check:md` 退出 0（验证：命令退出码）
- [x] 4.5 扫 `openspec/specs/` 全目录做三态时效检查（更新/新增/退役），
      结论留痕本文件末尾（config.yaml apply 钩子要求）

## 三态时效检查留痕（4.5）

扫描 `openspec/specs/` 全目录，与本 change 相关的时效结论：

- **新增**：`dependency-upgrade` spec 的「版本限制记录数据文件」「版本限制记录与
  坏版本降级」「限制记录读取的错误语义」三条 Requirement 已随 sync 写入主 spec。
- **退役**：主 spec `dependency-upgrade` 原「坏版本降级与 blocked 触发式实施」
  Requirement（spec.md:125）及正文 "blocked" 措辞（spec.md:15/137/143/146/153/239），
  由本 change delta 的 REMOVED 段声明移除，sync/archive 时删除——主 spec 现仍含
  旧措辞属未同步的正常中间态，非漏改。
- **更新**：`scripts/versions/README.md`（登记指南 + 退出码）、`Plan/软件升级.md`
  （删两节 + blocked 措辞改指 restrictions.json）、`lessons-learned`（LL-080/081
  已存，本会话补 LL-082/083）均已随本轮更新。
- **无残留**：`grep -rn "blocked" Plan/` 零命中；`grep -rn "always 0" scripts/` 零命中。

## Workflow follow-up

- 人工 review 通过后，运行 `/opsx:archive` 或要求归档本 change，
  归档时按 config.yaml archive 钩子执行 Plan/ 瘦身与三态时效检查。
- 体检门禁化（暂名 `add-freshness-schedule-gate`）不在本 change 内，
  待人工拍板后另行 propose；实现时复用 `lib/restrictions.py` 的过滤结果，
  禁止另造第二套判断。
