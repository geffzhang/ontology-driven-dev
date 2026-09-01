# OpenClaw ValidateJsonLdTool.cs 跨仓库集成路径

> 本文档记录 **ontology-driven-dev** 仓库与 **openclaw.net** 仓库之间的 JSON-LD
> 验证工具集成路径。本仓库（ontology-driven-dev）只负责定义集成契约与文档；
> 实际的 `ValidateJsonLdTool.cs` 实现在 openclaw.net 仓库内单独提 PR，不在本工作树提交。

---

## 一、目标文件路径

| 项 | 值 |
|---|---|
| 仓库 | `E:/GitHub/openclaw.net` |
| 命名空间 | `OpenClaw.Agent.Tools` |
| 类名 | `ValidateJsonLdTool` |
| 目标文件路径 | `src/OpenClaw.Agent/Tools/ValidateJsonLdTool.cs` |
| 注册名（`ITool.Name`） | `"validate_json_ld"` |

> **注意**：该文件当前**不存在**。它是阶段 5.5 路线图中"OpenClaw JSON-LD 校验通道"
> 的占位实现，对应 [spec § 阶段 2 / 阶段 3 / 阶段 5](../../../docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md)。
> 实际编写与提 PR 在 openclaw.net 仓库完成，**本工作树不直接 commit**。

---

## 二、ITool 接口契约

### 2.1 接口签名（参考 `OpenClaw.Core.Abstractions/ITool.cs`）

```csharp
namespace OpenClaw.Core.Abstractions;

public interface ITool
{
    string Name { get; }
    string Description { get; }
    string ParameterSchema { get; }
    ValueTask<string> ExecuteAsync(string argumentsJson, CancellationToken ct);
}
```

约定：

- **AOT 兼容**：使用 `JsonDocument.Parse` 解析入参/出参，**禁止**使用 `JsonSerializer.Deserialize<T>`
  反射路径（参考 [`ValidateYamlReferencesTool.cs`](E:/GitHub/openclaw.net/src/OpenClaw.Agent/Tools/ValidateYamlReferencesTool.cs)
  的 AOT 注释）。
- **错误信封**：任何抛错场景（`JsonException` / `FileNotFoundException` / `InvalidDataException`）
  须返回 `{"status":"ERROR","error_code":"<code>","error":"<message>"}`，
  而非抛出未捕获异常。
- **成功信封**：返回 `{"status":"OK"|"FAIL","json_ld_files":[...],...}`
  与 YAML 通道结构对齐。

### 2.2 `ValidateJsonLdTool` 参数 Schema

```json
{
  "type": "object",
  "properties": {
    "jsonLdFiles": {
      "type": "array",
      "items": {"type": "string"},
      "description": "绝对路径数组；运行时按 @context IRI 路由到对应 SHACL shape"
    },
    "vocabStrategy": {
      "type": "string",
      "enum": ["od", "meta"],
      "description": "默认 'od'；显式 'meta' 用于 M6 流程模型（meta:hasStep ≤ 12）"
    },
    "manifest": {
      "type": "string",
      "description": "可选；yaml/manifest.json 路径，用于跨 YAML↔JSON-LD 一致性核验"
    }
  },
  "required": ["jsonLdFiles"]
}
```

### 2.3 输出契约

```json
{
  "status": "OK" | "FAIL" | "ERROR",
  "json_ld_files": ["<path1>", "<path2>"],
  "checks": [
    {
      "id": "jsonld_parse" | "shacl_basic" | "shacl_m6_stepcount" | "shacl_m3_rule" | "id_consistency",
      "status": "PASS" | "FAIL" | "SKIP",
      "message": "<human-readable>",
      "violations": [
        {"focusNode": "<uri>", "path": "<iri>", "message": "<sh:message>"}
      ]
    }
  ],
  "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
}
```

字段语义对齐 `ValidateYamlReferencesTool` 的 6-check 设计：
`status` 大写枚举、`violations` 数组统一承载 SHACL `sh:ValidationResult`、
`summary` 三段计数。

---

## 三、词表路由策略（od: / meta: / sh:）

工具内部按 `@context` IRI 路由到不同的 SHACL 形状集：

