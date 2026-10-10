# Design

## 架构总览

`Touchstone` 是 core 新模块 `core/src/touchstone.rs`：状态类（持
`Frequency` + 交错 f64 S + 每端口 z0 + 元数据），解析/换算/渲染全为类私有
函数。三端绑定按既有形态接入：Python `#[pyclass]`、node napi class、浏览器
经 `"touchstone"` 命名空间 handle 走常驻 worker（复用既有 handle/method/args
泛化分发模板，worker JS 零改动——api-contract 既定机制）。

## 核心数据结构

```text
struct Touchstone {
    frequency: Frequency,          // 频率轴唯一权威（Hz，递增）
    s: Vec<f64>,                 // 交错 re/im 扁平（铁律一）
    z0: Vec<f64>,               // 每端口实数（规范禁复数）
    nports: u32,                // 冗余自 z0 长度，热路径免间接
    name: Option<String>,
    comments: String,
    version: String,            // "1.0"/"1.1"；与公开面同型，未来 2.0/2.1 扩值不改类型
    parameter: TouchstoneParameter,
}
```

enum `TouchstoneParameter`{S,Y,Z,G,H} / `TouchstoneFormat`{RI,MA,DB} /
`TouchstoneError`（thiserror）同文件定义，绑定宏反射三端。

## 解析管线（fromText 主干，fromFile/fromUrl 只换取字节方式）

1. 逐行扫描：`!` 收集进 comments；`#` 进 `parse_option_line`（单位/域/格式/
   R 归一 z0，大小写归一）；其余数字 token 拼成连续流（行只是排版，
   v1.0/1.1 矩阵行可跨行，五源一致）。
2. token 流按 stride = `1 + 2×nports²` 切频点（同 SI `values_per_freq`、
   旧库 `countColumn`、skrf `numbers_per_line` 同法）；总数不整除 →
   `TouchstoneError`。噪声行（每行 5 项）混入必破坏整除性 → 自然报错，
   v1 无专门的噪声识别（与 SI/旧库同策）。
3. 每频点块进 `parse_data_line`（按 format 三分支换算复数）。
4. `sort_and_check_f`：排序 + 重复检测（重复→`TouchstoneError`；乱序与
   噪声拒收互不冲突：频点边界与 stride 有关、与频率序无关）。
5. `parameter != S` → `convert_to_s` 换算入库（唯一实现，构造器共用）。

名字流水线（三工厂共用）：`filenameFromPath(path)` → filename →
`nameFromFilename`/`nportsFromFilename`（文法 `\.[ghsyz]\d+p`，不匹配则
整段即 stem / nports 报错）。`filename` 一词全仓统一 = 含扩展名文件名，
`basename` 退役。nports 来源优先级：显式参数 > filename 文法抠 > 报错；
`path` 目录部分忽略，stem 存 `name`。读时扩展名域字母不作准
（`#` 行 parameter 为权威），写时 `write_path` 必拼 `.{P}Np`。

## 数据面

- `s`：零拷贝视图（Python ndarray borrow / node Buffer / wasm 线性内存
  offset 视图）。`z`/`y`/`g`/`h`：`s_to_domain` 现算（2 端口 G/H 闭式，
  非 2 端口报错）。
- `data(parameter?, format?)`：默认 `(S,RI)` 转发 `s`；MA/DB 走 `to_ma`/
  `to_db` 产 `(nfreq,nports,nports,2)`。JS 端返回 values（Float64Array）+
  shape 元数据对象（shape 与扁平索引公式进 JSDoc 与对拍测试）。

## 写出与文件名

- `writeTouchstone(parameter, format)`：`s_to_domain`（非 S）→ `to_ma`/
  `to_db`（按 format）→ `render_text`（`#` 行用存储的 version 字段——
  解析自文件记录，纯数据构造时由 z0 推导入库，写出时不重推；
  `format_number` shortest-roundtrip：Rust `ryu` 或 `{:?}` 语义实测选型，
  验收 = 往返逐 bit）。
