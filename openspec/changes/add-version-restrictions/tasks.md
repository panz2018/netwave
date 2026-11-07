# Tasks

## 1. 限制记录读取与判定（TDD 先 red）

- [ ] 1.1 先写失败测试 `scripts/tests/versions/lib/test_restrictions.py`：断言
      `load_restrictions` 对"文件不存在"返回空记录、对四类不合契约输入（非法 JSON、
      缺 `reason`、缺 `combos`、包名缺生态前缀）抛 `RestrictionFormatError`，
      验证 `uv run pytest scripts/tests/versions/lib/test_restrictions.py` 因模块不存在
      而 red
- [ ] 1.2 实现 `scripts/versions/lib/restrictions.py` 的 `load_restrictions(root)`
      与 `RestrictionFormatError`，使 1.1 全绿（验证：同命令通过；文件不存在返回 `[]`）
- [ ] 1.3 补失败测试：`is_restricted(combo, restrictions)` 全等命中（当前锁定版本
      同时等于组合内每个包版本才算命中）、同记录多组合"或"、
      **未实测交叉组合判为放行**（登记 `TS7.0.0×tsdown0.23.0` 与
      `TS7.0.1×tsdown0.23.1` 时，`TS7.0.0×tsdown0.23.1` 必须判 False），
      再实现使其 green
- [ ] 1.4 补失败测试：`pick_unrestricted(package, candidates, peers, restrictions)`
      在候选含已登记版本时返回"与对端搭配后未登记的最高可用版本"（方向不预设：
      最新稳定版未命中即返回最新），全候选命中时返回 `None`，再实现使其 green
- [ ] 1.5 补失败测试：包名生态前缀定位锁定版本——`npm:` 从 `pnpm-lock.yaml`
      提取 `name@version` 键、`cargo:` 与 `pypi:` 从 `Cargo.lock` / `uv.lock` 的
      `[[package]]` 读取（夹具用临时目录构造 lockfile），记录引用的包在仓库不存在时
      该条判为不命中且不报错、记录保留，再实现使其 green
- [ ] 1.6 跑 `uv run pytest --cov=scripts/versions --cov-report=term` 加
      `--cov-fail-under=100`，确认 `lib/restrictions.py` 覆盖率 100%（铁律七），
      缺口补测试至绿

## 2. 体检消费与退出码语义

- [ ] 2.1 先写失败测试 `scripts/tests/versions/test_check_outdated.py`：断言
      target 计算调用 `pick_unrestricted`，命中已登记组合时输出含
      `SKIP <id/原因>` 且 target 不是被登记的版本；未命中时 target 仍是最新稳定版
      （验证：`uv run pytest scripts/tests/versions/test_check_outdated.py` red）
- [ ] 2.2 改 `scripts/versions/check_outdated.py`：项目依赖段接入
      `lib/restrictions.py`，逐包 target 按 2.1 语义输出（只调整本行包，对端不动），
      使 2.1 green
- [ ] 2.3 先写失败测试：断言网络段失败时 `main()` 返回非零、且其余段仍产出报告；
      断言脚本不再存在"恒返回 0"路径
- [ ] 2.4 改 `check_outdated.py` 退出码：网络失败段记录失败并继续其余段，
      末尾返回非零；更新文件 docstring 删除"Exit code: always 0"措辞，使 2.3 green
- [ ] 2.5 核对 `scripts/check_ci.py` 与 `.github/workflows/ci.yml`：确认
      `check:outdated` 未被任何 PR 门禁调用，且无残留"退出码恒 0"断言或注释
      （验证：`python3 scripts/check_ci.py` 退出 0，`grep -rn "always 0" scripts/`
      零命中）
- [ ] 2.6 人工跑 `pnpm check:outdated` 一次，确认四段照常输出、限制记录被消费、
      无网络时以非零退出并点名失败服务（验证：观察输出与 `echo $?`）

## 3. 实测 typescript × tsdown 并登记首批记录

- [ ] 3.1 用 `pnpm -C typescript build:shells` 逐个实测 `typescript@7.0.0` 与
      tsdown 各候选版本（0.23.0 起沿 0.23 线逐个试，另试 0.24 及以上首个可用版），
      记录每个组合的通过/失败结论（验证：每个组合有明确命令与退出码留痕）
- [ ] 3.2 按 3.1 结果创建 `scripts/versions/restrictions.json`：同一原因下的失败
      组合合并进一条记录的 `combos`，包名带 `npm:` 前缀、版本写实测具体值
      （验证：`uv run python -c "from lib.restrictions import load_restrictions"` 能
      读出且条数与失败组合数一致）
- [ ] 3.3 同轮收紧 `typescript/package.json` 的 `tsdown` 版本要求：沿用 caret 写法
      只抬下界（如 `^0.23.0` → `^0.23.2`），MUST NOT 改成 `>=` 或钉死；
      验证：`pnpm install` 后 `grep -n "tsdown@" pnpm-lock.yaml` 锁定版本落在新范围内
- [ ] 3.4 跑 `pnpm check` 全绿 + `pnpm check:cross` 四端对拍（容差不变），
      确认收紧范围与登记未破坏构建与数值行为

## 4. 文档与波及面同步

- [ ] 4.1 `scripts/versions/README.md` 补「登记一条版本限制」小节：跑哪条命令确认
      失败、往 `restrictions.json` 加什么格式（含 `reason` + `combos` 示例）、
      包名必须带生态前缀、只写实测版本禁写范围、同轮如何收紧钉版文件；
      验证：新人照文档能独立登记一条并让体检输出 SKIP
- [ ] 4.2 `Plan/软件升级.md` 删除「blocked 落地」「pairs JSON 化」两节与
      「落地形态汇总」中对应两条（结论已入主 spec 与数据文件），
      「过期检查门禁化」节内 blocked 措辞改指 `restrictions.json`，
      「Python 3.15 升级」节的暂缓理由删去"blocked 未实施、pairs 未落地"两条
      （验证：`grep -rn "blocked" Plan/` 零命中）
- [ ] 4.3 登记 lessons-learned 两条并更新 INDEX：无官方文档且无本仓实测的
      "必须配套升级"规矩属凭空生成、一律删除（workflow 分片）；收紧依赖范围只抬下界、
      禁止新增未实测上界（ci 或 workflow 分片）（验证：
      `openspec/specs/lessons-learned/INDEX.md` 出现两条新编号）
- [ ] 4.4 跑 `pnpm check:md` 退出 0（验证：命令退出码）
- [ ] 4.5 扫 `openspec/specs/` 全目录做三态时效检查（更新/新增/退役），
      结论留痕本文件末尾（config.yaml apply 钩子要求）

## Workflow follow-up

- 人工 review 通过后，运行 `/opsx:archive` 或要求归档本 change，
  归档时按 config.yaml archive 钩子执行 Plan/ 瘦身与三态时效检查。
- 体检门禁化（暂名 `add-freshness-schedule-gate`）不在本 change 内，
  待人工拍板后另行 propose；实现时复用 `lib/restrictions.py` 的过滤结果，
  禁止另造第二套判断。
