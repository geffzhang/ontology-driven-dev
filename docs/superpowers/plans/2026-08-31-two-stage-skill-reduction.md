# Two-Stage Skill Reduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce the ontology-driven-dev skill to requirement exploration and ontology modeling only.

**Architecture:** Remove the bundled application-construction assets, then revise the skill contract and both public READMEs so their stated inputs, outputs, and trigger phrases end with seven-model YAML. Verify the repository has neither deleted assets nor application-construction terminology in its maintained entry points.

**Tech Stack:** Markdown, YAML examples, Git, ripgrep.

## Global Constraints

- Delete `techbase/` in full.
- Delete only the three named construction-oriented reference documents from `references/`.
- Do not modify files under `reference-example/`.
- `SKILL.md`, `README.md`, and `README_EN.md` describe a two-stage pipeline ending with seven-model YAML and `manifest.json`.
- Requirement exploration ends at stage zero through stage six; it does not include a UI-prototype stage.

---

## File Structure

- Delete: `techbase/` - bundled Flask/React application base no longer included in the skill.
- Delete: `references/本体模型业务功能开发指导书.md` - implementation guide no longer applicable.
- Delete: `references/AI 原生应用技术架构设计文档.md` - application architecture guide no longer applicable.
- Delete: `references/UI-UE界面设计规范.md` - UI design guide no longer applicable after removing the UI-prototype stage.
- Modify: `SKILL.md` - authoritative skill workflow, supported entry points, outputs, and references.
- Modify: `README.md` - Chinese public documentation matching the reduced skill contract.
- Modify: `README_EN.md` - English public documentation matching the reduced skill contract.

### Task 1: Remove Application-Construction Assets

**Files:**
- Delete: `techbase/`
- Delete: `references/本体模型业务功能开发指导书.md`
- Delete: `references/AI 原生应用技术架构设计文档.md`
- Delete: `references/UI-UE界面设计规范.md`

**Interfaces:**
- Consumes: The approved deletion list in `docs/superpowers/specs/2026-08-31-two-stage-skill-design.md`.
- Produces: A repository without the application base or construction-only reference material.

- [ ] **Step 1: Delete the construction assets**

Run:

```powershell
Remove-Item -Recurse -Force techbase
Remove-Item -Force 'references/本体模型业务功能开发指导书.md'
Remove-Item -Force 'references/AI 原生应用技术架构设计文档.md'
Remove-Item -Force 'references/UI-UE界面设计规范.md'
```

- [ ] **Step 2: Verify every specified asset is absent**

Run:

```powershell
$paths = @('techbase', 'references/本体模型业务功能开发指导书.md', 'references/AI 原生应用技术架构设计文档.md', 'references/UI-UE界面设计规范.md')
$paths | ForEach-Object { "$_ = $(Test-Path $_)" }
```

Expected: every line ends with `False`.

### Task 2: Reduce the Authoritative Skill Workflow

**Files:**
- Modify: `SKILL.md`

**Interfaces:**
- Consumes: The remaining requirement-exploration and ontology-modeling reference documents.
- Produces: A two-stage skill contract whose final output is `yaml/` containing seven model YAML files and `manifest.json`.

- [ ] **Step 1: Rewrite the skill's scope and pipeline**

Update `SKILL.md` so that its frontmatter promises requirements and seven-model YAML, not a runnable application. Keep the existing stage-one confirmation gates and stage-two consistency gates. Change stage one to stage zero through stage six, ending with roles and permissions. Remove the entire application-construction stage, the construction-only entry point, output rows for `code-app` and `techbase`, construction disciplines, construction reference entries, and runtime instructions. Update trigger wording so it promises requirements and modeling rather than a runnable business system.

- [ ] **Step 2: Search the skill for removed concepts**

Run:

```powershell
rg -n 'techbase|code-app|code-paas|应用构建|仅构建|AI 对话|AI原生应用技术架构设计文档|本体模型业务功能开发指导书|UI-UE界面设计规范|阶段七|stage7' SKILL.md
```

Expected: no output and exit code `1`.

### Task 3: Align Chinese and English Public Documentation

**Files:**
- Modify: `README.md`
- Modify: `README_EN.md`

**Interfaces:**
- Consumes: The two-stage workflow defined in `SKILL.md`.
- Produces: Bilingual installation and usage documentation with no claims of application construction.

- [ ] **Step 1: Revise the Chinese README**

Update `README.md` to describe a two-stage requirement-exploration and ontology-modeling skill. Remove the `techbase/` directory tree, all construction reference documents, the stage-three section, the construction-only trigger row, Node/Python runtime requirements, and the tech-base license note. Change the requirement-exploration sequence to stage zero through stage six and state that the final deliverable is the requirement document plus `yaml/` seven-model YAML and `manifest.json`.

- [ ] **Step 2: Revise the English README**

Update `README_EN.md` with the same contract: two stages, no UI-prototype stage, no tech base, no runnable-app claims, no construction-only trigger, and no application runtime requirements. Use `Requirement Exploration -> Ontology Modeling` and describe the final deliverable as the requirement specification plus seven YAML models and `manifest.json`.

- [ ] **Step 3: Verify public entry points contain no construction claims**

Run:

```powershell
rg -n -i 'techbase|code-app|code-paas|应用构建|app construction|construction only|仅构建|runnable (business|management) system|AI 对话|AI chat|AI-native app|AI原生应用|本体模型业务功能开发指导书|AI 原生应用技术架构设计文档|UI-UE界面设计规范|阶段七|stage 3|stage seven' SKILL.md README.md README_EN.md
```

Expected: no output and exit code `1`.

### Task 4: Repository-Level Acceptance Check

**Files:**
- Verify: `SKILL.md`
- Verify: `README.md`
- Verify: `README_EN.md`
- Verify: deleted assets listed in Task 1

**Interfaces:**
- Consumes: Completed deletion and document changes.
- Produces: Evidence that the repository implements the approved scope reduction without touching the example assets.

- [ ] **Step 1: Confirm deleted paths and stale document references are absent**

Run:

```powershell
$paths = @('techbase', 'references/本体模型业务功能开发指导书.md', 'references/AI 原生应用技术架构设计文档.md', 'references/UI-UE界面设计规范.md')
if ($paths | Where-Object { Test-Path $_ }) { exit 1 }
rg -n '本体模型业务功能开发指导书|AI 原生应用技术架构设计文档|UI-UE界面设计规范|techbase|code-app|code-paas' --glob '!docs/superpowers/**' .
```

Expected: exit code `1` from `rg` after the path check succeeds; no stale references are printed.

- [ ] **Step 2: Review the final change set**

Run:

```powershell
git status --short
git diff --check
git diff -- SKILL.md README.md README_EN.md
```

Expected: the three documentation files are modified, four asset paths are deleted, the design and plan documents are new, and `git diff --check` reports no whitespace errors.