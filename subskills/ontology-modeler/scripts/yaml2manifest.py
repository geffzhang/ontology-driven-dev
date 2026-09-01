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