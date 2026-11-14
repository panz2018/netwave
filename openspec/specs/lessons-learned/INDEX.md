# Lessons-learned index

一行一条：`LL 编号 | scope | 一句话规则`。动手前扫此表；命中再打开对应
scope 分片。条目格式四要素：编号 / scope / 犯过证据 / 规则+复发检测。
编号只增不复用。

| LL     | scope      | 规则                                                                                               |
| ------ | ---------- | -------------------------------------------------------------------------------------------------- |
| LL-003 | ci         | 禁止关闸门/跳平台求绿，修失败格本身                                                                |
| LL-004 | ci         | CI 改动先本地模拟每格，禁止 push-and-pray                                                          |
| LL-005 | docs       | 让人执行的命令先自己验证存在                                                                       |
| LL-006 | docs       | 脚本输出写绝对路径                                                                                 |
| LL-010 | docs       | 读非 ASCII 文件显式 `encoding="utf-8"`                                                             |
| LL-011 | ci         | Windows `GITHUB_PATH` 用原生路径且安装/使用分 step                                                 |
| LL-013 | ci         | release API 查询带 `GITHUB_TOKEN`；`env:` 含表达式用 block                                         |
| LL-014 | python     | pyo3 venv 三件套 `VIRTUAL_ENV`/`PYO3_PYTHON`/`LD_LIBRARY_PATH`                                     |
| LL-015 | core       | 交错复数布局与终态借用细节                                                                         |
| LL-016 | python     | 零拷贝 base-object 绑定与打包细节                                                                  |
| LL-017 | typescript | napi/wasm 绑定实现细节与坑                                                                         |
| LL-018 | oracle     | golden 数据只由 `gen_golden.py` 再生，禁手改                                                       |
| LL-019 | core       | 触碰 core 后重建全部绑定再对拍                                                                     |
| LL-020 | core       | `#[coverage(off)]` 是 nightly-only，stable 禁用                                                    |
| LL-021 | core       | 真实基准必须 `black_box` 包裹输入输出                                                              |
| LL-023 | python     | 改 core 后先 maturin develop；缓存异常全清重建                                                     |
| LL-024 | typescript | 改 core 后重建 node/wasm 再测试                                                                    |
| LL-025 | typescript | 覆盖率豁免 `v8 ignore` 逐条附理由                                                                  |
| LL-026 | typescript | 容器 machine-id 须 32 位十六进制                                                                   |
| LL-028 | docs       | archive 自带 sync，手动 sync 后须去重                                                              |
| LL-029 | docs       | 第三方许可表：GPL 源禁抄代码，只读思想                                                             |
| LL-032 | docs       | 持久文档禁写临时名称与无意义日期，只留最终结论，追溯靠 git log                                     |
| LL-034 | ci         | tsdown dts 需双 glue 先建：CI 先 build:wasm 再 build:native                                        |
| LL-036 | ci         | 改完 TS 必跑 typecheck，`pnpm check` 不含类型门禁                                                  |
| LL-040 | ci         | 合并只走 PR 禁直推 main；PR 用 git credential helper 建                                            |
| LL-041 | ci         | 钉版 toolchain 后组件要补装到激活工具链（rustup component add）                                    |
| LL-042 | core       | 精确常量比较逐 bit ==，不引用 core_tol（容差只管计算结果）                                         |
| LL-044 | core       | clippy --workspace 特性统一：napi/wasm 属性须 not() 互斥门控                                       |
| LL-046 | core       | 绑定宏 glue 计入 core 覆盖率，属性+导入须 not(coverage) 剥离                                       |
| LL-047 | ci         | 跨端一致性检查归构建各端产物的集成步骤，勿下沉单端测试段                                           |
| LL-048 | ci         | 跨平台步骤用 bash 子 shell 语义须钉 `shell: bash`（Win 默认 PS）                                   |
| LL-050 | typescript | 入口全下沉 core 后 glue 须 `extern crate netwave` 强制链接                                         |
| LL-051 | typescript | napi 跨端整数返回用 u32，usize→bigint 破坏三端类型平价                                             |
| LL-052 | core       | 泛化表≠泛化分发：wasm 导出恒单条 `call`，加方法只改资源 match                                      |
| LL-054 | typescript | napi-cli 与 napi crate 配对升级，升级后 grep 生成 mjs 枚举名                                       |
| LL-057 | core       | `--fail-under-lines` 读 report 恒差，100% 闸门读 codecov.json                                      |
| LL-061 | workflow   | openspec apply 连续跑完不等催，仅真阻塞才停                                                        |
| LL-062 | core       | worker 内无 `window`，wasm 取全局走 `js_sys::global()` 转 scope                                    |
| LL-064 | workflow   | 迁移/推迟只推实施，契约措辞必须与终裁同步，禁抄已废弃旧契约                                        |
| LL-065 | workflow   | 活文档指针先指 delta 路径，sync/archive 时改指主 spec 链接                                         |
| LL-066 | workflow   | rustup 无 GitHub Releases，查最新版用 tags API                                                     |
| LL-069 | python     | uv 删依赖后旧 .venv 残留旧二进制，以 uv.lock 为准，清理用 `--exact`                                |
| LL-072 | core       | 钉死交错布局的三条理由与代价（铁律一 rationale）                                                   |
| LL-073 | workflow   | Plan/ 草案条文未转正即非契约，禁据此新建工件；决策唯一存 design.md                                 |
| LL-074 | workflow   | 新增 Requirement 先查重，同一门禁多节要求合为一条（RENAMED+MODIFIED）                              |
| LL-075 | workflow   | 照搬旧文须按现行规则洗词，黑话不随复制复活（豁免须注明去向）                                       |
| LL-076 | workflow   | 同一知识两份清单必漂移，共用常量/算法收编 lib 单一来源（同 LL-034）                                |
| LL-077 | python     | 同秒等长还原源文件后 pytest 跑陈旧字节码，还原后清 `__pycache__`                                   |
| LL-078 | python     | 测试离线防护点在 `socket.getaddrinfo`，patch `socket.socket` 拦不住 urllib                         |
| LL-079 | python     | runpy 重执行门面按 sys.modules 重绑定，桩须打 lib 源头模块非门面                                   |
| LL-080 | workflow   | "必须配套升级"须有官方出处或本仓实测，否则不得写入 spec/已写入者删除                               |
| LL-081 | ci         | 收紧依赖版本范围只抬下界，禁加未实测上界或扩大未实测放行面                                         |
| LL-082 | workflow   | 具体版本号写入常驻工件前须 registry 可核+实测留痕，口述不直写                                      |
| LL-083 | workflow   | 宣称门禁失效先造受控错误实测取证，无证据只能说"疑似缺口"                                           |
| LL-084 | ci         | 本机 node 26 无 corepack，npm 装 pnpm 须 `--allow-scripts`，验证看 `pnpm -v`                       |
| LL-085 | ci         | `~/.cargo/bin` 遮蔽 `~/.local/bin`，直装工具升级后须 `which` 确认命中新版                          |
| LL-086 | workflow   | 跨机器钉版须自动生效（干净终端实测），`.nvmrc` 被动声明不算钉版                                    |
| LL-087 | workflow   | 多段报告禁 tail 截断后下"无问题"结论，须看 SUMMARY 总览行或完整输出                                |
| LL-088 | python     | abi3-py310 门控掉 `pyo3::buffer`，memoryview 走 `tobytes()`、PyBytes 0.30 签名                     |
| LL-089 | workflow   | 流程规则只写本步动作并核对步骤锚点，禁前移后置动作/复述 commit                                     |
| LL-090 | workflow   | 规划/设计文档的名字是未来接口提案，禁按现行 spec 判冲突（先判句子的时态）                          |
| LL-091 | ci         | llvm-cov show-env 泄漏污染构建致假失败：子 shell 内用+清独立 target+env -i 复跑                    |
| LL-092 | ci         | 外部驱动胶水覆盖率三坑：vitest threads 池倒 profraw、napi report 须 --target、maturin 须 cd python |
| LL-093 | ci         | 覆盖率口径漂移假绿：退役执行者须 grep 实证前提，胶水报告须验命中 > 0                               |
| LL-094 | python     | 改 pytest 全局配置须当轮全量跑并贴覆盖率文件清单证据（pythonpath≠覆盖率范围）                      |
| LL-095 | ci         | llvm-cov 不建输出目录：CI 写 coverage/ 前须 mkdir -p，本地模拟先删 gitignored 目录                 |
