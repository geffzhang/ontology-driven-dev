#!/usr/bin/env python3
"""
yaml2od_jsonld.py — M1/M5/M7 YAML → JSON-LD with od: 词表 PoC

依据 docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md § 五:
- M1/M3/M5/M7 使用 od: 自建词表 IRI（区别于 M6 的 meta: 复用）
- @context 引用 https://ontology.ontology-driven.dev/v9#
- 跨模型引用用 urn:od:<domain>:<model>:<id>

输入：m1-object-model.yaml / m5-actor-model.yaml / m7-report-model.yaml
输出：m1-object-model.jsonld / m5-actor-model.jsonld / m7-report-model.jsonld
"""

import json
import sys
from pathlib import Path

import yaml

OD_VOCAB_IRI = "https://ontology.ontology-driven.dev/v9#"
SKOS_IRI = "http://www.w3.org/2004/02/skos/core#"
RDFS_IRI = "http://www.w3.org/2000/01/rdf-schema#"
XSD_IRI = "http://www.w3.org/2001/XMLSchema#"
DOMAIN_SLUG = "contract-mgmt"


# ── IRI helpers ──────────────────────────────────────────────────────
def aggregate_iri(aid: str) -> str:
    return f"urn:od:{DOMAIN_SLUG}:M1:{aid}"


def actor_iri(aid: str) -> str:
    return f"urn:od:{DOMAIN_SLUG}:M5:{aid}"


def role_iri(rid: str) -> str:
    return f"urn:od:{DOMAIN_SLUG}:M5:{rid}"


def perm_iri(pid: str) -> str:
    return f"urn:od:{DOMAIN_SLUG}:M5:{pid}"


def behavior_iri(bid: str) -> str:
    return f"urn:od:{DOMAIN_SLUG}:M2:{bid}"


def report_iri(rid: str) -> str:
    return f"urn:od:{DOMAIN_SLUG}:M7:{rid}"


def assoc_iri(aid: str) -> str:
    return f"urn:od:{DOMAIN_SLUG}:M1:{aid}"


def dict_iri(did: str) -> str:
    return f"urn:od:{DOMAIN_SLUG}:M1:{did}"


# ── 共享 context ─────────────────────────────────────────────────────
OD_CONTEXT = {
    "@vocab": OD_VOCAB_IRI,
    "od": OD_VOCAB_IRI,
    "skos": SKOS_IRI,
    "rdfs": RDFS_IRI,
    "xsd": XSD_IRI,
    "label": "rdfs:label",
    "type": "@type",
    "id": "@id",
    # URN 引用谓词：值为字符串时被解释为 IRI（urn:od:...）
    "od:sourceAggregate": {"@type": "@id"},
    "od:targetAggregate": {"@type": "@id"},
    "od:hasRole": {"@type": "@id"},
    "od:hasPermission": {"@type": "@id"},
    "od:objectRef": {"@type": "@id"},
    "od:boundBehavior": {"@type": "@id"},
}


# ── M1: aggregates / dictionaries / associations ─────────────────────
def convert_attribute(attr: dict) -> dict:
    node = {
        "@type": "od:Attribute",
        "od:name": attr["name"],
        "od:label": attr["label"],
        "od:dataType": attr["type"],
        "od:required": bool(attr.get("required", False)),
        "od:unique": bool(attr.get("unique", False)),
    }
    # 保留 dictionaryRef（让 SPARQL Q2 跨字典引用可查询）
    if "dictionaryRef" in attr:
        ref = attr["dictionaryRef"]
        node["od:dictionaryRef"] = {
            "od:dictionaryId": ref.get("dictionaryId", ""),
            "od:typeCode": ref.get("typeCode", ""),
        }
    return node


def convert_invariant(inv: dict) -> dict:
    return {
        "@type": "od:Invariant",
        "od:name": inv["name"],
        "od:expression": inv["expression"],
        "od:violationMessage": inv.get("violationMessage", ""),
        "od:enforcedAt": inv.get("enforcedAt", "ALWAYS"),
    }


def convert_aggregate(agg: dict) -> dict:
    """aggregate → od:AggregateRoot 节点"""
    node = {
        "@id": aggregate_iri(agg["id"]),
        "@type": "od:AggregateRoot",
        "od:id": agg["id"],
        "od:name": agg["name"],
        "od:alias": agg.get("alias", ""),
        "od:description": agg.get("description", ""),
        "od:lifecycle": agg.get("lifecycle", []),
        "od:tags": agg.get("tags", []),
    }
    if "attributes" in agg:
        node["od:hasAttribute"] = [convert_attribute(a) for a in agg["attributes"]]
    if "entities" in agg:
        node["od:hasEntity"] = [
            {
                "@type": "od:Entity",
                "od:name": e["name"],
                "od:alias": e.get("alias", ""),
                "od:localId": e.get("localId", ""),
                "od:cardinality": e.get("cardinality", "ONE"),
                "od:hasAttribute": [convert_attribute(a) for a in e.get("attributes", [])],
            }
            for e in agg["entities"]
        ]
    if "invariants" in agg:
        node["od:hasInvariant"] = [convert_invariant(i) for i in agg["invariants"]]
    return node


