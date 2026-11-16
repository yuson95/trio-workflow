# 方案九：示例

## 1. 待决定的事
| 编号 | 问题 | 选项 | 默认 |
| --- | --- | --- | --- |
| D-1 | 合计用 MWh 吗 | MWh / kWh | MWh |

## 2. 需求
### R1 摘要页显示全年合计
- 类型：功能
- 现状（出处）：`web/summary.js` renderTotals
- 你会看到：摘要表最后一行是“合计 1,234 MWh”
- 单元验证：`tests/test_summary.py` 新增 test_yearly_total
- 实际操作验证：打开合成项目的摘要页并截图，合计行出现即通过
- 走查：需要
- 原型：`docs/mockups/summary_MOCKUP.html`

## 3. 批次、并行和文件归属
| 批次 | 需求编号 | 依赖 | 独占文件 | 可以并行 |
| --- | --- | --- | --- | --- |
| B1 | R1 | 无 | `web/summary.js`、`tests/test_summary.py` | — |

## 附录 C. 风险，落在哪个批次
无。
