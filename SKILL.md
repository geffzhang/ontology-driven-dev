---
name: ontology-driven-dev
description: "Use this meta-skill when the user wants to turn a business requirement into a requirement specification and a seven-model ontology YAML set through the two-stage pipeline 'requirement exploration -> ontology modeling'. It runs a 12-step DAG with three hard human-confirmation gates in stage 1 and three model-generation layers plus one cross-reference validation pass in stage 2. Do not use it for ad-hoc Q&A, generic chat, single-stage tasks outside the two-stage pipeline, or non-ontology deliverables."
kind: meta
meta_priority: 50
always: false
final_text_mode: "step:validate_cross_refs"
triggers: ["本体驱动", "需求探索", "本体建模", "七模型", "业务需求规格", "MetaSkill 驱动"]
provenance: {"origin": "ontology-driven-dev", "license": "MIT"}
composition:
  steps:
    # ========== 步骤 1：入口检测与业务域抽取 ==========
    - id: detect_entry
      kind: llm_chat
      output_contract:
        format: json
        required_properties: [entry, domain]
      with:
        system: |
          You are the entry router for ontology-driven-dev. From the user request
          alone, classify the entry mode (full / only_modeling / reconfirm_stage_<N>),
          extract the business domain name (in Chinese), and conditionally extract
          the absolute path to an existing requirement specification document.
          Return only the JSON object below, with no extra prose, no Markdown
          fences, and no commentary.
        task: |
          输出严格的 JSON 对象（不带任何额外文字）：
          {
            "entry": "full" | "only_modeling" | "reconfirm_stage_<N>",
            "domain": "<业务域中文名，如：销售合同执行管理>",
            "baseline_doc_path": "<需求规格说明书绝对路径，仅 entry='only_modeling' 时必填，否则置空字符串>"
          }
          判别规则：
          - 用户给出业务需求描述（自然语言）→ entry="full"，baseline_doc_path=""
          - 用户已提供需求规格说明书路径或内容 → entry="only_modeling"，baseline_doc_path 必填
          - 用户说"重做阶段 N"或"修改阶段 N" → entry="reconfirm_stage_<N>"（N ∈ 0..6），baseline_doc_path=""
          - entry 字段值必须严格匹配以上三种格式之一。

          用户输入：{{ input | xml_escape | truncate(2048) }}
      route:
        - when: "outputs.detect_entry.entry == 'only_modeling'"
          to: p2_objects_roles
        - when: "outputs.detect_entry.entry | starts_with('reconfirm_stage_')"
          to: p1_foundation_explore

    # ========== 阶段一：需求探索（7 阶段 → 3 簇）==========

    # ---------- 簇 1：foundation（阶段 0-2）----------
    - id: p1_foundation_explore
      kind: agent
      skill: req-explorer
      with:
        stage_range: "0-2"
        domain: "{{ outputs.detect_entry.domain }}"
        prior_confirms: ""
      depends_on: [detect_entry]
      retry:
        max_attempts: 2
        backoff_ms: 2000
      output_contract:
        format: json
        required_properties: [stages, appendix_b_state]

    - id: p1_foundation_confirm
      kind: user_input
      depends_on: [p1_foundation_explore]
      retry:
        max_attempts: 1
        backoff_ms: 500
      clarify:
        mode: form
        nl_extract: false
        fields:
          # 簇级批量决策
          - name: bulk_decision
            type: enum
            options: [accept_all_ai, review_each_stage]
            default: review_each_stage
            required: true

          # 阶段零
          - name: stage0_ai_suggestion
            type: string
            required: true
            max_length: 1000
          - name: stage0_ai_reason
            type: string
            required: true
            max_length: 1000
          - name: stage0_decision
            type: enum
            options: [accept, modify, skip]
            default: accept
            required: true
          - name: stage0_modification
            type: string
            required: false
            max_length: 1000

          # 阶段一
          - name: stage1_ai_suggestion
            type: string
            required: true
            max_length: 1000
          - name: stage1_ai_reason
            type: string
            required: true
            max_length: 1000
          - name: stage1_decision
            type: enum
            options: [accept, modify, skip]
            default: accept
            required: true
          - name: stage1_modification
            type: string
            required: false
            max_length: 1000

          # 阶段二
          - name: stage2_ai_suggestion
            type: string
            required: true
            max_length: 1000
          - name: stage2_ai_reason
            type: string
            required: true
            max_length: 1000
          - name: stage2_decision
            type: enum
            options: [accept, modify, skip]
            default: accept
            required: true
          - name: stage2_modification
            type: string
            required: false
            max_length: 1000

          # 簇级回退
          - name: cluster_modification
            type: string
            required: false
            max_length: 1000
        cancel_words: ["算了", "取消", "cancel", "stop", "abort"]
        timeout_seconds: 1800

    # ---------- 簇 2：flow（阶段 3-4）----------
    - id: p1_flow_explore
      kind: agent
      skill: req-explorer
      with:
        stage_range: "3-4"
        domain: "{{ outputs.detect_entry.domain }}"
        prior_confirms: "{{ outputs.p1_foundation_confirm }}"
      depends_on: [p1_foundation_confirm]
      output_contract:
        format: json
        required_properties: [stages]

    - id: p1_flow_confirm
      kind: user_input
      depends_on: [p1_flow_explore]
      clarify:
        mode: form
        nl_extract: false
        fields:
          - name: bulk_decision
            type: enum
            options: [accept_all_ai, review_each_stage]
            default: review_each_stage
            required: true
          - name: stage3_ai_suggestion
            type: string
            required: true
            max_length: 1000
          - name: stage3_ai_reason
            type: string
            required: true
            max_length: 1000
          - name: stage3_decision
            type: enum
            options: [accept, modify, skip]
            default: accept
            required: true
          - name: stage3_modification
            type: string
            required: false
            max_length: 1000
          - name: stage4_ai_suggestion
            type: string
            required: true
            max_length: 1000
          - name: stage4_ai_reason
            type: string
            required: true
            max_length: 1000
          - name: stage4_decision
            type: enum
            options: [accept, modify, skip]
            default: accept
            required: true
          - name: stage4_modification
            type: string
            required: false
            max_length: 1000
          - name: cluster_modification
            type: string
            required: false
            max_length: 1000
        cancel_words: ["算了", "取消", "cancel", "stop", "abort"]
        timeout_seconds: 1800

    # ---------- 簇 3：tail（阶段 5-6）----------
    - id: p1_tail_explore
      kind: agent
      skill: req-explorer
      with:
        stage_range: "5-6"
        domain: "{{ outputs.detect_entry.domain }}"
        prior_confirms: "{{ outputs.p1_flow_confirm }}"
      depends_on: [p1_flow_confirm]
      output_contract:
        format: json
        required_properties: [stages]

    - id: p1_tail_confirm
      kind: user_input
      depends_on: [p1_tail_explore]
      clarify:
        mode: form
        nl_extract: false
        fields:
          - name: bulk_decision
            type: enum
            options: [accept_all_ai, review_each_stage]
            default: review_each_stage
            required: true
          - name: stage5_ai_suggestion
            type: string
            required: true
            max_length: 1000
          - name: stage5_ai_reason
            type: string
            required: true
            max_length: 1000
          - name: stage5_decision
            type: enum
            options: [accept, modify, skip]
            default: accept
            required: true
          - name: stage5_modification
            type: string
            required: false
            max_length: 1000
          - name: stage6_ai_suggestion
            type: string
            required: true
            max_length: 1000
          - name: stage6_ai_reason
            type: string
            required: true
            max_length: 1000
          - name: stage6_decision
            type: enum
            options: [accept, modify, skip]
            default: accept
            required: true
          - name: stage6_modification
            type: string
            required: false
            max_length: 1000
          - name: cluster_modification
            type: string
            required: false
            max_length: 1000
        cancel_words: ["算了", "取消", "cancel", "stop", "abort"]
        timeout_seconds: 1800

    # ========== 步骤 8：写入需求规格说明书 ==========
    - id: write_requirement_doc
      kind: tool_call
      tool: write_file
      tool_allowlist: [write_file]
      depends_on: [p1_tail_confirm]
      skip_if: "outputs.detect_entry.entry == 'only_modeling'"
      retry:
        max_attempts: 2
        backoff_ms: 1000
      tool_args:
        path: "{{ inputs.workspace_dir }}/{{ outputs.detect_entry.domain }}-需求规格说明书-V9.md"
        content: |
          # {{ outputs.detect_entry.domain }} 需求规格说明书（V9.0）

          > 生成方式：ontology-driven-dev MetaSkill（OpenClaw）
          > 业务域：{{ outputs.detect_entry.domain }}
          > 入口模式：{{ outputs.detect_entry.entry }}

          ## 阶段零 总体理解确认

          - 建议：{{ outputs.p1_foundation_confirm.stage0_ai_suggestion }}
          - 理由：{{ outputs.p1_foundation_confirm.stage0_ai_reason }}
          - 决定：{{ outputs.p1_foundation_confirm.stage0_decision }}
          - 修改：{{ outputs.p1_foundation_confirm.stage0_modification | default("无") }}

          ## 阶段一 业务对象

          - 建议：{{ outputs.p1_foundation_confirm.stage1_ai_suggestion }}
          - 理由：{{ outputs.p1_foundation_confirm.stage1_ai_reason }}
          - 决定：{{ outputs.p1_foundation_confirm.stage1_decision }}
          - 修改：{{ outputs.p1_foundation_confirm.stage1_modification | default("无") }}

          ## 阶段二 业务功能与规则

          - 建议：{{ outputs.p1_foundation_confirm.stage2_ai_suggestion }}
          - 理由：{{ outputs.p1_foundation_confirm.stage2_ai_reason }}
          - 决定：{{ outputs.p1_foundation_confirm.stage2_decision }}
          - 修改：{{ outputs.p1_foundation_confirm.stage2_modification | default("无") }}

          ## 阶段三 跨对象联动识别

          - 建议：{{ outputs.p1_flow_confirm.stage3_ai_suggestion }}
          - 理由：{{ outputs.p1_flow_confirm.stage3_ai_reason }}
          - 决定：{{ outputs.p1_flow_confirm.stage3_decision }}
          - 修改：{{ outputs.p1_flow_confirm.stage3_modification | default("无") }}

          ## 阶段四 端到端协同流与审批流

          - 建议：{{ outputs.p1_flow_confirm.stage4_ai_suggestion }}
          - 理由：{{ outputs.p1_flow_confirm.stage4_ai_reason }}
          - 决定：{{ outputs.p1_flow_confirm.stage4_decision }}
          - 修改：{{ outputs.p1_flow_confirm.stage4_modification | default("无") }}

          ## 阶段五 查询统计与固定报表

          - 建议：{{ outputs.p1_tail_confirm.stage5_ai_suggestion }}
          - 理由：{{ outputs.p1_tail_confirm.stage5_ai_reason }}
          - 决定：{{ outputs.p1_tail_confirm.stage5_decision }}
          - 修改：{{ outputs.p1_tail_confirm.stage5_modification | default("无") }}

          ## 阶段六 角色权限

          - 建议：{{ outputs.p1_tail_confirm.stage6_ai_suggestion }}
          - 理由：{{ outputs.p1_tail_confirm.stage6_ai_reason }}
          - 决定：{{ outputs.p1_tail_confirm.stage6_decision }}
          - 修改：{{ outputs.p1_tail_confirm.stage6_modification | default("无") }}

          ---

          ## 附录 B 确认状态

          | 阶段 | 类别 | 决定 | 修改 |
          |---|---|---|---|
          | 阶段零 | - | {{ outputs.p1_foundation_confirm.stage0_decision }} | {{ outputs.p1_foundation_confirm.stage0_modification | default("-") }} |
          | 阶段一 | - | {{ outputs.p1_foundation_confirm.stage1_decision }} | {{ outputs.p1_foundation_confirm.stage1_modification | default("-") }} |
          | 阶段二 | - | {{ outputs.p1_foundation_confirm.stage2_decision }} | {{ outputs.p1_foundation_confirm.stage2_modification | default("-") }} |
          | 阶段三 | - | {{ outputs.p1_flow_confirm.stage3_decision }} | {{ outputs.p1_flow_confirm.stage3_modification | default("-") }} |
          | 阶段四 | - | {{ outputs.p1_flow_confirm.stage4_decision }} | {{ outputs.p1_flow_confirm.stage4_modification | default("-") }} |
          | 阶段五 | - | {{ outputs.p1_tail_confirm.stage5_decision }} | {{ outputs.p1_tail_confirm.stage5_modification | default("-") }} |
          | 阶段六 | - | {{ outputs.p1_tail_confirm.stage6_decision }} | {{ outputs.p1_tail_confirm.stage6_modification | default("-") }} |

    # ========== 阶段二：本体建模（步骤 9-12）==========

    - id: p2_objects_roles
      kind: agent
      skill: ontology-modeler
      depends_on: [write_requirement_doc]
      # write_requirement_doc 在 only_modeling 模式下通过 skip_if 透传，本步骤仍可执行
      with:
        models: ["M1", "M5"]
        domain: "{{ outputs.detect_entry.domain }}"
        baseline_doc: >-
          {% if outputs.detect_entry.baseline_doc_path and outputs.detect_entry.baseline_doc_path != "" %}
          {{ outputs.detect_entry.baseline_doc_path }}
          {% else %}
          {{ inputs.workspace_dir }}/{{ outputs.detect_entry.domain }}-需求规格说明书-V9.md
          {% endif %}
        prior_models: {}
        write_manifest: false
      retry:
        max_attempts: 2
        backoff_ms: 2000
      output_contract:
        format: json
        required_properties: [model_files, generation_log]

    - id: p2_behaviors_rules
      kind: agent
      skill: ontology-modeler
      depends_on: [p2_objects_roles]
      with:
        models: ["M2", "M3", "M7"]
        domain: "{{ outputs.detect_entry.domain }}"
        baseline_doc: >-
          {% if outputs.detect_entry.baseline_doc_path and outputs.detect_entry.baseline_doc_path != "" %}
          {{ outputs.detect_entry.baseline_doc_path }}
          {% else %}
          {{ inputs.workspace_dir }}/{{ outputs.detect_entry.domain }}-需求规格说明书-V9.md
          {% endif %}
        prior_models:
          M1: "{{ outputs.p2_objects_roles.model_files.M1 }}"
          M5: "{{ outputs.p2_objects_roles.model_files.M5 }}"
        write_manifest: false
      retry:
        max_attempts: 2
        backoff_ms: 2000
      output_contract:
        format: json
        required_properties: [model_files, generation_log]

    - id: p2_flows_ui
      kind: agent
      skill: ontology-modeler
      depends_on: [p2_behaviors_rules]
      with:
        models: ["M5-perm", "M6", "MU"]
        domain: "{{ outputs.detect_entry.domain }}"
        baseline_doc: >-
          {% if outputs.detect_entry.baseline_doc_path and outputs.detect_entry.baseline_doc_path != "" %}
          {{ outputs.detect_entry.baseline_doc_path }}
          {% else %}
          {{ inputs.workspace_dir }}/{{ outputs.detect_entry.domain }}-需求规格说明书-V9.md
          {% endif %}
        prior_models:
          M1: "{{ outputs.p2_objects_roles.model_files.M1 }}"
          M2: "{{ outputs.p2_behaviors_rules.model_files.M2 }}"
          M3: "{{ outputs.p2_behaviors_rules.model_files.M3 }}"
          M5-actor: "{{ outputs.p2_objects_roles.model_files.M5 }}"
          M7: "{{ outputs.p2_behaviors_rules.model_files.M7 }}"
        write_manifest: true
      retry:
        max_attempts: 2
        backoff_ms: 2000
      output_contract:
        format: json
        required_properties: [model_files, generation_log, manifest_path]

    - id: validate_cross_refs
      # 9 条检查的语义定义见 subskills/model-validator/SKILL.md 第一节；
      # 脚本实现 scripts/validate_yaml_refs.py（6 条跨引用检查 + 3 条 JSON-LD 门禁，
      # 经子进程委托 ontology-modeler 验证器）。
      kind: skill_exec
      skill: model-validator
      skill_exec_entrypoint: scripts/validate_yaml_refs.py
      skill_exec_parse_mode: json
      skill_exec_args:
        - "{{ inputs.workspace_dir }}/yaml"
        - "{{ outputs.p2_flows_ui.manifest_path }}"
      depends_on: [p2_flows_ui]
      retry:
        max_attempts: 2
        backoff_ms: 1000
