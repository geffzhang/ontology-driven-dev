# MU UI 模型 AI 原生化设计（MCP Apps + A2UI）

- 日期：2026-08-31
- 状态：设计已确认，待写实施计划
- 影响范围：`references/ontology_modeling_framework_v9.md` 第八章及散点、`references/AI需求探索与确认提示词V9.0.md` 阶段七及散点、`reference-example/` 全套、`SKILL.md`、`README.md` / `README_EN.md`

---

## 一、背景与目标

现行 MU UI 模型（v9.0 第八章）面向传统 B/S 管理系统：一级菜单 → 二级菜单 → 屏幕（ASCII 布局）→ 操作功能点。其隐含前提是「人用鼠标点菜单找功能」。

AI 原生应用的交互前提不同：**用户表达意图，智能体路由到能力，界面由协议声明式下发**。业界已有两套成熟协议承接这件事：

- **A2UI**（a2ui.org，Google 开源，Apache 2.0）：声明式 JSON UI 协议。扁平**邻接表**组件模型（组件通过 ID 引用子节点，而非嵌套），配套数据模型与 action 回传；组件受 **catalog 白名单**约束，不执行任意代码；消息为 `createSurface` / `updateComponents` / `updateDataModel` / `deleteSurface`，支持流式增量渲染，可在 Web / Flutter / 原生移动端渲染。
- **MCP Apps**（SEP-1865）：MCP 扩展。服务端以 `ui://` URI 暴露 HTML 界面资源（`text/html;profile=mcp-app`），工具结果通过 `_meta` 挂载界面模板，宿主在 iframe 中渲染，界面经 postMessage 以 `ui/tools/call` 反向调用工具。

本设计将第八章 MU 模型**彻底替换**为基于这两个协议的 AI 原生界面模型，并保持七模型编号体系（M1/M2/M3/M5/M6/M7/MU）不变。

**核心目标**：MU 仍是七模型的**入口层 / 追溯层**，但「入口」从菜单导航变为能力路由，「界面」从 ASCII 示意变为可直接渲染的协议结构，且**可追溯门禁比现行版本更硬**（新增行为↔工具 1:1 双向校验）。

---

## 二、已确认的设计决策

| # | 决策 | 结论 |
|---|---|---|
| D1 | 改造范围 | **彻底替换为 AI 原生**。删除一级/二级菜单树、四种 `screenType`、ASCII 布局规则 |
| D2 | MCP Apps 与 A2UI 分工 | **双形态并列，按场景选**：`A2UI_SURFACE`（声明式组件）与 `MCP_APP`（`ui://` HTML，自带前端的重界面） |
| D3 | 界面确定时机 | **混合，用 `renderMode` 标注**：`STATIC`（建模期写死，门禁全量校验）/ `GENERATED`（运行期由智能体按约束生成，仅限只读探索） |
| D4 | 连带修改 | **全仓跟改**，含阶段一需求探索提示词与范例需求文档 |

**明确的取舍与代价**：

1. ASCII 布局图整体删除。组件邻接表是可直接渲染的真结构，约束比 ASCII 更严格，但**人工评审的直观性下降**——评审看的是组件树而非画面示意。这是接受的代价。
2. A2UI 官方 basic catalog 缺少企业系统必需的语义组件（跳选框、分页表格）。本设计新增 `ontology-basic` 自定义目录（见 §4.4），否则 M1 的 `AggregateRootRef` 语义在界面层断链。
3. `tools` 段独立存在于 MU 而非并入 M2 行为模型。理由：MCP 工具契约是**界面/智能体侧的暴露面**，属于入口层职责；M2 保持纯业务行为语义，不被协议细节污染。

---

## 三、模型元素总览

层级从四层塌为三层：

```
application（应用 + 协议声明）
  └─ capabilities（能力目录 —— 替代菜单树，意图路由入口）
       ├─ intent / utterances     语义描述与自然语言触发样例
       ├─ toolRef                 可直达的 MCP 工具
       └─ uiUnitRef               承载该意图的界面单元
  └─ tools（M2 行为的 MCP 工具契约面，与行为 1:1）
  └─ uiUnits（界面单元 —— 替代 screens）
       ├─ unitType: A2UI_SURFACE | MCP_APP
       ├─ renderMode: STATIC | GENERATED
       ├─ surface / mcpApp / generationContract（按形态三选一）
       └─ actions（action event → toolRef → behaviorRef）
```