| 检测 | `@context` 关键字段 | 路由词表 | 调用 SHACL Shape |
|---|---|---|---|
| M1 对象 | `od` = `https://ontology.ontology-driven.dev/v9#` | `od:` | `od:AggregateRootShape` + `od:DataDictionaryShape` |
| M5 主体 | `od` = `.../v9#` | `od:` | `od:ActorShape` + `od:RoleShape` + `od:PermissionShape` |
| M2 行为元数据 | `od` = `.../v9#` | `od:` | 暂无独立 shape：由 M2 双层对账承担（`validate_m2_yaml_jsonld_alignment`：ID 集一致 + `od:yamlPointer` 反向链接）；shape 待补 |
| M3 规则 SHACL | `sh` = `http://www.w3.org/ns/shacl#`（顶层 Shape 文件） | `sh:` | 内置 `m3-rule-model.shacl.ttl` |
| M6 流程 | `meta` = `https://openclaw.dev/meta/v1#` | `meta:` | `meta:FlowShape`（含 `meta:hasStep` ≤ 12 硬约束） |
| M7 报表 | `od` = `.../v9#` | `od:` | `od:ReportShape` |
| MU UI | — | — | **跳过**（spec § 11.1 显式声明 MU 不迁 JSON-LD） |

词表 IRI 详见 [framework § 11.2](ontology_modeling_framework_v9.md#112-词表-iri未注册-w3id)：
- `od:` → `https://ontology.ontology-driven.dev/v9#`
- `meta:` → `https://openclaw.dev/meta/v1#`
- `sh:` → `http://www.w3.org/ns/shacl#`

### 路由伪代码

```text
for each jsonLdFile in jsonLdFiles:
    ctx = read @context
    if ctx.sh is set:
        vocab = "sh"; shape = "m3-rule-model.shacl.ttl"
    elif ctx.meta == META_IRI:
        vocab = "meta"; shape = "m6_flow_shape.ttl"
    elif ctx.od == OD_IRI:
        # 按文件名映射到对应 od: shape
        vocab = "od"
        shape = filename → od: shape (m1→aggregate, m5→actor, m7→report；m2 暂无 shape，走双层对账旁路)
    else:
        return ERROR "unrecognized vocab"
    run_shacl(jsonld, shape)
```

### 与本仓库 `validate.py` 的关系

| 维度 | `validate.py` (Python, ontology-driven-dev) | `ValidateJsonLdTool` (C#, openclaw.net) |
|---|---|---|
| 验证对象 | JSON-LD | JSON-LD |
| 词表 | `od:` / `meta:` 按 `@context` 路由 | 同左（`sh:` 走 M3 旁路） |
| SHACL 引擎 | `pyshacl`（rdflib + shacl 0.40+） | dotNetRDF SHACL API |
| 调度方 | 本地 CLI / GitHub Actions cron | OpenClaw 运行时（agent step） |
| 角色 | PoC / CI 烟雾测试 | 运行时门禁（MetaSkill step 12） |

`validate.py` 是**正交旁路**：本仓库 CI cron（见 Task 9）每周跑一次 `validate.py` + `drift_check.py`；
`ValidateJsonLdTool` 是 OpenClaw 运行时集成点，agent 每次跑 MetaSkill step 12 都会调。
两者**不重叠**、**互相补位**。

---

## 四、MetaSkill 步骤 12 调用方式

当前 MetaSkill 步骤 12 为 `skill_exec`（YAML 通道），entrypoint 指向本仓库
`subskills/model-validator/scripts/gate.ps1`，6 条检查的 Python 移植
`validate_yaml_refs.py` 语义对齐 `ValidateYamlReferencesTool.cs`（来源见
[`SKILL.md` § 五](../../SKILL.md#五tool_call-与-skill_exec-实现)）：

```yaml
- id: validate_cross_refs
  kind: skill_exec
  skill: model-validator
  skill_exec_entrypoint: scripts/gate.ps1
  skill_exec_parse_mode: json
  skill_exec_args:
    - "{{ inputs.workspace_dir }}/yaml"
    - "{{ outputs.p2_flows_ui.manifest_path }}"
```

> 演进记录：步骤 12 原为 `tool_call → validate_yaml_references`（OpenClaw 内置 C# 工具），
> 后改为 `skill_exec → model-validator`（本地 Python 门禁，退出码非 0 = 步骤失败），
> 使校验逻辑与 Skill 同仓演进，不必等待 openclaw.net 发版。

### 4.1 未来两步走（YAML → YAML + JSON-LD 并行）

```yaml
# 当前 — 仅 YAML 通道（skill_exec）
- id: validate_cross_refs
  kind: skill_exec
  skill: model-validator
  skill_exec_entrypoint: scripts/gate.ps1
  skill_exec_parse_mode: json
  skill_exec_args:
    - "{{ inputs.workspace_dir }}/yaml"
    - "{{ outputs.p2_flows_ui.manifest_path }}"
```

```yaml
# 阶段 6（spec 路线图）— YAML + JSON-LD 双通道
- id: validate_cross_refs_yaml
  kind: skill_exec
  skill: model-validator
  skill_exec_entrypoint: scripts/gate.ps1
  skill_exec_parse_mode: json

- id: validate_cross_refs_jsonld
  kind: tool_call
  tool: validate_json_ld         # ← ValidateJsonLdTool.Name
  tool_allowlist: [validate_json_ld]
  with:
    jsonLdFiles: "{{ outputs.p2_flows_ui.manifest_path | jsonld_paths }}"  # 由 manifest 反查
    vocabStrategy: "od"             # 默认 od；M6 文件单独传 meta
```

> **阶段 6 计划不变**：在 MetaSkill `SKILL.md` 加 `validate_json_ld` 步骤；
> JSON-LD 门禁也可在 `model-validator` Skill 内新增 entrypoint 承载（见其 SKILL.md § 六）。

### 4.2 OpenClaw 工具分发

OpenClaw 运行时按 `ITool.Name` 字面量（`StringComparer.Ordinal` 严格相等）在
`_toolsByName` 字典中查找。引用：
[`OpenClawToolExecutor.cs:207`](E:/GitHub/openclaw.net/src/OpenClaw.Agent/OpenClawToolExecutor.cs#L207)。
步骤 8 的 `write_file` 为 OpenClaw 自带，**开箱即用、无需额外注册或路径桥接**。
步骤 12 的 `skill_exec` 不经过工具注册表——entrypoint 按 Skill 根目录解析为子进程执行。

---

## 五、跨仓库 PR 流程

阶段 5.5 的 Task 11 跨仓库集成按以下顺序推进，**严格分仓**：

### 5.1 本仓库（ontology-driven-dev）— 仅 README / 文档 PR

本仓库负责契约定义、词汇表、PoC 工具链。Task 11 的可交付物只有：

- 本文档 `subskills/ontology-modeler/references/openclaw-integration.md`（Task 11 唯一产物）
- 阶段 5.5 收尾报告中"跨仓库 PR 待办"标记（Task 12 输出）

本仓库**绝不**修改 openclaw.net 内任何 `.cs` 文件。

### 5.2 openclaw.net 仓库 — ValidateJsonLdTool.cs PR

| 步骤 | 内容 |
|---|---|
| 1 | Fork / 拉取 `E:/GitHub/openclaw.net`；新开分支 `feat/validate-jsonld-tool` |
| 2 | 新建 `src/OpenClaw.Agent/Tools/ValidateJsonLdTool.cs`（参考本文件 § 二、§ 三） |
| 3 | 添加 dotNetRDF NuGet 依赖（如未引入）：`dotnetrdf >= 2.x`（**注意 AOT 兼容性**，参考 [spec § 九 风险表](../../../docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md#九风险与权衡)） |
| 4 | 编写 6 条 `check`：`jsonld_parse` / `shacl_basic` / `shacl_m6_stepcount` / `shacl_m3_rule` / `id_consistency` / `manifest_xref` |
| 5 | 在 `OpenClawToolExecutor` 中**自动注册**（通过 `AddOpenClawTools` 反射枚举 `OpenClaw.Agent.Tools` 命名空间下所有 `ITool` 实现即可；与 `ValidateYamlReferencesTool` 同一注册路径） |
| 6 | 写单元测试：`tests/OpenClaw.Agent.Tests/Tools/ValidateJsonLdToolTests.cs`，覆盖黄金范例（`m1`/`m5`/`m6`/`m7`）+ 一个 `@context` 不识别场景 |
| 7 | 跑现有 YAML 通道回归测试（`ValidateYamlReferencesTool`），确保**不破坏**现有 6-check 行为（对应 Task 12 AC5） |
| 8 | 提 PR，PR 描述引用本仓库 commit + spec 链接 + 阶段 5.5 收尾报告 |

### 5.3 跨仓库联动时间线

```
[本仓库]                                       [openclaw.net 仓库]
  T1 词汇冻结 od: ─┐
  T2 manifest ─────┤
  T3-T9 转换+drift─┤
  T10 §11 文档 ────┤
                   │
  T11 (本任务) ────┼──────►  T11-openclaw PR  ──► review ──► merge
                   │         (本仓库仅文档)     (dotnetrdf 验证
                   │                              + YAML 回归不破)
                   │
  T12 验收 ────────┴──────►  AC5 跨仓库回归  ◄── 已合入 main
```

### 5.4 风险与注意

| 风险 | 缓解 |
|---|---|
| dotNetRDF AOT 兼容性 | 参考现有 `IsAotCompatible=true` 设计，使用反射无关 API；CI 跑 `PublishTrimmed` 烟雾 |
| `@context` IRI 漂移 | 词表 IRI 集中定义在本仓库 `references/od-context-v9.jsonld`，openclaw.net 端用常量字符串匹配 |
| SHACL shape 漂移 | 形状文件集中存放于 `scripts/shacl/`（m1_aggregate_shape / m5_actor_shape / m6_flow_shape / m7_report_shape），CI 按文件名匹配；M3 用 `reference-example/m3-rule-model.shacl.ttl`（转换器派生产物） |
| 双重注册风险 | 复用 `ValidateYamlReferencesTool` 的注册路径，不引入新的 `AddOpenClawTools` |

---

## 六、相关链接

### 本仓库

- 词汇表：[`od-vocabulary-v9.ttl`](od-vocabulary-v9.ttl)
- 上下文：[`od-context-v9.jsonld`](od-context-v9.jsonld)
- 规范文档：[`ontology_modeling_framework_v9.md` § 11](ontology_modeling_framework_v9.md#十一jsonld-序列化约定)
- MetaSkill 步骤 12 调用：[`../../SKILL.md` § 五](../../SKILL.md#五tool_call-实现)
- ontology-modeler 子 Skill：[`../SKILL.md` § 九 与 MetaSkill 的衔接](../SKILL.md#九与-metaskill-的衔接)
- 工具链：[`../scripts/README.md`](../scripts/README.md)
- 漂移检测 cron：[`.github/workflows/drift-check.yml`](../../../.github/workflows/drift-check.yml)（Task 9 产出）
- 阶段 5.5 收尾报告：[`docs/superpowers/specs/2026-09-01-stage55-report.md`](../../../docs/superpowers/specs/2026-09-01-stage55-report.md)（Task 12 输出，本任务时未生成）

### 上游 spec

- [YAML → JSON-LD 设计 spec § 三 双轨制策略](../../../docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md#三总体方案分层治理--双轨制)
- [spec § 阶段 2 / 3 / 5 / 6](../../../docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md#七阶段划分)（阶段 2/3/5 定义 ValidateJsonLdTool 的功能需求，阶段 6 是统一收尾）
- [spec § 九 AOT 风险](../../../docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md#九风险与权衡)
- [spec § 十一 后续步骤](../../../docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md#十一后续步骤)

### openclaw.net 仓库（参考实现）

- [`ValidateYamlReferencesTool.cs`](E:/GitHub/openclaw.net/src/OpenClaw.Agent/Tools/ValidateYamlReferencesTool.cs)（模板参考）
- [`ITool.cs`](E:/GitHub/openclaw.net/src/OpenClaw.Core/Abstractions/ITool.cs)（接口定义）
- [`OpenClawToolExecutor.cs:207`](E:/GitHub/openclaw.net/src/OpenClaw.Agent/OpenClawToolExecutor.cs#L207)（工具分发点）

### SDD 流程文档

- 实施计划：[`docs/superpowers/plans/2026-09-01-yaml-to-jsonld-impl.md`](../../../docs/superpowers/plans/2026-09-01-yaml-to-jsonld-impl.md)
- Task 11 brief：[`.superpowers/sdd/2026-09-01-yaml-to-jsonld-impl/task-11-brief.md`](../../../.superpowers/sdd/2026-09-01-yaml-to-jsonld-impl/task-11-brief.md)
- Task 11 报告：[`.superpowers/sdd/2026-09-01-yaml-to-jsonld-impl/task-11-report.md`](../../../.superpowers/sdd/2026-09-01-yaml-to-jsonld-impl/task-11-report.md)
- Task 9 cron 漂移：[`.superpowers/sdd/2026-09-01-yaml-to-jsonld-impl/task-9-brief.md`](../../../.superpowers/sdd/2026-09-01-yaml-to-jsonld-impl/task-9-brief.md)
- Task 12 验收（AC5 引用本工具）：[`.superpowers/sdd/2026-09-01-yaml-to-jsonld-impl/task-12-brief.md`](../../../.superpowers/sdd/2026-09-01-yaml-to-jsonld-impl/task-12-brief.md)

---

## 七、当前状态

- [x] **本仓库**：本文档已落地（Task 11 唯一产物）
- [ ] **openclaw.net**：`ValidateJsonLdTool.cs` 待 PR（**不在本工作树实施**）
- [x] **本仓库 MetaSkill SKILL.md**：步骤 12 已改为 `skill_exec → model-validator`（Python 门禁，见 § 四）；阶段 6 的 `validate_json_ld` 步骤待加
- [ ] **Task 12 AC5**：跨仓库回归测试，待 openclaw.net 端 PR 合入后跑现有 YAML 测试不破（`ValidateYamlReferencesTool.cs` 的 6-check 单测不受本仓库变更影响）
