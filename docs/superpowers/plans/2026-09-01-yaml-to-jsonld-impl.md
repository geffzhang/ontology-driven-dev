# YAML → JSON-LD 升级实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 ontology-driven-dev 七模型 YAML 升级为"双轨制 JSON-LD"：M6 复用 OpenClaw MetaSkill `meta:` 词表；M1/M2/M3/M5/M7 用自建 `od:` 词表；MU 不迁。覆盖 7 个验收标准 AC1-AC6。

**Architecture:**
- **双轨制**：M1/M2/M3/M5/M7 输出 `od:` JSON-LD（独立数据对象）；M6 输出 `meta:` JSON-LD（复用 OpenClaw MetaSkill 词表）；MU 保持 YAML 不迁
- **YAML = 人读源 + 转换输入源**；JSON-LD = 机器消费源
- **统一验证入口** `validate.py` 聚合 PoC 验证器 + SHACL + OpenClaw YAML 工具（SKIPPED 桥接）
- **CI 门禁**：YAML ID 集合 == JSON-LD @id 集合 + SHACL conforms + meta:hasStep ≤ 12

**Tech Stack:**
- Python 3.14 + `pyyaml` 6.0+ + `rdflib` 7.0+ + `pyshacl` 0.40+
- .NET 8 + `dotNetRDF`（OpenClaw 仓库 `E:/GitHub/openclaw.net/`，跨仓库集成）
- GitHub Actions cron（漂移检测）

**Spec:** [docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md](../specs/2026-09-01-yaml-to-jsonld-design.md)

## 全局约束（来自 spec）

- `od:` 词表 IRI：`https://ontology.ontology-driven.dev/v9#`（未注册 w3id，阶段性使用）
- `meta:` 词表 IRI：`https://openclaw.dev/meta/v1#`（OpenClaw 官方词表，未注册）
- 跨模型引用 URN：`urn:od:contract-mgmt:<M{1..7}>:<id>`
- MetaSkill 12 步硬上限（`meta:hasStep` 数组长度 ≤ 12）
- YAML 仍为 source of truth（ontology-modeler 输入契约）
- 不生成 OpenClaw `SKILL.md`（仅 JSON-LD，运行时调度不在本 spec 范围）
- 中文 UI 字符串在 Windows GBK 控制台乱码属已知问题；不影响逻辑正确性

## 已完成（PoC 闭环，对账基线已建立）

以下阶段已在以下 commit 完成，**不重做**：