`unitType` 与 `renderMode` 是**两个正交维度**，取代原来「四选一 `screenType`」的单一分类。

---

## 四、新第八章结构

### 4.1 §8.1 设计目标与边界

保留 MU「只引用、不重定义」的定位，边界条款改写为 6 条：

1. **只引用、不重定义**：MU 通过稳定 ID 引用 M1/M2/M6/M7，不重新定义对象、行为、规则、流程或报表；
2. **不承载视觉设计**：配色、字体、间距、图标、主题由渲染端 catalog 实现决定；MU 只声明组件类型、层级与数据绑定；
3. **不替代 M6**：端到端/审批流转归 M6；MU 只声明 action 与工具入口的对应关系；
4. **不承载业务校验公式**：输入校验引用 M3 规则或 M1 属性约束；组件级格式（掩码、联动启用）仅限本组件内；
5. **不定义传输**：A2UI 消息如何经 SSE / WebSocket / A2A 下发、MCP 如何握手，属实现层，不在本模型；
6. 纯展示界面单元允许无 action，但必须有组件或 `mcpApp` 声明。

### 4.2 §8.2 模型元素规范

#### 8.2.1 应用（Application）

| 属性 | 类型 | 说明 |
|---|---|---|
| name | String | 系统名称（中文） |
| uiProtocols.a2ui.version | String | A2UI 协议版本，如 `v0.9` |
| uiProtocols.a2ui.catalogRef | String | 组件目录标识，默认 `ontology-basic/v1` |
| uiProtocols.mcpApps.version | String | MCP Apps 规范版本，如 `SEP-1865` |

#### 8.2.2 能力（Capability）—— 替代 Menu

| 属性 | 类型 | 说明 |
|---|---|---|
| capabilityId | String | 唯一标识 |
| name | String | 能力名称（中文） |
| intent | String | 语义描述：这个能力让用户完成什么 |
| utterances | String[] | 自然语言触发样例，**至少 1 条**，建议 2-3 条 |
| toolRef | ToolRef | 可选；可直达执行的工具（无需界面的能力） |
| uiUnitRef | UIUnitRef | 可选；承载该意图的界面单元 |
| permissionRef | PermissionRef[] | 可选；控制能力可见性的 M5 权限 |

约束：`toolRef` 与 `uiUnitRef` **至少存在其一**。能力目录是扁平的，不再有层级；如需分组展示，由宿主按 `permissionRef` 或业务域自行归类，不在模型内。

#### 8.2.3 工具契约（Tool）—— 新增

M2 行为面向智能体与界面的暴露面，与 M2 中 `triggerType=USER_ACTION` 的行为**严格 1:1**。`triggerType=SYSTEM` 的行为（跨对象联动、系统触发）**不暴露为工具**——它们由行为的 `syncTriggers` 在服务端自动触发，不是用户或智能体可直接调用的能力。

| 属性 | 类型 | 说明 |
|---|---|---|
| toolName | String | MCP 工具名（snake_case，全局唯一） |
| behaviorRef | BehaviorRef | 对应的 M2 行为 |
| title | String | 人类可读标题 |
| description | String | 供 LLM 选择工具的语义描述 |
| inputSchema.objectRef | ObjectRef | 输入所属 M1 聚合 |
| inputSchema.fields | FieldPath[] | 输入字段（由 M1 属性派生类型与必填性） |
| outputSchema.objectRef | ObjectRef | 输出所属 M1 聚合或 M7 报表对象 |
| outputSchema.fields | FieldPath[] | 输出字段 |
| annotations.readOnlyHint | Boolean | 是否只读（M2 `QUERY` 行为恒为 true） |
| annotations.destructiveHint | Boolean | 是否破坏性（删除类行为为 true） |
| permissionRef | PermissionRef[] | 可选；M5 权限 |

#### 8.2.4 界面单元（UIUnit）—— 替代 Screen

| 属性 | 类型 | 说明 |
|---|---|---|
| uiUnitId | String | 唯一标识 |
| name | String | 业务名称（中文） |
| unitType | Enum | `A2UI_SURFACE` / `MCP_APP` |
| renderMode | Enum | `STATIC` / `GENERATED` |
| surface | Surface | `unitType=A2UI_SURFACE` 且 `renderMode=STATIC` 时必填 |
| generationContract | GenerationContract | `renderMode=GENERATED` 时必填 |
| mcpApp | McpApp | `unitType=MCP_APP` 时必填 |
| actions | ActionPoint[] | 操作功能点集合 |

