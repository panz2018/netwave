# Design

## 决策：`## 已定裁决` 段格式

proposal.md 末尾一节，标题精确为 `## 已定裁决`。每条决定一行，格式固定：
反引号包裹的关键词 + 全角冒号 + 详细解释。示例：

```markdown
## 已定裁决

- `裁决段`：决定写进 proposal 的已定裁决段，再转 tasks 任务行。
- `双层`：CI 闸门 + AGENTS.md 双层保障。
```

`check_proposal.py` 提取段内关键词集合：行首为短横线、紧跟一对反引号包裹的
非空内容、再接全角冒号（正则见 `scripts/check_proposal.py` 实现）。

## 决策：关键词与任务行挂钩

`tasks.md` 任务行任意位置含反引号包裹的关键词即视为该决定的载体：提取
任务行内所有反引号包裹的非空内容（正则见 `scripts/check_proposal.py` 实现）。

一个任务行可挂多个关键词。判定只查存在性：每个 proposal 段内关键词至少被
一个任务行引用，缺哪个报哪个。反引号中文关键词不触发 `check_md.py` 的
DECISION TAG 禁令（该禁令只拦临时编号式标记，不拦反引号关键词）。

## 决策：校验时机与范围

`check_proposal.py` 扫在途 change（`openspec/changes/*/`，排除 `archive/`）：

1. proposal.md 含 `## 已定裁决` 段且段内 ≥1 个关键词，否则红。
2. 段内每个关键词在 tasks.md 有引用任务行，否则红并指名关键词。
3. 收尾打勾：仅当 change 的 tasks.md 全部任务已打勾（视为 apply 完成态）时，
   要求每个关键词的引用任务行本身为 `- [x]`；未全勾时跳过此项（实施中允许未勾）。

无在途 change 时整项通过。归档不回溯。

## 决策：扩容 vs 新开（行为准则，非机器判）

"决定是否属于当前 change 主题域"无法机器判，落 `AGENTS.md` 准则：先尝试扩容
（同域改宽命名/追加任务），不强塞；异域或无在途则新开 change。机器只兜"落笔后
每个关键词有载体"，不兜"该不该塞进这个 change"。

## 决策：取代旧裁决

`AGENTS.md` 对话效率段"拍板即记"收紧为"写回在途 change 的已定裁决段"，
并加一句显式声明：旧"琐碎文档修复直接改不新开 change"作废，琐碎修复同样
进 change（必要时新开）。

## 收编的文档修复

- `python/README.md` Layout 节：测试文件清单改为指向 `tests/` 目录一句。
- `scripts/README.md` 与 `scripts/check_ci.py`：删 `LL-037` 编号，保留机制句
  "CI 不跑的测试不算闸门"。
- `scripts/README.md` 脚本清单表：check 类脚本改指针（`package.json` 的
  `check:meta`/`check:cross`），表只留非 check 入口工具（install 脚本、
  bench/coverage gate、`versions/`）。
- 修复完成后 `Plan/体检-2026-11-15.md` 对应章节当场删除（结论已落本 change）。

## 边界

闸门拦不住"决定漏列"（脚本看不到对话），由 AGENTS.md 准则兜底，不设第二道
机器闸——与 Non-goals 一致。
