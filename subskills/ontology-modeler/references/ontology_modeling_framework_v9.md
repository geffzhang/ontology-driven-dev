# 本体驱动的软件建模方案
**Ontology-Driven Software Modeling Framework（单体同步版）**

> 完整建模规范 · 七大模型元文件 · 实施指南
> 版本 9.1 | 2026年8月
>
> v9.1 在 v9.0 基础上重做 MU 模型以适配 AI 原生交互（详见 §8）。其余 M1/M2/M3/M5/M6/M7 语义不变。
> v9.0 由 v6.0 裁剪而来，面向**单体同步部署的中小型业务系统**（如销售合同执行管理系统），
> 以"同步流程编排"替代"事件驱动解耦"。裁剪与改造要点：
>
> 1. **移除四个模型**：ME 事件模型、M4 场景模型、MM 对象-数据表映射模型、MI 接口模型；
> 2. **M2 行为模型**：移除 `producedEvents` 与 `triggerType=EVENT`，新增 `syncTriggers` 字段，
>    用于表达"行为成功后同步调用下游行为"的跨对象联动，条件判断引用 M3 规则；
> 3. **M3 规则模型**：移除 `EVENT_DRIVEN` 事件驱动规则及订阅/触发字段，规则一律"被同步调用"；
> 4. **M5 主体模型**：移除外部实体（ExternalEntity）与外部接口契约，仅保留内部角色与权限；
> 5. **M6 流程模型**：移除事件触发、事件等待与场景调用活动，端到端协同流与审批流均为同步编排；
> 6. **M7 查询报表模型**：参考 SQL 改为可选（物理表名在实现阶段确定）；
> 7. **MU UI 模型（v9.1 重做）**：由"菜单树 + ASCII 屏幕"改为面向 AI 原生交互的"应用 → 能力目录 → 工具契约 → 界面单元（`unitType` × `renderMode` 两个正交维度）→ 操作功能点"五层结构，并新增 A2UI Surface 与 MCP App 双形态、A2UI 组件目录映射（§8.3）、GENERATED 模式只读约束与"带审批功能必须含保存草稿/提交双动作点"规则。

---

## 目录

