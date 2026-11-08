# Tasks

本 change 不触碰四端绑定与数值路径，跨绑定对拍与教学式 docs 验收不适用；
闸门以 `pnpm check`（含 `check:py` 覆盖率 100%）与 `pnpm check:md` 为准。
TDD（铁律二）：每个实现任务前均有先红的测试任务。

## 1. peers 扩展（lib/repository.py）

- [ ] 1.1 红：写测试——`runtime_pins(root)` 从 `.python-version` 产出
      `pypi:python`（minor 粒度）、从 `rust-toolchain.toml` 产出
      `cargo:rustc`、从 workflow `uses:` 产出 `github:<repo>`；夹具含
      "登记 `pypi:python 3.16 × pypi:numpy 2.3.0` + python 钉 3.15 +
      numpy 锁 2.3.0 → 组合命中"与"numpy 升 2.4.0 → 组合失效"正反例；
      运行确认失败
- [ ] 1.2 绿：实现 `runtime_pins(root)`，与 `locked_versions` 合并为
      peers 供 restrictions 判定；1.1 转绿

## 2. facade 接线（check_outdated.py）

- [ ] 2.1 红：写测试——全段 target 行过 `pick_unrestricted`：CLI 探针、
      直装工具、CI actions、`.python-version` 段的最新版命中已登记组合时
      改报最高可用版 + `SKIP <reason>`；运行确认失败
- [ ] 2.2 绿：出行为统一走 `target_line()`（candidates 缺失时以 latest
      单候选过 `is_restricted`），判定仍唯一入口 `lib/restrictions.py`；
      2.1 转绿
- [ ] 2.3 红：写测试——源失败重试一次仍败 → 该行 SKIP、不计 FAILED、
      退出码 0；本地探针缺失或 `restrictions.json` 破损 → FAILED 非零；
      运行确认失败
- [ ] 2.4 绿：实现重试一次 + SKIP/FAILED 分层退出码；2.3 转绿
- [ ] 2.5 更新 `check_outdated.py` 模块 docstring 与退出码说明
      （SKIP/FAILED 分层 、apply 末尾触发；只写当前契约事实，不留变更叙述）

## 3. 触发与授权接线

- [ ] 3.1 `openspec/config.yaml` 双写接线：`operations.apply.guidance` 新增
      一条 + `rules.tasks` 新增一条（tasks.md 最后一项任务 MUST 是
      `pnpm check:outdated` 并按 dependency-upgrade spec 预授权消化 LAG：
      升级+全闸门+四端对拍，上游 bug/不兼容登记回退不阻塞；设计级适配、
      `restrictions.json` 破损、流程走不通才停下报告；下限变更等人工发起）
- [ ] 3.2 `AGENTS.md` 硬护栏段加例外句：apply 末尾体检所报 LAG 的升级 =
      已获授权动作（附出处：dependency-upgrade spec「apply 末尾体检与
      升级预授权」）；例外仅授执行+验证，不含 commit——升级改动在
      提交全景表单列一组，仍等人工点名

## 4. 文档同步

- [ ] 4.1 改写 `scripts/versions/README.md`：Exit codes 节改 SKIP/FAILED
      分层、Usage 节补 apply 末尾触发、登记示例补运行时组合一条
- [ ] 4.2 `Plan/软件升级.md`：「过期检查门禁化」节改写为本形态并标记
      已定案（apply 完成即整节删除，归档时执行 Plan/ 瘦身检查）
- [ ] 4.3 波及面自查：grep 全仓 `check:outdated`、`restricted`、
      `升级分级` 引用，确认 CI（`ci.yml` 不含该命令）、README、spec、
      `scripts/README.md`、`AGENTS.md` 无旧事实残留

## 5. 闸门与收尾

- [ ] 5.1 `pnpm check:py` 全绿且 `scripts/versions` 覆盖率维持
      `--cov-fail-under=100`
- [ ] 5.2 `pnpm check` 全绿（含 check:meta 的 check_proposal /
      check_ci / check_else 等）
- [ ] 5.3 `pnpm check:md` 退出码 0
- [ ] 5.4 真实环境手动跑一次 `pnpm check:outdated` 确认四段输出与退出码
      符合新语义；`openspec validate` 加 `--strict` 通过
- [ ] 5.5 按 apply 指引扫 `openspec/specs/` 三态时效（更新/新增/退役）
      留痕本文件；LL 登记：本 change 若踩非版本性坑当轮进
      lessons-learned 分片 + INDEX
- [ ] 5.6 本 change 末尾体检（新规则示范）：跑 `pnpm check:outdated`，
      所报 LAG 按预授权消化（升级+全闸门+四端对拍，红则登记回退），
      升级改动在提交全景表单列一组等人工点名
