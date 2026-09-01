# ontology-modeler / scripts

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
| `merge_rdf.py` | **并图打包**：逐模型 RDF → 单图（新增产物） | 目录内派生 `.jsonld` + `.shacl.ttl` | `<dir>/ontology-merged.ttl` |

## validate.py 用法

```bash
# 默认 text 输出（聚合）
python scripts/validate.py reference-example/

# JSON 输出（agent / IDE 友好）
python scripts/validate.py reference-example/ --format json | jq '.[] | {path, passed}'

# 把 SKIPPED（YAML）也当失败处理
python scripts/validate.py reference-example/ --strict

# 单文件验证
python scripts/validate.py reference-example/m6-flow-model.jsonld
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

## 与 model-validator 门禁的关系

跨文件 YAML 引用校验（6 条）由 [`subskills/model-validator/`](../../model-validator/) 承担——MetaSkill 步骤 12 经 `skill_exec` 调用其 `scripts/validate_yaml_refs.py`，该脚本又经子进程复用本目录的 `validate.py` / `shacl/run_shacl.py` / `drift_check.py` 完成 JSON-LD 门禁（3 条）。

| 维度 | model-validator `validate_yaml_refs.py` | 本目录 `validate.py` 等 |
| --- | --- | --- |
| 验证对象 | 跨文件 YAML 引用（6 条自研）+ 编排 | JSON-LD 解析 / 词表路由 / SHACL / 漂移 |
| 词表 | 不绑定词表 | 绑定 od: / meta: 词表 IRI |
| 调度方 | MetaSkill 步骤 12（skill_exec）/ CI | model-validator 子进程 / CI |

两者互补，不重叠；本目录脚本不校验 YAML（`validate.py` 路由为 SKIP）。

## 合并产物（ontology-merged.ttl）

```bash
# 逐模型派生文件齐备后，并成单一 Turtle 图（打包产物）
python scripts/merge_rdf.py reference-example/            # → reference-example/ontology-merged.ttl
python scripts/merge_rdf.py reference-example/ --format json
```

- **流程中必做**：ontology-modeler 步骤 7 在六份派生齐备的批次**必须**打包（见 [`SKILL.md`](../SKILL.md) 步骤 7 / 行为纪律 10），输出契约报告 `merged_rdf`。
- **并图 = 新增产物，不替代**：逐模型 JSON-LD / SHACL、manifest.jsonld 全部原样保留；门禁（`validate.py` / 步骤 12 的 9 条检查）不消费该文件，`validate.py` 收集目标时天然忽略 `.ttl`。
- **源清单固定**：m1/m2/m3/m5/m6/m7 六个派生文件；`manifest.jsonld`（索引元数据）与 `m3-*-fixture.jsonld`（测试数据）不并入。缺哪个跳过哪个，不报错。
- **自包含 SHACL bundle**：M3 的形状与其余模型的数据在同一图，拿 merged 文件既当数据图又当形状图可直接 `pyshacl` 校验。
- 退出码：0 成功；2 目录不存在或无任何可并源文件。黄金范例为 1872 triples，重跑输出确定（CI 有 diff 校验）。

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
python scripts/shacl/run_shacl.py reference-example/m6-flow-model.jsonld scripts/shacl/m6_flow_shape.ttl

# M1 / M5 结构约束
python scripts/shacl/run_shacl.py reference-example/m1-object-model.jsonld scripts/shacl/m1_aggregate_shape.ttl
python scripts/shacl/run_shacl.py reference-example/m5-actor-model.jsonld scripts/shacl/m5_actor_shape.ttl

# M7 Report 约束（5 报表：LIST_QUERY / DETAIL_QUERY / STATISTICAL_QUERY / REPORT）
python scripts/shacl/run_shacl.py reference-example/m7-report-model.jsonld scripts/shacl/m7_report_shape.ttl

# M3 rule shape validation
# - 负面 fixture：混合实例（AGG-CONTRACT-001 通过 / AGG-CONTRACT-002 违反 Rule 2；AGG-RECEIPT-001 通过 / AGG-RECEIPT-002 违反 Rule 7）→ 期望 exit 1，列出 2 条 SPARQL violation
python scripts/shacl/run_shacl.py reference-example/m3-fixture.jsonld reference-example/m3-rule-model.shacl.ttl

# - 正面 fixture：仅含合规实例（AGG-CONTRACT-001 + AGG-RECEIPT-001）→ 期望 exit 0，conforms true
python scripts/shacl/run_shacl.py reference-example/m3-fixture-positive.jsonld reference-example/m3-rule-model.shacl.ttl

# JSON 格式输出（便于 CI 解析）
python scripts/shacl/run_shacl.py <data> <shape> --format json
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
python scripts/sparql_queries.py --list

# 跑单个
python scripts/sparql_queries.py --query Q1

# 跑全部
python scripts/sparql_queries.py --all
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
| `merge_rdf.py` | 6 源并图 → ontology-merged.ttl | ✅ 1872 triples，回读一致，自校验 conforms |

## 后续路线（来自 spec）

| 阶段 | 任务 |
| --- |---|
| 5 | `pyshacl` SHACL 校验集成；补全 `od:DictionaryType.items[]` / `od:Report.joins` / 双向 Actor-Role 引用 |
| 6 | 把 `validate_od_jsonld.py` + `validate_m6jsonld.py` 整合到 ontology-modeler 的内置 step（本目录） | 
