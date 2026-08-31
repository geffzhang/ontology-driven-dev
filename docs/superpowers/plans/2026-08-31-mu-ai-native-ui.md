# MU AI 原生建模语义实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 MU UI 模型升级为“能力目录 + 工具契约 + 界面单元”的 AI 原生建模语义，同时保持技能的终态仅为七模型 YAML，不恢复需求探索阶段七或应用构建。

**Architecture:** 重写建模框架第八章以及框架内与 MU 有关的散点说明，令 MU 从菜单/屏幕/ASCII 表达迁移到能力、工具与界面单元。以销售合同范例的 `mu-ui-model.yaml` 验证新元模型，并仅同步 SKILL 与 README 中的阶段二模型术语；不改需求探索提示词、需求文档范例、技术底座或运行时实现。

**Tech Stack:** Markdown、YAML、Git、PowerShell `Select-String`。

## Global Constraints

- 模型编号和文件名不变：仍使用 `MU` 与 `mu-ui-model.yaml`；`manifest.json` 的模型键和 `model_files` 均不改名。
- `mu-ui-model.yaml` 的 `version` 从 `"1.0"` 升为 `"2.0"`，不兼容 `menus`、`screens`、`screenType` 或 `layout` 字段。
- 框架版本更新为 v9.1；M1/M2/M3/M5/M6/M7 的语义不变。
- MU 仅是本体模型中的入口与追溯层；不包含任何 UI 渲染实现、MCP 服务、A2UI 传输、SSE、WebSocket、HTML、前后端代码或运行说明。
- 需求探索流程仍止于阶段六；不得修改 `references/AI需求探索与确认提示词V9.0.md`，不得增加 UI 原型阶段或附录 D 的界面描述。
- 不修改 `reference-example/合同管理需求规格说明书-V9.md`、`reference-example/m1-object-model.yaml`、`m2-behavior-model.yaml`、`m3-rule-model.yaml`、`m5-actor-model.yaml`、`m6-flow-model.yaml` 或 `m7-report-model.yaml`。
- 仅可修改 `references/ontology_modeling_framework_v9.md`、`reference-example/mu-ui-model.yaml`、`SKILL.md`、`README.md`、`README_EN.md`；`reference-example/manifest.json` 仅在它实际包含 MU 版本或描述字段时修改。
- 工具名必须为 `snake_case`；界面单元与组件 ID 必须为描述性的 `kebab-case`。
- `tools` 与 M2 中 `triggerType=USER_ACTION` 的行为严格 1:1；`triggerType=SYSTEM` 行为不得出现在 `tools`。
- `renderMode=GENERATED` 仅可调用 `readOnlyHint=true` 的工具，且不得定义 `actions`。
- 不运行 `git add -A`，不自动提交；提交由用户另行决定。

---

## File Structure

- Modify: `references/ontology_modeling_framework_v9.md` - MU 元模型定义及仅与 MU 语义有关的散点引用。
- Modify: `reference-example/mu-ui-model.yaml` - 按 v2.0 元模型重写的范例。
- Modify: `SKILL.md` - 仅更新阶段二中 MU 的建模称谓和可追溯门禁。
- Modify: `README.md` - 仅更新中文的阶段二 MU 模型说明。
- Modify: `README_EN.md` - 仅更新英文的阶段二 MU 模型说明。
- Conditionally modify: `reference-example/manifest.json` - 仅当存在 MU 的版本或描述元数据。

### Task 1: 定义 MU v2.0 建模边界

**Files:**

- Modify: `references/ontology_modeling_framework_v9.md`

**Interfaces:**

- Consumes: M1 属性、M2 行为、M5 权限、M6 流程与 M7 报表的既有稳定标识。
- Produces: MU v2.0 的顶层段 `application`、`capabilities`、`tools`、`uiUnits`，供范例 YAML 与技能文档引用。

- [ ] **Step 1: 记录现有第八章边界和版本表位置**

Run:

```powershell
Select-String -Path 'references/ontology_modeling_framework_v9.md' -Pattern '^# 第八章|^# 第九章|版本|变更历史' | ForEach-Object { "$($_.LineNumber):$($_.Line)" }
```

Expected: 输出第八章与第九章的边界；若找到版本表，记录其位置。

