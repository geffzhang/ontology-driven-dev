---
name: ontology-modeler
description: |
  按 models 列表生成对应本体 YAML（单一事实来源），并同步派生 JSON-LD / SHACL（双轨制），依据 ontology_modeling_framework_v9 规范（含 §11 JSON-LD 序列化协议）。
  输入参数（由 MetaSkill 通过 with + Jinja 注入）：
    - models (array, 必填): ["M1","M5"] / ["M2","M3","M7"] / ["M5-perm","M6","MU"]
    - domain (string, 必填): 业务域中文名
    - baseline_doc (string, 必填): 需求规格说明书绝对路径
    - prior_models (object, 可选): {模型名: yaml路径} 映射，用于跨模型引用
    - write_manifest (boolean, 可选): 仅当 models 含 "MU" 时传 true，触发 manifest.json / manifest.jsonld 写出
  输出契约：JSON 对象，含 model_files（YAML 路径）、jsonld_files（JSON-LD/SHACL 派生路径）映射、generation_log 数组；write_manifest=true 时附加 manifest_path。
  触发词：本体建模、模型生成、YAML 生成、JSON-LD、双轨制、SHACL、漂移检测、七模型、manifest。
---

# 本体建模执行器（ontology-modeler）

被 [`ontology-driven-dev`](../SKILL.md) MetaSkill 步骤 9/10/11 调用。运行在子 Agent 中，**只读访问规范文档，必写权限用于产出 YAML 及其 JSON-LD / SHACL 派生文件**。

> **路径约定**：本 SKILL.md 位于 `subskills/ontology-modeler/`，子目录 `references/` 与 `reference-example/` 即本 Skill 自带的规范文档与黄金范例；输出 YAML 写至项目根 `yaml/` 目录（`../../yaml/`，相对本 SKILL.md），JSON-LD / SHACL 派生文件与对应 YAML **同目录同命名**（仅扩展名不同）。

## 一、唯一依据

`references/ontology_modeling_framework_v9.md`（七模型元文件规范 + 各模型 YAML 模板 + § 十一 JSON-LD 序列化协议 + §11.6 M2 双层约定）。

执行前**必须**先 Read 此文件，定位到 `models` 参数中每个模型对应的章节；涉及 JSON-LD 派生时同时 Read § 十一。

## 二、模型调用映射

| MetaSkill 步骤 | `models` 参数 | 产出 YAML | 模型语义 |
|---|---|---|---|
| 9 (`p2_objects_roles`) | `["M1", "M5"]` | `yaml/m1-object-model.yaml`、`yaml/m5-actor-model.yaml` | 对象 + 角色主体 |
| 10 (`p2_behaviors_rules`) | `["M2", "M3", "M7"]` | `yaml/m2-behavior-model.yaml`、`yaml/m3-rule-model.yaml`、`yaml/m7-report-model.yaml` | 行为 + 规则 + 查询 |
| 11 (`p2_flows_ui`) | `["M5-perm", "M6", "MU"]` | `yaml/m5-actor-model.yaml`（追加权限块）、`yaml/m6-flow-model.yaml`、`yaml/mu-ui-model.yaml` | 权限 + 流程 + UI |

> **注意**：步骤 11 的 `M5-perm` 与步骤 9 的 `M5` 写入同一文件，权限块追加在角色块之后（不覆盖）。
> **命名提示**：V9 规范（§ 一）与黄金范例的权威文件名为 `m5-actor` / `m6-flow` / `m7-report`；既往文档中出现的 `m5-role` / `m6-process` / `m7-query` 为历史别名，指向同一模型。

### 双轨制转换表（YAML → JSON-LD / SHACL）

YAML 是单一事实来源；派生文件一律经 `tools/` 转换器生成。本批次每个模型产出 YAML 后，立即按其行执行派生（见第四节步骤 7）：

