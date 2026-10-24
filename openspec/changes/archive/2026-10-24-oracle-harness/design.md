# Design: oracle-harness

## Context

交叉验证现状三处分散：`testdata/`（manifest + 3 个 dut 样本 + LICENSE-NOTES）、
`scripts/cross_compare.py`（阅卷）、`.cross-tmp/`（平铺 36 个
`<end>_ts_<case>_<field>.bin`）。本变更为纯结构迁移 + 布局重排，不新增功能；
golden 纵向轴（对 skrf）整体推迟（见 proposal Non-goals）。

## Decisions

### D1 命名 `oracle/`（弃 verify/conformance）

未来项目含 GUI，泛化词 verify/conformance 会与界面验收歧义。oracle =
数值真值参照 + 阅卷，与 scikit-rf 作为 oracle 的既有术语一致，GUI 不可能
占用此名。目录短名符合 workspace-layout 风格。

### D2 golden 不进 git，CI 现算（推翻原"committed golden"设计）

原设计（golden 提交进 git + 周更 diff 守护）被人工裁决废弃：bin 文件在 git
中不可审计，维护数据变更负担大于收益。新契约：golden 由 `gen_golden.py` 在
CI 现算、只活在 `oracle/tmp/golden/`；skrf 版本靠 `oracle/uv.lock` 钉死，
升级 = 显式改 lock 的 PR（标准版本化由 lock 承担，不再由 golden 文件承担）。
本变更只立骨架，gen_golden 与 uv 环境下期落地；铁律四措辞本次即按新契约
改写（golden 不入库、CI 现算、uv.lock 治理、周更作废）——推迟的是 CI 内
跑 skrf 的实施，不是契约本身，spec 作为真相源不得抄录已废弃旧契约。

### D3 阅卷集中、各端只 dump；命名 compare_cross

全部比较逻辑收进 `oracle/compare_cross.py`（横向轴），各端测试不再做跨端
比较。理由：容差语义只实现一次，避免 Rust/Python/JS 三处比较器漂移；
"运动员兼裁判"的根治是参照物外置（golden=skrf），core 在横向轴仅作互比锚点，
不代表权威。golden 纵向轴（四端 vs skrf）同样集中到 oracle（compare_golden，
下期），不在各端测试内。命名弃 `compare_native`：`native` 与
`typescript/native/`（napi crate）撞词而语义不同（此处指"原生三端 vs wasm"
的分层规则）；`cross`（横向轴）与 `golden`（纵向轴）成对，两文件名自解释
两条轴。

### D4 答卷区 `oracle/tmp/`，分层 `<end>/<sample>/<field>.bin`

平铺长文件名随 case 增长失控；`.cross-tmp` 是阅卷分散时代的遗留名（当时
阅卷在 scripts/，临时区只能放仓库根靠隐藏点提示）。阅卷集中后答卷区随
阅卷迁入 oracle：`oracle/tmp/`（不加点，可见性好）。分层两轴：end（4）→
sample（样本名，空格 sanitize 为下划线；原件名不改，空格仍是解析测试维度）
→ field（s/z0/version.txt）。不设 `ts/` 中间层（输入几乎全是 Touchstone，
层是废话）；不设 s/z/y/h 目录层（每域一个 bin，做文件名 `z.bin` 即可）。
非 TS 轴（freq.bin）直接挂 end 下。忽略规则写 `oracle/.gitignore`（内容
`tmp/`）；根 `.gitignore` 的旧 `.cross-tmp/` 死行随迁移一并删除。

### D5 容差分层实证修正

核查证实 core 测试（`core/tests/touchstone_domain.rs` 等）从未运行时读取
manifest，是硬编码 `const TOL`，注释"from testdata/manifest.json"仅为出处
声明。与其让注释假装读 manifest，不如承认分层：core 自校验容差 = 测试自述
常量；跨端阅卷容差 = manifest 唯一来源。铁律三据此改写（见 delta）。

### D6 CI 落点维持 node job

阅卷需要四端产物齐，node job 已构建 napi+wasm+python 扩展并跑
`pnpm check:cross`，路径同步即可，不新建 job、不传 artifact。多平台阅卷
天然保留（node job 4 个 OS cell 各自 dump+比对）。

## Risks / Trade-offs

- core 测试不再引用 manifest：容差值可能漂移出两处（core const 与
  manifest core_tol）。接受——分层语义下两者本就不要求同源；review 时对照。
- 路径大迁移波及 CI/文档/脚本多处：tasks 逐文件列全，`pnpm check` +
  `check_ci.py` + `check_md.py` 作闸门兜底。
- 纵向轴推迟期间"对 skrf 正确性"无自动验证：与现状相同（golden 本就未
  实现），无回退。

## Migration Plan

单 PR 完成：建 oracle/（含 `.gitignore`：`tmp/`）→ 迁数据与脚本 → 改
dump/compare 路径 → 改 package.json/ci.yml → 删 testdata/ 与根
`.cross-tmp/` 旧产物 → 同步全部文档 → `pnpm check` + `pnpm check:cross`
全绿。回滚 = revert 单 PR。