- [ ] **Step 2: 重写第八章为 MU v2.0 元模型**

保留标题 `# 第八章  MU UI 模型`，以如下结构替换该章全部旧内容：

```markdown
## 8.1 设计目标与边界
## 8.2 模型元素规范
### 8.2.1 应用（Application）
### 8.2.2 能力（Capability）
### 8.2.3 工具契约（Tool）
### 8.2.4 界面单元（UIUnit）
### 8.2.5 Surface（声明式界面结构）
### 8.2.6 生成契约（GenerationContract）
### 8.2.7 宿主界面声明（McpApp）
### 8.2.8 操作功能点（ActionPoint）
## 8.3 M1 属性类型到组件映射规则（强制）
### 8.3.1 ontology-basic 组件目录
## 8.4 界面单元组织模式（强制）
## 8.5 审批双动作规则（强制）
## 8.6 YAML 元文件模板
## 8.7 一致性约束（MU 门禁）
```

元模型必须包含以下内容：

```yaml
application:
  name: <String>
  uiProtocols:
    a2ui: { version: "v0.9", catalogRef: "ontology-basic/v1" }
    mcpApps: { version: "SEP-1865" }

capabilities:
  - capabilityId: <kebab-case>
    name: <String>
    intent: <String>
    utterances: [<String>]
    toolRef: <snake_case ToolRef> # 与 uiUnitRef 至少存在一个
    uiUnitRef: <kebab-case UIUnitRef>
    permissionRef: [<M5 PermissionRef>]

tools:
  - toolName: <snake_case>
    behaviorRef: <M2 BehaviorRef>
    title: <String>
    description: <String>
    inputSchema: { objectRef: <M1 ObjectRef>, fields: [<M1 FieldPath>] }
    outputSchema: { objectRef: <M1 ObjectRef or M7 QueryReportRef>, fields: [<FieldPath>] }
    annotations: { readOnlyHint: <Boolean>, destructiveHint: <Boolean> }
    permissionRef: [<M5 PermissionRef>]

uiUnits:
  - uiUnitId: <kebab-case>
    name: <String>
    unitType: A2UI_SURFACE # A2UI_SURFACE | MCP_APP
    renderMode: STATIC # STATIC | GENERATED
    surface: <required only for A2UI_SURFACE + STATIC>
    generationContract: <required only for GENERATED>
    mcpApp: <required only for MCP_APP>
    actions: [<ActionPoint>]
```

`Surface` 使用扁平组件邻接表：`surfaceId`、`root`、`dataModel`、`components`。组件字段包含 `id`、`component`、可选 `label`、`value`、`required`、`dataBinding`、`children`、`action` 与 `refRules`。组件类型至少规定 `Column`、`Row`、`Card`、`Heading`、`Text`、`TextField`、`NumberInput`、`TextArea`、`Select`、`DateTimeInput`、`Checkbox`、`Button`、`EntityPicker`、`DataTable`、`StatusBadge`、`Chart`。

`GenerationContract` 包含 `intent`、`dataSources`、`allowedComponents`、`allowedTools` 和可选 `requiredActions`。`McpApp` 包含 `resourceUri`、`mimeType`、`templateOfTool`、`allowedTools`。`ActionPoint` 包含 `actionId`、`name`、`actionType`、`event`、`toolRef`、`behaviorRef` 和可选 `permissionRef`；`actionType` 仅允许 `EXECUTE`、`SUBMIT`、`DRAFT`、`APPROVE`、`REJECT`、`RETURN`、`QUERY`、`EXPORT`。

第 8.3 节必须规定：`AggregateRootRef -> EntityPicker`（带 `targetAggregate`），`Enum`/`DictionaryRef -> Select`，日期 -> `DateTimeInput`，数值 -> `NumberInput`，长文本 -> `TextArea`，布尔 -> `Checkbox`，一般字符串 -> `TextField`，明细/查询结果 -> `DataTable`，状态 -> `StatusBadge`。第 8.3.1 节规定 `ontology-basic/v1` 及 `EntityPicker`、`DataTable`、`StatusBadge`、`Chart` 的等价语义。