| 模型 | 转换器 | 词表 | 派生产出 |
|---|---|---|---|
| M1 | `tools/yaml2od_jsonld.py` | od: | `<同名>.jsonld` |
| M5 | `tools/yaml2od_jsonld.py` | od: | `<同名>.jsonld` |
| M7 | `tools/yaml2od_jsonld.py` | od: | `<同名>.jsonld` |
| M2 | `tools/yaml2m2jsonld.py` | od: | `<同名>.jsonld`（仅元数据层；控制流留 YAML，见 §11.6 双层约定） |
| M3 | `tools/yaml2m3shacl.py` | sh: | `<同名>.shacl.ttl` |
| M6 | `tools/yaml2m6jsonld.py` | meta: | `<同名>.jsonld`（复用 OpenClaw MetaSkill 词表） |
| MU | — 不迁移（按设计） | — | 仅 YAML；manifest.jsonld 中标记 `od:notMigrated: true` |

## 三、输入约定

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `models` | array[string] | 是 | 见上表三种取值之一 |
| `domain` | string | 是 | 业务域中文名（写 YAML 头部 `metadata.domain`） |
| `baseline_doc` | string (path) | 是 | 需求规格说明书绝对路径 |
| `prior_models` | object | 步骤 10/11 必填 | `{M1: "...yaml", M5: "...yaml", ...}` |
| `write_manifest` | boolean | 步骤 11 传 `true` | 是否同步写 manifest.json + manifest.jsonld |

### `prior_models` 引用关系表

| 当前模型 | 引用上游模型 | YAML 字段 |
|---|---|---|
| M5（角色） | M1 对象 | `M5.role[*].objectRef → M1.object.id` |
| M5-perm（权限） | M5 角色 + M2 行为 | `M5.permission[*].roleRef / behaviorRef` |
| M2（行为） | M1 对象 + M3 规则 + M5 角色 | `M2.behavior[*].objectRef / ruleRef / roleRef` |
| M3（规则） | M1 对象 | `M3.rule[*].conditionObject / conclusionObject` |
| M6（流程） | M1/M2/M3/M5 全部 | `M6.flow[*].roleRef / behaviorRef / subFlowRef / ruleRef` |
| M7（查询） | M2 QUERY 行为 | `M7.report[*].behaviorRef ↔ M2.queryReportRef` |
| MU（UI） | M2 USER_ACTION 行为 | `MU.screen[*].operation[*].behaviorRef` |

## 四、执行流程

### 步骤 1：加载规范

```
Read references/ontology_modeling_framework_v9.md
定位到 models 中每个模型对应的章节，记录：
- YAML 字段定义
- 必填字段清单
- 引用字段格式（ref 语法）
```

### 步骤 2：加载基线

```
Read baseline_doc（即需求规格说明书）
重点提取：
- 附录 C 七模型建模输入基线（确定性输入）
- 阶段一各 confirm 的 stage_X_modification（如有）
- 业务域中文名（与 domain 参数交叉验证）
```

### 步骤 3：加载上游模型

```
for model_name, path in prior_models.items():
    Read path
    提取 ID 字典（model: id 列表）用于构造本模型的 ref 字段
```

### 步骤 4：生成 YAML

按 V9 规范逐个模型生成 YAML 内容。每个 YAML 必须：

1. **结构对齐规范**：字段顺序、嵌套层级、`required`/`optional` 与规范一致
2. **ref 字段真实存在**：所有 `*Ref` 字段值必须在 `prior_models` 或本批次 `models` 产出的 ID 字典中查得到
3. **跨模型一致性自检**：
   - M2 USER_ACTION 行为必须在 MU 中至少有一个 operation 引用（**前瞻性**：即使 MU 在下一批次，也必须留好 hook）
   - M7 行为必须在 M2 中存在对应 QUERY 行为
   - M6 的所有 ref 字段必须存在
4. **域元数据**：`metadata.domain = domain`、`metadata.generated_by = "ontology-driven-dev MetaSkill"`

### 步骤 5：写盘

```
mkdir -p ../../yaml/  （首次时）

for model_name in models:
    yaml_path = ../../yaml/<m{N}-<name>-model.yaml>
    if file exists and model == "M5-perm":
        # M5-perm 追加权限块，不覆盖
        Read yaml_path
        append permission block to existing YAML
        Write yaml_path (overwrite with merged content)
    else:
        Write yaml_path (new file)
```

