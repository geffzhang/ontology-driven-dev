# ontology-driven-dev

> 一套「需求探索 → 本体建模」两阶段的**本体驱动需求与建模技能**（OpenClaw MetaSkill 版）。
> 基于七模型本体 YAML（M1/M2/M3/M5/M6/M7/MU），强制每个需求探索阶段人工确认，最终产出严格对齐需求规格的七模型 YAML。

---

## 一、这个技能能做什么

把一段业务需求（一句话或一段描述）变成**需求规格说明书与七模型 YAML**，且保证：

- **需求可追溯**：每个功能都能回溯到需求文档的某个条目；
- **模型一致性**：M2/MU、M7/M2 与 M6 引用均经过强制核对；
- **人工门禁不可跳过**：需求探索的 3 个簇（覆盖阶段 0-6），每一簇都必须**暂停等人确认**后才推进；
- **明确交付物**：产出需求规格说明书、M1/M2/M3/M5/M6/M7/MU 七个 YAML 和 `manifest.json`。

> **运行时要求**：本技能为 MetaSkill（12 步 DAG，类型 `kind: meta`），支持 MetaSkill 的运行时可用。WorkBuddy / Claude Code / Codex 等不支持 MetaSkill 编排的环境暂不兼容。

---

## 二、包含内容

```
ontology-driven-dev/
├── SKILL.md                                # MetaSkill 主文件（kind: meta，12 步 DAG）
├── README.md / LICENSE
└── subskills/
    ├── req-explorer/                       # 阶段一：需求探索执行器
    │   ├── SKILL.md
    │   ├── references/
    │   │   └── AI需求探索与确认提示词V9.0.md      # 含《软件需求编写规范 V9.0》全文
    │   └── reference-example/
    │       └── 合同管理需求规格说明书-V9.md         # 黄金范例（销售合同执行管理）
    └── ontology-modeler/                   # 阶段二：本体建模执行器
        ├── SKILL.md
        ├── references/
        │   └── ontology_modeling_framework_v9.md  # 七模型元规范 + YAML 模板
        └── reference-example/
            ├── m1-object-model.yaml … m7-report-model.yaml + mu-ui-model.yaml
            └── manifest.json
```

`tool_call` 步骤依赖的工具均为 **OpenClaw 内置 ITool**：

- 步骤 8 → [`FileWriteTool`](E:/GitHub/openclaw.net/src/OpenClaw.Agent/Tools/FileWriteTool.cs)（`write_file`）
- 步骤 12 → [`ValidateYamlReferencesTool`](E:/GitHub/openclaw.net/src/OpenClaw.Agent/Tools/ValidateYamlReferencesTool.cs)（`validate_yaml_references`）

开箱即用，无需额外注册或 Python 桥接。

每个 sub-skill 自带规范与范例，独立可移植。

---

## 三、安装（OpenClaw 运行时）

### 3.1 用户级（所有项目可用）

```bash
cp -r ontology-driven-dev ~/.openclaw/skills/ontology-driven-dev
```

### 3.2 项目级（仅当前项目）

```bash
cp -r ontology-driven-dev <你的项目>/.openclaw/skills/ontology-driven-dev
```

确保 OpenClaw 配置启用子目录扫描：

```yaml
# ~/.openclaw/config.yaml 或项目级 .openclaw/config.yaml
Skills:
  Load:
    ScanSubdirectories: true
```

---

## 四、使用流程（详细）

技能分**强顺序两阶段**，阶段之间及阶段一内部都必须人工确认。

### 阶段一：需求探索 → 软件需求规格说明书

- **依据**：[`subskills/req-explorer/references/AI需求探索与确认提示词V9.0.md`](subskills/req-explorer/references/AI需求探索与确认提示词V9.0.md)（含《软件需求编写规范 V9.0》全文）。
- **推进**：按 MetaSkill 步骤 2/4/6 三簇执行——阶段 0-2（foundation：总体/对象/功能规则）→ 阶段 3-4（flow：联动/协同流）→ 阶段 5-6（tail：查询/权限）。
- **门禁**：每簇结束触发 `user_input` 强门禁表单（13/9/9 字段），必须**硬暂停等人确认**；企业专属（B 类）内容 `decision` 不可 `skip`。
- **产出**：`<业务域>-需求规格说明书-V9.md`（含附录 C 七模型建模输入基线），由步骤 8 统一写入。

### 阶段二：本体建模 → 七模型 YAML

- **依据**：[`subskills/ontology-modeler/references/ontology_modeling_framework_v9.md`](subskills/ontology-modeler/references/ontology_modeling_framework_v9.md)。
- **输入**：阶段一需求文档的附录 C 基线（确定性输入，不再做大范围业务拆分）。
- **产物**：M1 对象 / M2 行为 / M3 规则 / M5 主体 / M6 流程 / M7 查询报表 / MU UI（v9.1 AI 原生：应用 → 能力目录 → 工具契约 → 界面单元 → 操作功能点）共七个 YAML + `manifest.json`，输出到项目根 `yaml/` 目录。
- **生成顺序**（步骤 9-11）：
  - 步骤 9：M1 + M5(角色)
  - 步骤 10：M2 + M3 + M7
  - 步骤 11：M5'(权限，追加到 M5 文件) + M6 + MU + manifest.json
- **一致性门禁**（步骤 12）：可追溯性、M7↔M2 一对一、M6 引用无环等 6 条强制核对，由 OpenClaw 内置 [`ValidateYamlReferencesTool`](E:/GitHub/openclaw.net/src/OpenClaw.Agent/Tools/ValidateYamlReferencesTool.cs) 实现（`tool: validate_yaml_references`）。

---

## 五、触发语（直接对 agent 说）

| 意图 | 示例 |
|---|---|
| 完整流程 | 「帮我梳理一个 XX 管理需求并完成本体建模」 |
| 仅建模 | 「基于这份需求规格说明书，做本体建模」 |
| 关键字 | 本体驱动、需求探索、本体建模、七模型、业务需求规格、MetaSkill 驱动 |

入口模式由 MetaSkill 步骤 1（`detect_entry`）自动判定（`full` / `only_modeling` / `reconfirm_stage_<N>`）。

---

## 六、子 Skill 单独调用

每个子 Skill 也可独立调用（需 OpenClaw 支持子 Skill 直调）：

```yaml
# 仅触发 req-explorer
skill: req-explorer
with:
  stage_range: "0-2"
  domain: "<业务域>"
  prior_confirms: {}
```

```yaml
# 仅触发 ontology-modeler
skill: ontology-modeler
with:
  models: ["M1", "M5"]
  domain: "<业务域>"
  baseline_doc: "<需求规格说明书绝对路径>"
  prior_models: {}
  write_manifest: false
```

详见 [`subskills/req-explorer/SKILL.md`](subskills/req-explorer/SKILL.md) 与 [`subskills/ontology-modeler/SKILL.md`](subskills/ontology-modeler/SKILL.md)。

---

## 七、许可

本项目以 **MIT License** 发布，可自由使用、修改与再分发，详见 [LICENSE](./LICENSE)。