1. [方案概述与设计哲学](#第一章--方案概述与设计哲学)
2. [M1 对象模型](#第二章--m1-对象模型)
3. [M2 行为模型](#第三章--m2-行为模型)
4. [M3 规则模型](#第四章--m3-规则模型)
5. [M5 主体模型](#第五章--m5-主体模型)
6. [M6 流程模型](#第六章--m6-流程模型)
7. [M7 查询统计与报表模型](#第七章--m7-查询统计与报表模型)
8. [MU UI 模型](#第八章--mu-ui-模型)
9. [传统需求覆盖度分析](#第九章--传统需求覆盖度分析)
10. [实施指南与最佳实践](#第十章--实施指南与最佳实践)
11. [附录：术语对照表](#附录--术语对照表)

---

# 第一章  方案概述与设计哲学

## 1.1  框架定位

本方案面向具有明确领域边界、**采用单体同步部署**的中小型业务软件，以"本体"（Ontology）作为系统设计的核心隐喻，将业务世界中的"存在（What）"、"行为（How）"、"规则（Why）"、"主体权限（Who）"、"流程流转（Workflow）"、"查询表达（Read/Report）"和"界面入口（UI）"分离建模，并通过**同步流程编排**实现跨对象协作。

本版本不再引入事件驱动架构（EDA）。跨对象联动由"行为完成后同步调用下游行为（经规则判断）"或"端到端协同流中的同步步骤"承载，所有处理在同一事务边界内顺序完成，符合单体系统的简单性与可调试性要求。

与传统需求分析方法（如 UML 用例图、功能规格说明书）相比，本框架具有以下核心差异：

- **语义驱动**：模型元素具有明确的业务语义，而非纯粹的技术描述；
- **正交分解**：对象、行为、规则、主体、流程、查询报表和界面各自承担单一职责，可独立演进；
- **同步编排**：跨对象协作通过流程编排或行为后置同步调用完成，链路顺序、可预测、可调试；
- **流程分离**：端到端协同流和审批流独立建模，不与行为内部逻辑混合；
- **读写分离**：跨对象查询、统计和固定报表独立建模，不把复杂查询结构塞入原子行为或业务规则；
- **可追溯性**：每个实现单元都可以溯源到具体的本体模型定义。

## 1.2  七大模型元文件总览

| 编号 | 模型名称 | 核心职责 |
|------|----------|----------|
| **M1** | 对象模型 Object Model | 定义数据实体、实体属性、实体间的双向关联与参照完整性约束 |
| **M2** | 行为模型 Behavior Model | 定义对象的原子行为方法、触发条件、前置后置约束及同步联动（syncTriggers） |
| **M3** | 规则模型 Rule Model | 定义跨对象、跨行为或需要独立复用的业务决策规则（被同步调用） |
| **M5** | 主体模型 Actor Model | 定义系统参与者、角色、权限边界及行为执行授权关系 |
| **M6** | 流程模型 Flow Model | 定义端到端业务协同流和审批流，描述角色任务、系统活动、网关、条件和子流程调用 |
| **M7** | 查询统计与报表模型 Query & Report Model | 定义跨对象查询、统计分析和固定业务报表的来源、关联、条件、结果列、聚合及可选参考 SQL |
| **MU** | UI 模型 UI Model | 定义应用、用户能力目录、M2 行为面向智能体的工具契约、A2UI Surface / MCP App 双形态界面单元及其组件结构、操作功能点；MU 仅作入口与追溯层，不重定义业务语义，也不承载渲染实现与传输协议 |

> 说明：模型编号沿用历史体系（M1～M7、ME、M4、MU、MM、MI）。v9.0 起 **ME、M4、MM、MI 不再建模**，故七个模型编号为 M1、M2、M3、M5、M6、M7、MU，编号顺序不连续属有意保留，便于与历史版本及既有工具链对齐。v9.1 仅重做 MU 的内部结构（M1～M7 语义不变）。

## 1.3  模型间关系全景

七个模型之间的依赖与引用关系如下：

```
M6 流程模型      依赖   M1 对象模型 + M2 行为模型 + M3 规则模型 + M5 角色模型
M7 查询报表模型  依赖   M1 对象模型 + M2 查询行为（一对一绑定）
M2 行为模型      依赖   M1 对象模型 + M3 规则模型 + M5 主体模型（+ syncTriggers 同步联动）
M3 规则模型      引用   M1 对象模型（只读）
M5 主体模型      引用   M1 对象模型 + M2 行为模型（权限绑定）
MU UI 模型      依赖   M1 对象模型 + M2 行为模型 + M6 流程模型 + M7 查询报表模型
```

**关键设计决策**：

1. M2 行为保持原子性：一个行为只操作一个对象，产生确定性的状态变更；跨对象联动通过 `syncTriggers` 同步调用下游行为。
2. `syncTriggers` 中的条件判断必须引用 M3 规则，规则只判断、不直接修改对象状态；对象状态变化始终由行为完成。
3. M6 统一承载端到端业务协同流和审批流。人工活动只能通过 `roleRef` 引用 M5 中的 `roleId`，不得直接引用具体人员或填写自由文本参与人。
4. M6 可以调用 M2 行为、M3 规则及其他 M6 子流程，但不得复制这些模型中的定义。
5. M7 只与 M1、M2 发生直接关系。M7 定义查询内容，M2 定义执行该查询报表对象的原子行为，两者严格一对一；M7 不直接引用 M3、M5 或 M6。
6. MU 是入口层/追溯层：只通过稳定 ID 引用 M1～M7，不重新定义这些模型的任何语义，也不承载 UI 渲染实现、传输协议或前后端代码；MU 的操作功能点是"一次用户动作 → 调用一个工具 → 执行一个 M2 行为"的唯一界面入口。
7. **可追溯门禁**：M2 中 `triggerType=USER_ACTION` 的行为必须被至少一个 MU 操作功能点引用；MU 操作功能点引用的行为必须存在（反向可追溯、正向一致）。

## 1.4  同步联动的标准语义

跨对象联动在本框架中的标准表达如下：

**无条件联动（直接同步调用）**：

```text
源对象行为
-> 成功后同步调用下游行为（无额外条件）
-> 目标对象行为
```

**有条件联动（规则介入）**：

```text
源对象行为
-> 成功后同步调用 M3 规则判断
-> 规则满足：同步调用目标行为；规则不满足：不执行目标行为
-> 目标对象行为
```

> 强制语义边界：行为只回答"做什么并改变什么状态"；规则只回答"条件是否满足"；行为之间的联动关系由 `syncTriggers` 显式声明。禁止把"全部收齐时关闭合同"这类条件结论写进源行为本身，必须拆为"M3 关闭校验规则 + 目标关闭行为"。

---

# 第二章  M1 对象模型

## 2.1  设计目标与领域建模原则

对象模型是整个本体体系的基础，负责描述业务域中的核心领域对象及其关系，对应领域驱动设计（DDD）中的领域模型层。其核心设计原则是：

- **业务完整性优先**：从业务视角建模，而非数据库表结构视角；
- **聚合边界清晰**：通过聚合根（Aggregate Root）保证业务不变性；
- **实现延迟绑定**：对象模型关注业务语义，数据库表拆分在实现阶段决策。

> **关键设计理念**：对象模型描述的是"业务对象"而非"数据库表"。例如，合同（包含合同头和付款条款明细）在业务层面是一个完整的聚合，不应拆分为两个独立实体建模。数据库层面的表拆分是持久化实现阶段的技术决策，v9.0 中不再由独立映射模型（MM）承载，而由实现阶段的 ORM 注解或 DDL 直接落地。

## 2.2  领域对象分类体系

| 对象类型 | 说明 | 标识特征 | 生命周期 |
|----------|------|----------|----------|
| **聚合根（Aggregate Root）** | 业务完整性的边界，对外暴露的唯一入口，包含子实体和值对象 | 有全局唯一标识 | 有独立生命周期，可独立存在 |
| **实体（Entity）** | 聚合内部的子对象，有标识但不能脱离聚合根独立存在 | 有聚合内唯一标识 | 依赖聚合根生命周期，级联删除 |
| **值对象（Value Object）** | 无标识的不可变对象，通过属性值判断相等性，描述聚合的某个特征 | 无标识，通过值相等 | 依附于聚合根或实体，不可变 |

### 2.2.1  聚合根设计原则

1. **唯一入口原则**：外部只能通过聚合根访问聚合内部对象，不能直接操作子实体；
2. **事务边界原则**：一个事务只修改一个聚合根，跨聚合通过同步联动（syncTriggers）或流程编排完成；
3. **不变性保护**：聚合根负责维护聚合内的业务不变性约束；
4. **引用原则**：聚合之间通过 ID 引用，而非对象引用，避免聚合边界模糊。

### 2.2.2  聚合识别指南

| 判断维度 | 聚合内（同一聚合） | 聚合间（独立聚合） |
|----------|-------------------|-------------------|
| 业务完整性 | 必须同时存在才有业务意义 | 可以独立存在 |
| 生命周期 | 同生共死，级联删除 | 独立生命周期 |
| 事务边界 | 必须在同一事务中修改 | 可在不同事务中修改 |
| 访问路径 | 只能通过聚合根访问 | 可以直接访问 |
| 引用方式 | 对象引用（组合/聚合） | ID 引用（关联） |

**示例**：
- ✅ 合同 + 付款条款 → 同一聚合（合同是聚合根，条款是子实体）；
- ✅ 合同 + 开票明细 → 独立聚合（开票有独立生命周期，通过合同 ID 关联）；
- ❌ 合同 + 客户 → 独立聚合（通过客户 ID 关联，而非组合）；
- ❌ 合同 + 产品 → 独立聚合（产品有独立生命周期）。

## 2.3  模型元素规范

### 2.3.1  聚合根（Aggregate Root）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| id | String / UUID | 聚合根全局唯一标识 |
| name | String | 聚合根业务名称（中文，需唯一） |
| alias | String | 英文标识符，用于代码映射 |
| description | String | 业务含义说明 |
| aggregateType | Enum | AGGREGATE_ROOT（标识为聚合根） |
| lifecycle | Enum[] | 聚合根生命周期状态列表 |
| attributes | Attribute[] | 聚合根自身属性集合 |
| entities | Entity[] | 聚合内子实体集合（组合关系） |
| valueObjects | ValueObject[] | 聚合内值对象集合 |
| invariants | Invariant[] | 聚合不变性约束（业务规则） |
| tags | String[] | 分类标签 |

### 2.3.2  子实体（Entity）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| name | String | 子实体名称 |
| alias | String | 英文标识符 |
| description | String | 业务含义说明 |
| localId | String | 聚合内唯一标识字段名 |
| attributes | Attribute[] | 子实体属性集合 |
| cardinality | Enum | 与聚合根的基数关系：ONE / ZERO_OR_ONE / ONE_OR_MORE / ZERO_OR_MORE |
| cascadeDelete | Boolean | 是否级联删除（默认 true） |

### 2.3.3  值对象（Value Object）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| name | String | 值对象名称 |
| alias | String | 英文标识符 |
| description | String | 业务含义说明 |
| attributes | Attribute[] | 值对象属性集合 |
| immutable | Boolean | 是否不可变（默认 true） |
| equalityFields | String[] | 用于判断相等性的字段列表 |

### 2.3.4  属性（Attribute）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| name | String | 属性名（英文 camelCase） |
| label | String | 业务展示名（中文） |
| type | DataType | 类型：String / Integer / Decimal / Date / DateTime / Boolean / Enum / Money / ValueObject / AggregateRootRef / DictionaryRef |
| required | Boolean | 是否必填 |
| unique | Boolean | 是否唯一（仅对聚合根属性有效） |
| defaultValue | Any | 默认值 |
| enumValues | String[] | 当 type=Enum 时的枚举值列表 |
| valueObjectRef | String | 当 type=ValueObject 时引用的值对象名称 |
| targetAggregate | AggregateRef | 当 type=AggregateRootRef 时必填，指向被引用聚合根的 ID |
| dictionaryRef | DictionaryTypeRef | 当 type=DictionaryRef 时必填，包含 dictionaryId 和 typeCode |
| refRules | AttributeRule[] | 可选；只依赖当前属性值、可在该属性内部完整定义的扩展规则 |

`AggregateRootRef` 表示"存储另一个聚合根 ID 的标量属性"，而不是内嵌对象或数据库外键对象。该类型在代码生成时仍可映射为目标聚合根 ID 的实际标量类型，但在本体层必须通过 `targetAggregate` 显式声明目标。**在 MU UI 模型（§8）中，AggregateRootRef 属性映射为 `EntityPicker` 组件（跳选框），必须声明 `targetAggregate` 与 `searchToolRef`。**

`DictionaryRef` 表示属性值来自 M1 对象模型中的数据字典类型。业务数据保存字典项稳定的 `code`，界面显示 `label`。`DictionaryRef` 不得同时声明 `enumValues`。**在 MU UI 模型（§8）中，DictionaryRef 与 Enum 属性映射为 `Select` 组件（下拉列表框）。**

#### 属性扩展规则（AttributeRule / refRules）

`refRules` 用于定义只依赖当前属性值即可判断的局部规则。此类规则属于 M1 对象模型，不得重复放入 M3 规则模型。

| 属性名 | 类型 | 说明 |
|--------|------|------|
| name | String | 属性规则名称，在当前属性内唯一 |
| description | String | 规则业务说明 |
| expression | String | 属性规则表达式，使用 `value` 表示当前属性值 |
| violationMessage | String | 规则不满足时返回的业务提示 |
| enforcedAt | Enum | ON_CREATE / ON_UPDATE / ON_DELETE / ALWAYS |

属性规则分层原则：

1. 可以用内置字段表达的约束，优先使用内置字段（如 `required`、`unique`），不重复写入 `refRules`；
2. 无法由内置字段表达、但只依赖当前属性值的规则使用 `refRules`（如金额必须大于 0）；
3. 依赖同一对象多个属性或聚合内部子实体的规则使用聚合 `invariants`（如付款比例合计等于 100%）；
4. 依赖其他独立对象、多个行为结果或需要被多个行为复用的规则，进入 M3 规则模型。

### 2.3.5  数据字典（Data Dictionary）

数据字典是对象模型中的引用数据定义，不是值对象、聚合根或运行时业务实体。同一个数据字典对象可以维护多个平级字典类型。

#### 字典类型

| 属性名 | 类型 | 说明 |
|--------|------|------|
| typeCode | String | 数据字典对象内唯一的稳定编码 |
| typeName | String | 中文显示名称 |
| description | String | 可选说明 |
| items | DictionaryItem[] | 平级字典项，不允许 parentCode |

#### 字典项

| 属性名 | 类型 | 说明 |
|--------|------|------|
| code | String | 类型内唯一的稳定业务存储值 |
| label | String | 界面显示文本，可修改但不影响已有业务数据 |
| enabled | Boolean | 是否可被新增数据选择；已使用项应停用而非删除 |
| sortOrder | Integer | 显示顺序 |

#### 字典引用约束

- `dictionaryRef.dictionaryId` 必须指向存在的数据字典对象；
- `dictionaryRef.typeCode` 必须指向该对象内存在的字典类型；
- 数据字典项当前为平级结构，规范中不定义 `parentCode` 或其他层级字段。

### 2.3.6  聚合不变性约束（Invariant）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| name | String | 约束名称 |
| expression | String | 约束表达式，可跨聚合内的子实体和值对象 |
| violationMessage | String | 违反约束时的业务错误消息 |
| enforcedAt | Enum | ON_CREATE / ON_UPDATE / ON_DELETE / ALWAYS |

### 2.3.7  聚合间关联（Aggregate Association）

聚合之间通过 ID 引用建立关联：

| 属性名 | 类型 | 说明 |
|--------|------|------|
| id | String | 关联唯一标识 |
| sourceAggregate | AggregateRef | 来源聚合根 |
| targetAggregate | AggregateRef | 目标聚合根 |
| associationType | Enum | REFERENCE（引用）/ DEPENDENCY（依赖） |
| sourceRole | String | 来源端角色名 |
| targetRole | String | 目标端角色名 |
| cardinality | Enum | ONE_TO_ONE / ONE_TO_MANY / MANY_TO_ONE / MANY_TO_MANY |
| referenceField | String | 存储目标聚合根 ID 的字段名 |

## 2.4  YAML 元文件模板（合同聚合示例）

```yaml
# M1 对象模型元文件 - m1-object-model.yaml
model_type: OBJECT
version: "2.1"
domain: "销售合同执行管理"

aggregates:
  - id: AGG-CONTRACT-001
    name: 合同
    alias: Contract
    aggregateType: AGGREGATE_ROOT
    description: 对外销售产生的合同签订信息，包含合同基本信息和付款条款明细
    lifecycle: [草稿, 待审批, 已生效, 已关闭, 已作废]
    tags: [核心域]

    attributes:
      - name: contractNo
        label: 合同编号
        type: String
        required: true
        unique: true
      - name: contractName
        label: 合同名称
        type: String
        required: true
        refRules:
          - name: 合同名称长度限制
            description: 合同名称最多 100 个字符
            expression: "LENGTH(value) <= 100"
            violationMessage: 合同名称不能超过 100 个字符
            enforcedAt: ALWAYS
      - name: contractType
        label: 合同类型
        type: DictionaryRef
        dictionaryRef:
          dictionaryId: DICT-CONTRACT-BASE
          typeCode: CONTRACT_TYPE
        required: true
      - name: productId
        label: 所属产品
        type: AggregateRootRef
        targetAggregate: AGG-PRODUCT-001
        required: true
      - name: customerId
        label: 所属客户
        type: AggregateRootRef
        targetAggregate: AGG-CUSTOMER-001
        required: true
      - name: departmentId
        label: 所属部门
        type: AggregateRootRef
        targetAggregate: AGG-DEPARTMENT-001
        required: true
      - name: ownerId
        label: 责任人
        type: AggregateRootRef
        targetAggregate: AGG-EMPLOYEE-001
        required: true
      - name: signDate
        label: 签订时间
        type: Date
        required: true
      - name: totalAmount
        label: 合同总金额（含税）
        type: Money
        required: true
        refRules:
          - name: 合同总金额必须为正数
            description: 合同总金额必须大于 0
            expression: "value > 0"
            violationMessage: 合同总金额必须大于 0
            enforcedAt: ALWAYS
      - name: purchaseAmount
        label: 对外采购金额
        type: Money
      - name: taxRate
        label: 合同税率
        type: Decimal
        required: true
        refRules:
          - name: 税率合法范围
            description: 税率取值在 0 到 1 之间
            expression: "value >= 0 AND value <= 1"
            violationMessage: 税率取值应在 0 到 1 之间
            enforcedAt: ALWAYS
      - name: status
        label: 合同状态
        type: Enum
        enumValues: [草稿, 待审批, 已生效, 已关闭, 已作废]
        required: true

    entities:
      - name: 付款条款
        alias: PaymentStage
        description: 合同付款阶段明细
        localId: stageId
        cardinality: ONE_OR_MORE
        cascadeDelete: true
        attributes:
          - name: stageId
            label: 付款阶段编号
            type: Integer
            required: true
          - name: stageName
            label: 付款阶段名称
            type: String
            required: true
          - name: payRatio
            label: 付款比例
            type: Decimal
            required: true
            refRules:
              - name: 付款比例合法范围
                description: 付款比例在 0 到 100 之间
                expression: "value > 0 AND value <= 100"
                violationMessage: 付款比例应在 0 到 100 之间
                enforcedAt: ALWAYS

    invariants:
      - name: 付款比例合计等于 100
        expression: "SUM(stages.payRatio) == 100"
        violationMessage: 付款阶段付款比例合计必须等于 100
        enforcedAt: ON_CREATE

  # 其余聚合（产品、客户、部门、人员、开票明细、收款）略，结构同上
  - id: AGG-INVOICE-001
    name: 开票明细
    alias: Invoice
    aggregateType: AGGREGATE_ROOT
    description: 基于付款阶段对客户开票形成的开票明细
    lifecycle: [未收款, 部分收款, 已收款, 已作废]
    attributes:
      - name: invoiceNo
        label: 开票编号
        type: String
        required: true
        unique: true
      - name: contractId
        label: 对应合同
        type: AggregateRootRef
        targetAggregate: AGG-CONTRACT-001
        required: true
      - name: invoiceAmount
        label: 开票金额
        type: Money
        required: true
      - name: invoiceTaxRate
        label: 开票税率
        type: Decimal
        required: true
      - name: invoiceDate
        label: 开票时间
        type: Date
        required: true
      - name: receivedFlag
        label: 是否收款
        type: Boolean
        required: true
        defaultValue: false
      - name: receivedDate
        label: 收款时间
        type: Date

# 数据字典
data_dictionaries:
  - id: DICT-CONTRACT-BASE
    name: 合同基础数据字典
    types:
      - typeCode: CONTRACT_TYPE
        typeName: 合同类型
        items:
          - code: PRODUCT
            label: 产品合同
            enabled: true
            sortOrder: 10
          - code: SERVICE
            label: 服务合同
            enabled: true
            sortOrder: 20
          - code: INTEGRATION
            label: 集成合同
            enabled: true
            sortOrder: 30

# 聚合间关联
aggregate_associations:
  - id: ASSOC-CONTRACT-INVOICE
    sourceAggregate: AGG-CONTRACT-001
    targetAggregate: AGG-INVOICE-001
    associationType: REFERENCE
    sourceRole: 产生开票
    targetRole: 所属合同
    cardinality: ONE_TO_MANY
    referenceField: contractId
```

## 2.5  聚合建模最佳实践

### 2.5.1  聚合大小控制

- **小聚合优先**：聚合越小，并发冲突越少，性能越好；
- **业务完整性优先**：不能为了性能牺牲业务完整性；
- **经验法则**：一个聚合包含的子实体不超过 3-5 个，总字段数不超过 30 个。

### 2.5.2  聚合拆分时机

| 拆分信号 | 处理方式 |
|----------|----------|
| 子实体有独立生命周期 | 提升为独立聚合根，通过 ID 引用 |
| 子实体被多个聚合引用 | 提升为独立聚合根 |
| 聚合内部分字段很少一起修改 | 拆分为多个聚合，通过同步联动保持一致性 |

### 2.5.3  数据冗余策略

为避免跨聚合查询，可在聚合内冗余其他聚合的关键展示信息（如名称、编码），通过同步联动保持最终一致。只冗余展示用的稳定字段，不冗余频繁变化的字段。

### 2.5.4  聚合根 ID 设计

| ID 类型 | 适用场景 | 示例 |
|---------|----------|------|
| UUID | 分布式系统，客户端生成 ID | `550e8400-...` |
| 业务编号 | 有业务规则的编号体系 | `HT-2026-08-0001` |
| 自增 ID | 单库自增主键 | `10001` |

---

# 第三章  M2 行为模型

## 3.1  设计目标

行为模型定义对象能够执行的原子行为方法。每个行为是单一对象发出的、不可再分的核心操作单元。复杂判断通过规则模型注入；跨对象联动通过 `syncTriggers` 同步调用下游行为；端到端和审批流转通过 M6 流程编排。

> **关键设计原则**：行为模型的核心约束是"原子性"——每个行为方法只做一件事，操作一个对象，产生确定性的状态变更。跨对象的联动关系必须通过 `syncTriggers` 显式声明，不得在行为方法内部隐含地直接操作其他聚合。

## 3.2  模型元素规范

### 3.2.1  行为（Behavior）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| id | String | 行为唯一标识，建议格式：{EntityAlias}_{ActionName} |
| name | String | 行为业务名称（中文动宾短语） |
| ownerEntity | EntityRef | 行为所属对象 |
| behaviorType | Enum | COMMAND（指令，改变状态）/ QUERY（查询，只读） |
| triggerType | Enum | USER_ACTION（用户触发）/ SYSTEM（系统自动） |
| preconditions | Condition[] | 前置条件集合，全部满足才可执行 |
| postconditions | StateChange[] | 执行后的状态变更描述 |
| appliedRules | RuleRef[] | 调用的规则模型引用 |
| requiredPermissions | PermissionRef[] | 执行所需权限（引用 M5 主体模型） |
| syncTriggers | SyncTrigger[] | 执行成功后同步调用的下游行为（跨对象联动） |
| queryReportRef | QueryReportRef | 当 behaviorType=QUERY 且行为执行 M7 查询统计或报表对象时填写；与 M7.behaviorRef 严格一对一 |

### 3.2.2  同步联动（SyncTrigger）

`syncTriggers` 是 v9.0 替代原事件模型的跨对象联动载体。行为执行成功后，按顺序同步执行 `syncTriggers` 中声明的联动：

| 属性名 | 类型 | 说明 |
|--------|------|------|
| ruleRef | RuleRef | 可选；条件判断规则引用。填写时表示"规则满足才触发下游行为" |
| behaviorRef | BehaviorRef | 必填；满足条件（或无额外条件）时同步调用的下游行为 |
| description | String | 联动业务说明 |

约束：

1. `ruleRef` 省略表示无条件联动，下游行为直接同步调用；
2. `ruleRef` 填写时必须引用 M3 规则，规则只判断条件，不修改状态；
3. 同一行为可声明多条 `syncTriggers`，按声明顺序执行；
4. 下游行为必须作用于另一个独立聚合（跨对象），同一聚合内部变化不得用 `syncTriggers` 表达；
5. 联动失败（规则不满足或下游行为异常）的语义必须在行为的 `postconditions` 或 M6 流程中明确，禁止隐含吞掉异常。

### 3.2.3  前置/后置条件（Condition / StateChange）

使用简洁的谓词表达式语法：

- 前置条件示例：`contract.status == '待审批'  AND  contract.totalAmount > 0`
- 状态变更示例：`contract.status = '已生效'  |  contract.activateAt = NOW()`
- 支持跨实体引用：`invoice.receivedAmount <= invoice.invoiceAmount`

## 3.3  YAML 元文件模板

```yaml
# M2 行为模型元文件 - m2-behavior-model.yaml
model_type: BEHAVIOR
version: "1.0"
domain: "销售合同执行管理"

behaviors:
  # ══════════════════════════════════════════════════════════
  # 命令行为 + 跨对象联动（收款完成后自动判断关闭合同）
  # ══════════════════════════════════════════════════════════
  - id: Receipt_Record
    name: 录入收款
    ownerEntity: AGG-RECEIPT-001
    behaviorType: COMMAND
    triggerType: USER_ACTION
    preconditions:
      - "收款信息合法"
      - "关联的开票记录存在"
    postconditions:
      - field: receipt.status
        setValue: "已收款"
    appliedRules:
      - RULE-RECEIPT-AMOUNT-CHECK
    requiredPermissions:
      - PERM-RECEIPT-RECORD
    syncTriggers:
      - ruleRef: RULE-CONTRACT-CLOSE-CHECK
        behaviorRef: Contract_Close
        description: 收款录入后检查合同是否全部收齐，满足则同步关闭合同

  # ══════════════════════════════════════════════════════════
  # 无审批功能的保存行为（无 syncTriggers）
  # ══════════════════════════════════════════════════════════
  - id: Contract_SaveAsDraft
    name: 保存合同草稿
    ownerEntity: AGG-CONTRACT-001
    behaviorType: COMMAND
    triggerType: USER_ACTION
    preconditions:
      - "合同基本信息完整"
    postconditions:
      - field: contract.status
        setValue: "草稿"
    appliedRules: []
    requiredPermissions:
      - PERM-CONTRACT-CREATE
    syncTriggers: []

  - id: Contract_Submit
    name: 提交合同审批
    ownerEntity: AGG-CONTRACT-001
    behaviorType: COMMAND
    triggerType: USER_ACTION
    preconditions:
      - "contract.status == '草稿'"
    postconditions:
      - field: contract.status
        setValue: "待审批"
    appliedRules: []
    requiredPermissions:
      - PERM-CONTRACT-CREATE
    syncTriggers: []

  # ══════════════════════════════════════════════════════════
  # 查询行为（与 M7 一对一绑定）
  # ══════════════════════════════════════════════════════════
  - id: Contract_QueryExecutionAnalysis
    name: 查询合同执行情况分析
    ownerEntity: AGG-CONTRACT-001
    behaviorType: QUERY
    triggerType: USER_ACTION
    preconditions: []
    postconditions: []
    appliedRules: []
    requiredPermissions:
      - PERM-CONTRACT-ANALYSIS
    syncTriggers: []
    queryReportRef: QR-CONTRACT-EXECUTION-001
```

> **说明**：`syncTriggers` 字段替代历史版本的 `producedEvents`。普通单聚合命令行为可不填写（空数组）；查询行为不产生状态变化，`syncTriggers` 必须为空。

## 3.4  一致性约束

1. `triggerType=USER_ACTION` 的行为必须被至少一个 MU 操作功能点引用（可追溯性门禁，防止孤儿行为）；
2. `syncTriggers` 中引用的 `behaviorRef`、`ruleRef` 必须分别存在于 M2、M3；
3. `syncTriggers` 的下游行为必须操作另一个独立聚合（跨对象），禁止同聚合内自我联动；
4. 行为 `postconditions` 描述的状态变更，应与 MU 操作功能点的回显/刷新行为衔接（如保存成功后刷新列表）；
5. `queryReportRef` 只出现在 `behaviorType=QUERY` 的行为上，并与 M7 `behaviorRef` 双向一致、严格一对一。

---

# 第四章  M3 规则模型

## 4.1  设计目标与边界

规则模型专注于跨对象、跨行为或需要独立复用的解耦业务规则，是从对象局部约束和行为逻辑中分离出来的独立关切。其核心价值在于：同一规则可以被多个行为引用，规则变更不影响对象结构和行为定义。

> **重要边界说明**：能够在单个属性内部定义清楚的规则不进入 M3。必填、唯一、类型、枚举和数据字典约束直接使用 M1 属性字段；只依赖当前属性值的扩展表达式使用属性 `refRules`；依赖同一对象多个属性或聚合内部子实体的规则使用聚合 `invariants`。M3 只处理超出单个对象内部边界的业务判断、计算、推导，并且**一律由行为同步调用**。

### 4.1.1  M1 局部规则与 M3 规则的判定

| 规则特征 | 归属位置 | 示例 |
|----------|----------|------|
| 属性内置约束 | M1 Attribute 字段 | 必填、唯一、枚举、字典引用 |
| 只读取当前属性值 | M1 Attribute.refRules | 金额大于 0、名称长度不超过 100 |
| 读取同一对象多个属性或聚合内部子实体 | M1 Aggregate.invariants | 付款比例合计等于 100% |
| 读取两个或多个独立对象 | M3 Rule | 累计收款金额达到合同总金额 |
| 依赖行为执行结果或被多个行为复用 | M3 Rule | 合同关闭资格校验、阶段开票上限校验 |
| 调用外部规则引擎或外部数据决策 | M3 Rule | 信用风险评分、合规名单校验 |

判断顺序：

```text
内置字段能表达？
-> 是：使用属性内置字段
-> 否：是否只依赖当前属性值？
   -> 是：使用 Attribute.refRules
   -> 否：是否只依赖同一聚合内部数据？
      -> 是：使用 Aggregate.invariants
      -> 否：进入 M3 规则模型（被行为同步调用）
```

## 4.2  规则分类体系

| 规则类型 | 说明 | 触发方式 |
|----------|------|----------|
| 验证规则（Validation Rule） | 对跨属性、跨对象或行为上下文执行验证，返回 true/false，不改变状态 | 被行为调用 |
| 计算规则（Calculation Rule） | 根据输入参数计算并返回结果值 | 被行为调用 |
| 推导规则（Derivation Rule） | 基于已知属性推导出其他属性值 | 被行为调用 |
| 转换规则（Transformation Rule） | 将一种数据格式转换为另一种 | 被行为调用 |
| 风控规则（Risk Rule） | 评估业务风险，返回风险等级或通过/拒绝决策 | 被行为调用 |

> v9.0 移除"事件驱动规则（EVENT_DRIVEN）"。所有规则均是被行为（或经 `syncTriggers`）同步调用的被动组件，不主动订阅任何事件，也不直接触发行为。规则只负责判断与计算，对象状态变化始终由行为完成。

## 4.3  模型元素规范

### 4.3.1  通用规则属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| id | String | 规则唯一标识，建议格式：RULE-{Domain}-{Seq} |
| name | String | 规则业务名称 |
| ruleType | Enum | VALIDATION / CALCULATION / DERIVATION / TRANSFORMATION / RISK |
| description | String | 规则的业务逻辑说明 |
| inputParams | Param[] | 输入参数定义（名称、类型、来源字段） |
| outputType | DataType | 返回值类型，通常为 Boolean 或结构化结果 |
| expression | String | 规则表达式（支持伪代码或 DSL，不限定具体语言） |
| reusedBy | BehaviorRef[] | 引用本规则的行为列表（反向追踪） |
| externalEngine | String | 若委托外部规则引擎，填写引擎名称（可选） |
| version | String | 规则版本，支持规则的独立版本管理 |

### 4.3.2  输入参数（Param）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| name | String | 参数名称 |
| type | DataType | 参数类型 |
| sourceField | String | 来源字段路径，如 "contract.totalAmount" |
| required | Boolean | 是否必填 |
| description | String | 参数说明 |

## 4.4  YAML 元文件模板

```yaml
# M3 规则模型元文件 - m3-rule-model.yaml
model_type: RULE
version: "2.0"
domain: "销售合同执行管理"

rules:
  - id: RULE-CONTRACT-CLOSE-CHECK
    name: 合同关闭资格校验
    ruleType: VALIDATION
    description: 判断合同累计收款金额是否已达到合同总金额，达到则可关闭
    inputParams:
      - name: contractId
        type: String
        sourceField: Contract.contractId
        required: true
      - name: totalAmount
        type: Decimal
        sourceField: Contract.totalAmount
        required: true
      - name: receivedAmount
        type: Decimal
        sourceField: Receipt.aggregatedAmount
        required: true
    outputType: Boolean
    expression: |
      receivedAmount >= totalAmount
    reusedBy:
      - Receipt_Record          # 通过 syncTriggers 引用
    version: "1.0"

  - id: RULE-INVOICE-AMOUNT-CHECK
    name: 阶段开票金额上限校验
    ruleType: VALIDATION
    description: 校验某付款阶段累计开票金额不超过该阶段应开票金额
    inputParams:
      - name: stageAmount
        type: Decimal
        sourceField: PaymentStage.amount
        required: true
      - name: invoicedAmount
        type: Decimal
        sourceField: Invoice.aggregatedAmount
        required: true
    outputType: Boolean
    expression: |
      invoicedAmount <= stageAmount
    reusedBy:
      - Invoice_Issue
    version: "1.0"
```

## 4.5  最佳实践

- **单一职责**：一个规则只判断一个业务条件；
- **明确输入输出**：清晰定义输入参数和输出结果；
- **无副作用**：规则只判断/计算，不改变任何对象状态；
- **规则失败不阻断其他处理**：规则校验失败应返回明确业务提示，由调用方（行为）决定后续处理；
- **版本管理**：规则升级时保持输入输出接口兼容，支持独立版本管理与回滚。

---

# 第五章  M5 主体模型

## 5.1  设计目标

主体模型解决"谁能做什么"的问题，采用 RBAC（基于角色的访问控制）为基础，支持 ABAC（基于属性的访问控制）扩展。

> **设计决策**：权限定义不内嵌于行为模型，而是在行为模型中声明 `requiredPermissions`，在主体模型中定义权限的授予关系。这样角色权限的变化不影响行为模型定义。

> **v9.0 裁剪**：移除外部实体（ExternalEntity）与外部接口契约（externalContract），本系统不涉及外部系统交互，主体模型仅定义内部参与者、角色与权限。

## 5.2  模型层次

| 层次 | 说明 |
|------|------|
| 参与者（Actor） | 与系统交互的主体，分为：人类用户（Human）、系统账户（System） |
| 角色（Role） | 权限的集合单元，一个参与者可拥有多个角色，角色支持继承 |
| 权限（Permission） | 对特定对象或行为的操作授权，粒度到行为级别 |
| 权限组（PermissionGroup） | 权限的分组管理，便于批量授予 |

## 5.3  模型元素规范

### 5.3.1  参与者（Actor）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| actorId | String | 主体唯一标识 |
| actorType | Enum | HUMAN / SYSTEM |
| roles | RoleRef[] | 拥有的角色列表 |
| attributes | Map | 主体属性（用于 ABAC 条件评估，如 department, level） |

### 5.3.2  角色（Role）

角色除了承载权限集合，也是 M6 人工任务的唯一参与人类型。删除或重命名角色前，必须分析所有 M6 流程中的 `roleRefs` 和活动 `roleRef`。

| 属性名 | 类型 | 说明 |
|--------|------|------|
| roleId | String | 角色唯一标识 |
| name | String | 角色名称 |
| inheritsFrom | RoleRef[] | 继承的父角色（支持多继承） |
| permissions | PermissionRef[] | 直接授予的权限列表 |
| permissionGroups | GroupRef[] | 授予的权限组 |

### 5.3.3  权限（Permission）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| permissionId | String | 权限标识，建议格式：PERM-{Domain}-{Action} |
| targetType | Enum | 授权目标类型：BEHAVIOR（行为）/ ENTITY（实体数据） |
| targetRef | Ref | 授权目标引用 |
| dataScope | Enum | 数据范围：ALL / OWN / DEPT / CUSTOM |
| abacCondition | String | ABAC 条件表达式，如 `actor.dept == resource.dept` |

## 5.4  YAML 元文件模板

```yaml
# M5 主体模型元文件 - m5-actor-model.yaml
model_type: ACTOR
version: "1.0"
domain: "销售合同执行管理"

actors:
  - actorId: ACTOR-SALES
    name: 销售人员
    actorType: HUMAN
    roles:
      - ROLE-SALES
  - actorId: ACTOR-FINANCE
    name: 财务人员
    actorType: HUMAN
    roles:
      - ROLE-FINANCE
  - actorId: ACTOR-FINANCE-MANAGER
    name: 财务经理
    actorType: HUMAN
    roles:
      - ROLE-FINANCE-MANAGER
  - actorId: ACTOR-GENERAL-MANAGER
    name: 总经理
    actorType: HUMAN
    roles:
      - ROLE-GENERAL-MANAGER
  - actorId: ACTOR-EMPLOYEE
    name: 普通员工
    actorType: HUMAN
    roles:
      - ROLE-EMPLOYEE

roles:
  - roleId: ROLE-SALES
    name: 销售人员
    permissions:
      - PERM-CONTRACT-CREATE
      - PERM-CONTRACT-QUERY-ALL
  - roleId: ROLE-FINANCE
    name: 财务人员
    permissions:
      - PERM-CONTRACT-CREATE
      - PERM-INVOICE-ISSUE
      - PERM-RECEIPT-RECORD
      - PERM-CONTRACT-QUERY-ALL
  - roleId: ROLE-FINANCE-MANAGER
    name: 财务经理
    inheritsFrom: [ROLE-FINANCE]
    permissions:
      - PERM-CONTRACT-APPROVE-FINANCE
      - PERM-INVOICE-APPROVE
  - roleId: ROLE-GENERAL-MANAGER
    name: 总经理
    permissions:
      - PERM-CONTRACT-APPROVE-LARGE
  - roleId: ROLE-EMPLOYEE
    name: 普通员工
    permissions:
      - PERM-CONTRACT-QUERY-OWN-DEPT

permissions:
  - permissionId: PERM-CONTRACT-CREATE
    targetType: BEHAVIOR
    targetRef: Contract_SaveAsDraft
    dataScope: ALL
  - permissionId: PERM-CONTRACT-QUERY-OWN-DEPT
    targetType: BEHAVIOR
    targetRef: Contract_QueryList
    dataScope: DEPT
    abacCondition: "actor.dept == resource.dept"
  - permissionId: PERM-CONTRACT-APPROVE-FINANCE
    targetType: BEHAVIOR
    targetRef: Contract_ApproveFinance
    dataScope: ALL
  - permissionId: PERM-CONTRACT-APPROVE-LARGE
    targetType: BEHAVIOR
    targetRef: Contract_ApproveGeneralManager
    dataScope: ALL
```

---

# 第六章  M6 流程模型

## 6.1  设计目标与边界

M6 流程模型定义业务工作如何从开始流转到结束，承载两类流程：

1. `COLLABORATION`：端到端业务协同流，例如合同创建、审批、生效、开票、收款和关闭；
2. `APPROVAL`：围绕提交、审批、会签、驳回、退回和通过形成的审批流，可被协同流作为子流程调用。

M6 负责角色任务、系统活动、顺序、并行、条件网关和子流程调用。M6 不重新定义对象、行为、规则或角色，而是通过稳定 ID 引用其他模型。

> **强制角色约束**：所有 `USER_TASK` 和 `APPROVAL_TASK` 的参与人只能通过 `roleRef` 引用 M5 `roles.roleId`。不得引用 `actorId`，不得填写"财务经理"等自由文本，也不得直接绑定具体用户。

> **v9.0 裁剪**：移除事件触发（triggerType=EVENT）、事件等待活动（EVENT_WAIT）与场景调用活动（SCENARIO_CALL）。端到端协同流与审批流均为同步顺序编排，跨对象联动已由 M2 `syncTriggers` 承载，流程只编排粗粒度业务阶段与审批节点。

## 6.2  流程类型及组合关系

### 6.2.1  端到端业务协同流（COLLABORATION）

端到端协同流描述一个业务目标跨阶段、跨对象的完整生命周期。它可以调用 M2 行为、M6 审批子流程。

```text
合同创建（保存草稿/提交）
-> 调用合同审批子流程
-> 合同生效
-> 合同开票
-> 合同收款
-> 合同关闭
```

### 6.2.2  审批流（APPROVAL）

审批流描述由角色承担的人工决策过程。审批条件可直接使用流程表达式，也可通过 `ruleRef` 引用 M3 规则。金额、数量、状态、组织层级等可复用业务判断应优先进入 M3。

```text
合同提交
-> 财务经理审批
-> 合同金额判断
   -> 不超过 100 万元：审批通过
   -> 超过 100 万元：总经理审批
-> 审批完成
```

## 6.3  模型元素规范

### 6.3.1  流程（Flow）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| id | String | 流程唯一标识，建议格式 `FLOW-{DOMAIN}-{NNN}` |
| name | String | 流程业务名称 |
| flowType | Enum | `COLLABORATION` / `APPROVAL` |
| description | String | 流程目标和边界说明 |
| businessObjectRefs | AggregateRef[] | 流程涉及的 M1 聚合根 |
| roleRefs | RoleRef[] | 流程中允许承担人工活动的 M5 角色集合 |
| trigger | FlowTrigger | 流程启动方式 |
| preconditions | String[] | 流程启动前提 |
| postconditions | String[] | 流程完成后的业务状态 |
| startActivity | ActivityRef | 唯一开始活动 |
| endActivities | ActivityRef[] | 一个或多个合法结束活动 |
| activities | FlowActivity[] | 流程活动和网关集合 |
| version | String | 流程定义版本 |

### 6.3.2  流程触发器（FlowTrigger）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| triggerType | Enum | `MANUAL` / `BEHAVIOR` / `SCHEDULE` / `SUB_FLOW` |
| behaviorRef | BehaviorRef | `BEHAVIOR` 触发时引用 M2 行为 |
| scheduleExpression | String | `SCHEDULE` 触发时的 Cron 或伪代码表达式 |

### 6.3.3  流程活动（FlowActivity）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| activityId | String | 流程内唯一活动标识 |
| name | String | 活动业务名称 |
| activityType | Enum | `START` / `END` / `USER_TASK` / `APPROVAL_TASK` / `SYSTEM_TASK` / `BEHAVIOR_CALL` / `SUB_FLOW_CALL` / `GATEWAY` |
| roleRef | RoleRef | `USER_TASK` 和 `APPROVAL_TASK` 必填，只能引用 M5 角色 |
| behaviorRef | BehaviorRef | `BEHAVIOR_CALL` 或需要落到领域行为的任务引用 M2 行为 |
| subFlowRef | FlowRef | `SUB_FLOW_CALL` 引用 M6 中的另一流程，禁止直接或间接循环调用 |
| ruleRef | RuleRef | 可选，引用 M3 规则作为进入、完成或网关判断条件 |
| conditionExpression | String | 不需要独立复用时可使用的流程局部条件表达式 |
| approvalOutcomes | Enum[] | 审批任务允许的结果，如 `APPROVE` / `REJECT` / `RETURN` |
| timeout | Duration | 活动超时约束（可选） |
| nextActivities | ActivityRef[] | 普通活动的后继活动 |
| branches | FlowBranch[] | `GATEWAY` 的条件分支 |

### 6.3.4  流程分支（FlowBranch）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| branchName | String | 分支名称 |
| ruleRef | RuleRef | 可选，引用 M3 规则 |
| conditionExpression | String | 可选，流程局部判断表达式；与 ruleRef 至少填写一个，默认分支除外 |
| approvalOutcome | Enum | 可选，按 `APPROVE` / `REJECT` / `RETURN` 等审批结果分支 |
| targetActivity | ActivityRef | 目标活动 |
| isDefault | Boolean | 是否默认分支；同一网关最多一个默认分支 |

## 6.4  YAML 元文件模板

```yaml
# M6 流程模型元文件 - m6-flow-model.yaml
model_type: FLOW
version: "1.0"
domain: "销售合同执行管理"

flows:
  - id: FLOW-CONTRACT-001
    name: 合同全生命周期协同流
    flowType: COLLABORATION
    description: 从合同创建、审批、生效、开票和收款到合同关闭的端到端协同流程
    businessObjectRefs:
      - AGG-CONTRACT-001
      - AGG-INVOICE-001
      - AGG-RECEIPT-001
    roleRefs:
      - ROLE-SALES
      - ROLE-FINANCE
      - ROLE-FINANCE-MANAGER
      - ROLE-GENERAL-MANAGER
    trigger:
      triggerType: MANUAL
    preconditions:
      - "用户具备合同创建权限"
    postconditions:
      - "合同已关闭或流程已明确终止"
    startActivity: A01
    endActivities: [A08]
    activities:
      - activityId: A01
        name: 开始
        activityType: START
        nextActivities: [A02]
      - activityId: A02
        name: 创建合同（保存草稿/提交）
        activityType: USER_TASK
        roleRef: ROLE-SALES
        behaviorRef: Contract_Submit
        nextActivities: [A03]
      - activityId: A03
        name: 合同审批
        activityType: SUB_FLOW_CALL
        subFlowRef: FLOW-CONTRACT-APPROVAL-001
        nextActivities: [A04]
      - activityId: A04
        name: 合同生效
        activityType: BEHAVIOR_CALL
        behaviorRef: Contract_Activate
        nextActivities: [A05]
      - activityId: A05
        name: 合同开票
        activityType: BEHAVIOR_CALL
        behaviorRef: Invoice_Issue
        nextActivities: [A06]
      - activityId: A06
        name: 合同收款
        activityType: BEHAVIOR_CALL
        behaviorRef: Receipt_Record
        nextActivities: [A07]
      - activityId: A07
        name: 合同关闭（由收款行为 syncTriggers 自动触发）
        activityType: SYSTEM_TASK
        behaviorRef: Contract_Close
        nextActivities: [A08]
      - activityId: A08
        name: 结束
        activityType: END
        nextActivities: []

  - id: FLOW-CONTRACT-APPROVAL-001
    name: 合同创建审批流
    flowType: APPROVAL
    description: 合同先由财务经理审批，金额超过 100 万元时增加总经理审批
    businessObjectRefs:
      - AGG-CONTRACT-001
    roleRefs:
      - ROLE-FINANCE-MANAGER
      - ROLE-GENERAL-MANAGER
    trigger:
      triggerType: BEHAVIOR
      behaviorRef: Contract_Submit
    preconditions:
      - "contract.status == '待审批'"
    postconditions:
      - "合同审批通过、驳回或退回修改"
    startActivity: P01
    endActivities: [P06, P07]
    activities:
      - activityId: P01
        name: 开始
        activityType: START
        nextActivities: [P02]
      - activityId: P02
        name: 财务经理审批
        activityType: APPROVAL_TASK
        roleRef: ROLE-FINANCE-MANAGER
        behaviorRef: Contract_ApproveFinance
        approvalOutcomes: [APPROVE, REJECT, RETURN]
        nextActivities: [P03]
      - activityId: P03
        name: 财务审批结果判断
        activityType: GATEWAY
        branches:
          - branchName: 驳回或退回
            conditionExpression: "approval.outcome IN ['REJECT', 'RETURN']"
            targetActivity: P07
            isDefault: false
          - branchName: 财务审批通过
            conditionExpression: "approval.outcome == 'APPROVE'"
            targetActivity: P04
            isDefault: true
      - activityId: P04
        name: 大额合同判断
        activityType: GATEWAY
        branches:
          - branchName: 超过 100 万元
            conditionExpression: "contract.totalAmount >= 1000000"
            targetActivity: P05
            isDefault: false
          - branchName: 普通金额合同
            conditionExpression: null
            targetActivity: P06
            isDefault: true
      - activityId: P05
        name: 总经理审批
        activityType: APPROVAL_TASK
        roleRef: ROLE-GENERAL-MANAGER
        behaviorRef: Contract_ApproveGeneralManager
        approvalOutcomes: [APPROVE, REJECT, RETURN]
        nextActivities: [P06]
      - activityId: P06
        name: 审批通过结束
        activityType: END
        nextActivities: []
      - activityId: P07
        name: 驳回或退回结束
        activityType: END
        nextActivities: []
```

## 6.5  流程约束

1. 每条流程必须有且仅有一个 `startActivity`，并至少有一个 `endActivities`；
2. 除 `END` 外的可达活动必须存在合法后继路径；所有 `endActivities` 必须指向 `END` 活动；
3. `USER_TASK`、`APPROVAL_TASK` 必须填写有效 `roleRef`，且该角色必须包含在流程 `roleRefs` 中；
4. `GATEWAY` 至少有两个分支，最多一个默认分支；非默认分支必须提供 `ruleRef` 或 `conditionExpression` 或 `approvalOutcome`；
5. `SUB_FLOW_CALL` 不得形成直接或间接递归调用环；
6. 审批活动的处理结果必须显式覆盖通过、驳回、退回等实际业务结果，不得只有成功路径；
7. 流程局部条件可使用表达式；跨流程复用、跨对象或复杂决策应定义为 M3 规则并通过 `ruleRef` 引用；
8. 跨对象联动已由 M2 `syncTriggers` 承载，流程中可用 `SYSTEM_TASK` 标注联动触发的结果活动，但不得重复定义联动逻辑。

## 6.6  跨模型引用矩阵

| M6 字段 | 引用目标 | 一致性要求 |
|--------|----------|------------|
| `businessObjectRefs` | M1 `aggregates.id` | 引用对象必须存在 |
| `roleRefs`、`activity.roleRef` | M5 `roles.roleId` | 只允许角色，活动角色必须属于流程 roleRefs |
| `trigger.behaviorRef`、`activity.behaviorRef` | M2 `behaviors.id` | 引用行为必须存在 |
| `activity.ruleRef`、`branch.ruleRef` | M3 `rules.id` | 规则必须无副作用，流程只消费判断结果 |
| `activity.subFlowRef` | M6 `flows.id` | 子流程必须存在，且整个调用图无环 |

---

# 第七章  M7 查询统计与报表模型

## 7.1  设计目标与边界

M7 定义业务应用中的查询统计对象和固定报表对象，专门承载多个 M1 业务对象之间的关联查询、条件过滤、结果列、分组聚合、排序、分页和可选参考 SQL。

M7 不是 BI 指标模型，不定义事实表、维度表、宽表、数据集市、OLAP Cube、ETL 任务或自助分析语义。M7 也不定义独立指标资产；`COUNT`、`SUM`、`AVG`、`MIN`、`MAX` 等只作为具体查询对象内部的聚合表达式存在。

M7 的直接依赖严格限制为：

```text
M7 查询统计或报表对象 -> M1 对象及字段
M7 查询统计或报表对象 <-> M2 QUERY 行为（一对一）
```

M7 不直接引用 M3 规则、M5 主体或 M6 流程。查询条件、关联条件、聚合公式属于查询对象自身定义，不视为 M3 业务规则。数据访问权限暂不在 M7 建模，仍由 M2 行为通过 `requiredPermissions` 与 M5 建立关系。

> **v9.0 裁剪**：参考 SQL 改为可选。因移除 MM 映射模型，物理表名在实现阶段确定，M7 的语义定义（来源/条件/结果列/聚合）才是稳定业务语义，参考 SQL 仅作实现指导。

## 7.2  M2 查询行为与 M7 对象的分界

| 判断问题 | M2 QUERY 行为 | M7 查询统计与报表对象 |
|----------|--------------|-----------------------|
| 核心职责 | 定义"执行一次查询或生成报表"的原子行为 | 定义"查什么、如何关联、如何统计、返回什么" |
| 单聚合简单查询 | 可独立定义，不要求 M7 | 通常不建立 |
| 跨对象关联查询 | 通过 queryReportRef 调用 M7 | 定义来源对象、Join、条件和结果列 |
| 分组统计 | 负责执行入口 | 定义聚合、GROUP BY、HAVING |
| 固定报表 | 负责生成或导出行为 | 定义报表列、分组、小计、合计和导出格式 |
| 权限 | 通过 requiredPermissions 关联 M5 | 不定义权限或角色 |

一条 M2 行为最多引用一个 M7 对象，一个 M7 对象也必须且只能绑定一条 M2 行为。

## 7.3  对象类型

| objectType | 说明 | 典型示例 |
|------------|------|----------|
| `DETAIL_QUERY` | 跨对象详情查询，返回一条主要业务记录及关联信息 | 合同执行详情 |
| `LIST_QUERY` | 跨对象条件列表查询，通常支持分页和排序 | 已开票未收款合同列表 |
| `STATISTICAL_QUERY` | 包含聚合或分组统计的查询分析 | 按部门统计合同金额 |
| `REPORT` | 具有固定列、分组、小计、合计和导出要求的业务报表 | 部门合同执行汇总报表 |

## 7.4  模型元素规范

### 7.4.1  查询统计或报表对象（QueryReportObject）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| id | String | 对象唯一标识；查询建议 `QR-{DOMAIN}-{NNN}`，报表建议 `RPT-{DOMAIN}-{NNN}` |
| name | String | 查询统计或报表名称 |
| alias | String | 稳定英文别名，使用 lowerCamelCase |
| objectType | Enum | `DETAIL_QUERY` / `LIST_QUERY` / `STATISTICAL_QUERY` / `REPORT` |
| description | String | 业务目的和结果口径说明 |
| behaviorRef | BehaviorRef | 唯一绑定的 M2 QUERY 行为 |
| sourceObjects | QuerySource[] | 查询涉及的 M1 对象及别名 |
| joins | QueryJoin[] | 多对象关联定义 |
| parameters | QueryParameter[] | 查询输入参数和允许操作符 |
| conditions | QueryCondition[] | WHERE 条件语义定义 |
| resultColumns | ResultColumn[] | 查询结果列及聚合表达式 |
| groupBy | FieldExpression[] | 分组字段表达式 |
| having | QueryCondition[] | 聚合后的过滤条件 |
| orderBy | OrderBy[] | 默认排序 |
| pagination | Pagination | 分页约束 |
| reportOptions | ReportOptions | objectType=REPORT 时的固定报表设置 |
| referenceSql | ReferenceSql | 可选；参考 SQL、方言、参数绑定及结果映射 |
| version | String | 对象定义版本 |

### 7.4.2  查询来源（QuerySource）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| objectRef | AggregateRef | M1 聚合根 ID |
| alias | String | 查询内部唯一别名 |
| entityPath | FieldPath | 可选，查询聚合内某个子实体时填写 |
| primary | Boolean | 是否为主查询对象；每个 M7 对象必须且只能有一个主对象 |
| preAggregation | SourcePreAggregation | 可选；在参与 Join 前按关联键预聚合一对多明细，避免多个明细来源相乘 |

### 7.4.3  对象关联（QueryJoin）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| joinId | String | 查询对象内唯一关联标识 |
| joinType | Enum | `INNER` / `LEFT` / `RIGHT` / `FULL` |
| leftSource | SourceAlias | 左侧来源别名 |
| rightSource | SourceAlias | 右侧来源别名 |
| relationRef | AssociationRef | 可选，引用 M1 `aggregate_associations.id` |
| conditionExpression | String | 关联字段表达式 |

### 7.4.4  查询参数（QueryParameter）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| name | String | 参数名 |
| label | String | 参数显示名称 |
| dataType | String | String / Integer / Decimal / Boolean / Date / DateTime / Enum / DictionaryRef |
| required | Boolean | 是否必填 |
| defaultValue | Any | 默认值或表达式 |
| allowedOperators | Enum[] | `EQ` / `NE` / `GT` / `GE` / `LT` / `LE` / `IN` / `NOT_IN` / `LIKE` / `BETWEEN` |
| sourceField | FieldPath | 参数通常约束的 M1 字段路径，可选 |

### 7.4.5  结果列（ResultColumn）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| name | String | 稳定结果字段名 |
| label | String | 业务显示名称 |
| dataType | String | 结果数据类型 |
| sourceExpression | String | M1 字段路径、计算表达式或聚合表达式 |
| aggregateFunction | Enum | `NONE` / `COUNT` / `COUNT_DISTINCT` / `SUM` / `AVG` / `MIN` / `MAX` |
| format | String | 日期、金额、百分比等格式 |
| nullable | Boolean | 是否允许空值 |
| visible | Boolean | 默认是否输出 |
| sortable | Boolean | 是否允许排序 |

### 7.4.6  固定报表设置（ReportOptions）

仅当 `objectType=REPORT` 时使用：

| 属性名 | 类型 | 说明 |
|--------|------|------|
| title | String | 报表标题 |
| layout | Enum | 当前仅支持 `TABLE` |
| groupFields | ResultColumnRef[] | 报表分组列 |
| subtotalFields | ResultColumnRef[] | 分组小计列 |
| totalFields | ResultColumnRef[] | 全表合计列 |
| exportFormats | Enum[] | `XLSX` / `CSV` / `PDF` |
| emptyValueDisplay | String | 空值显示文本 |

## 7.5  YAML 元文件模板（合同执行情况分析）

```yaml
# M7 查询统计与报表模型元文件 - m7-report-model.yaml
model_type: REPORT
version: "1.0"
domain: "销售合同执行管理"

query_reports:
  - id: QR-CONTRACT-EXECUTION-001
    name: 合同执行情况分析
    alias: contractExecutionAnalysis
    objectType: STATISTICAL_QUERY
    description: 按合同汇总合同金额、已开票金额、已收款金额、未收款金额和收款完成率
    behaviorRef: Contract_QueryExecutionAnalysis
    sourceObjects:
      - objectRef: AGG-CONTRACT-001
        alias: contract
        primary: true
      - objectRef: AGG-INVOICE-001
        alias: invoiceAgg
        primary: false
        preAggregation:
          groupBy: [contractId]
          columns:
            - name: invoicedAmount
              sourceExpression: invoiceAmount
              aggregateFunction: SUM
      - objectRef: AGG-RECEIPT-001
        alias: receiptAgg
        primary: false
        preAggregation:
          groupBy: [contractId]
          columns:
            - name: receivedAmount
              sourceExpression: receivedAmount
              aggregateFunction: SUM
    joins:
      - joinId: J01
        joinType: LEFT
        leftSource: contract
        rightSource: invoiceAgg
        conditionExpression: "invoiceAgg.contractId == contract.contractId"
      - joinId: J02
        joinType: LEFT
        leftSource: contract
        rightSource: receiptAgg
        conditionExpression: "receiptAgg.contractId == contract.contractId"
    parameters:
      - name: departmentId
        label: 所属部门
        dataType: String
        required: false
        allowedOperators: [EQ]
        sourceField: contract.departmentId
      - name: signDateStart
        label: 签订开始日期
        dataType: Date
        required: false
        allowedOperators: [GE]
        sourceField: contract.signDate
      - name: signDateEnd
        label: 签订结束日期
        dataType: Date
        required: false
        allowedOperators: [LE]
        sourceField: contract.signDate
    conditions:
      - conditionId: C01
        leftExpression: contract.departmentId
        operator: EQ
        parameterRef: departmentId
        logicalConnector: AND
        group: BASE
        skipWhenParameterEmpty: true
      - conditionId: C02
        leftExpression: contract.signDate
        operator: GE
        parameterRef: signDateStart
        logicalConnector: AND
        group: BASE
        skipWhenParameterEmpty: true
      - conditionId: C03
        leftExpression: contract.signDate
        operator: LE
        parameterRef: signDateEnd
        logicalConnector: AND
        group: BASE
        skipWhenParameterEmpty: true
    resultColumns:
      - name: contractNo
        label: 合同编号
        dataType: String
        sourceExpression: contract.contractNo
        aggregateFunction: NONE
      - name: contractName
        label: 合同名称
        dataType: String
        sourceExpression: contract.contractName
        aggregateFunction: NONE
      - name: contractAmount
        label: 合同金额
        dataType: Decimal
        sourceExpression: contract.totalAmount
        aggregateFunction: MAX
        format: "#,##0.00"
      - name: invoicedAmount
        label: 已开票金额
        dataType: Decimal
        sourceExpression: invoiceAgg.invoicedAmount
        aggregateFunction: MAX
        format: "#,##0.00"
      - name: receivedAmount
        label: 已收款金额
        dataType: Decimal
        sourceExpression: receiptAgg.receivedAmount
        aggregateFunction: MAX
        format: "#,##0.00"
      - name: unreceivedAmount
        label: 未收款金额
        dataType: Decimal
        sourceExpression: "MAX(contract.totalAmount) - COALESCE(MAX(receiptAgg.receivedAmount), 0)"
        aggregateFunction: NONE
        format: "#,##0.00"
      - name: receiptRate
        label: 收款完成率
        dataType: Decimal
        sourceExpression: "COALESCE(MAX(receiptAgg.receivedAmount), 0) / NULLIF(MAX(contract.totalAmount), 0)"
        aggregateFunction: NONE
        format: "0.00%"
    groupBy:
      - contract.contractNo
      - contract.contractName
    having: []
    orderBy:
      - expression: contract.signDate
        direction: DESC
    pagination:
      enabled: true
      defaultPageSize: 20
      maxPageSize: 200
    reportOptions: null
    referenceSql: null
    version: "1.0"
```

## 7.6  依赖与一致性约束

1. M7 `sourceObjects.objectRef` 必须引用 M1 已存在的聚合根；字段路径必须可解析到 M1；
2. 每个 M7 对象必须填写唯一 `behaviorRef`，目标必须是 M2 `behaviorType=QUERY` 的行为；
3. M2 `queryReportRef` 与 M7 `behaviorRef` 必须双向一致、严格一对一；
4. M7 不得出现 `ruleRefs`、`requiredPermissions`、`roleRefs`、`flowRefs` 等跨模型字段；
5. 每个查询来源别名必须唯一，且必须有且仅有一个 `primary=true` 的主对象；
6. 两个或更多一对多来源同时参与聚合时，必须通过 `preAggregation` 分别按 Join 键汇总后再关联，禁止以 `SUM(DISTINCT amount)` 代替正确的预聚合；
7. `objectType=REPORT` 必须填写 `reportOptions`；其他类型的 `reportOptions` 应为空；
8. `referenceSql` 可选；若填写，其参数绑定与结果映射必须与语义定义一致。

---
# 第八章  MU UI 模型

## 8.1 设计目标与边界

**设计目标**：MU 是七个模型的**入口层 / 追溯层**，定义"用户想完成什么、系统暴露哪些可调用能力、这些能力由什么界面承载、界面上的一次动作最终执行哪个行为"，把界面与业务模型用稳定 ID 连成完整调用链。

本版 MU 面向 **AI 原生交互前提**：用户以自然语言表达意图，由能力目录路由到可调用能力，界面以声明式结构下发，而不是由人在固定菜单树中逐级点击查找功能。层级结构自上而下为：

```text
应用（Application）
  -> 能力目录（Capability）—— 一个用户意图对应一条能力
       -> 工具契约（Tool）—— M2 行为面向智能体与界面的唯一暴露面
       -> 界面单元（UIUnit）—— 承载该能力的界面
            -> 操作功能点（ActionPoint）—— 一次用户动作 -> 工具 -> M2 行为
```

界面单元有两种形态：**A2UI Surface**（声明式组件结构，由扁平组件邻接表与数据模型构成）与 **MCP App**（以 `ui://` 资源标识的宿主界面声明）。两种形态与"界面在建模期确定还是运行期生成"是两个**正交维度**，分别由 `unitType` 与 `renderMode` 表达。

**边界（强制）**：

1. **只引用、不重定义**：MU 只通过稳定 ID 引用 M1 / M2 / M6 / M7，不重新定义对象、行为、规则、流程或报表；
2. **不承载视觉设计**：配色、字体、间距、图标、主题、终端适配由渲染端决定；MU 只声明组件类型、层级关系与数据绑定；
3. **不替代 M6**：端到端协同流与审批流转归 M6；MU 只声明操作功能点与工具入口的对应关系；
4. **不承载业务校验公式**：输入校验引用 M3 规则或 M1 属性约束；组件级格式（掩码、格式化、联动启用）可作为组件属性，仅限本组件内；
5. **不定义传输与实现**：界面结构如何下发、宿主如何渲染、工具如何被调用，均属实现层，不在本模型；MU 只定义可被这些实现消费的建模语义；
6. 纯展示的界面单元允许没有操作功能点，但必须有组件结构声明或宿主界面声明。

## 8.2 模型元素规范

### 8.2.1 应用（Application）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| name | String | 系统名称（中文） |
| uiProtocols.a2ui.version | String | 声明式界面协议版本，固定 `v0.9` |
| uiProtocols.a2ui.catalogRef | String | 组件目录标识，默认 `ontology-basic/v1`（见 §8.3.1） |
| uiProtocols.mcpApps.version | String | 宿主界面规范版本，固定 `SEP-1865` |

### 8.2.2 能力（Capability）

能力是 MU 的入口单元，代表**一个用户意图**。能力目录取代了历史版本的菜单树：能力目录是**扁平**的，不存在一级/二级层级；如需分组展示，由宿主按权限或业务域自行归类，不在本模型内表达。

| 属性名 | 类型 | 说明 |
|--------|------|------|
| capabilityId | String | 能力唯一标识（kebab-case） |
| name | String | 能力名称（中文） |
| intent | String | 语义描述：这条能力让用户完成什么 |
| utterances | String[] | 自然语言触发样例，**至少 1 条**，建议 2-3 条，覆盖正式说法与口语说法 |
| toolRef | ToolRef | 可选；无需界面即可直接执行时，指向的工具 |
| uiUnitRef | UIUnitRef | 可选；承载该能力的界面单元 |
| permissionRef | PermissionRef[] | 可选；控制能力可见性的 M5 权限 |

约束：

1. `toolRef` 与 `uiUnitRef` **至少存在其一**；两者都存在时，表示该能力既可直接执行也可进入界面；
2. `utterances` 不得为空数组，且不得与其他能力的样例语义重复到无法区分；
3. 能力目录必须覆盖全部 `triggerType=USER_ACTION` 行为的可达性（见 §8.7 门禁第 5 条）。

### 8.2.3 工具契约（Tool）

工具契约是 M2 行为面向智能体与界面的**唯一暴露面**，与 M2 中 `triggerType=USER_ACTION` 的行为**严格 1:1**。

`triggerType=SYSTEM` 的行为（跨对象联动、系统触发）**不暴露为工具**——它们由上游行为的 `syncTriggers` 在同一事务边界内自动触发，不是用户或智能体可直接调用的能力。

| 属性名 | 类型 | 说明 |
|--------|------|------|
| toolName | String | 工具名（snake_case，全局唯一） |
| behaviorRef | BehaviorRef | 对应的 M2 行为 |
| title | String | 人类可读标题（中文） |
| description | String | 供智能体判断何时调用该工具的语义描述 |
| inputSchema.objectRef | ObjectRef | 输入所属的 M1 聚合 |
| inputSchema.fields | FieldPath[] | 输入字段，类型与必填性由 M1 属性派生，不在此重复定义 |
| outputSchema.objectRef | ObjectRef \| QueryReportRef | 输出所属的 M1 聚合或 M7 报表对象 |
| outputSchema.fields | FieldPath[] | 输出字段 |
| annotations.readOnlyHint | Boolean | 是否只读；M2 中的查询行为恒为 `true` |
| annotations.destructiveHint | Boolean | 是否具有作废、撤销或删除语义 |
| permissionRef | PermissionRef[] | 可选；执行该工具所需的 M5 权限 |

### 8.2.4 界面单元（UIUnit）

界面单元取代了历史版本的"屏幕（Screen）"。原来的四选一 `screenType` 由两个正交维度取代。

| 属性名 | 类型 | 说明 |
|--------|------|------|
| uiUnitId | String | 界面单元唯一标识（kebab-case） |
| name | String | 界面业务名称（中文） |
| unitType | Enum | `A2UI_SURFACE`（声明式组件结构）/ `MCP_APP`（宿主界面声明） |
| renderMode | Enum | `STATIC`（建模期确定结构）/ `GENERATED`（运行期按契约生成） |
| surface | Surface | `unitType=A2UI_SURFACE` 且 `renderMode=STATIC` 时**必填** |
| generationContract | GenerationContract | `renderMode=GENERATED` 时**必填** |
| mcpApp | McpApp | `unitType=MCP_APP` 时**必填** |
| actions | ActionPoint[] | 操作功能点集合；`renderMode=GENERATED` 时**不得声明** |

约束：

1. 事务型界面单元（涉及创建、修改、审批、作废等写操作）必须为 `renderMode=STATIC`；
2. `renderMode=GENERATED` 仅可用于只读探索分析类界面；
3. `unitType=MCP_APP` 适用于需要自带前端实现的重界面（复杂可视化看板、跨方对账等），其余场景一律使用 `A2UI_SURFACE`。

### 8.2.5 Surface（声明式界面结构）

Surface 采用**扁平组件邻接表**：组件不嵌套，而是通过 ID 引用子组件。该结构便于按 ID 定位与增量更新单个组件，也便于逐段生成。

| 属性名 | 类型 | 说明 |
|--------|------|------|
| surfaceId | String | Surface 标识 |
| root | ComponentId | 根组件 ID |
| dataModel | Map | 数据模型路径 -> M1 绑定，如 `"/contract": Contract` |
| components | Component[] | 扁平组件列表 |

**组件（Component）**：

| 属性名 | 类型 | 说明 |
|--------|------|------|
| id | String | 组件 ID，Surface 内唯一；必须为描述性 kebab-case 名称（`txt-contract-no`），禁止 `c1` 这类无语义命名 |
| component | Enum | 组件类型，取自 `catalogRef` 声明的目录（见 §8.3.1） |
| label | String | 可选；显示文案 |
| value | `{ literalString }` \| `{ path }` | 可选；字面量值，或指向数据模型路径的绑定 |
| required | Boolean | 可选；是否必填，与 M1 属性 `required` 对齐 |
| dataBinding | FieldPath | 可选；绑定的 M1 聚合属性路径，如 `Contract.contractNo` |
| children | `{ explicitList }` \| `{ template }` | 可选；静态子组件 ID 列表，或按数据数组逐项生成的模板 |
| action | `{ event }` | 可选；触发的动作事件名，必须匹配本单元某个操作功能点的 `event` |
| refRules | UIComponentRule[] | 可选；组件级规则（掩码、格式化、联动启用），仅限本组件内 |

除上表通用属性外，各组件可有自身特有属性（如 `EntityPicker.targetAggregate`、`DataTable.columns`），由 §8.3.1 的组件目录定义。

### 8.2.6 生成契约（GenerationContract）

`renderMode=GENERATED` 时，MU 不声明组件结构，只声明生成时必须遵守的约束。

| 属性名 | 类型 | 说明 |
|--------|------|------|
| intent | String | 界面意图 |
| dataSources | QueryReportRef[] | 可用数据来源，引用 M7 报表对象 |
| allowedComponents | ComponentType[] | 允许使用的组件白名单 |
| allowedTools | ToolRef[] | 允许调用的工具，**必须全部** `readOnlyHint=true` |
| requiredActions | ActionId[] | 可选；必须提供的动作 |

### 8.2.7 宿主界面声明（McpApp）

| 属性名 | 类型 | 说明 |
|--------|------|------|
| resourceUri | String | 界面资源标识，必须以 `ui://` 开头，如 `ui://contract/execution-report` |
| mimeType | String | 固定 `text/html;profile=mcp-app` |
| templateOfTool | ToolRef | 该界面作为哪个工具结果的输出模板 |
| allowedTools | ToolRef[] | 该界面可反向调用的工具集合 |

> MU 只声明上述标识与引用关系，不定义界面资源的具体实现内容。

### 8.2.8 操作功能点（ActionPoint）

操作功能点是界面与行为模型的衔接点，对应"界面上的一次用户动作 -> 调用一个工具 -> 执行一个 M2 行为"。

| 属性名 | 类型 | 说明 |
|--------|------|------|
| actionId | String | 功能点唯一标识 |
| name | String | 功能点名称（动作文案） |
| actionType | Enum | `EXECUTE` / `SUBMIT` / `DRAFT` / `APPROVE` / `REJECT` / `RETURN` / `QUERY` / `EXPORT` |
| event | String | 动作事件名，与组件 `action.event` 对应 |
| toolRef | ToolRef | 触发调用的工具 |
| behaviorRef | BehaviorRef | 最终执行的 M2 行为，**必须与 `toolRef` 所指工具的 `behaviorRef` 完全一致** |
| permissionRef | PermissionRef[] | 可选；控制功能点可用性的 M5 权限 |

## 8.3 M1 属性类型到组件映射规则（强制）

对象模型属性类型到界面组件类型的固定映射：

| M1 属性类型 | 组件类型 | 说明 |
|-------------|----------|------|
| Date / DateTime | `DateTimeInput` | 按类型开关日期与时间部分 |
| Enum | `Select` | 选项来自 `enumValues` |
| DictionaryRef | `Select` | 选项来自数据字典项（`label` 显示、`code` 存储） |
| AggregateRootRef | `EntityPicker` | 跳选目标聚合；**必须声明 `targetAggregate`** |
| String（长文本 / 备注） | `TextArea` | |
| Boolean | `Checkbox` | |
| Integer / Decimal / Money | `NumberInput` | |
| 其他 String | `TextField` | |
| 明细集合 / 查询结果 | `DataTable` | 配合 `children.template` 绑定数据模型中的数组路径 |
| 对象状态机当前状态 | `StatusBadge` | 声明 `stateMachineRef` 指向 M1 状态机 |

### 8.3.1 ontology-basic 组件目录

组件目录是允许使用的组件白名单。本规范默认目录为 `ontology-basic/v1`。

**通用组件**：`Column`、`Row`、`Card`、`Heading`、`Text`、`TextField`、`NumberInput`、`TextArea`、`Select`、`DateTimeInput`、`Checkbox`、`Button`。

**本体语义组件**（承载 M1 / M7 语义，通用目录无等价物，故由本规范定义）：

| 组件 | 用途 | 关键属性 |
|------|------|----------|
| `EntityPicker` | `AggregateRootRef` 属性的跳选 | `targetAggregate`（目标聚合）、`searchToolRef`（该聚合的查询工具） |
| `DataTable` | 明细集合维护与查询结果展示 | `columns[{field,label}]`、`pagination`、`inlineEdit`、`rowActions[{actionId}]` |
| `StatusBadge` | 对象状态机当前状态展示 | `value{path}`、`stateMachineRef` |
| `Chart` | M7 报表的可视化呈现 | `dataSourceRef`（M7 报表对象）、`chartType`、`dimensions`、`measures` |

> 项目可声明自有组件目录以匹配既有设计系统，但**必须提供上述四个本体语义组件的等价语义**，否则 M1 的 `AggregateRootRef`、状态机与 M7 报表语义在界面层断链。

## 8.4 界面单元组织模式（强制）

`renderMode=STATIC` 的 A2UI 界面单元必须按以下四种组件组织模式之一构造：

| 模式 | 适用场景 | 组件结构 |
|------|----------|----------|
| 单对象录入 | 单条记录的录入 / 维护 | `Column[ Heading, Card(字段组), Row(动作区) ]` |
| 主从维护 | 聚合根 + 明细集合 | `Column[ Card(主对象字段), DataTable(明细，`children.template` 绑定数组，`inlineEdit=true`，`rowActions` 含删除), Row(动作区) ]` |
| 查询列表 | M7 查询报表 | `Column[ Card(查询条件), DataTable(`pagination=true`), Row(动作区) ]` |
| 列表维护 | 主数据 / 数据字典 / 简单实体 | `Column[ Row(工具栏：关键词 + 查询 + 新增), DataTable(`rowActions` 含编辑、删除) ]`；新增与编辑由**第二个 Surface** 承载，主 Surface 不内联表单 |

**明确不由 MU 规定的内容**：字段一行排布几个、标签与控件的对齐方式、间距与响应式断点。这些由渲染端与组件目录实现决定，不属于本体语义。MU 只声明字段归属哪个分组容器以及在容器内的顺序。

## 8.5 审批双动作规则（强制）

如果一个功能本身带审批流，其"创建 / 录入"界面单元**必须提供两个独立的操作功能点**：

1. **保存草稿**（`actionType=DRAFT`）：仅保存数据，将对象置于"草稿"状态，不触发审批；对应 M2 的 `Xxx_SaveAsDraft` 行为；
2. **提交**（`actionType=SUBMIT`）：保存数据并提交进入审批流；对应 M2 的 `Xxx_Submit` 行为（该行为将对象置于"待审批"状态，并作为审批流的启动入口）。

约束：

- 两个功能点必须**独立**，分别绑定独立的工具契约与独立的 M2 行为，不得合并为单个"保存"动作；
- 提交行为在 M6 审批流中以 `trigger.behaviorRef` 引用，作为审批流启动入口；
- 带审批流的界面单元必须为 `renderMode=STATIC`；
- 无审批流的功能只需一个 `EXECUTE` 动作。

## 8.6 YAML 元文件模板

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

# ── 能力目录：一个用户意图一条，扁平无层级 ──
capabilities:
  - capabilityId: cap-contract-create
    name: 录入销售合同
    intent: 创建一份销售合同，保存草稿或提交进入审批流
    utterances:
      - "新建一个合同"
      - "帮我录入东方公司的销售合同"
    uiUnitRef: ui-contract-maintain
    permissionRef: [perm-contract-create]

  - capabilityId: cap-contract-detail
    name: 查看合同详情
    intent: 按合同编号或名称直接返回单份合同的完整信息
    utterances:
      - "查一下 HT-2026-001 的详情"
      - "看看那份东方公司的合同"
    toolRef: contract_query_detail
    permissionRef: [perm-contract-view]

# ── 工具契约：与 USER_ACTION 行为严格 1:1 ──
tools:
  - toolName: contract_save_as_draft
    behaviorRef: Contract_SaveAsDraft
    title: 保存合同草稿
    description: 保存合同数据并置为草稿状态，不触发审批
    inputSchema:  { objectRef: Contract, fields: [contractNo, contractName, contractType, customerId, paymentStages] }
    outputSchema: { objectRef: Contract, fields: [contractId, status] }
    annotations:  { readOnlyHint: false, destructiveHint: false }
    permissionRef: [perm-contract-create]

  - toolName: contract_submit
    behaviorRef: Contract_Submit
    title: 提交合同
    description: 保存合同数据并提交进入审批流
    inputSchema:  { objectRef: Contract, fields: [contractNo, contractName, contractType, customerId, paymentStages] }
    outputSchema: { objectRef: Contract, fields: [contractId, status] }
    annotations:  { readOnlyHint: false, destructiveHint: false }
    permissionRef: [perm-contract-create]

# ── 界面单元：unitType × renderMode 两个正交维度 ──
uiUnits:
  # 形态一：声明式组件结构 + 建模期确定
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
            children: { explicitList: [hd-title, card-main, tbl-stage, row-actions] } }
        - { id: hd-title, component: Heading, value: { literalString: "合同录入" } }
        - { id: card-main, component: Card,
            children: { explicitList: [txt-contract-no, txt-contract-name, sel-contract-type, pick-customer] } }
        - { id: txt-contract-no, component: TextField, label: 合同编号, required: true,
            value: { path: "/contract/contractNo" }, dataBinding: Contract.contractNo }
        - { id: txt-contract-name, component: TextField, label: 合同名称, required: true,
            value: { path: "/contract/contractName" }, dataBinding: Contract.contractName }
        - { id: sel-contract-type, component: Select, label: 合同类型, required: true,
            value: { path: "/contract/contractType" }, dataBinding: Contract.contractType }
        - { id: pick-customer, component: EntityPicker, label: 所属客户, required: true,
            value: { path: "/contract/customerId" }, dataBinding: Contract.customerId,
            targetAggregate: Customer, searchToolRef: customer_query }
        - { id: tbl-stage, component: DataTable, label: 付款阶段,
            children: { template: { dataPath: "/contract/stages" } },
            inlineEdit: true,
            columns: [{ field: stageNo, label: 阶段编号 }, { field: ratio, label: 付款比例 }] }
        - { id: row-actions, component: Row,
            children: { explicitList: [btn-draft, btn-submit] } }
        - { id: btn-draft,  component: Button, label: 保存草稿, action: { event: contract_save_draft } }
        - { id: btn-submit, component: Button, label: 提交,     action: { event: contract_submit } }
    actions:
      - { actionId: act-contract-draft,  name: 保存草稿, actionType: DRAFT,  event: contract_save_draft,
          toolRef: contract_save_as_draft, behaviorRef: Contract_SaveAsDraft }
      - { actionId: act-contract-submit, name: 提交,     actionType: SUBMIT, event: contract_submit,
          toolRef: contract_submit,        behaviorRef: Contract_Submit }

  # 形态二：宿主界面声明（自带前端实现的重界面）
  - uiUnitId: ui-execution-report
    name: 合同执行情况分析
    unitType: MCP_APP
    renderMode: STATIC
    mcpApp:
      resourceUri: "ui://contract/execution-report"
      mimeType: "text/html;profile=mcp-app"
      templateOfTool: contract_query_execution_analysis
      allowedTools: [contract_query_execution_analysis, contract_query_detail]
    actions:
      - { actionId: act-export-execution, name: 导出, actionType: EXPORT, event: export_execution_report,
          toolRef: contract_query_execution_analysis, behaviorRef: Contract_QueryExecutionAnalysis }

  # 形态三：运行期生成（仅限只读探索分析）
  - uiUnitId: ui-adhoc-analysis
    name: 合同执行自由分析
    unitType: A2UI_SURFACE
    renderMode: GENERATED
    generationContract:
      intent: 对合同执行情况按用户临时提问做探索式分析与可视化
      dataSources: [rpt_contract_execution, rpt_unreceived]
      allowedComponents: [Text, Heading, Card, DataTable, Chart, Button]
      allowedTools: [contract_query_execution_analysis, contract_query_invoiced_unreceived]
```

## 8.7 一致性约束（MU 门禁）

1. 组件 `dataBinding` 的字段路径必须可解析到 M1 聚合属性，且与 `dataModel` 中声明的路径绑定一致；
2. `generationContract.dataSources` 与 `Chart.dataSourceRef` 引用的 M7 报表对象必须存在；
3. 操作功能点的 `toolRef` 必须存在于 `tools`，且其 `behaviorRef` 必须与该工具的 `behaviorRef` 完全一致；
4. `tools` 与 M2 中 `triggerType=USER_ACTION` 的行为**严格 1:1**：每个 `USER_ACTION` 行为恰好一个工具，每个工具恰好一个行为；`triggerType=SYSTEM` 的行为不得出现在 `tools` 中；
5. **反向门禁**：每个 `triggerType=USER_ACTION` 行为对应的工具，必须被至少一个 `capability.toolRef` 或某个界面单元的 `actions[].toolRef` 引用（防止孤儿行为）；
6. 组件的 `component` 类型必须属于 `application.uiProtocols.a2ui.catalogRef` 声明的目录，且遵循 §8.3 的映射规则；
7. `renderMode=GENERATED` 的界面单元，其 `allowedTools` 必须全部 `readOnlyHint=true`，且不得声明 `actions`；
8. 带审批流的界面单元必须为 `renderMode=STATIC`，且必须同时包含 `DRAFT` 与 `SUBMIT` 两个独立操作功能点；
9. 组件邻接表完整性：`root` 必须存在于 `components`；`children.explicitList` 引用的组件 ID 必须存在；组件引用图必须**无环**；除根组件外，每个组件必须被恰好一个父组件引用一次（无孤儿、无重复挂载）；
10. 每个 `capability` 必须至少解析到 `uiUnitRef` 或 `toolRef` 之一，且 `utterances` 至少 1 条；
11. `mcpApp.resourceUri` 必须以 `ui://` 开头，`mimeType` 固定为 `text/html;profile=mcp-app`，`templateOfTool` 与 `allowedTools` 引用的工具必须存在于 `tools`。
---

# 第九章  传统需求覆盖度分析

## 9.1  与软件需求规格说明书的映射

| 需求维度 | 覆盖程度 | 承载模型 |
|----------|----------|----------|
| 领域概念、数据及聚合边界 | 完整覆盖 | M1 对象模型 |
| 原子功能、命令与查询入口 | 完整覆盖 | M2 行为模型 |
| 业务规则与一致性约束 | 完整覆盖 | M1 内置约束、refRules、invariants + M3 规则模型 |
| 跨对象同步联动 | 完整覆盖 | M2 `syncTriggers` + M3 规则（被同步调用） |
| 角色、权限 | 完整覆盖 | M5 主体模型；权限通过 M2 行为授权 |
| 端到端业务协同流 | 完整覆盖 | M6 `COLLABORATION` 流程 |
| 人工审批流 | 完整覆盖 | M6 `APPROVAL` 流程 + M5 角色 |
| 跨对象查询、统计分析 | 完整覆盖 | M7 查询统计对象 + 一对一 M2 QUERY 行为 |
| 固定业务报表 | 完整覆盖 | M7 REPORT 对象 + 一对一 M2 QUERY 行为 |
| 用户能力入口与界面单元结构 | 完整覆盖 | MU UI 模型（应用 → 能力目录 → 工具契约 → A2UI Surface / MCP App 界面单元 → 操作功能点） |
| 异常、驳回、退回路径 | 主要语义覆盖 | M2 前后置条件、M6 分支与终止路径 |
| 对象到数据库表的映射 | 框架外 | 实现阶段以 ORM 注解或 DDL 直接落地 |
| 本系统对外接口 / 外部接口 | 框架外（明确排除） | 本系统当前无外部系统交互 |
| 性能、容量、可用性、安全基线等 NFR | 框架外 | 非功能需求规格 |
| BI 数仓、自助分析和指标平台 | 明确排除 | M7 不是 BI 指标模型 |

## 9.2  覆盖结论

对于合同管理、资产管理、CRM 等采用单体同步部署的中小型业务系统，本框架能够承载软件需求中的核心业务语义：领域对象及聚合边界、原子用例、业务规则、角色权限、端到端流程、审批流程、跨对象同步联动、跨对象查询统计和固定报表，以及界面菜单导航与操作入口。

本框架不应被视为一份完整 SRS 的唯一物理载体。完整交付仍应把七模型与非功能需求、数据迁移、部署运维和测试验收标准组合起来。七模型完整覆盖"系统做什么、核心业务为何如此运转、用户如何驱动系统"，配套规格覆盖"达到什么质量目标以及如何部署运行"。

## 9.3  DDD 与同步编排架构体现

- M1 以聚合根、不变性、值对象和聚合间 ID 引用落实 DDD 领域边界；
- M2 把应用能力拆成原子行为，区分命令与查询；
- M2 `syncTriggers` 把跨聚合联动显式建模为同步调用链，保持事务一致性；
- M3 把业务判断从行为中分离，被同步调用、可独立复用与版本管理；
- M6 承担显式流程控制，并通过角色、行为、规则及子流程组合业务旅程；
- M7 将跨聚合读模型与写侧聚合解耦，体现 CQRS 式读写职责分离，但不引入独立 BI 数据模型；
- MU 将界面入口与业务行为解耦，操作功能点通过稳定 ID 引用行为。

## 9.4  已知边界

- **UI/UX**：MU 承载用户能力目录、工具契约、A2UI Surface / MCP App 界面单元结构与操作功能点；不建模视觉样式、组件目录实现、传输协议、动画、无障碍、主题与终端适配；
- **数据库映射**：对象到物理表/字段的映射由实现阶段 ORM/DDL 落地，不在本体层建模；
- **接口**：本系统不涉及外部接口，接口契约不建模；如未来需要对接外部系统，可后续补充；
- 不独立建模性能、容量、可靠性、安全合规等可量化质量属性；
- 不定义消息中间件、事件存储或事件溯源实现；
- 不定义数据仓库、指标平台、即席分析或可视化仪表盘。

---

# 第十章  实施指南与最佳实践

## 10.1  建模顺序推荐

七个模型之间存在依赖，建议按以下顺序建模：

| 阶段 | 建模对象 | 说明 |
|------|----------|------|
| 1 | M1 对象模型 | 识别聚合、属性、关联、内置约束、refRules 和 invariants |
| 2 | M5 主体模型（角色） | 识别内部角色及职责边界，权限可稍后补齐 |
| 3 | M3 规则模型 | 梳理跨对象、跨行为或需要独立复用的规则 |
| 4 | M2 行为模型 | 定义对象行为、规则调用、syncTriggers 联动及查询行为入口 |
| 5 | M7 查询统计与报表模型 | 在 M1 字段和 M2 查询行为稳定后，建立严格一对一查询报表定义 |
| 6 | M5 主体模型（权限） | 定义权限并绑定 M2 行为；M7 不直接绑定权限 |
| 7 | M6 流程模型 | 定义端到端协同流和审批流，引用角色、行为、规则及子流程 |
| 8 | MU UI 模型 | 定义应用、能力目录、工具契约、A2UI Surface / MCP App 界面单元与操作功能点，引用 M1/M2/M6/M7，并反向校验可追溯性 |

## 10.2  模型评审检查清单

### M1 对象模型评审
- [ ] 聚合边界是否清晰？每个聚合根是否代表一个完整的业务概念？
- [ ] 聚合内的子实体是否真的需要与聚合根同生共死？
- [ ] 聚合之间是否通过 ID 引用而非对象引用？
- [ ] 聚合不变性约束是否完整覆盖了业务规则？
- [ ] 必填、唯一、类型、枚举和数据字典约束是否优先使用属性内置字段？
- [ ] 只依赖当前属性值的扩展约束是否放入 refRules？
- [ ] 依赖同一聚合多个属性或子实体的约束是否放入 invariants？

### M2 行为模型评审
- [ ] 每个行为是否真正原子化，只操作一个对象？
- [ ] 前置条件是否完整覆盖了行为可执行的业务前提？
- [ ] 后置状态变更是否完整描述了行为的全部副作用？
- [ ] `syncTriggers` 是否只表达跨聚合联动？同聚合内部变化是否未误用 syncTriggers？
- [ ] `syncTriggers` 中的条件判断是否引用了 M3 规则，而非硬编码在行为里？
- [ ] `queryReportRef` 是否只出现在 behaviorType=QUERY 的行为上，且与 M7 双向一致？
- [ ] `triggerType=USER_ACTION` 的行为是否都能被 MU 操作功能点反向追溯？

### M3 规则模型评审
- [ ] 是否错误包含了可由属性内置字段、refRules 或 invariants 表达的对象内部规则？
- [ ] 每条规则是否至少涉及跨对象、跨行为或独立复用中的一种？
- [ ] 规则表达式是否无副作用（不改变系统状态）？
- [ ] 规则是否仅被行为同步调用，未保留任何事件订阅/触发语义？

### M5 主体模型评审
- [ ] 是否未残留外部实体或外部接口契约定义？
- [ ] ABAC 条件是否覆盖了数据隔离需求（如按部门隔离）？
- [ ] 角色继承关系是否符合最小权限原则？

### M6 流程模型评审
- [ ] 每条流程是否明确标记为 COLLABORATION 或 APPROVAL？
- [ ] 是否有且仅有一个开始活动，并至少有一个结束活动？
- [ ] USER_TASK 和 APPROVAL_TASK 是否只引用已存在的 M5 roleId？
- [ ] 活动 roleRef 是否同时包含在流程 roleRefs 中？
- [ ] 是否未使用事件触发、事件等待或场景调用活动？
- [ ] 协同流调用审批流时是否通过 subFlowRef 引用，而非复制审批活动？
- [ ] 网关是否至少两个分支、最多一个默认分支，且非默认分支存在判断条件？
- [ ] 审批流是否覆盖通过、驳回、退回等真实结果？
- [ ] 子流程调用图是否无循环？

### M7 查询统计与报表模型评审
- [ ] 每个对象是否仅直接引用 M1 对象/字段及唯一 M2 QUERY 行为？
- [ ] 是否未定义权限、角色、规则或流程引用？
- [ ] 是否有且仅有一个主查询来源，且所有来源别名和 Join 引用均有效？
- [ ] 多个一对多来源同时参与聚合时，是否先按关联键预聚合？
- [ ] REPORT 是否定义固定列、分组/合计及导出格式？

### MU UI 模型评审
- [ ] 能力目录是否覆盖所有 `triggerType=USER_ACTION` 行为（无孤儿、可反向追溯）？
- [ ] 每个 `USER_ACTION` 行为是否恰好对应一个 `toolRef`？`triggerType=SYSTEM` 行为是否均未出现在 `tools`？
- [ ] 每个 `capability` 是否至少解析到 `uiUnitRef` 或 `toolRef` 之一，且 `utterances` 不少于 1 条？
- [ ] 界面单元是否标注了 `unitType`（A2UI_SURFACE / MCP_APP）与 `renderMode`（STATIC / GENERATED）？两者是否正交使用？
- [ ] `renderMode=GENERATED` 单元的 `allowedTools` 是否全部 `readOnlyHint=true`，且未声明 `actions`？
- [ ] 组件类型是否来自 `catalogRef` 声明的目录？M1 属性类型到组件的映射是否符合 §8.3（Date→DateTimeInput、Enum/DictionaryRef→Select、AggregateRootRef→EntityPicker 等）？
- [ ] A2UI Surface 的组件邻接表是否无环、每个组件被恰好一个父组件引用一次、`root` 与 `children.explicitList` 引用全部存在？
- [ ] 带审批流的界面单元是否为 `renderMode=STATIC`，且同时包含 `DRAFT` 与 `SUBMIT` 两个独立操作功能点？
- [ ] 每个操作功能点的 `toolRef.behaviorRef` 与 `behaviorRef` 字段是否一致？
- [ ] `mcpApp.resourceUri` 是否以 `ui://` 开头、`mimeType` 固定为 `text/html;profile=mcp-app`、所引用工具均存在？

## 10.3  文件存储、导入与版本管理

模型文件统一位于 `yaml/` 目录：

```
yaml/
├── m1-object-model.yaml
├── m2-behavior-model.yaml
├── m3-rule-model.yaml
├── m5-actor-model.yaml
├── m6-flow-model.yaml
├── m7-report-model.yaml
├── mu-ui-model.yaml
└── manifest.json       # 可选，路径必须为相对路径
```

**版本管理约定**：

- 每个元文件内部维护自己的 `version` 字段；
- 跨模型的破坏性变更（如实体删除、行为签名变更）需要在 `CHANGELOG.md` 中记录；
- 规则模型支持独立版本；
- `manifest.json` 为可选文件，缺失时按固定文件名识别。

## 10.4  工具链建议

| 工具场景 | 建议方案 |
|----------|----------|
| 模型编辑 | VS Code + YAML 插件 + 自定义 JSON Schema 校验 |
| 可视化 | 生成聚合 ER 图、流程泳道图、能力目录视图、A2UI Surface 组件图与 MCP App 资源视图 |
| 一致性检查 | 检查行为 ownerEntity、syncTriggers 引用、M2/M7 一对一、M6 流程引用、MU 工具/能力/操作功能点门禁 |
| 代码生成 | 生成实体骨架、行为方法签名、权限枚举、查询 Service、报表导出骨架、A2UI Surface 声明与 MCP App 资源入口；渲染端、传输协议与前后端代码由实现层落地 |

---

# 附录  术语对照表

| 术语 | 定义 |
|------|------|
| 本体（Ontology） | 对某个领域中概念及其关系的形式化表达 |
| 聚合（Aggregate） | DDD 中的核心概念，是业务完整性的边界，由聚合根、子实体和值对象组成 |
| 聚合根（Aggregate Root） | 聚合的唯一入口，负责维护聚合内的业务不变性 |
| 子实体（Entity） | 聚合内部有标识的对象，依赖聚合根生命周期 |
| 值对象（Value Object） | 无标识的不可变对象，通过属性值判断相等性 |
| 聚合不变性（Invariant） | 聚合内必须始终满足的业务规则 |
| 原子行为（Atomic Behavior） | 不可再分的最小行为单元，只操作单一对象 |
| 同步联动（SyncTrigger） | 行为成功后同步调用下游行为的跨对象联动声明，条件判断可引用 M3 规则 |
| 端到端协同流（Collaboration Flow） | M6 中跨业务阶段从开始到结束的完整业务流程 |
| 审批流（Approval Flow） | M6 中由角色承担审批任务，并显式描述通过、驳回、退回及条件网关的流程 |
| 人工任务（Human Task） | 由 M5 角色承担的 USER_TASK 或 APPROVAL_TASK |
| 子流程（Sub Flow） | 被另一条 M6 流程通过 subFlowRef 调用的独立流程定义 |
| 查询报表对象（Query Report Object） | M7 中定义跨对象查询、统计分析或固定报表业务语义的对象，与一个 M2 QUERY 行为严格一对一 |
| RBAC | 基于角色的访问控制 |
| ABAC | 基于属性的访问控制，比 RBAC 更细粒度 |
| 数据字典（Data Dictionary） | 对象模型中的引用数据定义，业务数据保存 code、界面显示 label |
| 跳选框（Entity Picker） | 对象引用（AggregateRootRef）的界面组件（§8.3 中映射为 `EntityPicker`）：允许用户从目标聚合中检索并选定一个聚合根 ID |
| 操作功能点（Action Point） | MU 界面单元上的一个用户动作到工具再到 M2 行为的对应入口（actionPoint → toolRef → M2 behaviorRef） |
| 悬空引用（Dangling Reference） | 模型中引用了不存在的目标，需通过校验防止 |

---

*© 2026  Ontology-Driven Software Modeling Framework  v9.1（单体同步版 · 七模型）*

## 十一、JSON-LD 序列化约定

本框架支持 YAML → JSON-LD 双轨输出，详见 [spec § 三 双轨制策略](../../../docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md)。

### 11.1 双轨制对照

| 模型 | YAML | JSON-LD | 词表 |
|---|---|---|---|
| M1 对象 | ✅ source | ✅ full | `od:` |
| M2 行为 | ✅ 全量 | ⚠️ metadata-only | `od:` |
| M3 规则 | ✅ 全量 | ✅ shacl.ttl | `sh:` |
| M5 主体 | ✅ source | ✅ full | `od:` |
| M6 流程 | ✅ source | ✅ full（meta: 复用） | `meta:` |
| M7 查询 | ✅ source | ✅ metadata-only | `od:` |
| MU UI | ✅ source | ❌ 不迁 | — |

### 11.2 词表 IRI（未注册 w3id）

- `od:` → `https://ontology.ontology-driven.dev/v9#`
- `meta:` → `https://openclaw.dev/meta/v1#`
- `sh:` → `http://www.w3.org/ns/shacl#`

### 11.3 跨模型引用

所有跨节点引用使用 `urn:od:<domain>:<model>:<id>` URN 形式，例如：
- M1 AggregateRoot: `urn:od:contract-mgmt:M1:AGG-CONTRACT-001`
- M5 Role: `urn:od:contract-mgmt:M5:ROLE-SALES`
- M6 Flow: `urn:od:contract-mgmt:M6:FLOW-CONTRACT-001`
- M6 Step: `urn:od:contract-mgmt:M6:FLOW-CONTRACT-001:A02`

### 11.4 验证与转换工具

参见 [tools/README.md](../tools/README.md)。

### 11.5 引用 spec

- YAML → JSON-LD 迁移 spec：[2026-09-01-yaml-to-jsonld-design.md](../../../docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md)

### 11.6 M2 双层约定（metadata-only JSON-LD + 控制流 YAML）

M2 行为模型是双层协议（two-layer）的典型代表，**JSON-LD 只承载元数据，控制流留在 YAML**。这一边界由 spec § 五 阶段 4 确立，本节给出可操作的字段映射。

#### 11.6.1 字段归属表

| 字段 | 层 | 来源 |
| --- | --- | --- |
| `id`, `name`, `alias`, `description` | **JSON-LD** | 元数据，可被 SPARQL 跨文件查询 |
| `behaviorType`, `objectRef` | **JSON-LD** | 元数据；objectRef 指向 M1 AggregateRoot URN |
| `requiredPermissions` | **JSON-LD** | 元数据；权限 ID 列表，用于 SPARQL 反查 M5 |
| `yamlPointer` | **JSON-LD** | 反向引用 `#yaml/m2-behavior-model.yaml#behaviors[<id>]`，让 JSON-LD 节点能反查 YAML 控制流块 |
| `ownerEntity` | YAML | 关联 aggregate root；元数据但未迁 JSON-LD（暂留 YAML） |
| `triggerType` | YAML | USER_ACTION / SYSTEM |
| `preconditions` | YAML | 字符串条件表达式（DSL） |
| `postconditions` | YAML | 字段赋值规则 |
| `appliedRules` | YAML | 关联 M3 Rule ID 列表 |
| `syncTriggers` | YAML | 同步触发（ruleRef + behaviorRef） |

#### 11.6.2 桥接机制

- **JSON-LD → YAML**：`od:yamlPointer` 字段，值为 `#yaml/<yaml-filename>#behaviors[<id>]`。`validate.py` 的 `validate_m2_yaml_jsonld_alignment()` 用此字段校验 YAML 中存在对应 behavior。
- **YAML → JSON-LD**：`id` 字段（双方用同一 id）；`validate_m2_yaml_jsonld_alignment()` 做双向 ID set 对齐检查。

#### 11.6.3 不迁控制流字段的理由

1. **DSL 不易序列化**：`preconditions` 是字符串条件表达式（如 `contract.status == '草稿' AND 付款比例合计等于 100%`），不是结构化数据；序列化会丢失语义。
2. **控制流是人类可读的契约**：YAML 字符串 + 注释更适合业务分析师审阅；JSON-LD 是机器可读的索引层。
3. **避免语义分裂**：同一字段在 JSON-LD 是结构化、在 YAML 是 DSL，会导致双源真相问题。
4. **postconditions 是字段赋值规则**：JSON-LD 表达字段赋值需引入 SHACL/sparql 函数库，超出 spec § 五 阶段 4 范围。

#### 11.6.4 验证

- `python ../tools/validate.py ../reference-example/` 会自动触发 M2 双层对账（`validate_m2_yaml_jsonld_alignment`）。
- 漂移检测：见 [drift_check.py](../tools/drift_check.py)。
- 未来 M2-B 工作：将 `yamlPointer` 从字面量字符串升级为可在 YAML 中加载并定位的结构化反查。

参见：

- spec § 五 阶段 4（M2 双层）
- [validate.py: validate_m2_yaml_jsonld_alignment](../tools/validate.py)
- [yaml2m2jsonld.py](../tools/yaml2m2jsonld.py)
