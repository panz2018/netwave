# Proposal

## Why

versions 域两个工具（`check_versions.py` 离线闸门、`check_outdated.py` 联网体检）
的通过输出有黑话且信息不全：摘要行含 `pin`（违反 AGENTS.md「命名一眼懂」对输出
面的要求）、只报 rust 字段而看不出 python/pm/CI 也已检查；体检报告段 2/3 没有
OK/LAG 标记（落后要读者心算，而 spec「一条命令看全貌」Scenario 已明文要求输出
"是否落后"——现状实现对不上 spec），python 行含 `pin` 黑话且列宽溢出错位。

## What Changes

- **BREAKING**（输出契约变更）：`check_versions.py` 通过摘要行改为四律并列计数，
  `pin`→`toolchain`，保留前缀 `version laws OK:`。新措辞（真实数字示例）：
  `version laws OK: rust 4 members (rust-version 1.99, toolchain 1.99.1), python 2 projects, pnpm 1 manifest, ci 2 python-version files`
- `check_outdated.py` python 行去 `pin`、修列宽：
  `python-version <路径> <当前> -> latest stable <最新>  LAG|OK`
- `check_outdated.py` 段 2（全局 CLI）/段 3（直装工具）每行补尾部 `OK`/`LAG`
  标记，与段 4（CI actions）统一；比较前剥壳取纯版本号（`uv 0.13.5 (aarch64...)`、
  `rustc 1.99.1` vs `latest: 1.99` 这类带工具名/前缀字符串先归一，防误判）。
- 测试同步：`scripts/tests/versions/lib/test_rules.py` 摘要逐字断言改新措辞；
  `scripts/tests/versions/test_check_outdated.py` 新增锁新格式断言（python-version
  行 `->` 形状、段 2/3 每行带标记）。
- `scripts/versions/README.md` 已有描述核对（不补示例输出行——使用方法够用、
  输出细节易变，人工裁决）。

## Capabilities

### New Capabilities

- 无（skip_specs：输出措辞属实现细节，测试即契约；段 2/3 补标记是履行现有
  spec「一条命令看全貌」条款，不改 spec 级行为）

### Modified Capabilities

- 无（`dependency-upgrade` spec 现有条款已覆盖"输出当前版本、最新与是否落后"
  语义，摘要行格式按已定裁决不进 spec 冻结）

## Impact

- `scripts/versions/lib/rules.py`（`summary()`）、`scripts/versions/check_outdated.py`
  （python 行、段 2/3 标记）、`scripts/versions/lib/latest.py`（取数口径剥壳）
- `scripts/tests/versions/lib/test_rules.py`、`scripts/tests/versions/test_check_outdated.py`
- `scripts/versions/README.md`（描述核对）
- `Plan/软件升级.md`（本 change 定案章节按 apply 钩子当场删除）
- 无 CI/命令面变化：`check:meta`/`check:outdated` 命令与退出码契约不动
  （摘要行仅人读，无机器消费者；`test_check_versions.py` 用 monkeypatch 假
  摘要不受影响）

## Non-goals

- 不补 README 示例输出行（人工裁决：使用方法够用，输出细节易变）
- 不动段 1 原始输出墙（`cargo update` 等逐包清单是信息本体，不砍）
- 不把摘要行格式或 OK/LAG 标记写进 spec（格式留代码+测试当契约）
- 不改退出码契约（闸门 0/1、体检恒 0）与 `check:outdated` 不进 CI 的条款
- 不实施 blocked/pairs 机制（独立待触发项，禁止绑定）

## Prior art

- `scripts/versions/check_outdated.py` 段 4 已有 `OK`/`LAG`/`REF` 标记体系——
  本次把同一体系推广到段 2/3，不另造第二套。
- `pnpm outdated` 的 Current/Latest 表格列语义（段 1 内嵌输出）——`->` 箭头与
  尾部标记沿用其"当前→最新+状态"惯例。

## 专家增补

- `test_check_outdated.py` 现有断言（`"OK" in out`）在新格式下碰巧仍绿，必须
  新增锁格式断言，否则契约裸奔——落点
  `scripts/tests/versions/test_check_outdated.py`。
- 段 2/3 打标记前统一取数口径是前置：`lib/latest.py` 的 `latest_version` 返回
  值与 `run_cmd` 安装版字符串（含 uv/rustc 工具名前缀、`v` 前缀、括号架构后缀）
  须先剥壳，否则 `1.99.1 vs 1.99` 误判——落点 `scripts/versions/lib/latest.py`
  与 `lib/version.py` 的 `is_outdated(major_only=...)` 配合。
