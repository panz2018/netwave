# Design

## Context

见 proposal.md - Why。补充执行层事实：

- 被删段 = 主 spec 铁律七第二自然段中"「`--codecov` 走 cargo-llvm-cov 自带的
  行合并器……恒差 6 行）"的机制解释与实测数字；同事实的完整版已在
  `openspec/specs/lessons-learned/core.md` LL-057（含 `--fail-under-lines`
  不读 codecov 的上游实证），故本 change 为**去重**而非搬家。
- 闸门行为不受影响：CI 与 `scripts/coverage_gate.py` 读 codecov.json 的
  命令、阈值、判定逻辑均不改。

## Decisions

- **契约与机制的切分线**：约束 CI/度量行为的句子留宪法（按 crate 归属度量、
  两条 MUST NOT、三个 Scenario 逐字保留）；解释"工具为什么这样计数"的
  原理与实测数字删（去向=LL-057，已存在）。判据：删后若读者需要知道
  "为什么禁用 report 路径"，顺指针进账本即可——宪法不需要自证。
- **指针形态**：宪法正文写"只存账本 LL-057"（行内代码编号），不用文件链接
  ——账本分片文件名可能重排（scope 拆分史），LL 编号才是稳定标识；
  与铁律七既有写法（LL-020 同款）一致。
- **变更通道**：走完整 change（proposal + delta + tasks → sync → archive），
  不裸改主 spec——宪法正文从不裸改的通道先例（`add-dependency-upgrade-spec`
  等），即使契约语义不变。
- **新增 Scenario「工具机制解释不入宪法」**：把本次归位动作升格为可复查的
  契约，防未来再往铁律塞工具原理；review Standards 轴可对照。

## Risks / Trade-offs

- 风险：读者在宪法处想知道"为什么"时多一跳。接受——分层本就是"宪法薄、
  账本厚"的设计意图。
- 锚点稳定性：delta 内引用账本标题锚点会随归档路径变化断链（check_md.py
  实测 change 子目录相对路径易错），故 delta 与主 spec 均用 LL 编号行内
  代码而非链接。
