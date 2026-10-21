# LL ledger — scope: oracle

## Entries

### LL-018 golden 只由 gen_golden.py 再生

- 犯过：无（预防性，铁律四落地）
- 规则：golden 不入库（CI 现算，只活在 `oracle/tmp/golden/`），数值只由
  `gen_golden.py` 再生，禁手改；skrf 版本靠 `oracle/uv.lock` 钉；容差不
  硬编码，从 `oracle/manifest.json` 读（铁律三）
- 复发检测：review 检查 golden 无提交进 git、阅卷脚本无字面量容差

### LL-027 dump 用二进制 .bin（小端 f64）

- 犯过：`JSON.stringify(-0)` 输出 `"0"` 丢符号位，bit 级对拍失效
- 规则：四端 dump 一律二进制 `.bin` 小端 f64；契约见
  `openspec/specs/oracle-harness/`
- 复发检测：`pnpm check:cross` bit 级比较原生端
