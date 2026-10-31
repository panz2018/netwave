# Design

## 决策记录（本 change 定案，出处为 grilling 会话逐轮裁决）

1. **路由单入口**：`openspec/specs/README.md` 承担全部 spec 路由；
   AGENTS.md 收敛为一句硬护栏指针（注入保证：AGENTS.md 每次对话自动注入，
   README 靠护栏句驱动去读，故指针必须留在注入层、路由正文才搬得进 README）。
2. **governance 不拆分、不做 INDEX**：665 行 27 条仍在一次可读范围；
   全仓 40+ 处引用其路径/锚点（archive 冻结不可改），拆分爆炸半径大于收益。
   膨胀由「规则生命周期」分片阈值（>1000 行或 >40 条）兜底。
3. **门禁不新建脚本**：SPECS ROUTER 并入 `scripts/check_md.py`（同型先例：
   LEDGER SECTION / ARCHIVE PATH 均为目录↔文档一致性核对），`pnpm check:md`
   口径不变。
4. **退役判据入 lessons-learned spec**：加入与退出同处一本账的契约，
   不散落；governance 侧「规则生命周期」只管铁律/元规则/能力 spec 层。
5. **spec 全量时效检查**落 `openspec/config.yaml` operations 钩子
   （apply/archive 扫 specs/ 出"更新/新增/退役"三态结论）；结构一致性归
   SPECS ROUTER 门禁，内容时效归 review Standards 轴。
6. **`Plan/账本退役审计.md` 整文件删除**：三类判据→spec、逐条表→本文件
   映射表、机制裁决→M1–M7 工件、暂缓门禁项→本文件"暂缓项"节——全文有
   去向，符合 Plan 生命周期（结论吸收后删除，追溯靠 git log）。
7. **计数修正史**（诚实留痕）：审计初判表曾报"32 可删"，逐条核对后
   修正——LL-020/LL-057 被 `ci-matrix` 指名"唯一正文见账本"、LL-042 被
   `frequency-class`/`frequency-unit` 指名（见账本），禁删；LL-037 经核
   `check_ci.py` 源码确认闸门已强制（枚举 `test:*` 未接 ci.yml 即红），
   补入退役。**终数：31 删 / 42 留**（总数 73，编号 001–073）。

## 首批退役映射表（31 条，逐条确认载体）

去向标签：`spec`=判据1 覆盖方为 spec；`gate`=判据2 门禁/编译器/固化脚本；
`agents`=AGENTS.md 常驻正文覆盖。每条删除时同步删 INDEX 行。

### A 组：spec 完整覆盖（16 条）

| LL | 覆盖方 | 覆盖证据（已核实的正文位置） |
| --- | --- | --- |
| LL-001 | zero-copy-roundtrip「异步与 Worker 边界契约」 | 全进 worker、`_toY` 仅 node、元数据便车逐条成文 |
| LL-002 | governance 铁律十/十二 + api-contract | 命名单源、禁自造同义词 |
| LL-007 | api-contract（`_` 逃生口管辖条款） | 测试/示例只用公共面成文 |
| LL-027 | oracle-harness（dump 布局 Requirement） | `.bin` 小端 f64、`<end>/<sample>/<field>.bin` |
| LL-030 | governance 铁律八 | 主线程 MUST NOT init wasm/持副本 |
| LL-031 | zero-copy-roundtrip | 元数据未持有结果时 MUST 异步进 worker |
| LL-035 | governance「文档语言约定唯一正文在本 spec」+ AGENTS.md 语言段 | 对话镜像 + 分目录语言均成文 |
| LL-039 | governance「代码只写使用信息」+ check_comments.py | 元规则正文 + 门禁双承载 |
| LL-049 | 铁律十二 + check_verbs.py `FORBIDDEN` | `free`/`release` 上浮即红 |
| LL-053 | touchstone-core（option line Requirement） | `#` 行缺失报错、缺省 MA 非 RI，含规范原文引文 |
| LL-055 | touchstone-core「2 端口列序」 | legacy 序、I/O 边界交换、往返 bit-exact 三 scenario |
| LL-056 | governance 铁律十四 | 覆盖率不得牺牲性能全文即此规则 |
| LL-060 | governance 铁律十一 | 壳 MUST NOT 含计算 |
| LL-067 | 元规则「最小规则原则」Scenario 新增规则先查重 | 逐字对应 |
| LL-068 | lessons-learned spec「可门禁化条目转 check 脚本」 | 该 Requirement 即此规则 |
| LL-071 | AGENTS.md「改动要有去向」+ 最小规则原则 | 去向纪律成文 |

