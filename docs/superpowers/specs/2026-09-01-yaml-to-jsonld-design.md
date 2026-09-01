---
title: 本体模型 YAML → JSON-LD 迁移设计
status: draft
date: 2026-09-01
owner: ontology-driven-dev
related:
  - subskills/ontology-modeler/SKILL.md
  - subskills/ontology-modeler/references/ontology_modeling_framework_v9.md
  - SKILL.md
---

# 本体模型 YAML → JSON-LD 迁移设计

## 一、背景与动机

V9 框架当前以 YAML 作为七模型（M1/M2/M3/M5/M6/M7/MU）的唯一载体，配合 OpenClaw 内置的 `ValidateYamlReferencesTool` 完成跨引用校验。该方案在"人类可读 + 业务建模表达力"两个维度表现良好，但存在以下局限：

1. **缺乏语义互联能力**：模型 ID（如 `AGG-CONTRACT-001`）只是字符串，无法作为 URI 被外部 linked data 引用
2. **缺少形式化验证**：M1 不变量（invariants）与 M3 规则（refRules）的逻辑表达式仅以文本形式存在，无法被 SHACL/SPARQL 等标准工具验证
3. **与 MU v9.1 AI 原生方向不匹配**：v9.1 的 MU 模型已转向 A2UI / MCP App 等 AI Agent 原生交互，语义消费层在向"机器可消费"靠拢，但 M1-M7 仍停留在"人类可读"
4. **跨系统交换壁垒**：YAML 私有词表难以被 Protégé / Jena / SPARQL 生态消费

JSON-LD 作为 W3C 标准的链接数据序列化格式，是上述问题的标准答案。但**全量替换**会在 M2/MU 上损失表达力——本设计采用**分层治理**渐进迁移：

- **M1/M3/M5/M7** 走 JSON-LD（数据语义 + 形式化验证）；
- **M2** 走双层：元数据迁 JSON-LD，控制流留 YAML；
- **M6** 用 JSON-LD 表达，**复用 OpenClaw MetaSkill `composition.steps` 词表**（不造新词表，不生成 SKILL.md）；
- **MU** 保留 JSON（A2UI/MCP App 各自规范）。

## 二、目标与非目标

### 2.1 目标

- **G1**：M1 对象、M5 主体、M7 查询报表模型可输出为 JSON-LD，承载机器消费层
- **G2**：M3 规则可通过 SHACL 形状表达，获得形式化验证能力
- **G3**：M2 行为的元数据层迁 JSON-LD，控制流层（preconditions/postconditions/syncTriggers）保留 YAML 或专用 JSON
- **G4**：`manifest.json` 升级为 JSON-LD 顶层入口文档（`@context` + `@graph`）
- **G5**：`ValidateYamlReferencesTool` 增加 JSON-LD 校验通道（不替换 YAML 校验）
- **G6**：迁移过程不破坏 V9 现有表达力，M2/MU 仍可用 YAML 编辑与 review；M6 用 JSON-LD 表达 MetaSkill 语义，不生成 SKILL.md（OpenClaw 运行时仍按 YAML 路径调度）

### 2.2 非目标

- **N1**：不删除任何 YAML 文件——YAML 永远是"人读源"
- **N2**：M6 流程模型**不另造词表**，而是用 JSON-LD 复用 OpenClaw MetaSkill `composition.steps` 词表（详见 § 四）；**不生成 SKILL.md**——OpenClaw 运行时仍按 YAML 路径调度
- **N3**：MU UI 模型不迁 JSON-LD——A2UI/MCP App 各自规范已是 JSON，再包一层 JSON-LD 是噪声
- **N4**：本设计**不**引入 OWL 推理——若未来需要，本 spec 之外另行评估
- **N5**：本设计**不**替代 V9 规范本体——JSON-LD 是序列化约定，不是新框架

## 三、总体方案：分层治理 + 双轨制

