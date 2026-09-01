---
name: req-explorer
description: |
  按 stage_range 执行 V9.0 需求探索提示词的指定阶段，输出结构化建议供 MetaSkill 编排器消费。
  输入参数（由 MetaSkill 通过 with + Jinja 注入）：
    - stage_range (string, 必填): "0-2" | "3-4" | "5-6"
    - domain (string, 必填): 业务域中文名
    - prior_confirms (object, 可选): 前序确认结果，用于增量修改模式
    - retry_hint (string, 可选): 上一步失败时的提示
  输出契约：JSON 对象，含 stages 数组与 appendix_b_state。
  触发词：需求探索、阶段探索、阶段建议生成、需求建议。
---

# 需求探索阶段执行器（req-explorer）

被 [`ontology-driven-dev`](../SKILL.md) MetaSkill 的 `agent` kind 步骤调用，运行在子 Agent 中。子 Agent 拥有完整工具访问（Read / Glob / Grep 等），最终必须输出符合 `OutputContract` 的 JSON 结构。

> **路径约定**：本 SKILL.md 位于 `subskills/req-explorer/`，子目录 `references/` 与 `reference-example/` 即本 Skill 自带的规范文档与黄金范例。

## 一、唯一依据

`references/AI需求探索与确认提示词V9.0.md`（其附录一即《软件需求编写规范 V9.0》全文）。

执行前**必须**先 Read 此文件，定位到 `stage_range` 对应的章节。未读不可生成。

## 二、阶段映射

| `stage_range` | 涵盖阶段 | 主题 |
|---|---|---|
| `0-2` | 阶段零、阶段一、阶段二 | 总体理解 → 业务对象 → 功能与规则 |
| `3-4` | 阶段三、阶段四 | 跨对象联动 → 端到端协同流与审批流 |
| `5-6` | 阶段五、阶段六 | 查询统计与固定报表 → 角色权限 |

## 三、执行模式

### 模式 A：首次生成（`prior_confirms` 为空或缺省）

按 V9.0 提示词对应章节逐阶段生成建议。A 类自动补全、B 类带选项与修改入口。

### 模式 B：修订模式（`prior_confirms` 非空且含 `modification` 字段）

仅对被修改的阶段（`decision == modify`）重做，其余阶段直接复用 `prior_confirms` 中对应字段。

判定方法：

```yaml
modified_stages: []
for stage in prior_confirms:
  if stage.decision == "modify":
    modified_stages.append(stage.stage)
# 仅对 modified_stages 重新生成，其余原样保留
```

### 模式 C：重试模式（`retry_hint` 非空）

按 `retry_hint` 提示调整输出（例如"简化建议长度"），但仍需满足下方输出契约。

## 四、输出契约

```json
{
  "stages": [
    {
      "stage": 0,
      "ai_suggestion": "<该阶段核心建议的自由文本，<200 字>",
      "ai_reason": "<判断依据，<100 字>",
      "options": ["<选项 A>", "<选项 B>", "<选项 C>"],
      "quick_replies": ["按AI建议", "选项A", "选项B", "选项C", "我要修改"],
      "category": "A" | "B"
    }
  ],
  "appendix_b_state": {
    "pending_count": 0,
    "auto_complete_count": 0
  }
}
```

### 字段细则

| 字段 | 必填 | 类型 | 约束 |
|---|---|---|---|
| `stage` | 是 | integer | 0-6 |
| `ai_suggestion` | 是 | string | < 200 字 |
| `ai_reason` | 是 | string | < 100 字 |
| `options` | B 类必填，A 类可空 | string[] | ≥ 2 项 |
| `quick_replies` | 是 | string[] | 恒含 `"按AI建议"` 与 `"我要修改"` |
| `category` | 是 | enum | 仅 `"A"` 或 `"B"` |
| `appendix_b_state.pending_count` | 是 | integer | 仅 B 类计入 |
| `appendix_b_state.auto_complete_count` | 是 | integer | 仅 A 类计入 |

## 五、A/B 类分流规则

- **A 类（自动补全）**：行业通用、猜错无业务风险的内容。
  - 例：常见角色清单（系统管理员 / 普通用户）、通用查询模式
  - 输出 `category: "A"`，`options` 可省略，`quick_replies = ["按AI建议", "我要修改"]`
  - 在 MetaSkill 端的 `user_input` 表单中，`decision` 选项 `skip` 仅对 A 类可用

- **B 类（待确认）**：企业专属、猜错有真实业务风险的内容。
  - 例：本企业的具体业务对象、审批节点、自定义权限模型
  - 输出 `category: "B"`，`options` ≥ 2 项，`quick_replies` 含至少 2 个选项字母入口
  - 决策必填 `accept` / `modify`，不可 `skip`

## 六、行为纪律

1. **未读 V9.0 提示词前不得生成**：第一步必须是 Read `references/AI需求探索与确认提示词V9.0.md`。
2. **不可省略 `category` 字段**：A/B 分流是 MetaSkill 下游 `user_input` 表单的 `skip` 选项依据。
3. **不可混合 A/B**：单条 stage 必须二选一。
4. **不得扩展 `stage_range` 范围**：参数给 `"3-4"` 时，绝不输出 `stage: 5`。
5. **不写盘**：本 Skill 只生成建议文本，不直接写文件。文件写入由 MetaSkill 步骤 8 统一处理。
6. **JSON 输出无多余文字**：最终回复必须是合法 JSON，前后可有一行空行，但不得包含 Markdown 代码块包裹（MetaSkill 的 `OutputContract.Format: json` 会严格校验）。

## 七、与 MetaSkill 的衔接

```
MetaSkill 步骤 2/4/6 (agent → req-explorer)
  ↓ with: { stage_range, domain, prior_confirms }
子 Agent 读取 req-explorer/SKILL.md（即本文件）作为 system prompt
  ↓ 读取 references/AI需求探索与确认提示词V9.0.md
  ↓ 生成 JSON 输出
  ↓ 返回
MetaSkill 校验 OutputContract (required_properties: [stages, appendix_b_state])
  ↓ 注入到下一步 user_input 表单的 ai_suggestion / ai_reason 字段
MetaSkill 步骤 3/5/7 (user_input)
  ↓ 用户确认/修改
  ↓ 输出确认结果到 outputs.p1_*_confirm
后续 explore 步骤的 prior_confirms 即上一步 confirm 结果
```

## 八、参考

- 上游 MetaSkill：[`../SKILL.md`](../SKILL.md)
- 方法论提示词：[`references/AI需求探索与确认提示词V9.0.md`](references/AI需求探索与确认提示词V9.0.md)
- 黄金范例：[`reference-example/合同管理需求规格说明书-V9.md`](reference-example/合同管理需求规格说明书-V9.md)