### 步骤 6：manifest（仅当 `write_manifest == true`）

写盘路径：`yaml/manifest.json`：

```json
{
  "domain": "<domain>",
  "generated_at": "<ISO8601 时间戳>",
  "generated_by": "ontology-driven-dev MetaSkill",
  "models": {
    "M1": "yaml/m1-object-model.yaml",
    "M2": "yaml/m2-behavior-model.yaml",
    "M3": "yaml/m3-rule-model.yaml",
    "M5": "yaml/m5-actor-model.yaml",
    "M6": "yaml/m6-flow-model.yaml",
    "M7": "yaml/m7-report-model.yaml",
    "MU": "yaml/mu-ui-model.yaml"
  },
  "checksum": "<对 7 个 YAML 文件内容做 SHA-256>"
}
```

**并**用转换器同步写出 JSON-LD 顶层入口：

```bash
python tools/yaml2manifest.py ../../yaml ../../yaml/manifest.jsonld
```

- `manifest.json`：保留，供 OpenClaw 步骤 12 `validate_yaml_references` 回归校验（跨仓库 AC5）。
- `manifest.jsonld`：7 条 `od:ModelManifestEntry`，每条含 `od:yamlSource` / `od:jsonLdSource`；MU 条目为 `od:notMigrated: true`。

### 步骤 7：派生 JSON-LD / SHACL（双轨制，本批次每个模型必做）

JSON-LD / SHACL 一律由转换器从 YAML 派生，**不得手写**。以下命令以本 SKILL.md 所在目录为工作目录：

```bash
python tools/yaml2od_jsonld.py ../../yaml/m1-object-model.yaml      # → m1-object-model.jsonld
python tools/yaml2od_jsonld.py ../../yaml/m5-actor-model.yaml       # → m5-actor-model.jsonld
python tools/yaml2m2jsonld.py   ../../yaml/m2-behavior-model.yaml   # → m2-behavior-model.jsonld
python tools/yaml2m3shacl.py    ../../yaml/m3-rule-model.yaml       # → m3-rule-model.shacl.ttl
python tools/yaml2m6jsonld.py   ../../yaml/m6-flow-model.yaml       # → m6-flow-model.jsonld
python tools/yaml2od_jsonld.py  ../../yaml/m7-report-model.yaml     # → m7-report-model.jsonld
```

派生文件与对应 YAML **同目录同命名**（仅扩展名不同）。要点：

- M2 只迁元数据层：JSON-LD 中每个 behavior 保留 `od:yamlPointer` 反向指针，控制流字段留在 YAML（§11.6 双层约定）。
- M3 产出 SHACL Turtle：`sh:property` 按 inputParam 逐个生成，业务 DSL 经 5 模式翻译为合法 SPARQL；混合实体规则优雅降级为 `rdfs:comment`（转换器会打印 stderr 警告）。
- MU 不派生（按设计）。

### 步骤 8：一致性自检（交付门禁）

```bash
python tools/validate.py ../../yaml/ --format text   # 统一验证：0 failed 才可交付
python tools/drift_check.py ../../yaml/              # YAML ↔ JSON-LD ID 集漂移检测
```

- `validate.py` 覆盖：YAML 结构校验、JSON-LD rdflib 解析、M2 YAML↔JSON-LD 双向对齐、M2 `od:yamlPointer` 反向链接解析、manifest 路由。
- `drift_check.py` 报告任何只存在于单边格式的 ID；漂移非零 = 本步骤失败，回步骤 4 修正 YAML → 重跑步骤 7 转换器 → 复检。
- 两个命令的结果记入输出契约的 `validation` 字段（见下节）。

## 五、输出契约

```json
{
  "model_files": {
    "M1": "yaml/m1-object-model.yaml",
    "M5": "yaml/m5-actor-model.yaml"
  },
  "jsonld_files": {
    "M1": "yaml/m1-object-model.jsonld",
    "M5": "yaml/m5-actor-model.jsonld"
  },
  "generation_log": [
    "M1: 12 objects, 8 relationships",
    "M5: 4 roles, 0 permissions (M5-perm 后续追加)"
  ],
  "validation": {
    "validate_py": "9 passed, 0 failed, 7 skipped",
    "drift": "0 drift"
  },
  "manifest_path": "yaml/manifest.json"   // 仅 write_manifest=true 时存在
}
```