#### 8.2.5 Surface（A2UI 声明式界面）

| 属性 | 类型 | 说明 |
|---|---|---|
| surfaceId | String | A2UI surface 标识 |
| root | ComponentId | 根组件 ID |
| dataModel | Map<JsonPath, ObjectRef\|FieldPath> | 数据模型路径 → M1 绑定 |
| components | Component[] | **扁平邻接表**，非嵌套树 |

**Component**：

| 属性 | 类型 | 说明 |
|---|---|---|
| id | String | 组件 ID，surface 内唯一，使用描述性命名（`txt-contract-no`，不用 `c1`） |
| component | Enum | 组件类型，取自 `catalogRef` 声明的目录（见 §8.2.8） |
| label | String | 显示文案 |
| value | `{ literalString }` \| `{ path }` | 字面量或数据模型路径绑定 |
| required | Boolean | 与 M1 属性 `required` 对齐 |
| dataBinding | FieldPath | 绑定的 M1 聚合属性路径，如 `Contract.contractNo` |
| children | `{ explicitList }` \| `{ template }` | 静态子组件 ID 列表，或按数据数组生成的模板 |
| action | `{ event }` | 触发的 action event 名（须匹配某个 ActionPoint 的 `event`） |
| refRules | UIComponentRule[] | 可选；组件级规则（掩码、格式、联动启用），仅限本组件 |

除上表通用属性外，各组件可有自身特有属性（如 `EntityPicker.targetAggregate`、`DataTable.columns`），由 §8.3.1 的组件目录定义。

#### 8.2.6 GenerationContract（生成式界面契约）

`renderMode=GENERATED` 时，MU 不声明组件树，只声明约束：

| 属性 | 类型 | 说明 |
|---|---|---|
| intent | String | 界面意图 |
| dataSources | QueryReportRef[] | 可用数据来源，引 M7 报表对象 |
| allowedComponents | ComponentType[] | 允许使用的组件白名单 |
| allowedTools | ToolRef[] | 允许调用的工具，**必须全部 `readOnlyHint=true`** |
| requiredActions | ActionId[] | 可选；必须提供的 action（如导出） |

#### 8.2.7 McpApp（`ui://` 宿主应用）

| 属性 | 类型 | 说明 |
|---|---|---|
| resourceUri | String | `ui://` 前缀的资源 URI，如 `ui://contract/execution-report` |
| mimeType | String | 固定 `text/html;profile=mcp-app` |
| templateOfTool | ToolRef | 该界面作为哪个工具结果的输出模板（`_meta` 挂载点） |
| allowedTools | ToolRef[] | 界面经 `ui/tools/call` 可反向调用的工具集合 |

#### 8.2.8 操作功能点（ActionPoint）

| 属性 | 类型 | 说明 |
|---|---|---|
| actionId | String | 唯一标识 |
| name | String | 动作名称（按钮文案） |
| actionType | Enum | `EXECUTE` / `SUBMIT` / `DRAFT` / `APPROVE` / `REJECT` / `RETURN` / `QUERY` / `EXPORT` |
| event | String | A2UI action event 名（`MCP_APP` 形态下为 postMessage 事件名） |
| toolRef | ToolRef | 触发调用的 MCP 工具 |
| behaviorRef | BehaviorRef | 最终执行的 M2 行为（须与 `toolRef` 的 `behaviorRef` 一致） |
| permissionRef | PermissionRef[] | 可选；M5 权限 |

> 原 `actionType=BUTTON` 更名为 `EXECUTE`（BUTTON 是控件不是动作语义），新增 `QUERY` / `EXPORT`。

### 4.3 §8.3 M1 属性类型 → A2UI 组件映射（强制）

| M1 属性类型 | A2UI 组件 | 说明 |
|---|---|---|
| Date / DateTime | `DateTimeInput` | `enableDate` / `enableTime` 按类型开关 |
| Enum | `Select` | 选项来自 `enumValues` |
| DictionaryRef | `Select` | 选项来自数据字典项（`label` 显示、`code` 存储） |
| AggregateRootRef | `EntityPicker` | 跳选：显示目标对象名称，弹出选择；`targetAggregate` 必填 |
| String（长文本 / 备注） | `TextArea` | |
| Boolean | `Checkbox` | |
| Integer / Decimal / Money | `NumberInput` | |
| 其他 String | `TextField` | |
| 明细集合 / 查询结果 | `DataTable` + `children.template` | `dataPath` 指向数据模型数组路径 |
| 状态机当前状态 | `StatusBadge` | `stateMachineRef` 指向 M1 状态机 |

