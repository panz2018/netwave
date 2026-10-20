# Tasks: oracle-harness

## 1. oracle 骨架与数据迁移

- [ ] 1.1 建 `oracle/`：`README.md`（英文，只放本目录跑法：`python3
      oracle/compare_cross.py oracle/tmp` 与 `pnpm check:cross`；不重述
      容差规则，指向 governance spec）；`.gitignore`（内容 `tmp/`；根
      `.gitignore` 不改）
- [ ] 1.2 `git mv testdata/manifest.json oracle/manifest.json`（内容原样，
      schema 0；仅把 note 中的旧路径措辞改为 oracle）
- [ ] 1.3 `git mv testdata/touchstone oracle/samples`（dut.s1p/s2p/s4p
      原样，不改名）
- [ ] 1.4 `git mv testdata/LICENSE-NOTES.md oracle/LICENSE-NOTES.md`；
      删除空 `testdata/`

## 2. 阅卷脚本迁移与分层适配

- [ ] 2.1 `git mv scripts/cross_compare.py oracle/compare_cross.py`；
      读路径改分层：`<end>/freq.bin`、`<end>/<sample>/s.bin|z0.bin|
      version.txt`（sample 名空格 sanitize 为下划线）；manifest 读
      `oracle/manifest.json`；anti-tautology 自检随路径同步（扰动定位断言
      不变）
- [ ] 2.2 验证：先跑一次旧平铺 dump 产物喂新脚本应报缺文件（red），
      再跑新布局 dump 全绿（green）——证明读路径确实换干净

## 3. 三端 dump 分层输出

- [ ] 3.1 `core/scripts/dump.rs`：输入改 `oracle/samples/dut.<case>`，
      输出 `oracle/tmp/core/<sample>/<field>.bin` 与 `core/freq.bin`
- [ ] 3.2 `python/scripts/dump.py`：同 3.1（python 端）
- [ ] 3.3 `typescript/scripts/dump.mjs`：同 3.1（node + wasm 两段）
- [ ] 3.4 本地跑 `pnpm check:cross` 全绿（横向轴 PASS + 自检 PASS）

## 4. 管线与 CI 同步

- [ ] 4.1 根 `package.json` `check:cross`：四端 dump →
      `python3 oracle/compare_cross.py oracle/tmp` → 词表检查
      （check_vocab_types/check_verbs 不变）；`typescript/package.json` 的
      `cross-dump` 脚本路径同步（`../.cross-tmp` → `../oracle/tmp`）
- [ ] 4.2 `.github/workflows/ci.yml`：node job 内 `pnpm check:cross` 相关
      注释与路径同步（无新增步骤；确认无残留 testdata/cross_compare 引用）
- [ ] 4.3 `python3 scripts/check_ci.py` 通过（闸门完整性）

## 5. core 测试注释修正（仅注释，零行为）

- [ ] 5.1 `core/tests/` 中 "from testdata/manifest.json" 类注释改为自述
      常量措辞（"test-local tolerance; cross-end grading tolerances live in
      oracle/manifest.json"），涉及 touchstone_domain.rs、touchstone_write.rs、
      frequency_functional.rs、frequency_unit.rs、constants.rs

## 6. 文档同步（波及面改全）

- [ ] 6.1 `scripts/README.md`：删 cross_compare 条目，注明阅卷迁
      `oracle/compare_cross.py`；其余脚本条目不动
- [ ] 6.2 `CONTRIBUTING.md`：目录 layout 图 `testdata/` → `oracle/`；
      cross-binding 段路径与脚本名同步
- [ ] 6.3 `core/README.md`、`python/README.md`、`typescript/README.md`：
      dump 命令路径（`oracle/samples/`、`oracle/tmp/<end>/`）同步；根
      `README.md` 许可段链接 `testdata/LICENSE-NOTES.md` →
      `oracle/LICENSE-NOTES.md`
- [ ] 6.4 `scripts/check_md.py` LEDGER SECTION：台账清单中
      `testdata/README.md` → `oracle/README.md`（否则迁移后台账检查失效）
- [ ] 6.5 `Plan/测试规划.md` 改写：golden 层新契约（golden 不入库、CI
      现算、skrf 版本靠 oracle/uv.lock、周更作废）、阅卷集中（三端 runner
      表作废）、`oracle/tmp/` 分层布局、卷首语与全文 testdata 链接改
      oracle；新增下期任务清单（oracle uv 环境 + skrf 钉版、gen_golden.py、
      compare_golden.py 含扰动自检、manifest v1 =cases[]/sha256/删
      python_relative、17 样本入库+许可登记、scripts 其余脚本归属后议）
- [ ] 6.6 `pnpm check:md` 退出码 0（markdownlint + prettier + 链接校验）

## 7. 全量验收

- [ ] 7.1 `pnpm check` 全绿（md/ts/rs/py/meta；check_license 与
      check_vocab* 若含 testdata 路径假设，当场修正）
- [ ] 7.2 `pnpm check:cross` 全绿（横向轴 + 自检，linux 本地）
- [ ] 7.3 `grep -rn "testdata\|cross_compare\|compare_native\|\.cross-tmp"
      --include="*"` 除 openspec/changes/archive 与 git log 外零残留
      （design.md D4 命名决策段引用旧名作历史对照除外）；删除仓库根
      `.cross-tmp/` 旧产物目录
