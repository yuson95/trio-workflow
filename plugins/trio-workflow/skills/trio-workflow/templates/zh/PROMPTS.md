# 提示词 · {{project}}

把下面的一段复制到新的执行对话里（{{builder}}），并替换 `<…>` 的部分。

## 开工

```text
请按技能 trio-workflow 的执行者流程（builder.md）执行 <方案文件路径>，全部在本对话中完成，只在方案规定的停点停下。
技能文件在 {{skill_dir}}；技能列表里看不到时，直接读那里的 SKILL.md 和 builder.md。
先读：0_RULES.md；方案的总则章节；前面方案的交接文档 <文件名>（找不到就先停下告诉我）；AGENTS.md 和 CURRENT_STATUS.md。
集成分支 wip/<key>；进度 batch-notes/<KEY>_PROGRESS.md；决策记录 batch-notes/<KEY>_DECISIONS.tsv；停点材料 batch-notes/REVIEW_<key>_stop<N>.md。
交付方式：{{delivery}}。不推送到 main，不合并到 main，不用客户数据，不碰 {{service}}；重检查要等锁文件 {{lock}}。
现在开始，直接做到停点 1。
```

## 恢复

```text
继续执行 <方案>。先读 batch-notes/<KEY>_PROGRESS.md、最近一份交接说明和 batch-notes/<KEY>_DECISIONS.tsv 的末尾几行，再按技能 trio-workflow（{{skill_dir}}）builder.md 中“Resume”一节接手。以 git 的实际状态为准；不要重做已完成的批次；未提交的改动先提交为 wip: 再决定去留。
```