---

# 本体驱动需求与建模技能（MetaSkill 版）

支持 MetaSkill 的运行时可用。提供强类型表单、跨会话 checkpoint、DAG 校验、审计追踪。

> **路径约定**：
> - 本文件位于项目根 `SKILL.md`（`kind: meta`）
> - 子 Skill 由 OpenClaw SkillLoader 解析，需启用 `Skills.Load.ScanSubdirectories`：
>   - `subskills/req-explorer/SKILL.md`（阶段一 7 阶段探索执行器）
>   - `subskills/ontology-modeler/SKILL.md`（阶段二七模型生成执行器）
>   - `subskills/model-validator/SKILL.md`（步骤 12 跨引用门禁，skill_exec entrypoint）
> - 子 Skill 自带的规范与范例位于其各自的 `references/`、`reference-example/` 子目录

## 一、12 步骨架

| # | Id | Kind | 作用 |
|---|---|---|---|
| 1 | `detect_entry` | `llm_chat` | 路由检测（full / only_modeling / reconfirm_stage_N）+ 业务域抽取 |
| 2 | `p1_foundation_explore` | `agent → req-explorer` | 阶段 0-2 探索（总体 / 对象 / 功能与规则） |
| 3 | `p1_foundation_confirm` | `user_input` | foundation 簇硬门禁（13 字段表单） |
| 4 | `p1_flow_explore` | `agent → req-explorer` | 阶段 3-4 探索（联动 / 协同流） |
| 5 | `p1_flow_confirm` | `user_input` | flow 簇硬门禁（9 字段表单） |
| 6 | `p1_tail_explore` | `agent → req-explorer` | 阶段 5-6 探索（查询 / 权限） |
| 7 | `p1_tail_confirm` | `user_input` | tail 簇硬门禁（9 字段表单） |
| 8 | `write_requirement_doc` | `tool_call (write_file)` | 写入需求规格说明书到工作目录（`skip_if` 仅建模入口） |
| 9 | `p2_objects_roles` | `agent → ontology-modeler` | M1 + M5(角色) |
| 10 | `p2_behaviors_rules` | `agent → ontology-modeler` | M2 + M3 + M7 |
| 11 | `p2_flows_ui` | `agent → ontology-modeler` | M5'(权限) + M6 + MU + manifest.json |
| 12 | `validate_cross_refs` | `skill_exec (model-validator scripts/validate_yaml_refs.py)` | 6 条跨引用 + 3 条 JSON-LD 门禁一次性扫描 |