第 8.4 节只定义单对象录入、主从维护、查询列表、列表维护四种**组件组织模式**，明确字段的行列、样式与响应式布局由渲染端决定，不属于 MU。第 8.5 节规定审批对象的静态维护单元必须有独立 `DRAFT` 与 `SUBMIT` action。

第 8.7 节必须逐条列出以下 11 个门禁：M1 字段绑定有效、M7 引用有效、action-tool-behavior 一致、USER_ACTION 与工具严格 1:1、工具被 capability 或 action 引用、组件目录与映射有效、GENERATED 只读无 action、审批双动作、组件引用图无环且无孤儿/重复挂载、capability 可解析且有 utterance、MCP_APP 的 `ui://` URI/MIME/tool 引用有效。

- [ ] **Step 3: 同步框架中的 MU 散点语义**

只改与 MU 直接相关的导读、术语表、依赖图、建模原则、M1 属性到 UI 的映射说明、M2 可追溯说明、评审清单和术语表。将“菜单树、一级菜单、二级菜单、屏幕、ASCII 布局、跳选框、下拉列表框”改为“能力目录、工具契约、界面单元、组件结构、EntityPicker、Select”。不得改写任何阶段一、应用构建或运行时内容。

若框架有变更历史表，追加：

```markdown
| v9.1 | 2026-08-31 | MU UI 模型升级为能力目录、工具契约与界面单元；替换菜单树与 ASCII 布局；新增 11 条 MU 门禁 | |
```

- [ ] **Step 4: 验证第八章与散点变更**

Run:

```powershell
$document = Get-Content -Raw -Encoding UTF8 'references/ontology_modeling_framework_v9.md'
$chapter = [regex]::Match($document, '(?s)# 第八章.*?(?=^# 第九章)').Value
$requiredHeadings = @('## 8.1','## 8.2','### 8.2.1','### 8.2.2','### 8.2.3','### 8.2.4','### 8.2.5','### 8.2.6','### 8.2.7','### 8.2.8','## 8.3','### 8.3.1','## 8.4','## 8.5','## 8.6','## 8.7')
$missing = $requiredHeadings | Where-Object { $chapter -notmatch [regex]::Escape($_) }
$oldTerms = [regex]::Matches($chapter, '菜单树|一级菜单|二级菜单|ASCII|screenType|SINGLE_FORM|LIST_MAINTENANCE|MASTER_DETAIL_FORM|QUERY_LIST|跳选框|下拉列表框')
if ($missing -or $oldTerms) { $missing; $oldTerms.Value; exit 1 }
"Chapter headings: $($requiredHeadings.Count); old terms: $($oldTerms.Count)"
```

Expected: `Chapter headings: 16; old terms: 0`.

- [ ] **Step 5: 验证 11 条门禁**

Run:

```powershell
$document = Get-Content -Raw -Encoding UTF8 'references/ontology_modeling_framework_v9.md'
$gateSection = [regex]::Match($document, '(?s)## 8\.7.*?(?=^# 第九章)').Value
$rules = [regex]::Matches($gateSection, '(?m)^\d+\.').Count
if ($rules -ne 11) { "Gate count: $rules"; exit 1 }
'Gate count: 11'
```

Expected: `Gate count: 11`.

### Task 2: 将范例 MU YAML 迁移到 v2.0

**Files:**

- Modify: `reference-example/mu-ui-model.yaml`
- Conditionally modify: `reference-example/manifest.json`

**Interfaces:**

- Consumes: Task 1 的 MU v2.0 元模型；既有 M1/M2/M5/M7 中的稳定 ID。
- Produces: 符合 v2.0 门禁的范例 `mu-ui-model.yaml`。

- [ ] **Step 1: 提取既有模型事实，禁止编造引用**

Run:

```powershell
$behaviorFile = 'reference-example/m2-behavior-model.yaml'
$userActions = Select-String -Path $behaviorFile -Pattern 'triggerType: USER_ACTION' -Context 2,0 | ForEach-Object { $_.Context.PreContext + $_.Line } | Select-String -Pattern '^\s*- id:|^\s+id:' | ForEach-Object { ($_ -replace '^\s*-?\s*id:\s*','').Trim() }
$systemActions = Select-String -Path $behaviorFile -Pattern 'triggerType: SYSTEM' -Context 2,0 | ForEach-Object { $_.Context.PreContext + $_.Line } | Select-String -Pattern '^\s*- id:|^\s+id:' | ForEach-Object { ($_ -replace '^\s*-?\s*id:\s*','').Trim() }
"USER_ACTION=$($userActions.Count)"; $userActions
"SYSTEM=$($systemActions.Count)"; $systemActions
```

