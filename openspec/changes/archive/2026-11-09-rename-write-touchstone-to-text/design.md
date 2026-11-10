# Design

## Context

动机见 `proposal.md` - Why。当前状态：core `Touchstone::write_touchstone`
（`core/src/touchstone.rs`）是文本渲染动词，被 python/node 绑定、浏览器 dispatch
臂、`scripts/check_verbs.py` 的 `TOUCHSTONE_VERBS` 集合与主 spec
`touchstone-core`「写出接口」Requirement 多处钉死。读侧 `from_text` 已存在且命名
正确，本刀不动。

约束：改名是纯机械替换，不改行为、签名、容差、列序；`write_file`/`writeFile`/
私有 `write_path` 不在本刀范围（Q1=B）。

## Goals / Non-Goals

**Goals:**

- `write_touchstone`→`to_text` 在 core + 三端绑定 + 测试 + typing + 闸门 + 主 spec
  全链路一致改名。
- 退役名 `writeTouchstone` 进 `FORBIDDEN` 防复活。

**Non-Goals:**

- 不改 `write_file`/`writeFile`/`write_path`（落盘动词留下刀）。
- 不新增 `to_bytes`/`encoding`（I/O 字节边界刀）。
- 不立「输出动词统一 `to_*`」spec 规矩（`writeFile` 仍在，立即违约）。

## Decisions

1. **改名而非新建**：`from_text` 已存在，写侧只需把 `write_touchstone` 更名
   `to_text`，签名 `(parameter, format)` 不变。备选「新建 `to_text` 保留旧名做别名」
   被否——违反铁律十二一名一义，且未发布期无需兼容层。
2. **范围只到文本动词（Q1=B）**：`write_file` 留下刀。代价是过渡态 `to_text` 与
   `write_file` 并存（Q6 已接受）；收益是每刀可独立验证回滚，符合最小增量。
3. **spec 与闸门同轮改（Q2）**：`check_verbs.py` 的 `TOUCHSTONE_VERBS` 与主 spec
   「写出接口」「2 端口列序」「名字流水线」三处 Requirement 内的 `writeTouchstone`
   同步改 `toText`，否则闸门红、spec 与代码矛盾（LL-034 波及面同步）。
4. **浏览器载荷不变（Q4）**：dispatch 臂 `"writeTouchstone"`→`"toText"`、壳方法
   `writeTouchstone`→`toText`，返回仍 `{text, filename}`。字节化 `{filename, bytes}`
   依赖 core `to_bytes`（不存在），混入会让纯改名刀变质。
5. **`to_text` 与 Display 并存（Q5）**：`to_text` = 完整文件渲染，`__str__`/
   `toString` = 摘要（`PROTOCOL_HOOKS` 豁免跨端相等），语义不同、都保留；`to_text`
   命名也避开与 `to_string` 撞名。
6. **`_netwave.pyi` 重生成不手改**：stub_gen 产物，改 `python/src/lib.rs` 后重跑
   生成器，避免手写漂移。
7. **退役名入 FORBIDDEN（Q9=A）**：`writeTouchstone` 进 `check_verbs.py`
   `FORBIDDEN`，沿用 `free`/`release` 惯例。`writeFile` 本轮未退役，不进。
8. **家族统一规矩延后（Q8）**：「输出动词 MUST `to_*`」写入 `Plan/测试规划.md`
   未来项，随 `to_bytes`/`to_file` 落地时立 spec——此刻 `writeFile` 仍在，立规即自
   相矛盾。

## Risks / Trade-offs

- [过渡态命名不一致：`to_text` 与 `write_file` 并存] → Q6 已接受；`Plan/测试规划.md`
  未来项标注消除路径，读者不会误判家族已改齐。
- [漏改某处旧名导致闸门红或 spec 矛盾] → 以 `grep -rn write_touchstone\|writeTouchstone`
  全仓核对（排除 `openspec/changes/archive/**` 与 skrf 自有名 `Plan/测试规划.md` L120）
  作为完成判据；`check_verbs.py` 是兜底绊线。
- [`_netwave.pyi` 忘记重生成] → tasks 列显式重生成步骤，pytest 收集时 stub 与实现
  不一致会暴露。

## Migration Plan

未发布期，无外部用户，BREAKING 豁免。回滚 = revert 本 change 提交。实施顺序：
core 改名 → 三端绑定 → 测试 → typing 重生成 → 闸门 → 主 spec → Plan，最后跑全闸门。

## Open Questions

（无——所有决策已在 grilling 阶段钉死。）
