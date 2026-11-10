# Tasks

## 1. core 改名

- [x] 1.1 `core/src/touchstone.rs`：`pub fn write_touchstone`→`to_text`（L1133），
      内部调用点 L1222（`write_file` 内）、L1490/L1501（browser dispatch）同步改；
      L78 doc 注释 `writeTouchstone`→`toText`
- [x] 1.2 browser dispatch 臂 `"writeTouchstone"`→`"toText"`（L1487），返回载荷
      保持 `{text, filename}` 不变
- [x] 1.3 `core/tests/touchstone_write.rs`：所有 `.write_touchstone(`→`.to_text(`、
      测试函数名 `write_touchstone_*`→`to_text_*`、头注释同步
- [x] 1.4 验证：`cargo test -p netwave` 全绿

## 2. python 绑定改名

- [x] 2.1 `python/src/lib.rs`：`fn write_touchstone`→`to_text`（L463）+ 内部调用
      `self.core()?.write_touchstone`→`to_text`（L466）
- [x] 2.2 重生成 typing：跑 stub_gen 重出 `python/netwave/_netwave.pyi`
      （`write_touchstone`→`to_text`），不手改
- [x] 2.3 `python/tests/test_touchstone_class.py`：测试名 + 调用改名（L152–154）
- [x] 2.4 验证：`pytest` 全绿

## 3. node 绑定改名

- [x] 3.1 `typescript/native/src/lib.rs`：`pub fn write_touchstone`→`to_text`
      （L378）+ 内部调用（L382）
- [x] 3.2 `typescript/src/index.browser.ts`：壳方法 `writeTouchstone`→`toText`
      （L352）+ dispatch 字符串 `"writeTouchstone"`→`"toText"`（L353）
- [x] 3.3 `typescript/test/native/touchstone.test.ts`（L141–143）、
      `typescript/test/wasm/touchstone.test.ts`（L145–148）改名
- [x] 3.4 验证：`pnpm -C typescript test`（native + wasm）全绿

## 4. 闸门与主 spec 同步

- [x] 4.1 `scripts/check_verbs.py`：`TOUCHSTONE_VERBS` 集合 `writeTouchstone`→`toText`；
      `FORBIDDEN` 增列 `writeTouchstone`
- [x] 4.2 `openspec/specs/touchstone-core/spec.md`：「写出接口」「2 端口列序」
      「名字流水线」三 Requirement 内 `writeTouchstone`/`write_touchstone`→
      `toText`/`to_text`（仅文本动词；`writeFile`/`write_path` 不动）
- [x] 4.3 验证：`python3 scripts/check_verbs.py` 退出码 0

## 5. cross-binding 对拍

- [x] 5.1 跑 `pnpm check:cross`：四端 dump + 阅卷全绿（改名不改答卷字段，
      `compare_cross.py` 零改动；验证改名未破坏跨端一致）

## 6. Plan 同步

- [x] 6.1 `Plan/测试规划.md`：删除 L102「`write_touchstone` 改名 `to_text`」整条；
      L407 下期清单摘除「`write_touchstone`→`to_text`」子项（保留 `to_bytes`/encoding
      等未做内容）；新增未来项「输出动词家族统一 `to_*` 前缀 + spec 钉死规矩（随
      `to_bytes`/`to_file` 落地时立）」
- [x] 6.2 验证：`pnpm check:md` 退出码 0

## 7. 全量闸门

- [x] 7.1 跑 `pnpm check`（fmt/clippy/全测试/覆盖率）+ `pnpm check:md` 全绿
- [x] 7.2 全仓核对：`grep -rn 'write_touchstone\|writeTouchstone'` 仅剩
      `openspec/changes/archive/**`（历史冻结）与 `Plan/测试规划.md` 中 skrf 自有函数名
      （L120 附近），无其他残留
- [x] 7.3 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾体检与
      升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍，含全局 CLI/直装工具的
      机器级升级；上游 bug/不兼容登记回退不阻塞；仅设计级适配、restrictions.json
      破损、流程走不通才停下报告；下限变更等人工发起）。消化完成后 MUST 复跑
      `pnpm check:outdated` 至退出码 0（SUMMARY 归零）才算本项完成

## 完成记录（三态时效结论）

- 更新：`openspec/specs/touchstone-core/spec.md`（写出接口 / 2 端口列序 /
  名字流水线 三 Requirement 文本动词 `writeTouchstone`→`toText`）——已改。
- 新增：无（本 change 仅改名，不引入新 Requirement）。
- 退役：`writeTouchstone` 作为公开动词退役，进 `check_verbs.py` `FORBIDDEN`
  防复活；`writeFile`/`write_path` 未退役（过渡态，留 `to_file` 落地刀）。
- Plan/ 瘦身：`Plan/测试规划.md` 已删改名条目、摘除已完成子项、新增家族统一
  未来项（见任务 6.1）。
- 体检消化：`syn 3.0.9→3.0.10`（cargo）、`openspec 1.16.1→1.17.0`（全局 CLI），
  复跑 `pnpm check:outdated` SUMMARY 归零；syn 升级后重建三端产物 + 全闸门 +
  四端对拍全绿。