Run:

```powershell
Select-String -Path 'reference-example/m1-object-model.yaml','reference-example/m5-actor-model.yaml','reference-example/m7-report-model.yaml' -Pattern '^\s*- id:|^\s+id:' | ForEach-Object { "$($_.Path):$($_.Line.Trim())" }
```

Expected: 每个后续引用都可以从这些输出的真实 ID 中选择；不得保留任何占位 ID。

- [ ] **Step 2: 重写顶层结构与工具契约**

将文件替换为 v2.0 的 `application`、`capabilities`、`tools` 和 `uiUnits` 四段；`version` 写为 `"2.0"`。对每个 Step 1 发现的 USER_ACTION 行为创建一个且仅一个 `tools[]` 条目；`toolName` 由行为语义生成 snake_case 名称。

每个工具引用实际存在的 M1/M5/M7 ID，声明 `title`、`description`、输入/输出字段、`readOnlyHint`、`destructiveHint` 和权限。查询行为的 `readOnlyHint` 必须为 `true`；仅实际具有撤销、作废或删除语义的行为可设 `destructiveHint: true`。不得为 Step 1 发现的 SYSTEM 行为创建工具。

- [ ] **Step 3: 写能力目录与界面单元**

从原范例的业务能力迁移为扁平 `capabilities[]`：每项具备描述性 `capabilityId`、名称、意图、至少一条 `utterances`、真实 `toolRef` 或真实 `uiUnitRef`、以及适用权限。能力数与界面单元数不要求相等，但每个 capability 至少解析到一项有效引用。

定义下列三类界面单元各至少一个：

```yaml
- uiUnitId: ui-contract-maintain
  unitType: A2UI_SURFACE
  renderMode: STATIC

- uiUnitId: ui-execution-report
  unitType: MCP_APP
  renderMode: STATIC
  mcpApp:
    resourceUri: "ui://contract/execution-report"
    mimeType: "text/html;profile=mcp-app"

- uiUnitId: ui-adhoc-analysis
  unitType: A2UI_SURFACE
  renderMode: GENERATED
```

所有静态 A2UI 单元使用有效的 `surface.root` 和扁平 `surface.components` 邻接表；所有组件引用 M1 的真实字段。`ui-adhoc-analysis` 仅允许引用实际存在的 M7 数据源和 `readOnlyHint: true` 的工具，且完全不含 `actions` 段。带审批的维护单元使用两个独立 action：一个 `DRAFT`，一个 `SUBMIT`，分别引用与其 `behaviorRef` 完全一致的工具。

- [ ] **Step 4: 更新 manifest（仅在确有字段可更新时）**

读取 `reference-example/manifest.json`。若它仅含现有的 `model_files` 清单，如当前版本所示，则保持文件不变；若存在 MU 的版本或描述字段，将其更新到 `2.0` 与“能力目录 + 工具契约 + 界面单元”。不得新增无既有 schema 支持的 manifest 字段。

- [ ] **Step 5: 验证 v2.0 结构与不存在的旧字段**

Run:

```powershell
$file = 'reference-example/mu-ui-model.yaml'
$required = @('version: "2.0"','application:','capabilities:','tools:','uiUnits:','unitType: A2UI_SURFACE','unitType: MCP_APP','renderMode: STATIC','renderMode: GENERATED')
$missing = $required | Where-Object { -not (Select-String -Path $file -SimpleMatch -Pattern $_) }
$old = Select-String -Path $file -Pattern '^\s*menus:|^\s*screens:|^\s*screenId:|^\s*screenType:|^\s*layout:'
if ($missing -or $old) { $missing; $old; exit 1 }
'v2.0 structure present; legacy structural fields absent.'
```

Expected: `v2.0 structure present; legacy structural fields absent.`

- [ ] **Step 6: 验证行为与工具严格 1:1，且 SYSTEM 行为未暴露**

