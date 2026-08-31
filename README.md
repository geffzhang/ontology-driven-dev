# ontology-driven-dev

> 一套「需求探索 → 本体建模」两阶段的**本体驱动需求与建模技能**。
> 基于七模型本体 YAML（M1/M2/M3/M5/M6/M7/MU），强制每个需求探索阶段人工确认，最终产出严格对齐需求规格的七模型 YAML。

[English version → README_EN.md](./README_EN.md)

---

## 一、这个技能能做什么

把一段业务需求（一句话或一段描述）变成**需求规格说明书与七模型 YAML**，且保证：

- **需求可追溯**：每个功能都能回溯到需求文档的某个条目；
- **模型一致性**：M2/MU、M7/M2 与 M6 引用均经过强制核对；
- **人工门禁不可跳过**：需求探索的 7 个阶段，每一阶段都必须**暂停等人确认**后才推进；
- **明确交付物**：产出需求规格说明书、M1/M2/M3/M5/M6/M7/MU 七个 YAML 和 `manifest.json`。

---

## 二、包含内容

```
ontology-driven-dev/
├── SKILL.md                      # 技能核心指令（两阶段管线 + 门禁）
├── references/                   # 2 份方法论文档（强制规范）
│   ├── AI需求探索与确认提示词V9.0.md      # 含《软件需求编写规范 V9.0》全文
│   └── ontology_modeling_framework_v9.md  # 七模型元规范 + YAML 模板
└── reference-example/            # 黄金范例（销售合同执行管理）
│   ├── 合同管理需求规格说明书-V9.md
│   ├── m1-object-model.yaml … m7-report-model.yaml + mu-ui-model.yaml
│   └── manifest.json
```

---

## 三、安装（主流工具）

> 本技能**不依赖任何 WorkBuddy 专有机制**，可完整运行在 Claude Code、Codex、Cursor 等工具上。
> 唯一适配点：技能内相对路径以「本 SKILL.md 所在文件夹」为根，各工具会自动解析。

### 1. WorkBuddy

```bash
# 用户级（所有项目可用）
cp -r ontology-driven-dev ~/.workbuddy/skills/ontology-driven-dev

# 或项目级（仅当前项目）
cp -r ontology-driven-dev <你的项目>/.workbuddy/skills/ontology-driven-dev
```

在 WorkBuddy 对话中直接说触发语即可（见第五节）。

### 2. Claude Code

Claude Code 的 Skills 格式与本技能 frontmatter（`name` / `description`）完全一致，基本**直接复制**即可：

```bash
# 用户级
cp -r ontology-driven-dev ~/.claude/skills/ontology-driven-dev

# 或项目级
cp -r ontology-driven-dev .claude/skills/ontology-driven-dev
```

Claude Code 会自动发现 `.claude/skills/<name>/SKILL.md` 并按其流程执行。

### 3. Codex

Codex 没有原生 skill 注册表，但能加载仓库内的指令文件并在沙箱中执行 bash：

```bash
# 把技能放进仓库（目录名随意）
mkdir -p .codex/skills && cp -r ontology-driven-dev .codex/skills/
```

然后在仓库的 `codex.md`（或 `AGENTS.md`）中加入一句：

> 当用户要做「本体驱动 / 需求探索 / 本体建模 / 七模型 / 业务需求规格」时，
> 加载 `.codex/skills/ontology-driven-dev/SKILL.md` 并严格按其「两阶段 + 人工确认门禁」流程执行。

Codex 会把每阶段的人工确认映射为交互式提问/审批。

### 4. Cursor / Aider / Cline / 其他通用 Agent

把 `SKILL.md` 当作「方法论指令文件」注入项目上下文即可：
- Cursor：放入 `.cursorrules` 或项目规则；
- Cline / Aider：在对话开头粘贴 `SKILL.md` 全文，或引用其路径；
- 任何支持「系统指令 / 项目记忆」的 agent：加载本 SKILL.md 即可。

---

## 四、使用流程（详细）

技能分**强顺序两阶段**，阶段之间及阶段一内部都必须人工确认。

### 阶段一：需求探索 → 软件需求规格说明书
- **依据**：`references/AI需求探索与确认提示词V9.0.md`（含《软件需求编写规范 V9.0》全文）。
- **推进**：按「阶段零 ∼ 阶段六」七阶段——总体理解 → 业务对象 → 业务功能与规则 → 跨对象联动 → 端到端协同/审批流 → 查询统计与报表 → 角色权限。
- **门禁**：每个阶段结束必须按「问题 + AI 建议 + 理由 + 其他选项 + 快捷回复」格式提问，并**硬暂停等人确认**；企业专属（B 类）内容必须带 AI 建议提问，未确认不得进入下一阶段。
- **产出**：`<业务域>-需求规格说明书-V9.md`（含附录 C 七模型建模输入基线）。

### 阶段二：本体建模 → 七模型 YAML
- **依据**：`references/ontology_modeling_framework_v9.md`。
- **输入**：阶段一需求文档的附录 C 基线（确定性输入，不再做大范围业务拆分）。
- **产物**：M1 对象 / M2 行为 / M3 规则 / M5 主体 / M6 流程 / M7 查询报表 / MU UI 共七个 YAML + `manifest.json`，输出到 `yaml/`。
- **一致性门禁**：可追溯性、M7↔M2 一对一、M6 引用无环等强制核对。

---

## 五、触发语（直接对 agent 说）

| 意图 | 示例 |
|---|---|
| 完整流程 | 「帮我梳理一个 XX 管理需求并完成本体建模」 |
| 仅建模 | 「基于这份需求规格说明书，做本体建模」 |
| 关键字 | 本体驱动、需求探索、本体建模、七模型、业务需求规格 |

---

## 六、许可

本项目以 **MIT License** 发布，可自由使用、修改与再分发，详见 [LICENSE](./LICENSE)。