### 字段细则

| 字段 | 必填 | 类型 | 约束 |
|---|---|---|---|
| `model_files` | 是 | object[string, string] | 每个产出的模型 → YAML 相对路径（上游 MetaSkill 的 `prior_models` 依赖此字段，**不可**改为对象） |
| `jsonld_files` | 是 | object[string, string] | 每个迁移模型的派生路径（`.jsonld`；M3 为 `.shacl.ttl`）；MU 无此条目 |
| `generation_log` | 是 | string[] | 每行一条生成摘要，包含对象/规则/角色计数 |
| `validation` | 是 | object | `validate_py` 与 `drift` 汇总；任一 failed / 漂移非零即抛错，不得交付 |
| `manifest_path` | `write_manifest=true` 时必填 | string | manifest.json 相对路径（同目录另有 manifest.jsonld） |

## 六、行为纪律

1. **未读 V9 规范前不得生成**：第一步必须是 Read `references/ontology_modeling_framework_v9.md`。
2. **不得扩展 `models` 范围**：参数给 `["M1", "M5"]` 时绝不产出 M2/M3/M6/M7/MU。
3. **M5-perm 与 M5 同文件**：步骤 11 收到 `M5-perm` 时，必须先 Read 已有 `yaml/m5-actor-model.yaml`，再追加 permission 块，不得覆盖角色块。
4. **跨模型 ref 必须真实存在**：写盘前对所有 `*Ref` 字段做一次查表校验，缺失则抛错而非静默留空。
5. **M2 USER_ACTION 必须留 MU hook**：即使本批次不产 MU，也要为每个 USER_ACTION 行为预留 `muHook: "<expected-mu-screen-id>"` 注释，步骤 11 据此生成 MU 时填实。
6. **JSON 输出无多余文字**：最终回复必须是合法 JSON，前后可空一行，但不得有 Markdown 代码块包裹。
7. **双轨成对交付**：每个迁移模型必须 YAML + JSON-LD（M3 为 SHACL TTL）成对产出；只产其一视为任务失败。MU 例外（按设计不迁移）。
8. **JSON-LD 只能派生，不得手写**：一律经 `tools/` 转换器生成；需要新字段时改转换器，不改 JSON-LD 输出文件。
9. **0 failed / 0 drift 才可交付**：`validate.py` 与 `drift_check.py` 均须通过；失败时抛对应错误码（见第八节），不得静默降级为仅 YAML 交付。

## 七、工具使用清单

| 工具 | 用途 | 是否必需 |
|---|---|---|
| Read | 读 V9 规范、读基线文档、读上游 YAML | ✅ 必需 |
| Write | 写 YAML 文件、写 manifest.json | ✅ 必需 |
| Bash（mkdir）| 首次创建 yaml/ 目录 | ✅ 必需（仅步骤 9） |
| Bash（python）| 运行 `tools/` 转换器（yaml2od_jsonld / yaml2m2jsonld / yaml2m3shacl / yaml2m6jsonld / yaml2manifest） | ✅ 必需（步骤 7） |
| Bash（python）| 运行 `tools/validate.py` + `tools/drift_check.py` 自检 | ✅ 必需（步骤 8） |
| Bash（python）| `tools/shacl/run_shacl.py <data> <shape>`（pyshacl 验证，可选深度自检） | 可选 |
| Glob | 兜底查找 yaml/ 已有文件 | 可选 |
| Grep | 在上游 YAML 中查 ID | 可选 |

> MetaSkill 的 `agent` kind 默认赋予完整工具访问。子 Skill 如需缩窄，可由 MetaSkill 在 `with.tool_allowlist` 字段限定，本 Skill 当前不强制。

## 八、失败模式与处理

