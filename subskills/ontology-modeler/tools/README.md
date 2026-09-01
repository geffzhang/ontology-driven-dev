# ontology-modeler / tools

本目录存放 ontology-modeler 子 Skill 的验证与转换工具。**全部为 PoC/阶段工具**，最终集成由各阶段任务实施（见 [spec § 五 路线图](../../../../docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md)）。

## 工具清单

| 工具 | 角色 | 输入 | 输出 |
|---|---|---|---|
| `yaml2m6jsonld.py` | M6 YAML → JSON-LD 转换器（meta: 词表） | `m6-flow-model.yaml` | `m6-flow-model.jsonld` |
| `yaml2od_jsonld.py` | M1/M5/M7 YAML → JSON-LD 转换器（od: 词表） | `m{1,5,7}-*-model.yaml` | `m{1,5,7}-*-model.jsonld` |
| `validate_m6jsonld.py` | M6 JSON-LD 验证（单文件） | `m6-flow-model.jsonld` | exit 0/1 + 行输出 |
| `validate_od_jsonld.py` | M1/M5/M7 JSON-LD 验证（多文件） | `m{1,5,7}-*-model.jsonld` | exit 0/1 + 行输出 |
| `validate.py` | **统一入口**（本目录核心） | 目录 / 文件 | text 或 json + exit 0/1/2 |

## validate.py 用法

```bash
# 默认 text 输出（聚合）
python tools/validate.py reference-example/

# JSON 输出（agent / IDE 友好）
python tools/validate.py reference-example/ --format json | jq '.[] | {path, passed}'

# 把 SKIPPED（YAML）也当失败处理
python tools/validate.py reference-example/ --strict

# 单文件验证
python tools/validate.py reference-example/m6-flow-model.jsonld
```

### 退出码

| Code | 含义 |
|---|---|
| 0 | 全部 JSON-LD 通过；YAML 被 SKIPPED（除非 --strict） |
| 1 | 至少一个 JSON-LD 验证失败 |
| 2 | 配置错误（路径不存在 / --strict 下有 SKIPPED） |

### 路由逻辑

```
file.suffix
  ├─ .jsonld  →  read @context IRI
  │   ├─ "https://openclaw.dev/meta/v1#"           → validate_m6jsonld.py
  │   ├─ "https://ontology.ontology-driven.dev/v9#" → validate_od_jsonld.py
  │   └─ 其他                                       → FAIL "无法识别 vocab"
  ├─ .yaml / .yml  →  SKIPPED（不在本 Skill 职责）
  └─ 其他          →  忽略
```

## 与 OpenClaw ValidateYamlReferencesTool 的关系

`ValidateYamlReferencesTool.cs`（[OpenClaw.Agent.Tools](../../../../../../../GitHub/openclaw.net/src/OpenClaw.Agent/Tools/ValidateYamlReferencesTool.cs)）是 OpenClaw 运行时内置 ITool，**职责**：

- 校验 YAML 文件间的 `*Ref` 字段（`roleRef`、`behaviorRef`、`objectRef` 等）
- 由 MetaSkill step 12 通过 `tool: validate_yaml_references` 调度
- 实现跨文件 YAML 跨引用一致性

**`validate.py` 的职责**：

- 校验 JSON-LD 文件的 `od:` / `meta:` 词表结构
- 由 ontology-modeler 本地/CI 调用
- PoC 阶段；后续可由 ontology-modeler step 12 调用作为前置

**两者关系**：互补，不重叠。

| 维度 | `ValidateYamlReferencesTool` (C#) | `validate.py` (Python) |
|---|---|---|
| 验证对象 | YAML | JSON-LD |
| 词表 | 不绑定词表 | 绑定 od: / meta: 词表 IRI |
| 调度方 | OpenClaw 运行时（agent step） | 本地 CLI / CI |
| 仓库 | openclaw.net | ontology-driven-dev |

## 依赖

```bash
pip install pyyaml rdflib
```

- `pyyaml` ≥ 6.0
- `rdflib` ≥ 7.0（内置 JSON-LD Processor）

## 当前 PoC 状态

| 验证器 | 黄金范例 | 状态 |
|---|---|---|
| `validate_m6jsonld.py` | 4 flows | ✅ PASS |
| `validate_od_jsonld.py` | M1=23 / M5=39 / M7=5 节点 | ✅ PASS |
| `validate.py` 统一入口 | 4 jsonld + 7 yaml | ✅ PASS（exit 0） |

## 后续路线（来自 spec）

| 阶段 | 任务 |
|---|---|
| 5 | `pyshacl` SHACL 校验集成；补全 `od:DictionaryType.items[]` / `od:Report.joins` / 双向 Actor-Role 引用 |
| 6 | 把 `validate_od_jsonld.py` + `validate_m6jsonld.py` 整合到 ontology-modeler 的内置 step（本目录） |

详细见 [2026-09-01-yaml-to-jsonld-design.md § 五](../../../../docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md)。