### 4.4 §8.3.1 `ontology-basic` 组件目录（新增）

A2UI 官方 basic catalog 无法表达企业本体的若干核心语义，故定义 `ontology-basic/v1`：继承官方 basic catalog，新增 4 个组件。

**继承自 basic**：`Column`、`Row`、`Card`、`Heading`、`Text`、`TextField`、`NumberInput`、`TextArea`、`Select`、`DateTimeInput`、`Checkbox`、`Button`。

**新增自定义组件**：

| 组件 | 用途 | 关键属性 |
|---|---|---|
| `EntityPicker` | `AggregateRootRef` 跳选 | `targetAggregate`、`searchToolRef`（指向该聚合的 M7 查询工具） |
| `DataTable` | 明细维护 / 查询结果 | `dataPath`、`columns[{field,label,type}]`、`pagination`、`rowActions[{actionId}]`、`inlineEdit` |
| `StatusBadge` | 对象状态机当前状态 | `value{path}`、`stateMachineRef` |
| `Chart` | M7 报表可视化 | `dataSourceRef`（M7）、`chartType`、`dimensions`、`measures` |

> 若项目自建设计系统，可声明自有 `catalogRef`，但**必须提供上述 4 个组件的等价语义**，否则 M1 语义在界面层断链。

### 4.5 §8.4 Surface 组织模式（替代 ASCII 布局规则）

原四套 ASCII 模板改为四套**组件结构约定**，均为 `renderMode=STATIC`：

| 模式 | 适用 | 组件结构 |
|---|---|---|
| 单对象录入 | 单条记录录入/维护 | `Column[ Heading, Card(字段组), Row(动作区) ]` |
| 主从维护 | 聚合根 + 明细集合 | `Column[ Card(主对象字段), DataTable(明细，`children.template` 绑定数组，`inlineEdit=true`，`rowActions` 含删除), Row(动作区) ]` |
| 查询列表 | M7 查询报表 | `Column[ Card(查询条件), DataTable(`pagination=true`), Row(动作区) ]` |
| 列表维护 | 主数据 / 数据字典 / 简单实体 | `Column[ Row(工具栏：关键词 + 查询 + 新增), DataTable(`rowActions` 含编辑/删除) ]`，新增与编辑通过**第二个 surface**（`createSurface` 弹出）承载，主 surface 不内联表单 |

字段的行列排布（原「一行两个/三个控件」「标签右对齐」）**不再由 MU 规定**——那属于 catalog 渲染实现与响应式布局，MU 只声明字段归属哪个 `Card` 分组及顺序。

### 4.6 §8.5 审批双动作规则（保留）

带审批流的对象维护单元，必须提供两个**独立** ActionPoint：

1. `actionType=DRAFT` → 独立工具 → M2 `Xxx_SaveAsDraft` 行为，置草稿态，不触发审批；
2. `actionType=SUBMIT` → 独立工具 → M2 `Xxx_Submit` 行为，置待审批态，作为 M6 审批流 `trigger.behaviorRef` 启动入口。

不得合并为单个「保存」动作。无审批流的功能只需一个 `EXECUTE` 动作。

### 4.7 §8.6 YAML 元文件模板