- `write_path(path?)`（私有，snake_case 同其它 core 私有件；保持私有：
  属性收不了参数、藏 `is_dir()` 磁盘
  I/O，公开面 name/parameter/nports 已可自拼）：四形态见 spec；`path` 空取
  `name`；扩展名一律按文法剥除重拼 `.{P}Np`（P=真实 parameter、N=真实
  nports）；原生端目录歧义 `is_dir()` 实测。原生 `write_file` = `write_path` +
  `std::fs::write`；浏览器 worker 分发臂 `writeFile` 内部调 `write_touchstone` +
  `write_path` 返回 `{text, filename}`（浏览器无目录，filename 即下载文件名；字符串
  结构化克隆回主线程，壳 Blob+`<a download>`）。

## I/O 与异步边界

- 原生：`from_file` std::fs（大文件 memmap2 评估留实现期，铁律六）；
  `from_url` reqwest(rustls)。node 端两动词包 napi AsyncTask（async）；
  Python 端 `py.allow_threads` 包裹（同步签名放 GIL）。Rust 调用方同步。
- 浏览器：`fromFile(file: File)` 壳 `await file.arrayBuffer()` → transfer
  字节进 worker → core 解析；`fromUrl` core 内 cfg `web_sys::fetch` +
  `wasm_bindgen_futures`（Promise 直通壳）。
- Cargo features：`native-http = ["reqwest", "tokio"]` 门控 python/node
  crate；wasm crate 开 `browser` 走 fetch。浏览器产物零 reqwest（CI 依赖树
  断言）。

## 三端绑定

- Python：`#[pyclass] Touchstone`，构造器收 `Frequency` 对象 +
  ndarray/序列（`asarray().ravel()` 入口一行）+ float/ndarray z0；
  `data()` 返回 `Array3`/`Array4`（rust-numpy 零拷贝，照 Frequency 既有
  frozen-owner 模式）。
- node：napi class；`data()` 返回 `{values: Float64Array, shape}`。
- 浏览器：`touchstone::register()` 挂 `"touchstone"` 命名空间（工厂
  `fromText`/`fromUrl` + `filenameFromPath`/`nameFromFilename`/
  `nportsFromFilename` 经此路由，实例方法
  进 `impl Resource match`）；主线程壳
  持 handle，`writeFile`/`fromFile` 为壳专属 async 胶。TS 类型分端 .d.ts。

## 错误映射

`TouchstoneError`（thiserror）→ pyo3 `PyValueError`/napi `Error::new`/
wasm `JsValue::from_str`；消息含 offending 原文（行号/ token / 重复频点值）。

## 测试策略（TDD，red 先于 green）

- core 单测：解析各分支（option/data/stride 不整除报错/排序/重复）、域换算对
  skrf golden（manifest `core_tol`）、MA/DB 闭式反变换、write_path 四形态、
  roundtrip 逐 bit。
- 三端功能测试镜像（pytest / vitest native / vitest wasm+真浏览器）。
- 跨端对拍：`scripts/cross_compare.py` 扩 Touchstone 用例（同文件三端读
  → 哈希比对）。
- 覆盖率 100%（铁律七），不可达分支 `coverage(off)` 注理由。

## 选型记录（偏离说明）

- reqwest 偏离 ureq：要 async 与 napi AsyncTask 同构（已实测下载量对比，
  见规划文档 I/O 节）。
- `filename` 一词全仓统一 = 含扩展名文件名（对齐 pathlib `Path.name`
  语义，非 `stem`）；拼写出路径的私有方法叫 `write_path`（core 私有件
  全 snake_case，camelCase 只属 TS 公开面），与文件名区分。
- 浏览器 `writeFile` 动词存在于壳而非 wasm core：浏览器无文件系统，
  平台 I/O 胶是壳层职责（铁律十一允许），业务逻辑（渲染/命名）在 core。
