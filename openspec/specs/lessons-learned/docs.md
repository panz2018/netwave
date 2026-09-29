# LL ledger — scope: docs

## Entries

### LL-005 命令先验证存在

- 犯过：建议不存在的 `openspec validate` 子命令（session 两次追问）
- 规则：让用户/文档引用的命令先自己跑或引 `--help`
- 复发检测：review 抽查文档命令可执行

### LL-006 输出写绝对路径

- 犯过：dump 脚本只 print "dumped bin" 无位置（`5645e11` 修）
- 规则：写文件的脚本输出含完整文件路径
- 复发检测：可门禁化——脚本输出断言测试

### LL-008 改事实后 grep 全仓旧副本

- 犯过：两次全仓扫旧描述（`409b057`/`4f5a9bd` 修四处事实错误）
- 规则：改命令/改名/工具链事实后 grep 全 `.md` 更新每处；工具链状态变化
  同改动更新表格
- 复发检测：review Standards 轴要求 diff 覆盖所有旧引用点

### LL-010 读非 ASCII 文件显式 utf-8

- 犯过：Windows cp1252 读含中文 manifest 抛 `UnicodeDecodeError`（`89e28f2`）
- 规则：所有 `read_text()`/`open()` 显式 `encoding="utf-8"`
- 复发检测：可门禁化——grep `read_text()`/`open(` 无 encoding 即红

### LL-028 sync 后 archive 会重复追加 delta

- 犯过：手动 sync 后再跑 `openspec archive`，CLI 二次应用 delta，
  governance spec 出现重复需求块（MD024 红，2026-09-27）
- 规则：sync 与 archive 只选其一应用 delta；archive 自带 sync，手动
  sync 过则归档后必须 diff 主 spec 去重
- 复发检测：可门禁化——`pnpm check:md` MD024 重复标题即红（已生效）

### LL-029 第三方许可表与 GPL 红线

- 犯过：无（预防性登记，2026-09-27 license-compliance）
- 规则：参考第三方前先查本表——scikit-rf BSD-3-Clause
  (<https://github.com/scikit-rf/scikit-rf>) 可抄代码但声明随分发；
  SignalIntegrity GPL-3.0-or-later
  (<https://github.com/Nubis-Communications/SignalIntegrity>) **禁抄代码/
  禁逐行翻译，只读思想**；Touchstone spec v2.1 IBIS 条款
  (<https://ibis.org/touchstone_ver2.1/touchstone_ver2_1.pdf>) 实现自由、
  全文勿入仓；《S-Parameters for Signal Integrity》CUP 全版权
  (<https://doi.org/10.1017/9781108784863>) 禁复制原文/图表。借鉴实现
  MUST 在 rustdoc 标注出处
- 复发检测：元数据一致性已门禁化 `pnpm check:meta`；GPL 混入检测待立项；
  review Lessons 轴对照本表

### LL-032 持久文档禁写临时名称

- 犯过：spec/账本/Plan 写入"方案一""阶段 0/3/6"等讨论代号，代号随时改名导致
  引用漂移（2026-09-29 人工纠正，规则入 AGENTS.md 文档书写规范）
- 规则：持久文档用内容命名（如"worker 常驻架构"），需时点附定案日期；引用结论
  用标题跳转链接不用代号
- 复发检测：可门禁化——`check_md.py` grep "方案[一二三]/阶段 [0-9]" 于
  openspec/specs/ 即红；review Standards 轴对照