```yaml
# MU UI 模型元文件 - mu-ui-model.yaml
model_type: UI
version: "2.0"
domain: "销售合同执行管理"

application:
  name: 销售合同执行管理系统
  uiProtocols:
    a2ui:    { version: "v0.9", catalogRef: "ontology-basic/v1" }
    mcpApps: { version: "SEP-1865" }

capabilities:
  - capabilityId: cap-contract-create
    name: 录入销售合同
    intent: 创建一份销售合同并保存草稿或提交审批
    utterances: ["新建一个合同", "帮我录入XX公司的销售合同"]
    uiUnitRef: ui-contract-maintain
    permissionRef: [perm-contract-create]

tools:
  - toolName: contract_submit
    behaviorRef: Contract_Submit
    title: 提交合同
    description: 保存合同数据并提交进入审批流
    inputSchema:  { objectRef: Contract, fields: [contractNo, contractName, contractType, ...] }
    outputSchema: { objectRef: Contract, fields: [contractId, status] }
    annotations:  { readOnlyHint: false, destructiveHint: false }
    permissionRef: [perm-contract-create]

uiUnits:
  - uiUnitId: ui-contract-maintain
    name: 合同录入
    unitType: A2UI_SURFACE
    renderMode: STATIC
    surface:
      surfaceId: contract-maintain
      root: root-col
      dataModel:
        "/contract": Contract
        "/contract/stages": Contract.paymentStages
      components:
        - { id: root-col, component: Column,
            children: { explicitList: [hd, card-main, tbl-stage, bar] } }
        - { id: hd, component: Heading, value: { literalString: "合同录入" } }
        - { id: card-main, component: Card,
            children: { explicitList: [txt-no, txt-name, sel-type, pick-customer] } }
        - { id: txt-no, component: TextField, label: 合同编号, required: true,
            value: { path: "/contract/contractNo" }, dataBinding: Contract.contractNo }
        - { id: sel-type, component: Select, label: 合同类型, required: true,
            value: { path: "/contract/contractType" }, dataBinding: Contract.contractType }
        - { id: pick-customer, component: EntityPicker, label: 所属客户, required: true,
            value: { path: "/contract/customerId" }, dataBinding: Contract.customerId,
            targetAggregate: Customer, searchToolRef: customer_query }
        - { id: tbl-stage, component: DataTable, label: 付款阶段,
            children: { template: { dataPath: "/contract/stages" } },
            inlineEdit: true,
            columns: [{ field: stageNo, label: 阶段编号 }, { field: ratio, label: 付款比例 }] }
        - { id: bar, component: Row, children: { explicitList: [btn-draft, btn-submit] } }
        - { id: btn-draft,  component: Button, label: 保存草稿, action: { event: contract_save_draft } }
        - { id: btn-submit, component: Button, label: 提交,     action: { event: contract_submit } }
    actions:
      - { actionId: act-draft,  name: 保存草稿, actionType: DRAFT,  event: contract_save_draft,
          toolRef: contract_save_as_draft, behaviorRef: Contract_SaveAsDraft }
      - { actionId: act-submit, name: 提交,     actionType: SUBMIT, event: contract_submit,
          toolRef: contract_submit,        behaviorRef: Contract_Submit }

  - uiUnitId: ui-execution-report
    name: 合同执行情况分析
    unitType: MCP_APP
    renderMode: STATIC
    mcpApp:
      resourceUri: "ui://contract/execution-report"
      mimeType: "text/html;profile=mcp-app"
      templateOfTool: contract_execution_report
      allowedTools: [contract_execution_report, contract_detail_query]
    actions:
      - { actionId: act-export, name: 导出, actionType: EXPORT, event: export_report,
          toolRef: contract_execution_report, behaviorRef: Contract_ExecutionReport }

  - uiUnitId: ui-adhoc-analysis
    name: 合同执行自由分析
    unitType: A2UI_SURFACE
    renderMode: GENERATED
    generationContract:
      intent: 对合同执行情况按用户临时提问做探索式分析与可视化
      dataSources: [rpt_contract_execution, rpt_unreceived]
      allowedComponents: [Text, Heading, Card, DataTable, Chart, Button]
      allowedTools: [contract_execution_report, unreceived_report]
```

### 4.8 §8.7 一致性约束（MU 门禁）

替换原 9 条为 11 条：

1. `dataBinding` 字段路径必须可解析到 M1 聚合属性，且与 `dataModel` 的路径声明一致；
2. `generationContract.dataSources` 与 `Chart.dataSourceRef` 引用的 M7 对象必须存在；
3. `action.toolRef` 必须存在于 `tools`，且 `action.behaviorRef` 必须与该工具的 `behaviorRef` **完全一致**（防止串线）；
4. `tools` 与 M2 中 `triggerType=USER_ACTION` 的行为**严格 1:1**：每个 `USER_ACTION` 行为恰好一个工具，每个工具恰好一个行为；`triggerType=SYSTEM` 的行为**不得**出现在 `tools` 中；
5. **反向门禁**：M2 中 `triggerType=USER_ACTION` 的行为，其工具必须被至少一个 `capability.toolRef` 或 `uiUnit.actions[].toolRef` 引用；
6. 组件 `component` 类型必须属于 `application.uiProtocols.a2ui.catalogRef` 声明的目录，且遵循 §8.3 映射规则；
7. `renderMode=GENERATED` 的单元，`allowedTools` 必须**全部** `readOnlyHint=true`，且不得声明写操作 action —— 生成式界面永不触发事务；
8. 带审批流的对象维护单元必须 `renderMode=STATIC`，且必须同时包含 `DRAFT` 与 `SUBMIT` 两个 ActionPoint；
9. 组件邻接表完整性：`root` 必须存在；`children.explicitList` 引用的 id 必须存在；引用图**无环**；除 `root` 外每个组件必须被恰好一个父组件引用（无孤儿、无重复挂载）；
10. 每个 `capability` 必须至少解析到 `uiUnitRef` 或 `toolRef` 之一，且 `utterances` 至少 1 条；
11. `mcpApp.resourceUri` 必须以 `ui://` 开头，`mimeType` 固定 `text/html;profile=mcp-app`，`templateOfTool` 与 `allowedTools` 必须存在于 `tools`。