### B 组：门禁/编译器/固化脚本承载（5 条）

| LL | 承载方 | 两步走证明（apply 时执行） |
| --- | --- | --- |
| LL-012 | `scripts/install_binaryen.sh` 整树布局已固化 | 脚本即执行者，冒烟 = CI wasm-opt 步骤现存 |
| LL-022 | `core/Cargo.toml` `publish = false` 配置事实 | 文件现存即证据 |
| LL-037 | `scripts/check_ci.py`（已核实源码：`test:*` 未接 ci.yml 即红） | 临时注释 ci.yml 一处 `test:` 调用跑出红，还原 |
| LL-043 | `typescript/package.json` build 脚本已带 `--dts --no-const-enum`；缺 dts 时 typecheck 假绿自曝 | 去旗标跑 typecheck 出 unused directive 红 |
| LL-063 | ci.yml `stub_gen` 步骤 LIBDIR 导出行已固化 | 现存行即执行者 |

### C 组：AGENTS.md 常驻正文覆盖（6 条）

LL-008（改动波及面必须改全）、LL-009（终端命令规范 COREPACK 标志）、
LL-038（硬护栏·动词=授权全集）、LL-058（三次即搜）、LL-059（机制断言
先实证）、LL-070（正文自述已转正入 AGENTS.md 硬护栏）。

### D 组：check:md 系门禁承载（4 条）

| LL | 门禁 |
| --- | --- |
| LL-028 | markdownlint MD024 重复标题即红（正文自述已生效） |
| LL-032 | check_md.py STAGE WORD / VERSION TAG |
| LL-033 | check_md.py DECISION TAG |
| LL-045 | check_md.py 解析 archive 内相对链接，断链即红 |

## 保留清单（42 条，不退役理由分组）

- **spec 钦定唯一正文，禁删**：LL-029（知识产权元规则指名）、LL-072
  （铁律一指名）、LL-020/LL-057（ci-matrix/铁律七指名）、LL-042
  （frequency-class/frequency-unit 指名）
- **行为纪律，无机器兜底**：LL-003/004/005/040/061/064
- **跨机器实现细节/口诀**：LL-015/016/017/044/046/050/051/052/062/019/024/023/014/041/054
- **workflow 口诀**：LL-028 已删，余 LL-065
- **待落门禁（暂缓项，见下）**：LL-018/021/025/034/036/047
- **跨机器环境事实（一次性误标纠正）**：LL-011/013/026/048/066/069
- **脚本编写口诀**：LL-006/010
- **流程默认步骤**：LL-073（config.yaml 已有正文，账本留事故证据与口诀）

## 暂缓项（本 change 不做，需要时另起 change，不留 Plan/ 待办）

LL-025（coverage_gate.py 增 v8 ignore 附理由校验）、LL-036（typecheck 进
`pnpm check`）、LL-018（golden 禁手改哈希校验）、LL-021（black_box lint）、
LL-034/LL-047（check_ci.py 扩步骤顺序/归属检查）。落地一条、按判据 2
两步走证明、退役一条。

## specs/README.md 结构草案

1. 一句话定位：本文件是 spec 唯一路由，AGENTS.md 硬护栏指向此处。
2. 宪法路由：改产品代码/API/CI→铁律段；改文档/流程/法务→元规则段（锚点链接）。
3. 账本路由：动手前扫 INDEX，命中开分片。
4. 能力 spec 表：13 个 capability 各一行——`spec 名 | 何时读`
   （如 touchstone-core：改解析/写出/端口语义时）。
5. 维护规则：新增/删除 spec 目录必须同 change 更新本表（SPECS ROUTER 门禁）。

## 风险与对策

- **README 过期成第二套漂移源**：SPECS ROUTER 门禁强制目录↔行双向一致；
  内容"何时读"措辞过期靠 review Standards 轴 + apply 钩子三态检查。
- **误删 spec 钦定正文**：映射表已逐条 grep `LL-[0-9]+` 全 spec 排除
  （020/029/042/057/072）；apply 时再跑一次同 grep 作终检。
- **注入链变长**：AGENTS.md 保留硬护栏句 + 宪法指针 + 账本指针
  （反思铁律段不动），README 只接走"能力 spec 路由"这段新职责。
