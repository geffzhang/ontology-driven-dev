---
name: model-validator
description: |
  Use when running the cross-reference gate over the seven-model ontology YAML set (M1-M7+MU) declared in manifest.json — as MetaSkill step validate_cross_refs via skill_exec, or in CI. Triggers: 跨引用校验、6 条门禁、traceability、query_mapping、flow_refs、acyclic_call_graph、query_behavior_bidir、rule_condition_separation、manifest 校验、交付门禁。
---

# 模型校验器（model-validator）

被 [`ontology-driven-dev`](../../SKILL.md) MetaSkill 步骤 12 以 `skill_exec` 调用（entrypoint `scripts/gate.ps1`）。**纯确定性脚本**，无 LLM 参与：对七模型 YAML 集合做 6 条跨引用门禁，退出码非 0 = 步骤失败。

> **路径约定**：本 SKILL.md 位于 `subskills/model-validator/`；验证对象是**运行工作区的 `yaml/` 目录**（路径经 skill_exec args 传入绝对路径），与本体 `reference-example/` 无关。

## 一、6 条检查定义

绑定语义 = 原 MetaSkill 步骤 12 `tool_args.checks` 的 6 条 description（已下移至此，本表即权威定义）；字段路径与违规判定参考 OpenClaw [`ValidateYamlReferencesTool.cs`](E:/GitHub/openclaw.net/src/OpenClaw.Agent/Tools/ValidateYamlReferencesTool.cs)。

| id | 检查语义 | 读取的 YAML 字段 |
|---|---|---|
| `traceability` | 正向：M2 每个 `triggerType=USER_ACTION` 行为须被 ≥1 个 MU 工具引用；反向：MU 工具引用的行为须存在 | `M2.behaviors[].id/triggerType`、`MU.tools[].behaviorRef` |
| `query_mapping` | M7 报表 ↔ M2 行为（`queryReportRef`）严格 1:1，且引用双向存在 | `M7.query_reports[].id/behaviorRef`、`M2.behaviors[].id/queryReportRef` |
| `flow_refs` | M6 全部引用须真实存在（对象/角色/行为/子流程/规则） | `M6.flows[].businessObjectRefs/roleRefs`、`activities[].behaviorRef/roleRef/subFlowRef`、`branches[].ruleRef` |
| `acyclic_call_graph` | M6 `SUB_FLOW_CALL` 子流程调用图无环 | `M6.flows[].id`、`activities[].activityType/subFlowRef` |
| `query_behavior_bidir` | 正式报表（LIST/DETAIL/STATISTICAL/REPORT）↔ M2 QUERY 行为严格 1:1 | `M7.query_reports[].objectType/behaviorRef`、`M2.behaviors[].behaviorType/queryReportRef` |
| `rule_condition_separation` | syncTrigger 描述只写结论；出现条件语气词（如果/若/若果/假如/when/if/iff）即违规，条件须移入 M3 规则并经 `appliedRules` 引用 | `M2.behaviors[].syncTriggers[].description` |

判定细节（与 C# 逐条对齐）：

- 两侧均无数据 → `SKIP`（如 query_mapping 在 M7/M2 均无映射时）；`SKIP` 不导致 FAIL。
- 引用存在性按**全部 ID 集合**判定（如 MU 引用的行为只需存在于 M2 全部行为中，不限 USER_ACTION）。
- 空字符串列表项（businessObjectRefs/roleRefs）跳过；activity 级标量引用含空串 → 违规。
- 调用图 DFS 三色染色；指向未知流的边跳过（由 flow_refs 捕获）。

## 二、用法

```bash
python scripts/validate_yaml_refs.py <yaml_dir> <manifest> [--format json|text] [--check <id>]...
```

- `manifest` 路径解析：绝对 > 相对 CWD > 相对 `yaml_dir`；支持 `model_files` 数组（黄金范例形态）或 `models` 对象（MetaSkill 步骤 6 文档形态）两种 manifest。
- 检查子集用 `--check`（可重复），默认全部 6 条。

## 三、输出契约（skill_exec `parse_mode: json` 消费）

```json
{
  "status": "OK" | "FAIL" | "ERROR",
  "yaml_dir": "<绝对路径>",
  "model_files": ["m1-object-model.yaml", ...],
  "checks": [
    {"id": "traceability", "status": "PASS"|"FAIL"|"SKIP",
     "message": "...", "violations": [{"model", "path", "ref", "detail"}]}
  ],
  "summary": {"total": 6, "passed": 6, "failed": 0, "skipped": 0}
}
```

## 四、退出码与错误码

| 退出码 | 含义 |
|---|---|
| 0 | `status: OK`（无 FAIL；SKIP 允许） |
| 1 | `status: FAIL`（≥1 条检查存在 violation） |
| 2 | `status: ERROR`（参数/加载错误，信封含 `error_code`） |

错误码：`invalid_arguments` / `manifest_not_found` / `invalid_manifest` / `model_file_not_found` / `yaml_parse_error`。

## 五、与 ontology-modeler 工具链的关系

| 工具 | 职责 | 调度方 |
|---|---|---|
| 本验证器 `validate_yaml_refs.py` | **跨文件** 6 条门禁（YAML 通道） | MetaSkill 步骤 12（skill_exec）/ CI |
| `ontology-modeler/scripts/validate.py` | 单模型 JSON-LD 解析 + M2 双层对账 | ontology-modeler 内部步骤 8 / CI |
| `ontology-modeler/scripts/drift_check.py` | YAML ↔ JSON-LD ID 集漂移 | 同上 |

三者互补不重叠：本验证器管**模型之间**的引用一致性，另两者管**模型内部**与双轨派生的一致性。

## 六、行为纪律

1. **确定性**：本 Skill 无 LLM 步骤，不得在运行时改 YAML——只报告，不修复。
2. **不越界**：不校验 JSON-LD / SHACL（那是 ontology-modeler 步骤 8 的职责；阶段 6 引入 JSON-LD 门禁时在此 Skill 内新增 entrypoint，不改本脚本语义）。
3. **6 条语义变更须同步**：根 [`SKILL.md` 步骤 12 注释](../../SKILL.md)、本文件第一节、脚本实现三处必须一致；参考实现 `ValidateYamlReferencesTool.cs` 若更新，须评估是否回移。

## 七、参考

- 上游 MetaSkill：[`../../SKILL.md`](../../SKILL.md)（步骤 12 定义）
- C# 参考实现：[`ValidateYamlReferencesTool.cs`](E:/GitHub/openclaw.net/src/OpenClaw.Agent/Tools/ValidateYamlReferencesTool.cs)
- 黄金范例：[`../ontology-modeler/reference-example/`](../ontology-modeler/reference-example/)（7 模型 YAML + manifest.json，全部 6 条 PASS）
- 漂移守护 CI：[`../../.github/workflows/drift-check.yml`](../../.github/workflows/drift-check.yml)
- 跨仓库集成路线：[`../ontology-modeler/references/openclaw-integration.md`](../ontology-modeler/references/openclaw-integration.md)
