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
    ├── ontology-modeler/                   # 阶段二：本体建模执行器
    │   ├── SKILL.md
    │   ├── references/
    │   │   └── ontology_modeling_framework_v9.md  # 七模型元规范 + YAML 模板
    │   ├── scripts/                        # 确定性工具链（yaml2* / validate / drift_check / merge_rdf …）
    │   └── reference-example/
    │       ├── m1-object-model.yaml … m7-report-model.yaml + mu-ui-model.yaml
    │       ├── manifest.json               # 模型清单
    │       └── 派生产物：5 份 JSON-LD + m3 SHACL + manifest.jsonld + ontology-merged.ttl
    └── model-validator/                    # 阶段二门禁：跨引用 + JSON-LD 编排（步骤 12 单入口）
        ├── SKILL.md
        └── scripts/
            └── validate_yaml_refs.py       # 9 条门禁单入口（6 YAML 跨引用自研 + 3 JSON-LD 委托 ontology-modeler）
```

`tool_call` 步骤依赖的工具为 **OpenClaw 内置 ITool**：

- 步骤 8 → `write_file`

步骤 12 → `skill_exec` 调用本仓库 [`subskills/model-validator/`](subskills/model-validator/) 的 Python 门禁（`scripts/validate_yaml_refs.py`，9 条检查单入口），无需注册 ITool；JSON-LD 子门禁（`jsonld_parse` / `shacl` / `id_consistency`）通过子进程委托 `ontology-modeler/scripts/` 下的同义验证器。

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

### 阶段二：本体建模 → 七模型 YAML + 派生 RDF 制品

**产物清单**（全部落到运行工作区根 `yaml/` 目录）：

```text
yaml/
├── m1-object-model.yaml          # M1 对象模型
├── m2-behavior-model.yaml         # M2 行为模型
├── m3-rule-model.yaml             # M3 规则模型
├── m5-actor-model.yaml            # M5 主体模型（角色 + 权限）
├── m6-flow-model.yaml             # M6 流程模型
├── m7-report-model.yaml           # M7 查询报表模型
├── mu-ui-model.yaml               # MU UI 模型（v9.1 AI 原生）
├── manifest.json                  # 模型清单（步骤 11 落地）
│
│   ── 以下为派生层（yaml2* 转换器产出） ──
├── m1-object-model.jsonld
├── m2-behavior-model.jsonld
├── m3-rule-model.shacl.ttl        # M3 SHACL 形状（TTL）
├── m5-actor-model.jsonld
├── m6-flow-model.jsonld
├── m7-report-model.jsonld
├── manifest.jsonld                # 清单的 JSON-LD 派生
│
│   ── 以下仅在步骤 11 批次（六份派生齐备）由 merge_rdf.py 必做打包 ──
└── ontology-merged.ttl            # od: + meta: + sh: 单图 RDF（自包含 SHACL bundle）
```

- **依据**：[`subskills/ontology-modeler/references/ontology_modeling_framework_v9.md`](subskills/ontology-modeler/references/ontology_modeling_framework_v9.md)。
- **输入**：阶段一需求文档的附录 C 基线（确定性输入，不再做大范围业务拆分）。
- **产物**：M1 对象 / M2 行为 / M3 规则 / M5 主体 / M6 流程 / M7 查询报表 / MU UI（v9.1 AI 原生：应用 → 能力目录 → 工具契约 → 界面单元 → 操作功能点）共七个 YAML + `manifest.json`，输出到项目根 `yaml/` 目录。**派生层**：yaml2* 转换器产出 5 份 JSON-LD（M1/M2/M5/M6/M7）+ M3 SHACL TTL + `manifest.jsonld`；六份派生齐备的批次须额外由 `merge_rdf.py` 打包生成 `ontology-merged.ttl`（新产物，不替代任何逐模型文件）。
- **生成顺序**（步骤 9-11）：
  - 步骤 9：M1 + M5(角色)
  - 步骤 10：M2 + M3 + M7
  - 步骤 11：M5'(权限，追加到 M5 文件) + M6 + MU + manifest.json
  - 步骤 11 批次后（六份派生齐备）：**必做** `scripts/merge_rdf.py <yaml目录>` 打包 `ontology-merged.ttl`；仅六份齐备的批次执行，未齐备（步骤 9/10 批次）跳过。
- **一致性门禁**（步骤 12）：9 条门禁单入口 [`subskills/model-validator/scripts/validate_yaml_refs.py`](subskills/model-validator/scripts/validate_yaml_refs.py)（`skill_exec` 调用）。**6 条 YAML 跨引用**（自研）：`traceability` / `query_mapping` / `flow_refs` / `acyclic_call_graph` / `query_behavior_bidir` / `rule_condition_separation`；**3 条 JSON-LD 门禁**（委托 `ontology-modeler/scripts/` 下的同义验证器）：`jsonld_parse` / `shacl` / `id_consistency`。派生 JSON-LD 缺失时后 3 条按 `SKIP` 处理（前向兼容，不视为失败）。

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

> `model-validator` 不通过 `skill:` 直调，而是经 MetaSkill 步骤 12 `skill_exec` 调用其 Python 脚本；CI 或本地调试可直接执行该脚本：

```bash
# 完整 9 条门禁
python subskills/model-validator/scripts/validate_yaml_refs.py \
    <yaml_dir> <manifest> --format json

# 仅跑指定检查（可重复 --check）
python subskills/model-validator/scripts/validate_yaml_refs.py \
    <yaml_dir> <manifest> --check traceability --check query_mapping
```

退出码：`0` = OK / `1` = FAIL / `2` = ERROR（参数或加载错误）。详见 [`subskills/model-validator/SKILL.md`](subskills/model-validator/SKILL.md)。

---

## 七、许可

本项目以 **MIT License** 发布，可自由使用、修改与再分发，详见 [LICENSE](./LICENSE)。