---

## 五、跨文件改动清单

### 5.1 `references/ontology_modeling_framework_v9.md`

| 位置 | 改动 |
|---|---|
| L1487-1958（第八章全章） | 按 §4 全部重写，约 470 行 |
| L17 | 导读中 MU 描述改为「应用 → 能力目录 → 界面单元（A2UI Surface / MCP App）→ 操作功能点」 |
| L65 | 术语表 MU 行改为「定义能力目录、工具契约、界面单元及其与行为的调用关系」 |
| L79 | 依赖图：MU 依赖不变（M1+M2+M6+M7），补注「经 MCP 工具契约与 A2UI Surface 表达」 |
| L89-90 | 建模原则第 6/7 条：入口层描述与可追溯门禁改为工具契约双向 1:1 版本 |
| L217 | `AggregateRootRef` 的「跳选框」改为「`EntityPicker` 组件」 |
| L219 | `DictionaryRef` / `Enum` 的「下拉列表框」改为「`Select` 组件」 |
| L658 | M2 门禁第 1 条改为「必须暴露为 MCP 工具，且被 capability 或 action 引用」 |
| L661 | 行为 `postconditions` 与界面衔接描述改为「与 action 完成后的 `updateDataModel` 衔接」 |
| L1977 | 第九章覆盖度表「菜单导航与界面布局」行改为「能力路由与界面结构」 |
| L1998 | MU 解耦说明改为「通过工具契约解耦，action 经 toolRef 引用行为」 |
| L2002 | UI/UX 边界补充「不建模传输层与 catalog 渲染实现」 |
| L2026 | 第十章步骤表第 8 步改为「定义工具契约、能力目录与界面单元」 |
| L2046 | 自检项改为工具契约双向可追溯 |
| L2077 | MU 评审清单按新门禁 11 条重写 |
| L2100 | 文件清单说明保持 `mu-ui-model.yaml`（文件名不变，版本升 2.0） |
| L2117 | 一致性检查行补充「工具契约 1:1、组件图无环、GENERATED 只读」 |
| L2143 | 术语表：新增「能力（Capability）」「工具契约（Tool）」「界面单元（UIUnit）」「Surface」「组件目录（Catalog）」；「操作功能点」定义改为「action event → 工具 → 行为」 |

### 5.2 `references/AI需求探索与确认提示词V9.0.md`