## 二、关键设计决策

| 决策点 | 选择 | 说明 |
|---|---|---|
| 业务域来源 | 由 `detect_entry` 一次性抽取 | 省一步 user_input 预算 |
| `bulk_decision` 行为 | 表单字段始终展示，作为快捷覆盖 | MetaClarifySchema 无 field-level skip_if |
| M5 拆分 | M5(角色) 在步骤 9，M5'(权限) 在步骤 11 | 保留阶段二语义清晰度 |
| 失败兜底 | 全部步骤靠 `retry` 策略重试 | 受 12 步预算约束，不配置 on_failure 替代步骤 |

## 三、子 Skill 索引

| 子 Skill | 路径 | 自带资源 |
|---|---|---|
| `req-explorer` | `subskills/req-explorer/SKILL.md` | `references/AI需求探索与确认提示词V9.0.md`、`reference-example/合同管理需求规格说明书-V9.md` |
| `ontology-modeler` | `subskills/ontology-modeler/SKILL.md` | `references/ontology_modeling_framework_v9.md`、`reference-example/`（7 个 YAML + manifest.json）、`scripts/`（转换与校验工具链） |
| `model-validator` | `subskills/model-validator/SKILL.md` | `scripts/validate_yaml_refs.py`（6 条跨引用门禁 + 3 条 JSON-LD 门禁） |