| 失败模式 | 处理 |
|---|---|
| `baseline_doc` 不存在 | 抛错 `baseline_doc_not_found`，由 MetaSkill retry 策略处理 |
| `prior_models` 中某模型文件缺失 | 抛错 `prior_model_missing: <model_name>`，**不可** 静默用空字典继续 |
| 同一 ref 字段在不同 YAML 中不一致 | 抛错 `ref_inconsistency: <model>.<field>=<value> vs <other>.<field>=<value>` |
| V9 规范读不到 | 抛错 `framework_doc_not_found: references/ontology_modeling_framework_v9.md` |
| `drift_check.py` 报告单边 ID | 抛错 `drift_detected: <id>`；回步骤 4 修正 YAML → 重跑转换器 → 复检 |
| `validate.py` 报 SHACL / 对齐失败 | 抛错 `shacl_violation: <shape>` 或 `alignment_failed: <model>`；修正 YAML 后重派生 |
| rdflib 无法解析派生的 JSON-LD | 抛错 `jsonld_parse_failed: <file>`；修复转换器而非手改 JSON-LD |

## 九、与 MetaSkill 的衔接

```
MetaSkill 步骤 9  (agent → ontology-modeler, models=[M1,M5])
  ↓ with: { models, baseline_doc, prior_models={} }
  ↓ 产出 M1+M5（YAML + JSON-LD），model_files / jsonld_files 注入 outputs.p2_objects_roles

MetaSkill 步骤 10 (agent → ontology-modeler, models=[M2,M3,M7])
  ↓ with: { prior_models={M1: "...", M5: "..."} }
  ↓ 产出 M2+M3+M7（M3 为 SHACL TTL；M2 为元数据层 JSON-LD）

MetaSkill 步骤 11 (agent → ontology-modeler, models=[M5-perm,M6,MU], write_manifest=true)
  ↓ with: { prior_models={M1, M2, M3, M5-actor, M7} }
  ↓ 追加 M5 权限块 + 产出 M6+MU + 写 manifest.json + manifest.jsonld

MetaSkill 步骤 12 (tool_call → validate_yaml_references)
  ↓ 读 yaml/manifest.json 定位所有 YAML
  ↓ 执行 6 条跨引用校验
  ↓ 失败则终止 DAG；全部通过则 final_text_mode 返回
```

## 十、参考

- 上游 MetaSkill：[`../SKILL.md`](../SKILL.md)
- 方法论规范：[`references/ontology_modeling_framework_v9.md`](references/ontology_modeling_framework_v9.md)（§ 十一 JSON-LD 序列化协议；§11.6 M2 双层约定）
- 词表：[`references/od-vocabulary-v9.ttl`](references/od-vocabulary-v9.ttl) + [`references/od-context-v9.jsonld`](references/od-context-v9.jsonld)（冻结的 od: 词表 v9）
- 黄金范例：[`reference-example/`](reference-example/)（7 个模型 YAML + 5 份 JSON-LD + m3 SHACL + manifest.json + manifest.jsonld，平铺目录）
- 转换与校验工具：[`tools/`](tools/)（yaml2manifest / yaml2od_jsonld / yaml2m2jsonld / yaml2m3shacl / yaml2m6jsonld / validate / drift_check / sparql_queries；SHACL shapes 在 [`tools/shacl/`](tools/shacl/)）
- 漂移守护 CI：[`../../.github/workflows/drift-check.yml`](../../.github/workflows/drift-check.yml)（每周一 cron：validate + drift + SHACL + SPARQL smoke）
- 跨仓库集成路线：[`references/openclaw-integration.md`](references/openclaw-integration.md)（OpenClaw `ValidateJsonLdTool.cs` 改造路径 + MetaSkill step 12 wiring）
- 跨引用校验工具：[`ValidateYamlReferencesTool.cs`](E:/GitHub/openclaw.net/src/OpenClaw.Agent/Tools/ValidateYamlReferencesTool.cs)（OpenClaw 内置 ITool；步骤 12 通过 `tool: validate_yaml_references` 调用，OpenClaw 运行时按 `ITool.Name` 字面量分发）