Run:

```powershell
$behaviorFile = 'reference-example/m2-behavior-model.yaml'
$muFile = 'reference-example/mu-ui-model.yaml'
$userActions = Select-String -Path $behaviorFile -Pattern 'triggerType: USER_ACTION' -Context 2,0 | ForEach-Object { $_.Context.PreContext + $_.Line } | Select-String -Pattern '^\s*- id:|^\s+id:' | ForEach-Object { ($_ -replace '^\s*-?\s*id:\s*','').Trim() } | Sort-Object
$systemActions = Select-String -Path $behaviorFile -Pattern 'triggerType: SYSTEM' -Context 2,0 | ForEach-Object { $_.Context.PreContext + $_.Line } | Select-String -Pattern '^\s*- id:|^\s+id:' | ForEach-Object { ($_ -replace '^\s*-?\s*id:\s*','').Trim() } | Sort-Object
$toolBehaviors = Select-String -Path $muFile -Pattern '^\s+behaviorRef:' | ForEach-Object { ($_ -replace '^\s*behaviorRef:\s*','').Trim() } | Sort-Object
$duplicateToolBehaviors = $toolBehaviors | Group-Object | Where-Object Count -ne 1
if ((Compare-Object $userActions $toolBehaviors) -or $duplicateToolBehaviors -or ($systemActions | Where-Object { $_ -in $toolBehaviors })) { 'Behavior-tool mapping failed.'; Compare-Object $userActions $toolBehaviors; $duplicateToolBehaviors; exit 1 }
"Strict 1:1 mapping verified for $($userActions.Count) USER_ACTION behaviors."
```

Expected: `Strict 1:1 mapping verified for <count> USER_ACTION behaviors.`

- [ ] **Step 7: 验证 GENERATED 只读和组件图约束**

Run:

```powershell
$muFile = 'reference-example/mu-ui-model.yaml'
$contents = Get-Content -Raw -Encoding UTF8 $muFile
$generated = [regex]::Match($contents, '(?ms)^  - uiUnitId: ui-adhoc-analysis\b.*?(?=^  - uiUnitId:|\z)').Value
if (-not $generated -or $generated -match '(?m)^    actions:') { 'Generated unit is missing or declares actions.'; exit 1 }
$toolReadOnly = @{}
$toolBlocks = [regex]::Matches($contents, '(?ms)^  - toolName: (?<name>[a-z0-9_]+)\b.*?(?=^  - toolName:|^uiUnits:|\z)')
foreach ($block in $toolBlocks) { $toolReadOnly[$block.Groups['name'].Value] = $block.Value -match 'readOnlyHint:\s*true' }
$allowedTools = [regex]::Matches($generated, '(?m)^\s*-\s*([a-z0-9_]+)\s*$') | ForEach-Object { $_.Groups[1].Value }
$writeTools = $allowedTools | Where-Object { -not $toolReadOnly[$_] }
if ($writeTools) { "Generated unit has write tools: $($writeTools -join ', ')"; exit 1 }
'Generated unit has no actions and only read-only tools.'
```

Expected: `Generated unit has no actions and only read-only tools.`

人工逐个检查每个 STATIC surface：`root` 存在、所有 `explicitList` 子组件存在、每个非根组件有且仅有一个父引用，并且引用图无环。将每个 surface 的检查结果记录在提交说明或评审记录中。

### Task 3: 同步两阶段技能的 MU 术语

**Files:**

- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `README_EN.md`

**Interfaces:**

- Consumes: Task 1 的术语和 Task 2 的 v2.0 范例。
- Produces: 对外文档将 MU 描述为建模产物，不承诺 UI 原型或应用构建。

- [ ] **Step 1: 更新 SKILL.md 的阶段二内容**

将“MU UI”改为“MU 能力与界面”，将建模顺序末项改为“MU（工具契约 → 能力目录 → 界面单元）”。将 M2/MU 可追溯门禁改为：

```markdown
M2 `triggerType=USER_ACTION` 行为须 1:1 暴露为 MU 工具契约，且该工具被至少一个能力或操作功能点引用；MU 引用的工具与行为须存在且一致。
```