## 四、失败兜底

若本技能在任何步骤失败，**逐字回报失败信息**给用户：

1. **明确失败的步骤**（如 `p1_foundation_explore`、`validate_cross_refs`）。
2. **引用编排器的结构化错误信息**（如 `prior_model_missing: M1`、`framework_doc_not_found`、`ref_inconsistency: M6.behaviorRef=<x> vs M2.behaviorRef=<x>`）。
3. **立即终止**。不得临场编造 YAML、跳步补写、或跳过 `validate_cross_refs` 继续。

不得做的事：

- **不得**在未读到实际 YAML 文件的情况下宣称七模型已生成；如需验证，必须用 `read_file` 真读到 `yaml/m<1-7, u>-*-model.yaml`。
- **不得**伪造文件路径、模型 ID、对象 ID、引用关系。
- **不得**绕过门禁——例如跳过 `validate_cross_refs`、自动 `accept` 用户未确认的表单、或在 B 类字段强行 `skip`。
- **不得**把 `cancel_words` 触发后的退出当成正常完成；视为人工取消，向用户回执"流程已中止，未写盘"。

若用户想重试：

- `agent` kind 步骤的瞬时失败（子 Agent 解析/网络）靠本步骤的 `retry` 策略自动恢复。
- 子 Skill 抛出的结构性错误（缺基线、缺上游模型、引用断裂）需用户先解决底层问题，再重发原请求。
- 用户明确说"重做阶段 N"时，由 `detect_entry` 路由到 `entry="reconfirm_stage_<N>"`，从该阶段所在簇重启，不要从阶段 0 全量重跑。

