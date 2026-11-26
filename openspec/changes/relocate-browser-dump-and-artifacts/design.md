# Design

## 背景约束

- 铁律八：wasm 只活在常驻 worker，浏览器路径验收 MUST 真浏览器（node 模拟不算）。
- 已定裁决见 proposal `## 已定裁决` 段（单包发布、产物源头、dump拆分、真harness、
  端名、答卷、merge_browser、一个change）。

## harness 架构（browser/scripts/dump.mjs）

独立一次性脚本（非测试套件），`node browser/scripts/dump.mjs <out_dir>`，流程：

1. **静态服务器**：node `http` 起临时端口，挂两棵树——`browser/dist/`（壳、worker、
   `wasm/` glue+二进制、values 生成物）与 `oracle/samples/`（样本，路径前缀
   `/samples/`）。仅监听 127.0.0.1，进程退出即关。
2. **页面**：playwright chromium（headless）打开挂壳页面的最小 HTML，import
   `index.browser.mjs` 真壳（主线程零 wasm，计算走常驻 worker——与生产同路径）。
3. **λ↔f 轴**：壳 API `Frequency.fromF → wavelength → fromWavelength → f`，
   结果经 `page.evaluate` 回传 node，写 `<out>/browser/freq.bin`。
4. **Touchstone**：node 读样本字节 → `page.evaluate` 内构造 `File` →
   `Touchstone.fromFile`（真文件入口，覆盖浏览器 I/O 路径）→ 经壳 getter
   `ts.s`/`ts.z0`/`ts.version()` 取交错 f64 主数据、z0、版本串，经
   `page.evaluate` 回传 node 落盘 `<out>/browser/<sample>/{s.bin,z0.bin,version.txt}`。
   取数走 getter（历来 dump 正解），MUST NOT 依赖尚未落地的 `to_file`/`writeFile`
   文本导出路径——dump 要的是核心主数据，非渲染文本。
5. **取数回传**：结构化字段经 `page.evaluate` 直接回传 node 落盘。1.1 spike 已实证
   "静态服务器 + 真壳 + File 上传 + anchor 下载 saveAs"通路可用（结论留 tasks 1.1
   打勾），但 dump 取字段用 getter，不走 anchor 下载；`to_file` 落地属另一条延后线。

## 端名改名面（wasm → browser）

- `oracle/compare_cross.py`：`ENDS` 元组、`compare()` 的容差分支键、print 文案、
  扰动自检列表。
- `oracle/manifest.json`：note 措辞（键名 `core_tol.relative` 不动）。
- `oracle/README.md`、`scripts/README.md`、各包 README 的端名散文。
- **不动**：`wasm32-unknown-unknown`、`wasm-pack`、`wasm-bindgen`、
  `browser/dist/wasm/` 目录名、ci-matrix「wasm 覆盖率链」requirement 名（真技术
  语义）、lessons-learned 账本。

## 消费方改路径清单（typescript/dist → browser/dist）

| 文件                             | 现读                                                                               | 改读                                                                        |
| -------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `scripts/run/test_cross.sh` 探针 | `typescript/dist/wasm/netwave_browser_bg.wasm`                                     | `browser/dist/wasm/netwave_browser_bg.wasm`（提示 `pnpm -C browser build`） |
| `scripts/check_verbs.py`         | `typescript/dist/index.browser.d.mts`、`typescript/dist/wasm/netwave_browser.d.ts` | `browser/dist/` 同名                                                        |
| `scripts/check_vocab_types.py`   | browser 端 dts（typescript/dist）                                                  | `browser/dist/values.generated.d.mts` 等                                    |
| dump browser 段                  | `../dist/netwave.worker.js`（伪造 worker）                                         | 整体重写为 harness，读 `browser/dist/`                                      |

## 回滚单元

三段独立可回滚：(a) dump 拆分+harness；(b) 消费方路径改指；(c) oracle 端名改名。
(b)(c) 纯字符串/路径改动，(a) 是唯一新逻辑。

## 测试与验证

- harness 产物与旧 dump 在容差内一致：`pnpm test:cross` 全绿即证（compare_cross
  横向轴兜底）。
- wiring 镜像测试（`scripts/tests/`）随 test_cross.sh 命令变化同步断言。
- CI node job 增 `playwright install --only-shell chromium` 步骤（本地
  `browser/scripts/test.sh` 已有同款探测可参照）。