| 位置 | 改动 |
|---|---|
| L10 | 改造说明：阶段九/阶段七的 UI 探索基准改为「能力目录、界面单元、组件映射、审批草稿/提交双动作」 |
| L111 | UI 无关边界说明中的「菜单树、ASCII 布局、控件类型映射」改为「能力目录、Surface 组件结构、组件映射」 |
| L123 | 阶段零输出项「候选界面菜单」改为「候选能力目录」 |
| L160-161 | 「初步识别的界面菜单层级：[一级菜单 → 二级菜单]」改为「初步识别的能力目录：[能力名称 → 意图]」 |
| L484-493 | 阶段七 UI 原型探索整段重写：层级改为「应用 → 能力目录 → 界面单元 → 操作功能点」；`screenType` 四选一改为 `unitType` × `renderMode`；ASCII 布局条目删除，改为 Surface 组织模式四种；新增「哪些能力走 `MCP_APP`」「哪些只读分析允许 `GENERATED`」两个确认点 |
| L498 | 审批双按钮规则保留，措辞改为「双动作功能点」 |
| L505 / L563 | 「不得虚构界面原型」「输出菜单树与 ASCII 布局图」改为「输出能力目录与界面单元结构」 |
| L513-525 | 阶段七确认问题重写：删除「一行几个字段」「标签对齐」类布局问题；改为①是否输出 AI 原生界面模型 ②能力目录的意图命名与触发语 ③哪些重界面走 MCP App ④哪些只读分析允许生成式 |
| L543 | 附录 C 生成说明中「MU 菜单树/操作点与行为映射」改为「MU 能力目录/工具契约/界面单元与行为映射」 |
| L544 | 建模一致性预检中 MU 部分改为新门禁措辞 |
| L573 | 跨章节双向核对中「MU 操作功能点与行为一致」改为「工具契约与行为 1:1、action 与工具一致」 |
| L583 | 阶段七确认要求同步改写 |
| L661 | UI 剥离说明中「菜单树、ASCII 布局、操作功能点」改为「能力目录、界面单元、操作功能点」 |
| L1115（附录 C.7） | 改为「C.7 MU 能力与界面：能力目录（意图/触发语）、工具契约（行为→工具）、界面单元（unitType/renderMode）、组件与 M1 绑定、action→工具→行为映射」 |
| L1167（自检第 43 项） | 「一级菜单下至少一个二级菜单，二级菜单关联界面」改为「能力目录完整：每个 `USER_ACTION` 行为可由至少一个 capability 或 action 触达」 |
| L1277 | 变更历史追加 V9.1 行，记录 MU AI 原生化 |

### 5.3 `reference-example/`

| 文件 | 改动 |
|---|---|
| `mu-ui-model.yaml` | **952 行全量重写**：12 个二级菜单 → 对应能力目录；8 个屏幕 → 界面单元（事务型 `A2UI_SURFACE`+`STATIC`；3 个报表中至少 1 个改 `MCP_APP` 示范；新增 1 个 `GENERATED` 自由分析单元示范）；所有 M2 行为补齐 `tools` 段 |
| `合同管理需求规格说明书-V9.md` | 附录 C.7 与附录 D（UI 原型）按新结构重写 |
| `manifest.json` | 若含 MU 描述或版本号，同步更新 |
| 其余 6 个 YAML | 不改（MU 只引用，不反向要求 M1-M7 变更） |

### 5.4 `SKILL.md` 与 README

| 位置 | 改动 |
|---|---|
| `SKILL.md` L42 | 产物说明「MU UI」改为「MU 能力与界面」 |
| `SKILL.md` L43 | 建模顺序末项「MU 界面」改为「MU（工具契约 → 能力目录 → 界面单元）」 |
| `SKILL.md` L45 | 可追溯门禁改为「`USER_ACTION` 行为须 1:1 暴露为 MCP 工具，且被至少一个 capability 或 action 引用」 |
| `README.md` / `README_EN.md` | 第一节「模型一致性」与第四节阶段二措辞同步；README 结构树无需改（文件名不变） |

---

## 六、迁移与兼容

- `mu-ui-model.yaml` 的 `version` 由 `1.0` 升为 `2.0`，**不提供向后兼容**：`menus` / `screens` / `screenType` / `layout` 字段一律不再识别。
- 文件名与 `manifest.json` 中的模型编号保持 `MU` / `mu-ui-model.yaml` 不变，避免破坏既有工具链。
- 框架文档整体版本由 v9.0 记为 **v9.1**（仅 MU 章节与相关引用变更，M1/M2/M3/M5/M6/M7 语义不变）。

---

## 七、验收标准

1. 第八章不再出现「菜单」「一级/二级菜单」「ASCII」「`screenType`」「`SINGLE_FORM`/`LIST_MAINTENANCE`/`MASTER_DETAIL_FORM`/`QUERY_LIST`」等词；
2. 全仓 grep「菜单树」「ASCII 布局」无残留（变更历史与版本说明中的历史记述除外）；
3. `reference-example/mu-ui-model.yaml` 通过新 §8.7 全部 11 条门禁，可人工逐条核对；
4. 范例中每个 M2 `triggerType=USER_ACTION` 行为均有对应 `tools` 条目，且被 capability 或 action 引用；
5. 范例同时包含 `A2UI_SURFACE+STATIC`、`MCP_APP+STATIC`、`A2UI_SURFACE+GENERATED` 三种组合各至少一例；
6. 阶段一提示词的 47 项自检数量不变，第 43 项已按新语义改写；
7. `SKILL.md`、README 与框架文档三处对 MU 的描述完全一致，无新旧混用。
