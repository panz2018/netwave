# Design

## Context

版本域现状（apply 前）：`scripts/versions/check_versions.py` 是离线四律闸门
（`lib/rules.py` 判定、`lib/repository.py` 按发现扫 manifest、`lib/version.py`
版本比较单一来源），接进 `pnpm check:meta`；`scripts/versions/check_outdated.py`
是联网体检（`lib/latest.py` 探针），docstring 与 spec 均写明"退出码恒为 0"。
坏版本机制只存在于 spec 条款与 `Plan/软件升级.md`，无数据文件、无消费代码。

lockfile 可解析性已核实：`pnpm-lock.yaml`（lockfileVersion 9.0）包键形如
`tsdown@0.23.0`；`Cargo.lock` 与 `uv.lock` 均为 `[[package]] name/version` 表，
`tomllib` 原生可读，仓库无 PyYAML 依赖，故不引入 YAML 解析库。

动机见 proposal.md - Why；行为契约见 specs/dependency-upgrade/spec.md。

## Goals / Non-Goals

**Goals:**

- 一份数据文件承载全部坏版本事实，单包 bug 与多包联动同构表达。
- 判定逻辑与网络调用分离，使判定可在离线单测中 100% 覆盖（铁律七）。
- 体检 target 自动跳过已登记组合，人不记也能避开已知坑。
- 错误一律可见：格式错抛异常、网络错非零退出，取消"恒为 0"。

**Non-Goals:**

- 不把记录接进 `pnpm check` / CI（正确性归下游构建与测试）。
- 不做自动重试、不自动开 issue/PR（属 `add-freshness-schedule-gate`）。
- 不改四律实现、不改 `check_versions.py`。

## Decisions

### D1 记录结构：原因分组 + 组合清单

```json
{
  "restrictions": [
    {
      "reason": "tsdown dts 管线与 TS7 初版不兼容",
      "combos": [{ "npm:typescript": "7.0.0", "npm:tsdown": "0.23.0" }]
    }
  ]
}
```

理由：`reason` 在外层，同原因的多个实测失败组合共用一句说明，不重复；
`combos` 每项是"包名 → 具体版本"的映射，包数天然可变（1~N），无需为单包/多包
分两种结构。

备选：每包一个版本数组（`{"typescript": ["7.0.0"], "tsdown": ["0.23.0","0.23.1"]}`）
——被否，数组交叉相乘会把未实测组合说成坏的；`members` + 并列 `versions` 两数组
——被否，靠位置对齐的两份数据必漂移（LL-076）。

### D2 命中判定：全等匹配，不做交叉

组合命中 = 当前锁定版本**同时等于**组合内每个包的版本。同一记录内多条组合之间
是"或"，组合内各包之间是"且"。因此 `TS 7.0.0 × tsdown 0.23.1` 在只登记了
`7.0.0×0.23.0` 与 `7.0.1×0.23.1` 时判为放行。此语义是单测重点（见 proposal
专家增补）。

### D3 包名带生态前缀，按前缀定位 lockfile

`npm:` → `pnpm-lock.yaml`（正则 `^  <name>@<version>:` 提取，避开 YAML 依赖）；
`cargo:` → `Cargo.lock`（`tomllib` 读 `[[package]]`）；`pypi:` → 各 `uv.lock`
（复用 `lib/latest.py` 的 `find_uv_projects()` 发现思路，按 `uv.lock` 存在即覆盖）。

理由：`numpy` 同时是 PyPI 包与 Rust crate 名，`netwave` 同时是 npm 包与 Python
模块名，无前缀无法区分，且消歧逻辑比前缀更贵。备选"全仓找同名、多命中报错"
——被否，把已知会撞名的情况留给运行时翻车。

### D4 新模块 `lib/restrictions.py`：纯函数、不联网

对外三个能力：`load_restrictions(root)`（读文件、校验契约、抛异常）、
`is_restricted(combo, restrictions)`（D2 判定）、
`pick_unrestricted(package, candidates, peers, restrictions)`
（按候选版本从高到低返回首个未命中组合，方向不预设——最新稳定版未命中就直接返回它）。

理由：`check:py` 的覆盖率口径是 `--cov=scripts/versions` 且
`--cov-fail-under=100`，联网代码难以全覆盖，故网络留在 `check_outdated.py`，
判定与文件读取做成纯函数。备选"逻辑直接写进 `check_outdated.py`"——被否，
该文件是脚本 facade，现有风格是判定归 `lib/`。

### D5 错误语义分三类

| 情况                 | 行为                                                       |
| -------------------- | ---------------------------------------------------------- |
| 文件不存在           | 视为无记录，正常继续                                       |
| 文件存在但不合契约   | `raise`（自定义 `RestrictionFormatError`），traceback 可见 |
| 记录引用的包不在仓库 | 跳过该条判定，记录保留                                     |

同时删除 `check_outdated.py` 的"退出码恒为 0"：网络类失败照常报告该段失败，
其余段继续跑完（保住"一条命令看全貌"），末尾以非零退出码结束。
理由：连不上外网不是仓库的 bug，数据文件写坏了是——后果不同处理就该不同；
两类错误都必须让人看见。

### D6 收紧范围只抬下界

`^0.23.0` → `^0.23.2`（npm）、`"0.29"` → `"0.29.1"`（cargo 同理），沿用原写法
只改下界数字；caret 自带的同 major 上界是既有惯例，不删也不新加。写成
`>=0.23.2` 会放开未测的大版本，属"新增未实测的放行面"，spec 已用 MUST NOT 拦住。

## Risks / Trade-offs

- [记录不进闸门，漏登记无人拦] → 下游构建/测试必然踩到并失败，失败当轮即登记；
  本机制定位是"少踩一次已知坑"的加速器，不是正确性防线，接受此权衡。
- [记录只增不删，文件随时间变长] → 记录是实测事实的追加流水，体积增长缓慢；
  换来的是"回退进旧区间时不必重测"，且历史可追溯靠 git log 不靠删除。
- [取消恒零退出后，`check:outdated` 可能因网络抖动"红"] → 该命令本就 MUST NOT 进
  CI（spec 已定），只影响人工体检时的可读退出码；`scripts/check_ci.py` 若对其
  有断言需同步核对。
- [正则解析 `pnpm-lock.yaml` 而非 YAML 解析] → lockfile 第 9 版（`lockfileVersion`
  为 `9.0`）的包键格式稳定（`name@version:`），且避免为一个脚本引入 PyYAML；
  若上游改 lockfile 格式，解析失败会抛错而非静默，符合 D5。
- [组合语义要求"同因合并"，人工登记可能拆错原因] → review Standards 轴检查；
  拆错只造成可读性下降，不影响判定正确性。

## Migration Plan

1. 落地 `lib/restrictions.py` + 单测（TDD 先 red），`check_outdated.py` 接消费
   与退出码改造，`scripts/versions/README.md` 补登记方法。
2. 实测 typescript 7.0.0 × tsdown 各候选版本（`pnpm -C typescript build:shells`），
   把失败组合登记进新建的 `restrictions.json`，同轮收紧
   `typescript/package.json` 的 `tsdown` 范围并刷新 `pnpm-lock.yaml`。
3. 文档同步：`Plan/软件升级.md` 删除「blocked 落地」「pairs JSON 化」两节，
   「过期检查门禁化」节内 blocked 措辞改指 restrictions；spec 随归档更新。
4. 验证：`pnpm check` 全绿、`pnpm check:md` 绿、`pnpm check:outdated` 人工跑一次
   确认跳过行为与退出码语义。
5. 回滚 = `git revert`（数据文件与消费代码同笔，无外部状态）。
