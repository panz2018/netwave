# Lessons-learned index

一行一条：`LL 编号 | scope | 一句话规则`。动手前扫此表；命中再打开对应
scope 分片。条目格式四要素：编号 / scope / 犯过证据 / 规则+复发检测。
编号只增不复用。

| LL     | scope      | 规则                                                            |
| ------ | ---------- | --------------------------------------------------------------- |
| LL-001 | typescript | 计算全进常驻 worker（分流废止，浏览器 `_` 废、node 保留）       |
| LL-002 | core       | API 命名遵 api-contract（`f_scaled`），禁止自造同义词           |
| LL-003 | ci         | 禁止关闸门/跳平台求绿，修失败格本身                             |
| LL-004 | ci         | CI 改动先本地模拟每格，禁止 push-and-pray                       |
| LL-005 | docs       | 让人执行的命令先自己验证存在                                    |
| LL-006 | docs       | 脚本输出写绝对路径                                              |
| LL-007 | typescript | 测试/示例只用公共 API，禁 `_` escape hatch                      |
| LL-008 | docs       | 改命令/事实后 grep 全仓更新旧副本                               |
| LL-009 | ci         | 交互命令预先非交互化（corepack/llvm-cov）                       |
| LL-010 | docs       | 读非 ASCII 文件显式 `encoding="utf-8"`                          |
| LL-011 | ci         | Windows `GITHUB_PATH` 用原生路径且安装/使用分 step              |
| LL-012 | ci         | binaryen 整树安装（RUNPATH `$ORIGIN/../lib`）                   |
| LL-013 | ci         | release API 查询带 `GITHUB_TOKEN`；`env:` 含表达式用 block      |
| LL-014 | python     | pyo3 venv 三件套 `VIRTUAL_ENV`/`PYO3_PYTHON`/`LD_LIBRARY_PATH`  |
| LL-015 | core       | 交错复数布局与终态借用细节                                      |
| LL-016 | python     | 零拷贝 base-object 绑定与打包细节                               |
| LL-017 | typescript | napi/wasm 绑定实现细节与坑                                      |
| LL-018 | testdata   | golden 数据只由 `gen_golden.py` 再生，禁手改                    |
| LL-019 | core       | 触碰 core 后重建全部绑定再对拍                                  |
| LL-020 | core       | `#[coverage(off)]` 是 nightly-only，stable 禁用                 |
| LL-021 | core       | 真实基准必须 `black_box` 包裹输入输出                           |
| LL-022 | core       | core crate `publish = false`，版本随 workspace                  |
| LL-023 | python     | 改 core 后先 maturin develop；缓存异常全清重建                  |
| LL-024 | typescript | 改 core 后重建 node/wasm 再测试                                 |
| LL-025 | typescript | 覆盖率豁免 `v8 ignore` 逐条附理由                               |
| LL-026 | typescript | 容器 machine-id 须 32 位十六进制                                |
| LL-027 | testdata   | dump 一律二进制 .bin 小端 f64                                   |
| LL-028 | docs       | archive 自带 sync，手动 sync 后须去重                           |
| LL-029 | docs       | 第三方许可表：GPL 源禁抄代码，只读思想                          |
| LL-030 | typescript | 主线程不 init wasm，数据权威在常驻 worker                       |
| LL-031 | typescript | 元数据读取异步进 worker，描述符随结果便车回传                   |
| LL-032 | docs       | 持久文档禁写临时名称与无意义日期，只留最终结论，追溯靠 git log  |
| LL-033 | docs       | 决策编号不出决策文档，跨文件/代码引用用标题内容指引             |
| LL-034 | ci         | tsdown dts 需双 glue 先建：CI 先 build:wasm 再 build:native     |
| LL-035 | docs       | 对话镜像用户语言；文档仅 openspec/ 与 Plan/ 中文其余英文        |
| LL-036 | ci         | 改完 TS 必跑 typecheck，`pnpm check` 不含类型门禁               |
| LL-037 | ci         | 新增 test:* 必接进 CI，`check_ci.py` 已入门禁                   |
| LL-038 | docs       | 模糊指令只执行最小明确项，不可逆操作须显式确认                  |
| LL-039 | docs       | 注释只写当前契约事实，禁历史与路线图叙述                        |
| LL-040 | ci         | 合并只走 PR 禁直推 main；PR 用 git credential helper 建         |
| LL-041 | ci         | 钉版 toolchain 后组件要补装到激活工具链（rustup component add） |
| LL-042 | core       | 精确常量比较逐 bit ==，不引用 core_tol（容差只管计算结果）      |
| LL-043 | typescript | napi build 必带 --dts（.d.mts）+ --no-const-enum，否则类型假绿  |
| LL-044 | core       | clippy --workspace 特性统一：napi/wasm 属性须 not() 互斥门控    |
| LL-045 | docs       | 归档 mv 使目录加深，提交前跑全仓 check:md 修相对链接            |
| LL-046 | core       | 绑定宏 glue 计入 core 覆盖率，属性+导入须 not(coverage) 剥离    |
| LL-047 | ci         | 跨端一致性检查归构建各端产物的集成步骤，勿下沉单端测试段        |
