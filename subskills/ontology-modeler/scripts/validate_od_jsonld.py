#!/usr/bin/env python3
"""
validate_od_jsonld.py — 验证 M1/M5/M7 JSON-LD 输出

验证项：
1. JSON-LD 语法（rdflib 解析）
2. @context 引用 od: IRI
3. M1: 找到 N 个 od:AggregateRoot / od:Association / od:DataDictionary
4. M5: 找到 N 个 od:Role / od:Permission / od:Actor
5. M7: 找到 N 个 od:Report
6. 跨节点引用：M1 中 association 引用 URI 在 graph 内可解析
"""

import json
import sys
from pathlib import Path

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF

OD = Namespace("https://ontology.ontology-driven.dev/v9#")

EXPECTED_TYPES = {
    "m1-object-model.jsonld": ["od:AggregateRoot", "od:Association", "od:DataDictionary"],
    "m5-actor-model.jsonld": ["od:Actor", "od:Role", "od:Permission"],
    "m7-report-model.jsonld": ["od:Report"],
}


def validate_file(path: Path) -> bool:
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)

    ctx = doc.get("@context")
    expected_od = "https://ontology.ontology-driven.dev/v9#"
    assert ctx.get("od") == expected_od, f"od IRI mismatch: {ctx.get('od')}"
    print(f"[OK] {path.name}: @context od IRI = {expected_od}")

    g = Graph()
    g.parse(data=json.dumps(doc), format="json-ld")

    expected = EXPECTED_TYPES.get(path.name, [])
    all_ok = True
    for type_name in expected:
        cls = OD[type_name.split(":")[1]]
        nodes = list(g.subjects(RDF.type, cls))
        print(f"[OK] {path.name}: found {len(nodes)} {type_name}")
        if not nodes:
            all_ok = False

    # M1 特定检查：od:Association 的 sourceAggregate / targetAggregate 在 graph 中存在
    if path.name == "m1-object-model.jsonld":
        for assoc in g.subjects(RDF.type, OD.Association):
            src = g.value(assoc, OD.sourceAggregate)
            tgt = g.value(assoc, OD.targetAggregate)
            for ref, name in [(src, "sourceAggregate"), (tgt, "targetAggregate")]:
                if ref is None:
                    continue
                #  # ref 是 URI；检查 graph 中是否存在 @id 相同的 AggregateRoot
                exists = any(
                    str(s) == str(ref) for s in g.subjects(RDF.type, OD.AggregateRoot)
                )
                if not exists:
                    print(f"[FAIL] association {assoc} {name} -> {ref} NOT FOUND")
                    all_ok = False

    # M5 特定检查：role 的 hasPermission 引用全部存在
    if path.name == "m5-actor-model.jsonld":
        for role in g.subjects(RDF.type, OD.Role):
            perms = list(g.objects(role, OD.hasPermission))
            for p in perms:
                exists = any(
                    str(s) == str(p) for s in g.subjects(RDF.type, OD.Permission)
                )
                if not exists:
                    print(f"[FAIL] role {role} hasPermission -> {p} NOT FOUND")
                    all_ok = False

    # M7 特定检查：boundBehavior 引用是 URI 形式
    if path.name == "m7-report-model.jsonld":
        for report in g.subjects(RDF.type, OD.Report):
            beh = g.value(report, OD.boundBehavior)
            if beh is None:
                print(f"[FAIL] report {report} missing boundBehavior")
                all_ok = False

    return all_ok


def main():
    files = [
        Path("subskills/ontology-modeler/reference-example/m1-object-model.jsonld"),
        Path("subskills/ontology-modeler/reference-example/m5-actor-model.jsonld"),
        Path("subskills/ontology-modeler/reference-example/m7-report-model.jsonld"),
    ]
    if len(sys.argv) > 1:
        files = [Path(f) for f in sys.argv[1:]]

    overall_ok = True
    for path in files:
        if not path.exists():
            print(f"[FAIL] {path} not found")
            overall_ok = False
            continue
        if not validate_file(path):
            overall_ok = False
        print()

    if overall_ok:
        print("PASS: All M1/M5/M7 JSON-LD validations passed")
        return 0
    else:
        print("FAIL: Some validations failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())