不得增加阶段七、UI 原型、应用构建、运行命令或任何已删除资料的引用。

- [ ] **Step 2: 同步中英文 README 的阶段二介绍**

在 `README.md` 将 MU 表述改为“MU 能力与界面（能力目录、工具契约、界面单元）”；在 `README_EN.md` 使用“MU capabilities and UI (capability catalog, tool contracts, UI units)”。只修改阶段二及模型一致性表述，保持两阶段流程、阶段零至阶段六、安装与许可内容不变。

- [ ] **Step 3: 验证对外边界未回退**

Run:

```powershell
$files = @('SKILL.md','README.md','README_EN.md')
$forbidden = '阶段七|UI 原型|techbase|code-app|code-paas|应用构建|App Construction|仅构建|Construction only|本体模型业务功能开发指导书|AI 原生应用技术架构设计文档|UI-UE界面设计规范'
$matches = Select-String -Path $files -Pattern $forbidden
if ($matches) { $matches | ForEach-Object { "$($_.Path):$($_.LineNumber):$($_.Line)" }; exit 1 }
'Two-stage public boundary preserved.'
```

Expected: `Two-stage public boundary preserved.`

### Task 4: 最终验收

**Files:**

- Verify: `references/ontology_modeling_framework_v9.md`
- Verify: `reference-example/mu-ui-model.yaml`
- Verify: `SKILL.md`
- Verify: `README.md`
- Verify: `README_EN.md`

**Interfaces:**

- Consumes: Tasks 1-3.
- Produces: 可审核的 MU v2.0 建模语义和未破坏的两阶段技能边界。

- [ ] **Step 1: 验收 MU 术语与模型结构**

Run:

```powershell
$files = @('references/ontology_modeling_framework_v9.md','reference-example/mu-ui-model.yaml','SKILL.md','README.md','README_EN.md')
$required = '能力目录|工具契约|界面单元'
foreach ($file in $files) {
  if (-not (Select-String -Path $file -Pattern $required)) { "Missing MU v2 terminology: $file"; exit 1 }
}
'MU v2 terminology present in all required documents.'
```

Expected: `MU v2 terminology present in all required documents.`

- [ ] **Step 2: 复核运行时与需求探索边界未改变**

Run:

```powershell
$forbiddenPaths = @('techbase','references/本体模型业务功能开发指导书.md','references/AI 原生应用技术架构设计文档.md','references/UI-UE界面设计规范.md')
$existing = $forbiddenPaths | Where-Object { Test-Path $_ }
if ($existing) { $existing; exit 1 }
$forbiddenFiles = @('references/AI需求探索与确认提示词V9.0.md','reference-example/合同管理需求规格说明书-V9.md')
$changedForbidden = git diff --name-only | Where-Object { $_ -in $forbiddenFiles }
if ($changedForbidden) { $changedForbidden; exit 1 }
'No deleted construction asset restored and no stage-one artifact modified.'
```

Expected: `No deleted construction asset restored and no stage-one artifact modified.`

- [ ] **Step 3: 审阅精确变更范围与空白错误**

Run:

```powershell
git diff --check
git diff --name-only
```

Expected: `git diff --check` 无输出；变更仅限 Global Constraints 中列出的文件及已有的 `docs/superpowers/` 设计、计划文件。不得出现 `.codeartsdoer/` 或已删除资产的恢复。

## Self-Review 记录

- 规格边界：计划不修改任何阶段一文档、需求文档范例或已删除资产；Task 3 与 Task 4 均显式验证该约束。
- 可执行性：所有自动验证使用当前 PowerShell 可用的 `Select-String`、`Compare-Object` 与 Git，不依赖 `rg`、`sed`、`sort`、`diff` 或 `/tmp`。
- 引用完整性：Task 2 先从 M1/M2/M5/M7 抽取真实 ID，再写入范例，消除了原计划的 `dataSources` 占位值。
- 1:1 验证：Task 2 Step 6 比较排序后的完整列表、检查工具行为重复，并检查 SYSTEM 行为未暴露，能发现原集合比较遗漏的重复映射。
- 提交边界：计划禁止 `git add -A` 与自动提交，避免将当前已有的两阶段收敛工作或 `.codeartsdoer/` 本地缓存混入变更。