七模型按"语义稳定性 × JSON-LD 适配度"两维分类：

| 模型 | 语义类别 | JSON-LD 适配度 | 迁移策略 |
|---|---|---|---|
| M1 对象 | 数据建模 | 高 | ✅ 全量迁 JSON-LD |
| M5 主体 | 角色 + 权限 | 高 | ✅ 全量迁 JSON-LD |
| M7 查询报表 | 绑 M2 行为 | 中 | ✅ 轻量迁（仅元数据） |
| M3 规则 | 条件-结论 | 中 | ✅ 用 SHACL 表达 |
| M2 行为 | 控制流 + 状态机 | 中低 | ⚠️ 双层：元数据迁 / 控制流留 YAML |
| M6 流程 | 端到端协同 / 审批流 | 🆕 高（MetaSkill 词表复用） | ✅ 用 JSON-LD 表达，复用 MetaSkill `composition.steps` 词表（详见 § 四） |
| MU UI | AI 原生交互 | 低 | ❌ 不迁，保留 JSON（A2UI/MCP App 各自规范） |

**核心原则**：JSON-LD 价值集中在"数据语义 + 跨系统链接"，不应强行覆盖"控制流 + 渲染"。**控制流语义通过复用 OpenClaw MetaSkill 词表 IRI 表达**——M6 JSON-LD 在 `@context` 引入 `https://openclaw.dev/meta/v1#`，复用 `meta:Step` / `meta:agent` / `meta:user_input` 等现成词表，**不另造词表，不生成 SKILL.md**。

## 四、M6 → MetaSkill 语义 JSON-LD 表达

M6 流程不需要新造 JSON-LD 词表，而是在 `@context` 中**复用 MetaSkill 词表 IRI**（`https://openclaw.dev/meta/v1#`，暂定），直接用 MetaSkill 现成谓词（`meta:Step` / `meta:agent` / `meta:user_input` / `meta:dependsOn` 等）表达端到端流。

**M6 输出是一份 JSON-LD 文件**，OpenClaw MetaSkill 运行时仍按原 YAML 路径调度，**不生成 SKILL.md**。这样既复用 MetaSkill 语义（统一理解），又保持 JSON-LD 表达力（机器消费）。

### 4.1 概念映射表（YAML → JSON-LD，复用 MetaSkill 词表）

| M6 YAML 概念 | M6 JSON-LD 表达（用 MetaSkill 词表） |
|---|---|
| 端到端流 `flow` | `@type: meta:Flow`，`meta:name` |
| 节点 `nodes[]` | `meta:hasStep` 数组 |
| 系统活动 `systemTask` | `@type: meta:Step` + `meta:kind: "agent"` + `meta:skill` |
| 人工任务 `userTask` | `@type: meta:Step` + `meta:kind: "user_input"` |
| 审批节点 `approvalNode` | `@type: meta:Step` + `meta:kind: "user_input"` + `meta:enum: [...]` |
| 排他网关 `exclusiveGateway` | `@type: meta:Step` + `meta:kind: "llm_classify"` + `meta:outputChoices` |
| 并行网关 `parallelGateway` | 多个 `meta:Step` 无 `meta:dependsOn` |
| 子流程 `subFlowRef` | `@type: meta:Step` + `meta:kind: "skill_exec"` + `meta:skill` |
| 同步顺序 `dependsOn` | `meta:dependsOn: [<step_id>]` |
| 条件 `when` | `meta:when: "<jinja expr>"` |
| 错误处理 | `meta:onFailure: <fallback_id>` |
| 失败跳过 | `meta:continueOnError: true` |
| 重试策略 | `meta:retry: { maxAttempts, backoffMs }` |
| 超时 | `meta:timeoutSeconds: <N>` |
| 角色引用 `roleRef` | `meta:permissionRef`（指向 M5 JSON-LD） |
| 行为引用 `behaviorRef` | `meta:skill`（指向 M2 JSON-LD） |
| 规则引用 `ruleRef` | `meta:toolArgs: { ruleRef: RULE-X }`（指向 M3 SHACL） |

