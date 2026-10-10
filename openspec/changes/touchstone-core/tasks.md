# Tasks

## 1. core：类型与错误（先红后绿）

- [ ] 1.1 红：`core/tests/touchstone_types.rs`——钉 `TouchstoneParameter`
      成员恰 S/Y/Z/G/H、`TouchstoneFormat` 恰 RI/MA/DB、`TouchstoneError`
      Display 含 offending 原文
- [ ] 1.2 绿：`core/src/touchstone.rs` 定义两 enum（穷尽 `multiplier` 式
      穷尽匹配 + `FromStr` 大小写不敏感）+ `TouchstoneError`（thiserror）；
      `cargo test -p netwave` 绿

## 2. core：解析管线

- [ ] 2.1 红：`core/tests/touchstone_parse.rs`——`#` 行单位/域/格式/R
      归一（1.0 标量、1.1 每端口）、大小写混读、非法 token 报错含原文、
      z0 长度非 1/nports 报错
- [ ] 2.2 绿：`parse_option_line` + `parse_data_line`（RI/MA/DB 三分支，
      角度恒度、dB=20log₁₀）
- [ ] 2.3 红：频率轴测试——乱序排序入库、重复频点报错含频点值、
      token 总数不满足 stride = 1+2n² 整除时报错含实际数与期望 stride、
      噪声行（每行 5 项）混入 2 端口文件即报错（不静默吞）
- [ ] 2.4 绿：token 流 stride 切频点 + `sort_and_check_f`（无噪声识别逻辑）
- [ ] 2.5 红：`from_text` 端到端——nports 优先级（显式 > filename 文法抠 >
      报错）、path 含目录时目录忽略 stem 存 `name`、`nportsFromFilename` 无匹配
      报错、`filenameFromPath` 路径/URL 抠 filename、`nameFromFilename("2026.10.09")`
      整段不剥、`# GHZ Z` 文本命名 `.s2p` 时 `parameter`="Z"（域字母不作准）
- [ ] 2.6 绿：`parse_text` 主循环 + 公开静态流水线三件套 `filename_from_path`/
      `name_from_filename`/`nports_from_filename`（文法 `\.[ghsyz]\d+p`）；Y/Z/G/H
      文件解析即 `convert_to_s` 入 S（对拍 skrf golden，容差 manifest `core_tol`）

## 3. core：数据面与换算

- [ ] 3.1 红：域换算测试——`s_to_domain` Z/Y/G/H 对 skrf golden
      （`core_tol`）；G/H 非 2 端口报错；MA/DB 闭式反变换
      （`mag = 10^(db/20)`、deg 恒度）
- [ ] 3.2 绿：`s_to_domain` / `to_ma` / `to_db`（全私有）
- [ ] 3.3 红：`data(parameter, format)` 20 组合形状测试——RI 同形、
      MA/DB +2 维实数对；默认 `(S,RI)` 返回 `s` 本体（同指针/同 base）
- [ ] 3.4 绿：`data` 访问器 + 快捷属性 `s`/`z`/`y`/`g`/`h`/`f`/`z0`/
      `nports`/`name`/`comments`/`version`/`parameter`
- [ ] 3.5 红：纯数据构造器测试——`new(f, data, z0, parameter)` 校验
      （维度自洽、z0 形状、parameter 必填、G/H 端口数）、version 由 z0 推导
- [ ] 3.6 绿：数据构造器 + `convert_to_s` 共用路径

## 4. core：写出与文件名

- [ ] 4.1 红：`write_path(path?)` 四形态测试——空→`name.{P}Np`、目录→
      目录+`name.{P}Np`、目录+名→补扩展名、错扩展名→剥除重拼真实域字母与
      nports（2 端口 Z 对象传 `.s3p`→`z2p` 文件）、原生端目录末段 `is_dir()`
      实测拼默认名
- [ ] 4.2 绿：`write_path` 私有函数（扩展名恒 `.{parameter}{nports}p`）
- [ ] 4.3 红：`write_touchstone(parameter, format)` roundtrip 测试——
      写出→`from_text` 读回 `s` 逐 bit、元数据一致；`format_number`
      shortest-roundtrip（含 0、负数、极值）