## 五、tool_call 与 skill_exec 实现

| Step | 形式 | 名称 | 实现来源 | 说明 |
|---|---|---|---|---|
| 8 `write_requirement_doc` | `tool_call` | `write_file` | OpenClaw 内置（[`FileWriteTool.cs`](E:/GitHub/openclaw.net/src/OpenClaw.Agent/Tools/FileWriteTool.cs)） | 原子写入 + 自动创建父目录 + 路径策略沙箱保护 |
| 12 `validate_cross_refs` | `skill_exec` | `scripts/validate_yaml_refs.py` | 本仓库 [`subskills/model-validator/`](subskills/model-validator/) | 6 条交叉引用门禁 + 3 条 JSON-LD 门禁（子进程委托 ontology-modeler 验证器）；退出码非 0 = 步骤失败 |

- `tool_call` 步骤解析为 `ITool.Name` 字面量，OpenClaw 运行时按 Ordinal 严格相等在 `_toolsByName` 字典中查找（[`OpenClawToolExecutor.cs:207`](E:/GitHub/openclaw.net/src/OpenClaw.Agent/OpenClawToolExecutor.cs#L207)）——`write_file` 开箱即用，无需额外注册。
- `skill_exec` 步骤把 entrypoint 当子进程执行：entrypoint 必须位于 `skill:` 所指 Skill 根目录内（`subskills/model-validator/`）；`parse_mode: json` 要求 stdout 为合法 JSON；退出码非 0 → 步骤失败（`skill_exec_failed`），`retry` 与失败兜底照常生效。9 条检查语义、输出契约与错误码见 [model-validator SKILL.md](subskills/model-validator/SKILL.md)。