### 4.2 黄金范例对照（YAML → JSON-LD with meta: 词表）

M6 YAML：

```yaml
flows:
  - id: FLOW-CONTRACT-APPROVAL
    name: 合同登记审批流
    nodes:
      - id: save_draft
        type: systemTask
        behaviorRef: Contract_SaveAsDraft
      - id: finance_approve
        type: approvalNode
        roleRef: ROLE-FINANCE-MANAGER
        choices: [approve, reject]
        dependsOn: [save_draft]
      - id: gm_approve
        type: approvalNode
        roleRef: ROLE-GENERAL-MANAGER
        condition: totalAmount > THRESHOLD
        dependsOn: [finance_approve]
```

M6 JSON-LD（**复用 MetaSkill 词表，不生成 SKILL.md**）：

```json
{
  "@context": {
    "@vocab": "https://openclaw.dev/meta/v1#",
    "meta": "https://openclaw.dev/meta/v1#",
    "od": "https://ontology.ontology-driven.dev/v9#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@id": "urn:od:contract-mgmt:M6:FLOW-CONTRACT-APPROVAL",
  "@type": "meta:Flow",
  "meta:name": "合同登记审批流",
  "meta:hasStep": [
    {
      "@id": "urn:od:contract-mgmt:M6:step-save-draft",
      "@type": "meta:Step",
      "meta:id": "save_draft",
      "meta:kind": "agent",
      "meta:skill": "urn:od:contract-mgmt:M2:Contract_SaveAsDraft"
    },
    {
      "@id": "urn:od:contract-mgmt:M6:step-finance-approve",
      "@type": "meta:Step",
      "meta:id": "finance_approve",
      "meta:kind": "user_input",
      "meta:permissionRef": "urn:od:contract-mgmt:M5:PERM-CONTRACT-APPROVE-FINANCE",
      "meta:enum": ["approve", "reject"],
      "meta:dependsOn": ["save_draft"]
    },
    {
      "@id": "urn:od:contract-mgmt:M6:step-gm-approve",
      "@type": "meta:Step",
      "meta:id": "gm_approve",
      "meta:kind": "user_input",
      "meta:permissionRef": "urn:od:contract-mgmt:M5:PERM-CONTRACT-APPROVE-GM",
      "meta:enum": ["approve", "reject"],
      "meta:dependsOn": ["finance_approve"],
      "meta:when": "outputs.finance_approve.decision == 'approve' AND inputs.totalAmount > THRESHOLD"
    }
  ]
}
```

### 4.3 与 ontology-driven-dev 自带的同构

ontology-driven-dev 本身就是 12 步 DAG MetaSkill，每个 p1/p2 步骤都用 `depends_on` 串接。M6 黄金范例应直接对照 ontology-driven-dev 的步骤结构编写——但**只复用其语义词表到 JSON-LD**，不复制其 SKILL.md。

### 4.4 12 步上限约束（SHACL 校验）

OpenClaw MetaSkill 规定单 MetaSkill **不超过 12 步**。该约束在 M6 JSON-LD 中以 SHACL 形状校验：

```turtle
meta:FlowShape a sh:NodeShape ;
  sh:targetClass meta:Flow ;
  sh:property [
    sh:path meta:hasStep ;
    sh:maxCount 12 ;
    sh:message "M6 flow 步骤数 ≤ 12，超出请拆分子流"@zh ] .
```

ontology-modeler 阶段 5 应在生成 M6 JSON-LD 后立即执行此 SHACL 校验，超出则 fail-fast。

### 4.5 落盘约定（单层 JSON-LD）

- **人读 YAML**：`yaml/m6-flow-model.yaml`（保留 V9 原 schema，供 review/编辑）
- **机读 JSON-LD**：`yaml/m6-flow-model.jsonld`（复用 MetaSkill 词表，机器消费）

