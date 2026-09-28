# LL ledger — scope: testdata

## Entries

### LL-018 golden 只由 gen_golden.py 再生

- 犯过：无（预防性，铁律四落地）
- 规则：禁手改 `golden/*.bin`；改数据走 `gen_golden.py` 再生 + review diff；
  容差不硬编码，从 `manifest.json` 读（铁律三）
- 复发检测：可门禁化——CI 校验 golden 由脚本再生（diff 守护）

### LL-027 dump 用二进制 .bin（小端 f64）

- 犯过：`JSON.stringify(-0)` 输出 `"0"` 丢符号位，bit 级对拍失效
- 规则：四端 dump 一律二进制 `.bin` 小端 f64；契约见 testdata/README
- 复发检测：`pnpm check:cross` bit 级比较原生端
