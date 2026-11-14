# 三轴 review 结论（task 8.1）

按 governance spec「元规则 review 三轴」对照四件工件审实现 diff。
结论：硬伤清零；CI artifact 下载与标定轮数字（task 3.2/4.2/5.3/6.x）
依赖 push 后 CI 首轮，属流程后置而非未决硬伤。

## Standards 轴（是否守本仓编码/文档标准）

- ci.yml：三 job 改造均 `shell: bash`（LL-011）；`(cd python && ...)`
  子 shell 隔离目录（LL-011）；show-env/clean/build/test/report 同 step
  （环境变量不跨 step）；无 `if:` 跳格求绿（LL-003）。
- 注释只写当前契约事实，无路线图标记/考古叙述（用户注释风格）。
- 新增 `scripts/tests/test_coverage_gate.py` 走既有 import-main 惯例，
  ruff 干净；`pyproject.toml` pythonpath 补 `scripts` 有注释说明。
- 文档同步齐全（LL-034）：CONTRIBUTING、scripts/README、Plan 三档、
  账本 INDEX+ci.md；`pnpm check:md` 绿。
- review 中自查修正两处：spec/design 的"无代码围栏"改为"无可执行
  doctest"（唯一围栏是 bin target 的 `text`，不可执行）；tasks 8.2 的
  裸版本代号改点分版本（VERSION TAG 门禁）。

## Spec 轴（是否合 delta spec 与 proposal）

- ci.yml 命令字面与 delta spec 一致：core `-p netwave --codecov`、
  show-env `--no-cfg-coverage`、python `report --codecov`、
  native `report --target`；报告命名 `coverage-<对象>.json` 落 `coverage/`。
- 五格矩阵、铁律七两处 MODIFIED + 三条 ADDED 与实现对应；
  `cargo test --workspace` 退役前提（无可执行 doctest）grep 实证。
- 地板首轮全 0（两阶段标定），与「覆盖率地板两阶段标定」一致。
- `openspec validate --strict` 绿；`check:meta`（含 check_ci）绿。

## Lessons 轴（防复发是否落账/落闸门）

- LL-092（外部驱动胶水覆盖率三坑）、LL-093（口径漂移假绿）登记 ci.md
  - INDEX；LL-005/LL-040 复发、LL-091 已在前序提交登记。
- 可门禁化项：胶水报告"含目标 src 行且命中 > 0"的断言已落
  `test_coverage_gate.py`（2.1/2.2）；show-env 子 shell 约束落 LL-091。
- 依赖升级（8.2）按 dependency-upgrade 预授权消化，SUMMARY 0 LAG。

## 遗留（非硬伤，流程后置）

- task 3.2/4.2/5.3：upload-artifact 步骤已加，artifact 实际下载验证待 push。
- task 6.1/6.2/6.3：标定轮收六份数字、缺行定性、翻地板 100，依赖 CI 首轮。