**不生成 SKILL.md**。OpenClaw MetaSkill 运行时仍按 `yaml/m6-flow-model.yaml` 路径调度；JSON-LD 用于：

1. 跨系统 linked data 交换
2. SPARQL 查询（M6 流程与 M2/M5/M3 引用关系）
3. SHACL 验证（步骤数 ≤ 12、引用存在性等）

### 4.6 manifest 关联

manifest.jsonld 用 `od:m6JsonLdRef` 关联 YAML 与 JSON-LD：

```json
{
  "@id": "urn:od:contract-mgmt:M6",
  "@type": "od:M6FlowModel",
  "od:yamlSource": "yaml/m6-flow-model.yaml",
  "od:jsonLdSource": "yaml/m6-flow-model.jsonld",
  "od:context": "https://openclaw.dev/meta/v1#",
  "od:vocabularyStrategy": "reuse"
```

## 五、词表设计（od: Ontology-Driven Vocabulary）

### 4.1 IRI 命名约定

- 词表 IRI：`https://ontology.ontology-driven.dev/v9#`（暂定，未来可注册 w3id）
- 每个模型根类型前缀：`od:`（aggregate、behavior、rule、role、permission、report、capability、uiUnit）
- 实例 IRI：`urn:od:<domain>:<model>:<id>`，例如 `urn:od:contract-mgmt:M1:AGG-CONTRACT-001`

### 4.2 核心谓词草案

```turtle
# M1 对象模型
od:AggregateRoot a rdfs:Class ;
  rdfs:label "Aggregate Root"@zh .
od:Entity a rdfs:Class ;
  rdfs:subClassOf od:AggregateRoot .
od:ValueObject a rdfs:Class ;
  rdfs:subClassOf od:AggregateRoot .
od:hasAttribute a rdf:Property ;
  rdfs:domain od:AggregateRoot ;
  rdfs:range od:Attribute .
od:hasEntity a rdf:Property ;
  rdfs:domain od:AggregateRoot ;
  rdfs:range od:Entity .
od:hasInvariant a rdf:Property ;
  rdfs:domain od:AggregateRoot ;
  rdfs:range od:Invariant .

# M2 行为模型（仅元数据层）
od:Behavior a rdfs:Class ;
  rdfs:label "Behavior"@zh .
od:ownerEntity a rdf:Property ;
  rdfs:domain od:Behavior ;
  rdfs:range od:AggregateRoot .
od:requiresPermission a rdf:Property ;
  rdfs:domain od:Behavior ;
  rdfs:range od:Permission .
od:hasSyncTrigger a rdf:Property ;
  rdfs:domain od:Behavior ;
  rdfs:range od:Behavior .

# M3 规则模型（控制流由 SHACL 表达）
od:Rule a rdfs:Class ;
  rdfs:label "Rule"@zh .
od:appliesTo a rdf:Property ;
  rdfs:domain od:Rule ;
  rdfs:range od:AggregateRoot .

# M5 主体模型
od:Role a rdfs:Class ;
  rdfs:subClassOf skos:Concept .
od:Permission a rdfs:Class ;
  rdfs:subClassOf skos:Concept .

# M7 查询报表
od:Report a rdfs:Class ;
  rdfs:label "Query Report"@zh .
od:boundBehavior a rdf:Property ;
  rdfs:domain od:Report ;
  rdfs:range od:Behavior .

# MU UI（仅作 reference，不定义）
od:Capability a rdfs:Class ;
  rdfs:label "Capability"@zh .
od:UiUnit a rdfs:Class ;
  rdfs:label "UI Unit"@zh .
```

### 5.3 上下文（@context）示例

M1/M3/M5/M7 JSON-LD 使用 od: + 标准 RDF 词表：