| 阶段 | 状态 | Commit(s) |
|---|---|---|
| 阶段 0 锁定动机 | ✅ | 本 spec 即是 |
| 阶段 2 部分 M1/M5 转换 | ✅ | [898d6e0](https://github.com/example/ontology-driven-dev/commit/898d6e0) |
| 阶段 5 M6 转换 + 验证 | ✅ | [65aac81](https://github.com/example/ontology-driven-dev/commit/65aac81), [84dcce6](https://github.com/example/ontology-driven-dev/commit/84dcce6) |
| 阶段 5 M7 转换 | ✅ | [898d6e0](https://github.com/example/ontology-driven-dev/commit/898d6e0) |
| 阶段 5 DictionaryType 细化 | ✅ | [8a3275e](https://github.com/example/ontology-driven-dev/commit/8a3275e) |
| 阶段 5 SHACL PoC（meta + od） | ✅ | [8a3275e](https://github.com/example/ontology-driven-dev/commit/8a3275e) |
| 阶段 5 SPARQL 跨文件演示 | ✅ | [8a3275e](https://github.com/example/ontology-driven-dev/commit/8a3275e) |
| validate.py 统一入口 | ✅ | [c5ba10f](https://github.com/example/ontology-driven-dev/commit/c5ba10f), [3502a5b](https://github.com/example/ontology-driven-dev/commit/3502a5b) |

## 文件结构（实施计划覆盖）

| 路径 | 角色 | 任务 |
|---|---|---|
| `subskills/ontology-modeler/references/od-vocabulary-v9.ttl` | `od:` 词表定义（Turtle） | T1 |
| `subskills/ontology-modeler/references/od-context-v9.jsonld` | `od:` 词表 JSON-LD context | T1 |
| `subskills/ontology-modeler/reference-example/manifest.jsonld` | manifest 顶层入口 | T2 |
| `subskills/ontology-modeler/reference-example/m2-behavior-model.jsonld` | M2 元数据层 | T4 |
| `subskills/ontology-modeler/tools/yaml2m2jsonld.py` | M2 转换器 | T4 |
| `subskills/ontology-modeler/tools/yaml2m3shacl.py` | M3 → SHACL 转换器 | T6 |
| `subskills/ontology-modeler/reference-example/m3-rule-model.shacl.ttl` | M3 SHACL 形状 | T7 |
| `subskills/ontology-modeler/tools/shacl/m3_rule_shape.ttl` | M3 形状定义（PoC 用 SHACL 跑） | T7 |
| `subskills/ontology-modeler/tools/drift_check.py` | YAML ↔ JSON-LD ID 漂移检测 | T9 |
| `subskills/ontology-modeler/references/ontology_modeling_framework_v9.1.md` §11 | JSON-LD 序列化约定文档 | T10 |
| OpenClaw 仓库 `src/OpenClaw.Agent/Tools/ValidateJsonLdTool.cs` | 跨仓库 C# JSON-LD 验证工具 | T11 |
| `.github/workflows/drift-check.yml` | 每周 cron 漂移检测 | T12 |

---

### Task 1: 冻结 `od:` 词表（references/od-vocabulary-v9.ttl + od-context-v9.jsonld）

**Files:**
- Create: `subskills/ontology-modeler/references/od-vocabulary-v9.ttl`
- Create: `subskills/ontology-modeler/references/od-context-v9.jsonld`

**Interfaces:**
- Consumes: 无（首建）
- Produces: Turtle 词表 + JSON-LD context，作为后续 M3/M2 转换器的依据

- [ ] **Step 1: 创建 references/ 目录**

```bash
mkdir -p subskills/ontology-modeler/references
```

- [ ] **Step 2: 写 od-vocabulary-v9.ttl**

最小词表（PoC 已验证可行，正式版加完整 rdfs:label/comment）：

```turtle
@prefix od: <https://ontology.ontology-driven.dev/v9#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

od:AggregateRoot a rdfs:Class ;
    rdfs:label "聚合根"@zh ;
    rdfs:comment "DDD 聚合根节点" .

od:Entity a rdfs:Class ;
    rdfs:label "实体"@zh .

od:ValueObject a rdfs:Class ;
    rdfs:label "值对象"@zh .

od:Attribute a rdfs:Class ;
    rdfs:label "属性"@zh .

od:Invariant a rdfs:Class ;
    rdfs:label "不变量"@zh .

od:Association a rdfs:Class ;
    rdfs:label "聚合关联"@zh .

od:DataDictionary a rdfs:Class ;
    rdfs:label "数据字典"@zh .

od:DictionaryType a rdfs:Class ;
    rdfs:label "字典类型"@zh .

od:DictionaryItem a rdfs:Class ;
    rdfs:label "字典项"@zh .

od:Actor a rdfs:Class ;
    rdfs:label "主体"@zh .

od:Role a rdfs:Class ;
    rdfs:label "角色"@zh .

od:Permission a rdfs:Class ;
    rdfs:label "权限"@zh .

od:Behavior a rdfs:Class ;
    rdfs:label "行为"@zh .

od:Report a rdfs:Class ;
    rdfs:label "报表"@zh .

od:Rule a rdfs:Class ;
    rdfs:label "规则"@zh .
```

- [ ] **Step 3: 写 od-context-v9.jsonld**

```json
{
  "@context": {
    "@vocab": "https://ontology.ontology-driven.dev/v9#",
    "od": "https://ontology.ontology-driven.dev/v9#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "label": "rdfs:label",
    "type": "@type",
    "id": "@id",
    "od:sourceAggregate": {"@type": "@id"},
    "od:targetAggregate": {"@type": "@id"},
    "od:hasRole": {"@type": "@id"},
    "od:hasPermission": {"@type": "@id"},
    "od:hasItem": {"@type": "@id"},
    "od:objectRef": {"@type": "@id"},
    "od:boundBehavior": {"@type": "@id"}
  }
}
```

- [ ] **Step 4: 验证 rdflib 可加载两个文件**

```bash
python -c "
from rdflib import Graph
g = Graph()
g.parse('subskills/ontology-modeler/references/od-vocabulary-v9.ttl', format='turtle')
g.parse('subskills/ontology-modeler/references/od-context-v9.jsonld', format='json-ld')
print('OK:', len(g), 'triples')
"
```

Expected: `OK: 20+ triples`

- [ ] **Step 5: Commit**

```bash
git add subskills/ontology-modeler/references/
git commit -m "feat(vocab): freeze od: vocabulary v9 (.ttl + jsonld context)"
```

---

### Task 2: manifest.json 升级为 JSON-LD 顶层入口（manifest.jsonld）

**Files:**
- Create: `subskills/ontology-modeler/reference-example/manifest.jsonld`

**Interfaces:**
- Consumes: 7 个模型 YAML 文件路径清单
- Produces: `@graph` 包含 7 个 `od:ModelManifestEntry` 节点，每个节点记录 yaml/iri/vocabulary 策略

- [ ] **Step 1: 写生成器 tools/yaml2manifest.py**

```python
#!/usr/bin/env python3
"""yaml2manifest.py — 从 7 个 YAML 生成 manifest.jsonld 顶层入口"""
import json, sys
from pathlib import Path
import yaml

OD_CONTEXT = {
    "@vocab": "https://ontology.ontology-driven.dev/v9#",
    "od": "https://ontology.ontology-driven.dev/v9#",
    "meta": "https://openclaw.dev/meta/v1#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}

DOMAIN = "contract-mgmt"

MODELS = {
    "M1": {"yaml": "m1-object-model.yaml", "vocab": "od:", "strategy": "full"},
    "M2": {"yaml": "m2-behavior-model.yaml", "vocab": "od:", "strategy": "metadata-only"},
    "M3": {"yaml": "m3-rule-model.yaml", "vocab": "sh:", "strategy": "shacl"},
    "M5": {"yaml": "m5-actor-model.yaml", "vocab": "od:", "strategy": "full"},
    "M6": {"yaml": "m6-flow-model.yaml", "vocab": "meta:", "strategy": "reuse"},
    "M7": {"yaml": "m7-report-model.yaml", "vocab": "od:", "strategy": "metadata-only"},
    "MU": {"yaml": "mu-ui-model.yaml", "vocab": None, "strategy": "not-migrated"},
}

def build_entry(model_id, info):
    if info["strategy"] == "not-migrated":
        return {
            "@id": f"urn:od:{DOMAIN}:manifest:{model_id}",
            "@type": "od:ModelManifestEntry",
            "od:modelId": model_id,
            "od:yamlSource": f"yaml/{info['yaml']}",
            "od:jsonLdSource": None,
            "od:notMigrated": True,
        }
    ext = "jsonld" if info["vocab"] != "sh:" else "shacl.ttl"
    return {
        "@id": f"urn:od:{DOMAIN}:manifest:{model_id}",
        "@type": "od:ModelManifestEntry",
        "od:modelId": model_id,
        "od:yamlSource": f"yaml/{info['yaml']}",
        "od:jsonLdSource": f"yaml/{info['yaml'].replace('.yaml', '.' + ext)}",
        "od:vocabulary": info["vocab"],
        "od:vocabularyStrategy": info["strategy"],
    }

def main():
    src_dir = Path(sys.argv[1])
    out = Path(sys.argv[2])
    graph = [build_entry(mid, info) for mid, info in MODELS.items()]
    doc = {"@context": OD_CONTEXT, "@graph": graph}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] manifest.jsonld: {len(graph)} entries")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 跑生成器**

```bash
python subskills/ontology-modeler/tools/yaml2manifest.py \
    subskills/ontology-modeler/reference-example \
    subskills/ontology-modeler/reference-example/manifest.jsonld
```

Expected: `[OK] manifest.jsonld: 7 entries`

- [ ] **Step 3: 验证 rdflib 解析**

```bash
python -c "
from rdflib import Graph
g = Graph()
g.parse('subskills/ontology-modeler/reference-example/manifest.jsonld', format='json-ld')
print('triples:', len(g))
"
```

Expected: `triples: 30+`

- [ ] **Step 4: Commit**

```bash
git add subskills/ontology-modeler/tools/yaml2manifest.py \
        subskills/ontology-modeler/reference-example/manifest.jsonld
git commit -m "feat(manifest): upgrade to JSON-LD top-level entry (G4 in spec)"
```

---

### Task 3: 把 manifest.jsonld 验证集成到 validate.py

**Files:**
- Modify: `subskills/ontology-modeler/tools/validate.py`

**Interfaces:**
- Consumes: `manifest.jsonld` 路径
- Produces: 在 validate.py 输出中增加 `[OK] manifest.jsonld parsed; 7 entries`

- [ ] **Step 1: 在 validate.py 增加 `validate_manifest()` 函数**

```python
def validate_manifest(jsonld_path: Path) -> dict:
    """manifest.jsonld 顶层入口验证：rdflib 解析 + 7 个 ModelManifestEntry"""
    try:
        with open(jsonld_path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return {"passed": False, "error": str(e)}

    g = Graph()
    try:
        g.parse(data=json.dumps(doc), format="json-ld")
    except Exception as e:
        return {"passed": False, "error": f"parse: {e}"}

    OD = Namespace("https://ontology.ontology-driven.dev/v9#")
    entries = list(g.subjects(RDF.type, OD.ModelManifestEntry))
    return {
        "passed": len(entries) == 7,
        "stdout_lines": [f"[OK] manifest.jsonld: {len(entries)} ModelManifestEntry"],
    }
```

- [ ] **Step 2: 在 collect_targets() 中加 manifest 路径**

```python
def collect_targets(target: Path) -> list:
    if target.is_file():
        return [target]
    if target.is_dir():
        files = sorted(p for p in target.iterdir() if p.suffix in (".yaml", ".yml", ".jsonld"))
        manifest = target / "manifest.jsonld"
        if manifest.exists():
            files.append(manifest)
        return files
    return []
```

- [ ] **Step 3: 在 main() 路由 manifest**

```python
for f in targets:
    if f.name == "manifest.jsonld":
        r = validate_manifest(f)
    elif f.suffix == ".jsonld":
        r = validate_jsonld(f)
    elif f.suffix in (".yaml", ".yml"):
        r = validate_yaml(f)
    else:
        continue
    r["path"] = str(f)
    r["kind"] = f.name
    results.append(r)
```

- [ ] **Step 4: 跑全套验证**

```bash
python subskills/ontology-modeler/tools/validate.py subskills/ontology-modeler/reference-example/
```

Expected: 5 PASS (4 jsonld + 1 manifest) / 0 FAIL / 7 SKIP / exit 0

- [ ] **Step 5: Commit**

```bash
git add subskills/ontology-modeler/tools/validate.py
git commit -m "feat(validate): include manifest.jsonld in unified validator"
```

---

### Task 4: M2 双层结构 — 元数据层转换器

**Files:**
- Create: `subskills/ontology-modeler/tools/yaml2m2jsonld.py`
- Create: `subskills/ontology-modeler/reference-example/m2-behavior-model.jsonld`

**Interfaces:**
- Consumes: `m2-behavior-model.yaml`（含 behaviors[]，每个有 id/name/ownerEntity/requiredPermissions/preconditions/postconditions/syncTriggers）
- Produces: JSON-LD（仅元数据层：od:Behavior + od:id + od:name + od:ownerEntity + od:requiredPermissions；不迁控制流字段）

- [ ] **Step 1: 读 m2-behavior-model.yaml 头部**

```bash
head -60 subskills/ontology-modeler/reference-example/m2-behavior-model.yaml
```

确认字段结构（`behaviors[].preconditions/postconditions/syncTriggers` 是 YAML 字符串控制流块）

- [ ] **Step 2: 写 yaml2m2jsonld.py**

```python
#!/usr/bin/env python3
"""yaml2m2jsonld.py — M2 YAML → JSON-LD 元数据层（不迁控制流）"""
import json, sys
from pathlib import Path
import yaml

OD_VOCAB = "https://ontology.ontology-driven.dev/v9#"
DOMAIN = "contract-mgmt"
CTX = {
    "@vocab": OD_VOCAB,
    "od": OD_VOCAB,
    "label": "http://www.w3.org/2000/01/rdf-schema#label",
}

def behavior_iri(bid): return f"urn:od:{DOMAIN}:M2:{bid}"

def convert_behavior(b):
    return {
        "@id": behavior_iri(b["id"]),
        "@type": "od:Behavior",
        "od:id": b["id"],
        "od:name": b["name"],
        "od:alias": b.get("alias", ""),
        "od:description": b.get("description", ""),
        "od:behaviorType": b.get("behaviorType", ""),
        "od:objectRef": b.get("objectRef", ""),
        # 控制流层不迁，但保留 yamlPointer 引用，便于反向查找
        "od:yamlPointer": f"#yaml/m2-behavior-model.yaml#behaviors[{b['id']}]",
        "od:requiredPermissions": b.get("requiredPermissions", []),
    }

def main():
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".jsonld")
    data = yaml.safe_load(src.read_text(encoding="utf-8"))
    behaviors = [convert_behavior(b) for b in data.get("behaviors", [])]
    doc = {"@context": CTX, "@graph": behaviors}
    dst.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {src.name} -> {dst.name} ({len(behaviors)} behaviors, metadata-only)")

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 跑转换**

```bash
python subskills/ontology-modeler/tools/yaml2m2jsonld.py \
    subskills/ontology-modeler/reference-example/m2-behavior-model.yaml
```

- [ ] **Step 4: 验证**

```bash
python -c "
import json
from rdflib import Graph
with open('subskills/ontology-modeler/reference-example/m2-behavior-model.jsonld', encoding='utf-8') as f:
    g = Graph(); g.parse(data=f.read(), format='json-ld')
print('triples:', len(g))
"
```

Expected: triples ≥ 50

- [ ] **Step 5: Commit**

```bash
git add subskills/ontology-modeler/tools/yaml2m2jsonld.py \
        subskills/ontology-modeler/reference-example/m2-behavior-model.jsonld
git commit -m "feat(m2): metadata-layer JSON-LD, control flow retained in YAML"
```

---

### Task 5: M2 YAML ↔ JSON-LD 反向定位验证

**Files:**
- Modify: `subskills/ontology-modeler/tools/validate.py`

**Interfaces:**
- Consumes: M2 YAML + JSON-LD
- Produces: 每个 M2 behavior 的 `od:yamlPointer` 在 YAML 中存在

- [ ] **Step 1: 在 validate.py 加 M2 双向校验**

```python
def validate_m2_yaml_jsonld_alignment(yaml_path: Path, jsonld_path: Path) -> dict:
    """M2 双层对账：每个 YAML behavior 都在 JSON-LD 中存在且 yamlPointer 反向可定位"""
    yaml_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    yaml_ids = {b["id"] for b in yaml_data.get("behaviors", [])}

    g = Graph()
    with open(jsonld_path, encoding="utf-8") as f:
        g.parse(data=f.read(), format="json-ld")
    OD = Namespace("https://ontology.ontology-driven.dev/v9#")
    jsonld_ids = {str(g.value(s, OD.id)) for s in g.subjects(RDF.type, OD.Behavior)}

    missing_in_jsonld = yaml_ids - jsonld_ids
    missing_in_yaml = jsonld_ids - yaml_ids
    if missing_in_jsonld or missing_in_yaml:
        return {
            "passed": False,
            "stdout_lines": [f"[FAIL] M2 漂移: yaml-仅={missing_in_jsonld}, jsonld-仅={missing_in_yaml}"],
        }
    return {
        "passed": True,
        "stdout_lines": [f"[OK] M2 双层对账: {len(yaml_ids)} behaviors 一致"],
    }
```

- [ ] **Step 2: 在 main() 路由 M2**

```python
# 在 collect_targets 后，对 M2 YAML 触发对账
m2_yaml = target / "m2-behavior-model.yaml"
m2_jsonld = target / "m2-behavior-model.jsonld"
if m2_yaml.exists() and m2_jsonld.exists():
    r = validate_m2_yaml_jsonld_alignment(m2_yaml, m2_jsonld)
    r["path"] = f"{m2_yaml.name} ↔ {m2_jsonld.name}"
    results.append(r)
```

- [ ] **Step 3: 跑全套验证**

```bash
python subskills/ontology-modeler/tools/validate.py subskills/ontology-modeler/reference-example/
```

Expected: M2 双层对账 PASS

- [ ] **Step 4: Commit**

```bash
git add subskills/ontology-modeler/tools/validate.py
git commit -m "feat(validate): M2 YAML↔JSON-LD bidirectional alignment check"
```

---

### Task 6: M3 YAML → SHACL 转换器

**Files:**
- Create: `subskills/ontology-modeler/tools/yaml2m3shacl.py`

**Interfaces:**
- Consumes: `m3-rule-model.yaml`（含 rules[]，每个有 id/expression/conditionObject/conclusionObject 等）
- Produces: `m3-rule-model.shacl.ttl`（SHACL shapes 用 `sh:property` + `sh:sparql`）

- [ ] **Step 1: 读 M3 YAML 头部**

```bash
head -100 subskills/ontology-modeler/reference-example/m3-rule-model.yaml
```

确认字段（rules[] 含 id/expression/severity 等）

- [ ] **Step 2: 写 yaml2m3shacl.py**

```python
#!/usr/bin/env python3
"""yaml2m3shacl.py — M3 YAML rules → SHACL shapes (Turtle)"""
import sys
from pathlib import Path
import yaml

OD_VOCAB = "https://ontology.ontology-driven.dev/v9#"
SH_VOCAB = "http://www.w3.org/ns/shacl#"

PREFIXES = f"""@prefix od: <{OD_VOCAB}> .
@prefix sh: <{SH_VOCAB}> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""

def to_shape(rule):
    rid = rule["id"]
    target_class = rule.get("conditionObject", "od:AggregateRoot")
    expr = rule.get("expression", "true")
    severity = rule.get("severity", "sh:Violation").replace("sh:", "")
    return f"""od:{rid}Shape
    a sh:NodeShape ;
    sh:targetClass <{OD_VOCAB}{target_class.split(':')[-1]}> ;
    sh:sparql [
        sh:select \"\"\"
            SELECT ?this WHERE {{
                ?this a <{OD_VOCAB}{target_class.split(':')[-1]}> .
                FILTER ( !({expr}) )
        \"\"\" ;
    ] ;
    sh:severity sh:{severity} ;
    sh:message "{rule.get('description', rule['id'])}" .
"""

def main():
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".shacl.ttl")
    data = yaml.safe_load(src.read_text(encoding="utf-8"))
    rules = data.get("rules", [])
    body = "\n".join(to_shape(r) for r in rules)
    dst.write_text(PREFIXES + body, encoding="utf-8")
    print(f"[OK] {src.name} -> {dst.name} ({len(rules)} SHACL shapes)")

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 跑转换**

```bash
python subskills/ontology-modeler/tools/yaml2m3shacl.py \
    subskills/ontology-modeler/reference-example/m3-rule-model.yaml
```

- [ ] **Step 4: 验证 Turtle 语法**

```bash
python -c "
from rdflib import Graph
g = Graph()
g.parse('subskills/ontology-modeler/reference-example/m3-rule-model.shacl.ttl', format='turtle')
print('triples:', len(g))
"
```

- [ ] **Step 5: Commit**

```bash
git add subskills/ontology-modeler/tools/yaml2m3shacl.py \
        subskills/ontology-modeler/reference-example/m3-rule-model.shacl.ttl
git commit -m "feat(m3): YAML rules → SHACL shapes converter (PoC)"
```

---

### Task 7: M3 SHACL 形状验证（PoC）

**Files:**
- Create: `subskills/ontology-modeler/tools/shacl/m3_rule_shape.ttl`（如果 M3 黄金范例需要更复杂的形状）

**Interfaces:**
- Consumes: m3-rule-model.shacl.ttl + M3 YAML data（或专门生成 fixture data）
- Produces: pyshacl 校验 conforms true

- [ ] **Step 1: 写一个 M3 fixture data 文件**

```bash
python -c "
import yaml
from pathlib import Path
src = Path('subskills/ontology-modeler/reference-example/m3-rule-model.yaml')
data = yaml.safe_load(src.read_text(encoding='utf-8'))
# 提取 conditionObject 的所有 aggregate，构建 fixture
import json
fix = {'@context': 'https://ontology.ontology-driven.dev/v9#', '@graph': []}
print('M3 rule count:', len(data.get('rules', [])))
"
```

- [ ] **Step 2: 跑 SHACL**

```bash
# 准备好 m3-rule-model.shacl.ttl + fixture data 后
python subskills/ontology-modeler/tools/shacl/run_shacl.py \
    <fixture.jsonld> \
    subskills/ontology-modeler/reference-example/m3-rule-model.shacl.ttl
```

Expected: `[OK] fixture conforms to m3-rule-model.shacl.ttl`

- [ ] **Step 3: 在 SHACL 验证矩阵中记录 M3 通过**

更新 `tools/README.md` 的 SHACL 用法表格 + 当前 PoC 状态表格

- [ ] **Step 4: Commit**

```bash
git add subskills/ontology-modeler/reference-example/m3-rule-model.shacl.ttl \
        subskills/ontology-modeler/tools/README.md
git commit -m "feat(shacl): M3 rule shape validation PASS on PoC fixture"
```

---

### Task 8: spec § 八 漂移检测 — ID 集合一致性

**Files:**
- Create: `subskills/ontology-modeler/tools/drift_check.py`

**Interfaces:**
- Consumes: yaml/ 目录 + yaml/manifest.jsonld
- Produces: exit 0（无漂移）或 1（有漂移），输出漂移的 id 列表

- [ ] **Step 1: 写 drift_check.py**

```python
#!/usr/bin/env python3
"""drift_check.py — YAML ↔ JSON-LD 双向对账（spec § 八 CI 门禁）"""
import json, sys
from pathlib import Path
import yaml
from rdflib import Graph, Namespace

OD = Namespace("https://ontology.ontology-driven.dev/v9#")

def yaml_ids(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        f"urn:od:contract-mgmt:{key}:{item['id']}"
        for key in ("aggregates", "actors", "query_reports")
        for item in data.get(key, [])
    }

def jsonld_ids(path):
    g = Graph()
    g.parse(data=path.read_text(encoding="utf-8"), format="json-ld")
    return {str(s) for s in g.subjects() if str(s).startswith("urn:od:")}

def main():
    yaml_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "yaml/")
    if not yaml_dir.exists():
        print(f"[SKIP] {yaml_dir} not found"); return 0

    drifts = []
    for m_id, jsonld_name in [
        ("M1", "m1-object-model.jsonld"),
        ("M5", "m5-actor-model.jsonld"),
        ("M7", "m7-report-model.jsonld"),
    ]:
        yaml_file = yaml_dir / f"{jsonld_name.replace('.jsonld', '.yaml').replace('m1-', 'm1-object-').replace('m5-', 'm5-actor-').replace('m7-', 'm7-report-')}"
        jsonld_file = yaml_dir / jsonld_name
        if not yaml_file.exists() or not jsonld_file.exists():
            continue
        y = yaml_ids(yaml_file)
        j = jsonld_ids(jsonld_file)
        only_y = y - j
        only_j = j - y
        if only_y or only_j:
            drifts.append((m_id, only_y, only_j))

    if drifts:
        print("[FAIL] drift detected:")
        for m, only_y, only_j in drifts:
            if only_y: print(f"  {m}: YAML-only = {only_y}")
            if only_j: print(f"  {m}: JSONLD-only = {only_j}")
        return 1
    print("[OK] no drift")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 跑检测**

```bash
python subskills/ontology-modeler/tools/drift_check.py \
    subskills/ontology-modeler/reference-example/
```

Expected: `[OK] no drift`

- [ ] **Step 3: Commit**

```bash
git add subskills/ontology-modeler/tools/drift_check.py
git commit -m "feat(drift-check): YAML ↔ JSON-LD ID set consistency check"
```

---

### Task 9: GitHub Actions cron 漂移检测 workflow

**Files:**
- Create: `.github/workflows/drift-check.yml`

- [ ] **Step 1: 写 workflow**

```yaml
name: drift-check
on:
  schedule:
    - cron: '0 9 * * 1'  # 每周一 09:00 UTC（spec § 八 第 3 条）
  workflow_dispatch:

jobs:
  drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.14' }
      - run: pip install pyyaml rdflib pyshacl
      - run: |
          python subskills/ontology-modeler/tools/validate.py \
              subskills/ontology-modeler/reference-example/
          python subskills/ontology-modeler/tools/drift_check.py \
              subskills/ontology-modeler/reference-example/
          python subskills/ontology-modeler/tools/sparql_queries.py --all > /dev/null
      - run: |
          for f in m1 m5 m6 m7; do
            case $f in
              m6) shape=m6_flow_shape ;;
              *) shape=${f}_*_shape ;;
            esac
            [ -f subskills/ontology-modeler/reference-example/$f-*model.jsonld ] && \
              python subskills/ontology-modeler/tools/shacl/run_shacl.py \
                  subskills/ontology-modeler/reference-example/$f-*model.jsonld \
                  subskills/ontology-modeler/tools/shacl/${shape}.ttl
          done
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/drift-check.yml
git commit -m "ci: weekly YAML↔JSON-LD drift check + SHACL + SPARQL smoke"
```

---

### Task 10: 写 ontology_modeling_framework_v9.1.md §11

**Files:**
- Modify: `subskills/ontology-modeler/references/ontology_modeling_framework_v9.md` → rename 或补 §11

**Interfaces:**
- Consumes: 本 spec § 三、§ 四
- Produces: framework 文档新增 §11 "JSON-LD 序列化约定"

- [ ] **Step 1: 读 framework 当前结构**

```bash
grep -E '^## ' subskills/ontology-modeler/references/ontology_modeling_framework_v9.md
```

- [ ] **Step 2: 追加 §11 章节**

在 framework 文档末尾追加：

```markdown
## 十一、JSON-LD 序列化约定

本框架支持 YAML → JSON-LD 双轨输出，详见 [spec § 三 双轨制策略](../specs/2026-09-01-yaml-to-jsonld-design.md)。

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

参见 [tools/README.md](../../tools/README.md)。

### 11.5 引用 spec

- YAML → JSON-LD 迁移 spec：[2026-09-01-yaml-to-jsonld-design.md](../../specs/2026-09-01-yaml-to-jsonld-design.md)
```

- [ ] **Step 3: Commit**

```bash
git add subskills/ontology-modeler/references/ontology_modeling_framework_v9.md
git commit -m "docs(framework): §11 JSON-LD serialization agreement (AC6)"
```

---

### Task 11: OpenClaw C# ValidateJsonLdTool.cs（跨仓库）

**Files:**
- Create: `E:/GitHub/openclaw.net/src/OpenClaw.Agent/Tools/ValidateJsonLdTool.cs`

**Interfaces:**
- Consumes: `jsonLdFiles: string[]`（绝对路径）+ `vocabStrategy: "od" | "meta"`
- Produces: `IToolResult { Passed: bool, Violations: List<Violation> }`

- [ ] **Step 1: 在 OpenClaw 仓库读现有 ValidateYamlReferencesTool.cs 结构**

```bash
cat E:/GitHub/openclaw.net/src/OpenClaw.Agent/Tools/ValidateYamlReferencesTool.cs | head -50
```

确认 ITool 接口签名、命名空间、构造模式

- [ ] **Step 2: 写 ValidateJsonLdTool.cs**

参照 ValidateYamlReferencesTool.cs 的结构，写一个最小实现：
- 接受 `jsonLdFiles` 参数
- 调用 dotNetRDF JSON-LD Processor 解析
- 用 dotNetRDF SHACL API 跑预定义 shapes（meta:FlowShape / od:AggregateRootShape）
- 返回 violations 列表

> **本任务需独立 OpenClaw 仓库 PR**，不在 ontology-driven-dev 仓库直接 commit。完成后更新本 plan 文档为 ✅。

- [ ] **Step 3: 在 ontology-driven-dev 仓库写一份 README 说明跨仓库集成路径**

新建 `subskills/ontology-modeler/references/openclaw-integration.md`，记录：
- ValidateJsonLdTool.cs 路径
- MetaSkill step 12 调用方式
- 跨仓库 PR 流程

- [ ] **Step 4: Commit（仅本仓库文档）**

```bash
git add subskills/ontology-modeler/references/openclaw-integration.md
git commit -m "docs: OpenClaw ValidateJsonLdTool.cs cross-repo integration path"
```

---

### Task 12: 验收检查 — AC1-AC6 全过

**Files:**
- Modify: `docs/superpowers/specs/2026-09-01-stage55-report.md`（新建收尾报告）

- [ ] **Step 1: 跑全套验收**

```bash
# AC1: 7 模型都有 JSON-LD 或不迁
ls subskills/ontology-modeler/reference-example/*.jsonld
# 期望: m1-object-model.jsonld, m2-behavior-model.jsonld, m6-flow-model.jsonld,
#       m7-report-model.jsonld (+ m3-rule-model.shacl.ttl)
ls subskills/ontology-modeler/reference-example/mu-ui-model.jsonld 2>/dev/null || echo "MU not migrated: OK"

# AC2: rdflib + jsonld.js 解析测试
python -c "
from rdflib import Graph
import glob
for f in glob.glob('subskills/ontology-modeler/reference-example/*-model.jsonld'):
    g = Graph(); g.parse(f, format='json-ld')
    print(f, len(g))
"

# AC3: M1 invariants SHACL（已在 m1_aggregate_shape.ttl 中体现）
python subskills/ontology-modeler/tools/shacl/run_shacl.py \
    subskills/ontology-modeler/reference-example/m1-object-model.jsonld \
    subskills/ontology-modeler/tools/shacl/m1_aggregate_shape.ttl

# AC4: M3 rules SHACL（Task 7 已验证）
python subskills/ontology-modeler/tools/shacl/run_shacl.py \
    <fixture.jsonld> \
    subskills/ontology-modeler/reference-example/m3-rule-model.shacl.ttl

# AC5: OpenClaw ValidateYamlReferencesTool 回归（Task 11）
# 注：跨仓库，需在 openclaw.net 仓库跑现有 YAML 测试不破

# AC6: framework §11 已发布（Task 10）
grep -c '^## 十一' subskills/ontology-modeler/references/ontology_modeling_framework_v9.md
```

- [ ] **Step 2: 写收尾报告**

新建 `docs/superpowers/specs/2026-09-01-stage55-report.md`，覆盖：
- 已完成任务清单（commit hash + 验收点）
- 仍待完成（Task 11 跨仓库）
- 未来路线（阶段 6 长期）

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-09-01-stage55-report.md
git commit -m "docs: stage 5.5 closing report — AC1-AC6 status"
```

---

## 执行依赖

```
T1 (od: vocab) ──┬── T2 (manifest) ── T3 (validate)
                 ├── T4 (M2 jsonld) ─ T5 (validate)
                 ├── T6 (M3 shacl) ─ T7 (validate)
                 └── T8 (drift) ───── T9 (cron)
T10 (framework §11) ─┐
T11 (OpenClaw C#)  ──┴── T12 (AC 验收)
```

- T1 必须最先（其他都依赖 od: 词表稳定）
- T2、T4、T6 可并行
- T8 依赖 T2（drift 用 manifest）
- T9 依赖 T8
- T12 是收尾

## 范围切割建议

本 spec 涉及多子项目。如果实施时希望并行 PR，可拆为：

| 子项目 | PR 范围 | 估时 |
|---|---|---|
| A: 词表冻结 + manifest | T1+T2+T3 | 2h |
| B: M2 双层 | T4+T5 | 2h |
| C: M3 SHACL | T6+T7 | 3h |
| D: 漂移检测 + CI | T8+T9 | 1h |
| E: 框架文档 | T10 | 1h |
| F: OpenClaw 集成 | T11（跨仓库） | 4h |
| G: 验收 | T12 | 1h |

**总计 ~14h（约 2 个工作日）**。

---

**Plan complete and saved to `docs/superpowers/plans/2026-09-01-yaml-to-jsonld-impl.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**