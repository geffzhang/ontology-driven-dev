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