```json
{
  "@context": {
    "@vocab": "https://ontology.ontology-driven.dev/v9#",
    "od": "https://ontology.ontology-driven.dev/v9#",
    "meta": "https://openclaw.dev/meta/v1#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "prov": "http://www.w3.org/ns/prov#",
    "sh": "http://www.w3.org/ns/shacl#",
    "label": "rdfs:label",
    "type": "@type",
    "id": "@id",
    "domain": { "@id": "od:domain", "@type": "xsd:string" },
    "version": { "@id": "od:version", "@type": "xsd:string" }
  }
}
```

**M6 JSON-LD 复用 MetaSkill 词表**（`meta:` 前缀）：

```json
{
  "@context": {
    "@vocab": "https://openclaw.dev/meta/v1#",
    "meta": "https://openclaw.dev/meta/v1#",
    "od": "https://ontology.ontology-driven.dev/v9#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  }
}
```

M6 不新增 `od:` 词表——所有 M6 节点类型（`meta:Flow` / `meta:Step`）与谓词（`meta:hasStep` / `meta:dependsOn` / `meta:kind` / `meta:skill` / `meta:permissionRef` / `meta:when` / `meta:onFailure` / `meta:retry` / `meta:timeoutSeconds`）都来自 MetaSkill 词表 IRI。

## 六、Manifest 升级设计

当前 `manifest.json`：

```json
{
  "model_type": "MANIFEST",
  "version": "1.0",
  "domain": "...",
  "model_files": [...]
}
```

升级为 JSON-LD 顶层入口：

```json
{
  "@context": "https://ontology.ontology-driven.dev/v9/context.jsonld",
  "@id": "urn:od:contract-mgmt:manifest",
  "@type": "od:Manifest",
  "od:domain": "销售合同执行管理",
  "od:version": "9.1",
  "od:generatedBy": "ontology-driven-dev MetaSkill",
  "od:generatedAt": "2026-09-01T00:00:00Z",
  "od:checksum": "sha256-...",
  "od:includes": {
    "@graph": [
      { "@id": "urn:od:contract-mgmt:M1:manifest", "@type": "od:M1Manifest" },
      { "@id": "urn:od:contract-mgmt:M5:manifest", "@type": "od:M5Manifest" }
    ]
  },
  "od:notMigrated": [
    { "@id": "urn:od:contract-mgmt:MU", "@type": "od:MuUiModel",
      "od:format": "application/json",
      "od:reason": "AI-native UI model; A2UI/MCP App spec-defined; YAML or A2UI catalog is the canonical form" }
  ],
  "od:m6JsonLdRef": [
    { "@id": "urn:od:contract-mgmt:M6",
      "@type": "od:M6FlowModel",
      "od:yamlSource": "yaml/m6-flow-model.yaml",
      "od:jsonLdSource": "yaml/m6-flow-model.jsonld",
      "od:context": "https://openclaw.dev/meta/v1#",
      "od:vocabularyStrategy": "reuse",
      "od:stepCount": 4 }
  ]
}
```

## 七、阶段划分

### 阶段 0：锁定动机（1 周）

- **任务**：用 AskUserQuestion 确认主驱动（A 跨系统 / B SHACL / C AI Agent / D 工具链）
- **产出**：`docs/superpowers/specs/2026-09-01-yaml-to-jsonld-motivation.md`
- **退出标准**：用户明确选定主驱动

### 阶段 1：词表冻结 + manifest 升级

- **任务**：
  - 注册 `od:` 词表 IRI（暂时使用，未来可申请 w3id）
  - 编写 `ontology_modeling_framework_v9.1.md` 新增 §11 JSON-LD 序列化约定
  - `manifest.json` 升级为 JSON-LD 顶层入口
  - YAML 仍为 source of truth
- **产出**：
  - `subskills/ontology-modeler/references/od-vocabulary-v9.ttl`
  - `subskills/ontology-modeler/references/od-context-v9.jsonld`
  - `subskills/ontology-modeler/reference-example/manifest.jsonld`（黄金范例）
