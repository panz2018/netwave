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
