#!/usr/bin/env python3
"""
validate_m6jsonld.py — 验证 m6-flow-model.jsonld

验证项：
1. JSON-LD 语法（rdflib 解析）
2. @context 引用 https://openclaw.dev/meta/v1#
3. 每个 meta:Flow 的 meta:hasStep 数量 ≤ 12（MetaSkill 约束）
4. 每个 meta:Step 的 meta:dependsOn 引用目标存在
"""

import json
import sys
from pathlib import Path

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF

META = Namespace("https://openclaw.dev/meta/v1#")
OD = Namespace("https://ontology.ontology-driven.dev/v9#")


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "subskills/ontology-modeler/reference-example/m6-flow-model.jsonld"
    )

    # 1. 读 JSON
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)

    # 2. @context 静态检查
    ctx = doc.get("@context")
    assert "@vocab" in ctx, "missing @vocab"
    assert ctx.get("meta") == str(META), f"meta IRI mismatch: {ctx.get('meta')}"
    print(f"[OK] @context references meta IRI: {META}")

    # 3. rdflib JSON-LD 解析
    g = Graph()
    g.parse(data=json.dumps(doc), format="json-ld")
    flows = list(g.subjects(RDF.type, META.Flow))
    print(f"[OK] JSON-LD parsed; found {len(flows)} meta:Flow nodes")

    # 4. 每 flow 的 step 数 ≤ 12 + dependsOn 引用存在
    all_ok = True
    for flow in flows:
        flow_id = g.value(flow, META.id) or flow
        flow_name = g.value(flow, META.name) or ""
        steps = list(g.objects(flow, META.hasStep))

        if len(steps) > 12:
            print(f"[FAIL] {flow_id}: {len(steps)} steps > 12 (MetaSkill limit)")
            all_ok = False
        else:
            print(f"[OK]   {flow_id}: {len(steps)} steps <= 12  ({flow_name})")

        # dependsOn 引用目标存在
        for step in steps:
            step_id = g.value(step, META.id)
            deps = list(g.objects(step, META.dependsOn))
            for dep in deps:
                target = None
                for s in steps:
                    if str(g.value(s, META.id)) == str(dep):
                        target = s
                        break
                if target is None:
                    print(f"[FAIL] {step_id}.dependsOn -> '{dep}' NOT FOUND")
                    all_ok = False

        # GATEWAY routes: target 引用存在 + 仅一个 isDefault=true
        for step in steps:
            step_id = g.value(step, META.id)
            routes = list(g.objects(step, META.routes))
            if not routes:
                continue
            default_count = 0
            for route in routes:
                target = g.value(route, META.target)
                if target:
                    target_exists = any(str(g.value(s, META.id)) == str(target) for s in steps)
                    if not target_exists:
                        print(f"[FAIL] {step_id}.routes.target -> '{target}' NOT FOUND")
                        all_ok = False
                if g.value(route, META.isDefault):
                    default_count += 1
            if default_count > 1:
                print(f"[FAIL] {step_id}.routes has {default_count} defaults (must be 0 or 1)")
                all_ok = False
            elif default_count == 0:
                print(f"[WARN] {step_id}.routes has no default route")

    print()
    if all_ok:
        print("PASS: PoC v2 validation passed")
        return 0
    else:
        print("FAIL: PoC v2 validation failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())