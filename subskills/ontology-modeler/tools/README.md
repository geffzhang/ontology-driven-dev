# ontology-modeler / tools

本目录存放 ontology-modeler 子 Skill 的验证与转换工具。**全部为 PoC/阶段工具**，最终集成由各阶段任务实施（见 [spec § 五 路线图](../../../../docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md)）。

## 工具清单

| 工具 | 角色 | 输入 | 输出 |
| --- |---| --- |---|
| `yaml2m6jsonld.py` | M6 YAML → JSON-LD 转换器（meta: 词表） | `m6-flow-model.yaml` | `m6-flow-model.jsonld` |
| `yaml2od_jsonld.py` | M1/M5/M7 YAML → JSON-LD 转换器（od: 词表） | `m{1,5,7}-*-model.yaml` | `m{1,5,7}-*-model.jsonld` |
| `validate_m6jsonld.py` | M6 JSON-LD 验证（单文件） | `m6-flow-model.jsonld` | exit 0/1 + 行输出 |
| `validate_od_jsonld.py` | M1/M5/M7 JSON-LD 验证（多文件） | `m{1,5,7}-*-model.jsonld` | exit 0/1 + 行输出 |
| `validate.py` | **统一入口**（本目录核心） | 目录 / 文件 | text 或 json + exit 0/1/2 |
| `shacl/m6_flow_shape.ttl` | M6 FlowShape（12 步上限） | — | SHACL 形状 |
| `shacl/m1_aggregate_shape.ttl` | M1 AggregateRoot/Association/数据字典形状 | — | SHACL 形状 |
| `shacl/m5_actor_shape.ttl` | M5 Actor/Role/Permission 形状 | — | SHACL 形状 |
| `shacl/m7_report_shape.ttl` | M7 Report/SourceObject 形状 | — | SHACL 形状 |
| `shacl/run_shacl.py` | pyshacl 校验器 | data + shape | conforms bool + violations |
| `sparql_queries.py` | **跨文件 SPARQL 查询演示** | reference-example/*.jsonld | 表格结果 |

## validate.py 用法

```bash
# 默认 text 输出（聚合）
python tools/validate.py reference-example/

# JSON 输出（agent / IDE 友好）
python tools/validate.py reference-example/ --format json | jq '.[] | {path, passed}'

# 把 SKIPPED（YAML）也当失败处理
python tools/validate.py reference-example/ --strict

# 单文件验证
python tools/validate.py reference-example/m6-flow-model.jsonld
```

### 退出码

| Code | 含义 |
| --- |---|
| 0 | 全部 JSON-LD 通过；YAML 被 SKIPPED（除非 --strict） |
| 1 | 至少一个 JSON-LD 验证失败 |
| 2 | 配置错误（路径不存在 / --strict 下有 SKIPPED） |

### 路由逻辑

```text
file.suffix
  ├─ .jsonld  →  read @context IRI
  │   ├─ "https://openclaw.dev/meta/v1#"           → validate_m6jsonld.py
  │   ├─ "https://ontology.ontology-driven.dev/v9#" → validate_od_jsonld.py
  │   └─ 其他                                       → FAIL "无法识别 vocab"
  ├─ .yaml / .yml  →  SKIPPED（不在本 Skill 职责）
  └─ 其他          →  忽略
```

## 与 OpenClaw ValidateYamlReferencesTool 的关系

`ValidateYamlReferencesTool.cs`（[OpenClaw.Agent.Tools](../../../../../../../GitHub/openclaw.net/src/OpenClaw.Agent/Tools/ValidateYamlReferencesTool.cs)）是 OpenClaw 运行时内置 ITool，**职责**：

- 校验 YAML 文件间的 `*Ref` 字段（`roleRef`、`behaviorRef`、`objectRef` 等）
- 由 MetaSkill step 12 通过 `tool: validate_yaml_references` 调度
- 实现跨文件 YAML 跨引用一致性

**`validate.py` 的职责**：

- 校验 JSON-LD 文件的 `od:` / `meta:` 词表结构
- 由 ontology-modeler 本地/CI 调用
- PoC 阶段；后续可由 ontology-modeler step 12 调用作为前置

**两者关系**：互补，不重叠。

| 维度 | `ValidateYamlReferencesTool` (C#) | `validate.py` (Python) |
| --- |---| --- |
| 验证对象 | YAML | JSON-LD |
| 词表 | 不绑定词表 | 绑定 od: / meta: 词表 IRI |
| 调度方 | OpenClaw 运行时（agent step） | 本地 CLI / CI |
| 仓库 | openclaw.net | ontology-driven-dev |

## 依赖

```bash
pip install pyyaml rdflib pyshacl
```

- `pyyaml` ≥ 6.0
- `rdflib` ≥ 7.0（内置 JSON-LD Processor）
- `pyshacl` ≥ 0.40（SHACL 校验）

## SHACL 用法

```bash
# M6 stepCount ≤ 12 校验
python tools/shacl/run_shacl.py reference-example/m6-flow-model.jsonld tools/shacl/m6_flow_shape.ttl

# M1 / M5 结构约束
python tools/shacl/run_shacl.py reference-example/m1-object-model.jsonld tools/shacl/m1_aggregate_shape.ttl
python tools/shacl/run_shacl.py reference-example/m5-actor-model.jsonld tools/shacl/m5_actor_shape.ttl

# M7 Report 约束（5 报表：LIST_QUERY / DETAIL_QUERY / STATISTICAL_QUERY / REPORT）
python tools/shacl/run_shacl.py reference-example/m7-report-model.jsonld tools/shacl/m7_report_shape.ttl

# M3 rule shape validation
# - 负面 fixture：混合实例（AGG-CONTRACT-001 通过 / AGG-CONTRACT-002 违反 Rule 2；AGG-RECEIPT-001 通过 / AGG-RECEIPT-002 违反 Rule 7）→ 期望 exit 1，列出 2 条 SPARQL violation
python tools/shacl/run_shacl.py reference-example/m3-fixture.jsonld reference-example/m3-rule-model.shacl.ttl

# - 正面 fixture：仅含合规实例（AGG-CONTRACT-001 + AGG-RECEIPT-001）→ 期望 exit 0，conforms true
python tools/shacl/run_shacl.py reference-example/m3-fixture-positive.jsonld reference-example/m3-rule-model.shacl.ttl

# JSON 格式输出（便于 CI 解析）
python tools/shacl/run_shacl.py <data> <shape> --format json
```

### M3 fixture 说明

| Fixture | 内容 | 覆盖规则 | 期望结果 |
| --- | --- | --- | --- |
| `m3-fixture.jsonld` | AGG-CONTRACT-001（合规）+ AGG-CONTRACT-002（违反 Rule 2 status=草稿）+ AGG-RECEIPT-001（合规）+ AGG-RECEIPT-002（违反 Rule 7 validReceiptCount=0） | Rule 1, 2, 7 | exit 1，2 violation |
| `m3-fixture-positive.jsonld` | AGG-CONTRACT-001（合规）+ AGG-RECEIPT-001（合规） | Rule 1, 2, 7 | exit 0 conforms |

**关于 3/13 规则**：M3-A 仅把 3 条单实体规则（RULE-CONTRACT-APPROVAL-LEVEL / RULE-CONTRACT-INVOICE-ELIGIBLE / RULE-INVOICE-VOID-ELIGIBLE）翻译成可执行的 `sh:sparql`；其余 10 条混合实体规则（如 RULE-PAYSTAGE-REMAIN-QUOTA 等）按设计降级，仅产出 `rdfs:comment` + `sh:property` 形状，不参与本轮 SPARQL 校验。

## SPARQL 查询演示

```bash
# 列出 5 个可用查询
python tools/sparql_queries.py --list

# 跑单个
python tools/sparql_queries.py --query Q1

# 跑全部
python tools/sparql_queries.py --all
```

### 5 个查询

| ID | 跨文件 | 答案 |
| --- |---| --- |
| Q1 | M6 + M5 + M2 | M6 step 用到的 role + behavior（14 行） |
| Q2 | M7 → M1 → 字典 | REP-CONTRACT-LIST 关联的所有字典项（3 行） |
| Q3 | M5 + M2 | ACTOR-SALES 持有的 8 个 permission |
| Q4 | M6 | step kind 分布统计（31 步） |
| Q5 | M6 | 4 个 flow 的 GATEWAY routes（16 行） |

## 当前 PoC 状态

| 验证器 / 工具 | 黄金范例 | 状态 |
| --- |---| --- |
| `validate_m6jsonld.py` | 4 flows | ✅ PASS |
| `validate_od_jsonld.py` | M1=23 / M5=39 / M7=5 节点 | ✅ PASS |
| `validate.py` 统一入口 | 4 jsonld + 7 yaml | ✅ PASS（exit 0） |
| `shacl/run_shacl.py` M6 | stepCount ≤ 12 | ✅ conforms |
| `shacl/run_shacl.py` M1 | 聚合/关联/字典约束 | ✅ conforms |
| `shacl/run_shacl.py` M5 | 角色/权限约束 | ✅ conforms |
| `shacl/run_shacl.py` M7 | Report/SourceObject 约束（5 报表：4 query 类型 + primary 唯一） | ✅ conforms |
| `shacl/run_shacl.py` M3 | M3 SHACL: 3/13 rules translated cleanly (single-entity Contract); 10/13 mixed-entity rules emit rdfs:comment + property shapes only (degraded by design) | ✅ mixed + positive fixtures conform/violate as expected |
| `sparql_queries.py` Q1-Q5 | 5 跨文件查询 | ✅ 全部返回结果 |

## 后续路线（来自 spec）

| 阶段 | 任务 |
| --- |---|
| 5 | `pyshacl` SHACL 校验集成；补全 `od:DictionaryType.items[]` / `od:Report.joins` / 双向 Actor-Role 引用 |
| 6 | 把 `validate_od_jsonld.py` + `validate_m6jsonld.py` 整合到 ontology-modeler 的内置 step（本目录） |

详细见 [2026-09-01-yaml-to-jsonld-design.md § 五](../../../../docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md)。