- **退出标准**：manifest.jsonld 可被 dotNetRDF 解析且通过基础 JSON-LD Processor 校验

### 阶段 2：M1 + M5 全量迁移

- **任务**：
  - 编写 YAML → JSON-LD 转换器（建议 Python：`pyyaml` + `rdflib-jsonld`）
  - M1 对象、M5 主体全量迁 JSON-LD
  - ValidateYamlReferencesTool 增加 `validate_jsonld_basic` 通道：
    - `@id` 唯一性
    - `@type` 合法性（白名单：`od:AggregateRoot` / `od:Role` 等）
    - 跨文件 `@id` 引用一致性
- **产出**：
  - `subskills/ontology-modeler/tools/yaml2jsonld.py`
  - `subskills/ontology-modeler/reference-example/m1-object-model.jsonld`
  - `subskills/ontology-modeler/reference-example/m5-actor-model.jsonld`
- **退出标准**：黄金范例双向对账（YAML↔JSON-LD 互转无损）

### 阶段 3：M3 规则 → SHACL

- **任务**：
  - 把 `refRules[*].expression` 翻译为 SHACL `sh:property` + `sh:sparql`
  - 派生 `m3-rule-model.shacl.ttl`
  - ValidateYamlReferencesTool 集成 SHACL 引擎（dotnetrdf SHACL API）
- **产出**：
  - `subskills/ontology-modeler/reference-example/m3-rule-model.shacl.ttl`
- **退出标准**：对黄金范例执行 SHACL 验证，全部 `sh:conforms true`

### 阶段 4：M2 双层结构

- **任务**：
  - M2 行为 metadata（id、name、ownerEntity、requiredPermissions）迁 JSON-LD
  - `preconditions` / `postconditions` / `syncTriggers` **不迁**，留 YAML 或专用 JSON
  - 用 `@id` 把 YAML 控制流块引用回 JSON-LD 行为节点
- **关键决策**：M2 = JSON-LD 元数据层 + YAML/JSON 行为脚本层，**显式声明两层关系**
- **产出**：
  - `subskills/ontology-modeler/reference-example/m2-behavior-model.jsonld`（仅元数据）
- **退出标准**：JSON-LD 中每个 `od:Behavior` 节点可通过 `@id` 反向定位到 YAML 控制流块

### 阶段 5：M7 轻量迁 + M6 → MetaSkill 语义 JSON-LD + MU 不迁

- **任务**：
  - M7 元数据迁 JSON-LD（`od:Report` + `od:boundBehavior`）
  - **M6 流程生成 `yaml/m6-flow-model.jsonld`**，复用 MetaSkill 词表 IRI（不生成 SKILL.md）
  - manifest `od:m6JsonLdRef` 关联 YAML 与 JSON-LD
  - ValidateYamlReferencesTool 增加 `validate_jsonld_metaskill` 通道：
    - M6 JSON-LD 的 `@context` 引用 `https://openclaw.dev/meta/v1#`
    - `meta:hasStep` 数组长度 ≤ 12（meta-skills.md 约束）
    - `meta:dependsOn` 目标存在
- **产出**：
  - `subskills/ontology-modeler/reference-example/m7-report-model.jsonld`
  - `subskills/ontology-modeler/reference-example/m6-flow-model.jsonld`（复用 `meta:` 词表）
- **退出标准**：M6 黄金范例的 JSON-LD 通过 dotNetRDF + SHACL 验证（含 stepCount ≤ 12）；M7 元数据迁完

### 阶段 6：验证器统一（长期）

- **任务**：
  - ValidateYamlReferencesTool 全量支持 JSON-LD + SHACL
  - YAML 保留作为人读 review 副本，**仍可作为 ontology-modeler 的输入源**（与 N1 一致）
  - 工具链默认读 JSON-LD
- **退出标准**：JSON-LD 作为机器消费主路径；YAML 输入仍可走，但不作为运行时直接消费路径

## 八、双向对账机制

