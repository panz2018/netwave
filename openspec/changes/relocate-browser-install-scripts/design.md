# Design

## 搬迁的唯一隐藏坑：workspace 根 lockfile 相对路径

`install_wasm_bindgen_cli.sh` 靠脚本自身位置反推 workspace 根 `Cargo.lock`，读取
`wasm-bindgen` crate 版本以对齐要安装的 CLI 版本（glue 与 crate 版本必须一致，
否则运行时 abort）。当前实现：

```bash
version=$(sed -n '/^name = "wasm-bindgen"$/{n;s/^version = "\([^"]*\)".*/\1/p;}' \
  "$(dirname "$0")/../Cargo.lock" | head -1)
```

脚本在 `scripts/` 时 `$(dirname "$0")/..` = 仓库根，正确。搬到 `browser/scripts/`
后同一表达式 = `browser/`（无 Cargo.lock，workspace 单 lock 在根），版本读空 →
脚本以「could not read wasm-bindgen version」非零退出 → CI browser job 挂。

修法：搬迁同批把 `../Cargo.lock` 改为 `../../Cargo.lock`。验证：搬后直接跑该脚本
（或加一行 echo 版本）确认解析出的版本非空。

`install_wasi_sdk.sh` 无相对路径假设（装到 `~/.local/opt/wasi-sdk`，只认 GitHub
API），搬后自身零改动。

## 引用面清单（搬迁同批必改）

| 文件                               | 位置             | 改动                                          |
| ---------------------------------- | ---------------- | --------------------------------------------- |
| `browser/scripts/test.sh`          | L66/L70          | 探测提示命令路径加 `browser/` 前缀            |
| `.github/workflows/ci.yml`         | L161/L162        | 安装步命令加 `browser/` 前缀（checkout 在根） |
| `scripts/README.md`                | L18/L19          | 删两脚本表格行（说明迁 `browser/README.md`）  |
| `openspec/specs/ci-matrix/spec.md` | 三处 requirement | 经 delta 更新路径字符串                       |

实证不受影响：`scripts/tests/test_test_browser_wiring.py` L116-117 用文件名正则
（不带路径前缀），探测提示改新路径后断言仍命中。

## 提交粒度

- 第一笔：T1 typescript wasm 残留清理（`typescript/.gitignore` 删两条死规则；
  本地 `rm -rf typescript/target-wasm{,-cov}` 不进 git）。与其余文件零重叠。
- 第二笔：T2+T3 两脚本搬迁 + 引用面同步 + `browser/README.md` 新建。两者波及
  ci.yml 同一 run 块、README 相邻两行、spec 同批串，拆两笔会产生半搬中间态。
