# ontology-driven-dev

> A reusable **ontology-driven requirements and modeling skill** with a two-stage pipeline: **Requirement Exploration -> Ontology Modeling**.
> It uses a seven-model ontology YAML set (M1/M2/M3/M5/M6/M7/MU), requires human confirmation at every requirement-exploration stage, and produces seven YAML models strictly aligned with the requirement specification.

[中文版 → README.md](./README.md)

---

## 1. What this skill does

Turn a business requirement, from a sentence to a paragraph, into a **requirement specification and seven-model YAML set**, while guaranteeing:

- **Traceable requirements**: every feature maps back to an item in the requirement spec;
- **Model consistency**: M2/MU, M7/M2, and M6 references receive mandatory validation;
- **Non-skippable human gates**: each of the 7 requirement-exploration stages **pauses for explicit user confirmation** before proceeding;
- **Clear deliverables**: a requirement specification, seven YAML models (M1/M2/M3/M5/M6/M7/MU), and `manifest.json`.

---

## 2. What's included

```
ontology-driven-dev/
├── SKILL.md                      # Core skill instructions (two-stage pipeline + gates)
├── references/                   # 2 mandatory methodology documents
│   ├── AI需求探索与确认提示词V9.0.md      # incl. full "Software Requirement Spec V9.0"
│   └── ontology_modeling_framework_v9.md  # seven-model meta-spec + YAML templates
└── reference-example/            # Golden example (sales-contract execution management)
│   ├── 合同管理需求规格说明书-V9.md
│   ├── m1-object-model.yaml … m7-report-model.yaml + mu-ui-model.yaml
│   └── manifest.json
```

---

## 3. Installation (mainstream tools)

> This skill has **zero dependency on any WorkBuddy-specific mechanism** and runs fully on Claude Code, Codex, Cursor, etc.
> The only adaptation point: relative paths resolve against "the folder containing this SKILL.md", which each tool resolves automatically.

### 3.1 WorkBuddy

```bash
# user-level (available in all projects)
cp -r ontology-driven-dev ~/.workbuddy/skills/ontology-driven-dev

# or project-level (current project only)
cp -r ontology-driven-dev <your-project>/.workbuddy/skills/ontology-driven-dev
```

Then just say a trigger phrase in a WorkBuddy chat (see Section 5).

### 3.2 Claude Code

Claude Code's Skills format is identical to this skill's frontmatter (`name` / `description`), so it is essentially a **direct copy**:

```bash
# user-level
cp -r ontology-driven-dev ~/.claude/skills/ontology-driven-dev

# or project-level
cp -r ontology-driven-dev .claude/skills/ontology-driven-dev
```

Claude Code auto-discovers `.claude/skills/<name>/SKILL.md` and follows its pipeline.

### 3.3 Codex

Codex has no native skill registry, but it can load in-repo instruction files and run bash in a sandbox:

```bash
# drop the skill into the repo (any directory name)
mkdir -p .codex/skills && cp -r ontology-driven-dev .codex/skills/
```

Then add one line to your repo's `codex.md` (or `AGENTS.md`):

> When the user requests ontology-driven development, requirement exploration, ontology modeling, seven-model YAML, or a business requirement specification, load `.codex/skills/ontology-driven-dev/SKILL.md` and strictly follow its two-stage workflow with human-confirmation gates.

Codex maps each stage's human gate to an interactive prompt/approval.

### 3.4 Cursor / Aider / Cline / other generic agents

Treat `SKILL.md` as a "methodology instruction file" and inject it into the project context:
- Cursor: put it in `.cursorrules` or project rules;
- Cline / Aider: paste the full `SKILL.md` at the start of a chat, or reference its path;
- Any agent supporting "system instructions / project memory": just load this `SKILL.md`.

---

## 4. Usage (detailed)

The skill runs as **two strongly ordered stages**, each separated by mandatory human confirmation.

### Stage 1: Requirement Exploration → Software Requirement Spec
- **Basis**: `references/AI需求探索与确认提示词V9.0.md` (incl. full "Software Requirement Spec V9.0").
- **Flow**: seven stages, Stage Zero through Stage Six: overall understanding -> business objects -> functions and rules -> cross-object linkage -> end-to-end collaboration and approval flow -> queries and reports -> roles and permissions.
- **Gate**: at the end of each stage, ask in the format "question + AI suggestion + rationale + other options + quick reply" and **hard-pause for confirmation**; enterprise-specific (Type-B) content must be proposed with an AI suggestion and cannot proceed until confirmed.
- **Output**: `<domain>-需求规格说明书-V9.md` (incl. Appendix C, the seven-model input baseline).

### Stage 2: Ontology Modeling → Seven-model YAML
- **Basis**: `references/ontology_modeling_framework_v9.md`.
- **Input**: Appendix C baseline from Stage 1 (a deterministic input — no further large-scale business splitting).
- **Output**: seven YAML files — M1 object / M2 behavior / M3 rule / M5 actor / M6 flow / M7 query-report / MU UI (v9.1 AI-native: Application → Capability → Tool contract → UIUnit → ActionPoint) — plus `manifest.json`, written to `yaml/`.
- **Consistency gate**: traceability, M7↔M2 one-to-one, M6 references acyclic, etc.

## 5. Trigger phrases (just say to the agent)

| Intent | Example |
|---|---|
| Full workflow | "Help me clarify an XX management requirement and complete ontology modeling" |
| Modeling only | "Based on this spec, do the ontology modeling" |
| Keywords | ontology-driven, requirement exploration, ontology modeling, seven-model YAML, business requirement specification |

---

## 6. License

Released under the **MIT License** — free to use, modify, and redistribute. See [LICENSE](./LICENSE).