- [ ] 4.4 绿：`format_number`（选型：ryu vs `{:?}` 实测取往返 bit 一致者）
  - `render_text`（`#` 行用存储的 version 字段，写出不重推）
- [ ] 4.5 红：原生 `write_file` 测试——tempdir 落盘、path 三形态、
      落盘名经 `write_path` 纠正
- [ ] 4.6 绿：`write_file`（cfg native，std::fs）

## 5. core：from_url（原生）

- [ ] 5.1 加依赖：reqwest(rustls)+tokio，cfg 门控 native feature；
      `cargo tree` 断言 wasm target 零 reqwest
- [ ] 5.2 红：`from_url` 单测（本地 httpmock/127.0.0.1 测试服务器）——
      成功解析、HTTP 错误原样抛
- [ ] 5.3 绿：core 内 cfg 分后端 fetch（native=reqwest；browser=
      `web_sys::fetch`+`wasm_bindgen_futures` 编译面验证）

## 6. Python 绑定

- [ ] 6.1 红：`python/tests/test_touchstone_class.py`——三工厂+构造器+
      属性面+`data()` 形状（ndarray 多维）+错误映射（ValueError 含原文）
- [ ] 6.2 绿：`#[pyclass] Touchstone` + rust-numpy `Array3`/`Array4`
      零拷贝（照 Frequency frozen-owner 模式）；`from_file`/`write_file`
      同步 + `allow_threads`；`from_url` 同步 + 放 GIL
- [ ] 6.3 `python/scripts/dump.py` 与 `.pyi` 更新；pytest 全绿 +
      覆盖率 100%

## 7. node 绑定

- [ ] 7.1 红：`typescript/test/native/touchstone.test.ts`——三工厂+
      构造器+`data()` `{values, shape}`+扁平索引公式抽查+错误映射
- [ ] 7.2 绿：napi class；`from_file`/`write_file`/`from_url` AsyncTask
      （async 签名）；`--dts`/`--no-const-enum` 旗标照既有
- [ ] 7.3 vitest native 全绿 + 覆盖率 100%

## 8. 浏览器绑定（worker + 壳）

- [ ] 8.1 红：`typescript/test/wasm/touchstone.test.ts`——`"touchstone"`
      命名空间工厂路由、实例方法经 handle、`fromFile(file)` transfer 后
      buffer detached、`writeFile` 返回下载触发（fake anchor 断言
      `download` 属性名经 `write_path` 纠正）、`fromUrl` Promise
- [ ] 8.2 绿：`touchstone::register()` + `impl Resource` match；壳
      `index.browser.ts` 加 `Touchstone` 类（handle 壳 + async 胶：
      `fromFile` arrayBuffer→transfer、`writeFile` 收 `{text, filename}`→
      Blob+`<a download>`）
- [ ] 8.3 真浏览器跑通（vitest browser config；LD_LIBRARY_PATH 照账本）
  - 覆盖率 100%

## 9. 跨端对拍与闸门

- [ ] 9.1 `scripts/cross_compare.py` 扩 Touchstone 用例：同一 .s1p/.s2p/
      .s4p（含 1.1 多 z0、乱序、MA/DB）三端读→`s`/`z0`/`version` 哈希比对
      （容差 manifest `core_tol`）
- [ ] 9.2 `scripts/check_verbs.py` 动词名单扩 Touchstone 面（三端生成物
      动词集合相等）
- [ ] 9.3 `pnpm check` 全绿；llvm-cov 全 workspace 行覆盖 100% 底线闸门绿
      （绑定 lib.rs 沿用既有 ignore 正则）

## 10. 文档与销账

- [ ] 10.1 `core/src/touchstone.rs` rustdoc / Python docstring / TS JSDoc
      达教学式标准（governance 元规则）：公开面自包含、注释只写当前契约事实
- [ ] 10.2 `Plan/功能覆盖规划.md` 噪声行表述修正 + "功能覆盖非 API 同名"
      口径；`Plan/总体计划.md` I/O 待决条目销账
- [ ] 10.3 `Plan/Touchstone核心API规划.md` 已定案章节删除（Plan 瘦身），
      `pnpm check:md` 绿