为防止 YAML 与 JSON-LD 并存期间出现漂移，需建立对账流程：

1. **写盘前**：ontology-modeler 步骤 9/10/11 完成后，立即派生 JSON-LD（M1/M2 元数据/M3/M5/M6/M7）
2. **CI 门禁**：
   - YAML 与 JSON-LD 的 `@id` 集合必须一致
   - JSON-LD 必通过 JSON-LD Processor（compaction / expansion）测试
   - SHACL 必 `sh:conforms true`（M1 不变量 + M3 规则 + **M6 `meta:hasStep` ≤ 12**）
   - **M6 YAML 的 `flow.id` 与对应 JSON-LD 节点的 `@id` 一致**
3. **漂移检测**：每周 cron 比对 git diff，若漂移自动告警

## 九、风险与权衡

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| 词表 IRI 未注册（w3id） | 引用稳定性差 | 阶段性使用 `https://ontology.ontology-driven.dev/v9#`，待稳定后申请 w3id |
| dotNetRDF 在 AOT 下的兼容性 | ValidateYamlReferencesTool AOT 友好性丢失 | 参考现有 `IsAotCompatible=true` 设计，使用反射无关 API |
| YAML ↔ JSON-LD 互转信息损失 | 双轨漂移 | 阶段 2 锁定对账基线；保留 YAML 注释映射 |
| M2 双层结构增加学习成本 | 用户需理解"元数据 vs 控制流"分层 | 在规范文档显式说明，并在 SKILL.md 增章节 |
| M6 JSON-LD 复用 MetaSkill 词表增加理解成本 | 用户需理解 MetaSkill DAG 词表才能 review M6 JSON-LD | 在规范文档 V9.1 §10 增 "M6 → MetaSkill JSON-LD 映射示例"，引用 ontology-driven-dev 自身 12 步 DAG 作为活范例 |
| M6 流程超过 12 步上限 | SHACL 校验器拒绝 | ontology-modeler 生成时主动告警 + 拆分子流建议；提供 `fan_out` 嵌套模板 |
| M6 YAML ↔ JSON-LD 漂移 | 双层漂移风险 | § 八 对账机制强制 `flow.id ↔ @id` + SHACL stepCount ≤ 12 校验 |
| MetaSkill 词表 IRI 暂未注册 | 引用稳定性差 | 阶段性使用 `https://openclaw.dev/meta/v1#`，待 OpenClaw 官方词表稳定后同步 |
| 6 阶段路径偏慢 | 短期内无可见收益 | 每个阶段独立交付价值：阶段 1 即可被外部 JSON-LD 工具消费 |

## 十、验收标准

- **AC1**：7 个模型 YAML 中：M1/M3/M5/M7 有 JSON-LD 输出（用 `od:` + 标准 RDF 词表）；M2 有 JSON-LD 元数据层 + YAML 控制流层；**M6 有 JSON-LD 输出（复用 `meta:` 词表，不生成 SKILL.md）** + YAML 人读源；MU 仅在 manifest `od:notMigrated` 显式说明
- **AC2**：JSON-LD 通过 dotNetRDF + 任意标准 JSON-LD Processor（jsonld.js / pyld）解析测试
- **AC3**：M1 不变量通过 SHACL 验证
- **AC4**：M3 规则通过 SHACL 验证
- **AC5**：ValidateYamlReferencesTool 新增 JSON-LD 通道，回归现有 YAML 校验不破坏
- **AC6**：`ontology_modeling_framework_v9.1.md` §11 JSON-LD 序列化约定已发布

## 十一、后续步骤

- **完成本 spec 后**：进入 writing-plans skill，将阶段 0-6 拆为可执行任务（**建议每个阶段一个独立 plan**，本 spec 不强制一次性全量实施）
- **不在本 spec 内**：具体转换器代码实现、SHACL 形状具体内容（按阶段细化）
- **维护责任人**：ontology-modeler 子 Skill 维护者