def convert_association(assoc: dict) -> dict:
    """aggregate_association → od:Association 节点（跨 aggregate 引用 URI）"""
    return {
        "@id": assoc_iri(assoc["id"]),
        "@type": "od:Association",
        "od:id": assoc["id"],
        "od:sourceAggregate": aggregate_iri(assoc["sourceAggregate"]),
        "od:targetAggregate": aggregate_iri(assoc["targetAggregate"]),
        "od:associationType": assoc["associationType"],
        "od:sourceRole": assoc.get("sourceRole", ""),
        "od:targetRole": assoc.get("targetRole", ""),
        "od:cardinality": assoc.get("cardinality", ""),
        "od:referenceField": assoc.get("referenceField", ""),
    }


def convert_dictionary_item(item: dict, type_code: str, idx: int) -> dict:
    """YAML items[] → od:DictionaryItem 节点（带 @id）"""
    code = item.get("code", f"item-{idx}")
    return {
        "@id": dict_iri(f"{type_code}:{code}"),
        "@type": "od:DictionaryItem",
        "od:code": code,
        "od:label": item.get("label", ""),
        "od:enabled": bool(item.get("enabled", True)),
        "od:sortOrder": int(item.get("sortOrder", 0)),
    }


def convert_dictionary(d: dict) -> dict:
    return {
        "@id": dict_iri(d["id"]),
        "@type": "od:DataDictionary",
        "od:id": d["id"],
        "od:name": d["name"],
        "od:hasType": [
            {
                "@type": "od:DictionaryType",
                "od:typeCode": t["typeCode"],
                "od:typeName": t["typeName"],
                "od:hasItem": [
                    convert_dictionary_item(item, t["typeCode"], i)
                    for i, item in enumerate(t.get("items", []))
                ],
            }
            for t in d.get("types", [])
        ],
    }


def convert_m1(data: dict) -> list:
    nodes = []
    for agg in data.get("aggregates", []):
        nodes.append(convert_aggregate(agg))
    for assoc in data.get("aggregate_associations", []):
        nodes.append(convert_association(assoc))
    for d in data.get("data_dictionaries", []):
        nodes.append(convert_dictionary(d))
    return nodes


# ── M5: actors / roles / permissions ─────────────────────────────────
def convert_permission(p: dict) -> dict:
    return {
        "@id": perm_iri(p["permissionId"]),
        "@type": "od:Permission",
        "od:id": p["permissionId"],
        "od:targetType": p.get("targetType", ""),
        "od:targetRef": p.get("targetRef", ""),
        "od:dataScope": p.get("dataScope", "ALL"),
    }


def convert_role(role: dict, all_perm_ids: set) -> dict:
    """role 节点 + hasPermission 引用 od:Permission URI"""
    perms = role.get("permissions", []) or []
    valid_refs = [perm_iri(p) for p in perms if p in all_perm_ids]
    return {
        "@id": role_iri(role["roleId"]),
        "@type": "od:Role",
        "od:id": role["roleId"],
        "od:name": role["name"],
        "od:hasPermission": valid_refs,
    }


def convert_actor(actor: dict) -> dict:
    return {
        "@id": actor_iri(actor["actorId"]),
        "@type": "od:Actor",
        "od:id": actor["actorId"],
        "od:name": actor["name"],
        "od:actorType": actor.get("actorType", "HUMAN"),
        "od:hasRole": [role_iri(r) for r in actor.get("roles", []) or []],
    }


def convert_m5(data: dict) -> list:
    nodes = []
    all_perm_ids = {p["permissionId"] for p in data.get("permissions", [])}

    # 先 permissions（保证 role 引用可解析）
    for p in data.get("permissions", []):
        nodes.append(convert_permission(p))
    # 再 roles
    for role in data.get("roles", []):
        nodes.append(convert_role(role, all_perm_ids))
    # 再 actors
    for actor in data.get("actors", []):
        nodes.append(convert_actor(actor))
    return nodes


# ── M7: query_reports ────────────────────────────────────────────────
def convert_query_report(report: dict) -> dict:
    """M7 query_report → od:Report 节点，boundBehavior 引用 M2 URI"""
    sources = report.get("sourceObjects", []) or []
    return {
        "@id": report_iri(report["id"]),
        "@type": "od:Report",
        "od:id": report["id"],
        "od:name": report["name"],
        "od:alias": report.get("alias", ""),
        "od:objectType": report.get("objectType", ""),
        "od:description": report.get("description", ""),
        "od:boundBehavior": behavior_iri(report["behaviorRef"]),
        "od:sourceObject": [
            {
                "@type": "od:SourceObject",
                "od:objectRef": aggregate_iri(s["objectRef"]),
                "od:alias": s.get("alias", ""),
                "od:primary": bool(s.get("primary", False)),
            }
            for s in sources
        ],
    }


def convert_m7(data: dict) -> list:
    return [convert_query_report(r) for r in data.get("query_reports", [])]


# ── 入口 ─────────────────────────────────────────────────────────────
def convert_yaml(src: Path) -> dict:
    with open(src, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    model_type = data.get("model_type", "")
    if model_type == "OBJECT":
        nodes = convert_m1(data)
    elif model_type == "ACTOR":
        nodes = convert_m5(data)
    elif model_type == "REPORT":
        nodes = convert_m7(data)
    else:
        raise ValueError(f"unsupported model_type: {model_type}")

    return {
        "@context": OD_CONTEXT,
        "@graph": nodes,
    }


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not src:
        print("Usage: yaml2od_jsonld.py <input.yaml> [output.jsonld]")
        sys.exit(1)
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".jsonld")

    doc = convert_yaml(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

    nodes = doc["@graph"]
    print(f"[OK] {src.name} -> {dst}")
    print(f"     model_type={src.stem.split('-')[0]}, nodes={len(nodes)}")


if __name__ == "__main__":
    main()