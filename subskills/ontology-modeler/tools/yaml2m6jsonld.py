#!/usr/bin/env python3
"""
yaml2m6jsonld.py — M6 YAML → JSON-LD with meta: 词表 PoC

依据 docs/superpowers/specs/2026-09-01-yaml-to-jsonld-design.md § 四:
- M6 输出是 JSON-LD 文件，复用 OpenClaw MetaSkill 词表 IRI
- @context 引用 https://openclaw.dev/meta/v1#
- 不生成 SKILL.md

输入：m6-flow-model.yaml（参考 reference-example/）
输出：m6-flow-model.jsonld（同一目录）

PoC 范围：验证转换可行性，不做生产级特性（无错误恢复、无批量处理）。
"""

import json
import sys
from pathlib import Path

import yaml

# ── 常量 ──────────────────────────────────────────────────────────────
META_VOCAB_IRI = "https://openclaw.dev/meta/v1#"
OD_VOCAB_IRI = "https://ontology.ontology-driven.dev/v9#"
XSD_IRI = "http://www.w3.org/2001/XMLSchema#"
DOMAIN_SLUG = "contract-mgmt"  # PoC 简化：单一域硬编码

# M6 activityType → meta:kind 映射
ACTIVITY_TYPE_TO_META_KIND = {
    "START": "start",
    "END": "end",
    "USER_TASK": "user_input",
    "SYSTEM_TASK": "agent",
    "APPROVAL_TASK": "user_input",  # with enum
    "SUB_FLOW_CALL": "skill_exec",
    "BEHAVIOR_CALL": "agent",
    "GATEWAY": "llm_classify",
}


# ── IRI 构造 ─────────────────────────────────────────────────────────
def flow_iri(flow_id: str) -> str:
    return f"urn:od:{DOMAIN_SLUG}:M6:{flow_id}"


def step_iri(flow_id: str, activity_id: str) -> str:
    return f"urn:od:{DOMAIN_SLUG}:M6:{flow_id}:{activity_id}"


def ref_iri(model: str, ref: str) -> str:
    """把行为/角色/对象引用转成 JSON-LD @id 形式"""
    return f"urn:od:{DOMAIN_SLUG}:{model}:{ref}"


# ── 依赖反转：nextActivities (出向) → dependsOn (入向) ──────────────
def reverse_depends_on(activities):
    """返回 {activity_id: [predecessor_ids]}"""
    deps = {a["activityId"]: [] for a in activities}
    for a in activities:
        for nxt in a.get("nextActivities", []) or []:
            if nxt in deps:
                deps[nxt].append(a["activityId"])
    return deps


# ── 单个 activity → meta:Step ────────────────────────────────────────
def convert_activity(flow_id: str, activity: dict, deps_map: dict) -> dict:
    aid = activity["activityId"]
    step = {
        "@id": step_iri(flow_id, aid),
        "@type": "meta:Step",
        "meta:id": aid,
        "meta:label": activity["name"],
        "meta:kind": ACTIVITY_TYPE_TO_META_KIND.get(activity["activityType"], "agent"),
    }

    if "roleRef" in activity:
        step["meta:permissionRef"] = ref_iri("M5", activity["roleRef"])

    if "behaviorRef" in activity:
        step["meta:skill"] = ref_iri("M2", activity["behaviorRef"])

    if "subFlowRef" in activity:
        step["meta:skill"] = ref_iri("M6", activity["subFlowRef"])

    if "approvalOutcomes" in activity:
        step["meta:enum"] = activity["approvalOutcomes"]

    if activity["activityType"] == "GATEWAY":
        step["meta:routes"] = convert_gateway_routes(flow_id, aid, activity)

    if deps_map.get(aid):
        step["meta:dependsOn"] = deps_map[aid]

    return step


def extract_choice_label(branch: dict, idx: int) -> str:
    """从 branch 提取 meta:choice 标签"""
    if branch.get("conditionExpression"):
        expr = branch["conditionExpression"]
        if "==" in expr:
            return expr.split("==", 1)[1].strip().strip("'\"")
        return expr
    if branch.get("ruleRef"):
        return branch["ruleRef"]
    return branch.get("branchName", f"branch_{idx}")


def convert_gateway_routes(flow_id: str, aid: str, activity: dict) -> list:
    """
    GATEWAY branches → meta:routes 嵌套数组

    每条 route 携带:
    - meta:choice: 分支标签
    - meta:target: 目标 activityId
    - meta:isDefault: 是否默认分支
    - meta:conditionExpression 或 meta:ruleRef: 触发条件
    - meta:branchName: 人类可读名
    """
    routes = []
    for idx, b in enumerate(activity.get("branches", []) or []):
        route = {
            "@id": step_iri(flow_id, f"{aid}-route-{idx}"),
            "@type": "meta:Route",
            "meta:choice": extract_choice_label(b, idx),
            "meta:target": b.get("targetActivity", ""),
            "meta:isDefault": bool(b.get("isDefault", False)),
            "meta:branchName": b.get("branchName", ""),
        }
        if b.get("conditionExpression") is not None:
            route["meta:conditionExpression"] = b["conditionExpression"]
        if b.get("ruleRef"):
            route["meta:ruleRef"] = ref_iri("M3", b["ruleRef"])
        routes.append(route)
    return routes


# ── 单个 flow → meta:Flow ────────────────────────────────────────────
def convert_flow(flow: dict) -> dict:
    flow_id = flow["id"]
    activities = flow["activities"]
    deps_map = reverse_depends_on(activities)

    result = {
        "@id": flow_iri(flow_id),
        "@type": "meta:Flow",
        "meta:id": flow_id,
        "meta:name": flow["name"],
        "meta:flowType": flow.get("flowType", "COLLABORATION"),
        "meta:description": flow.get("description", ""),
        "meta:businessObjectRefs": [
            ref_iri("M1", r) for r in flow.get("businessObjectRefs", []) or []
        ],
        "meta:roleRefs": [
            ref_iri("M5", r) for r in flow.get("roleRefs", []) or []
        ],
        "meta:preconditions": flow.get("preconditions", []) or [],
        "meta:postconditions": flow.get("postconditions", []) or [],
        "meta:startActivity": flow.get("startActivity", ""),
        "meta:hasStep": [convert_activity(flow_id, a, deps_map) for a in activities],
    }

    if "trigger" in flow:
        result["meta:trigger"] = flow["trigger"]

    return result


# ── 主流程 ──────────────────────────────────────────────────────────
def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "subskills/ontology-modeler/reference-example/m6-flow-model.yaml"
    )
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".jsonld")

    with open(src, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    flows_jsonld = [convert_flow(flow) for flow in data["flows"]]

    document = {
        "@context": {
            "@vocab": META_VOCAB_IRI,
            "meta": META_VOCAB_IRI,
            "od": OD_VOCAB_IRI,
            "xsd": XSD_IRI,
        },
        "@graph": flows_jsonld,
    }

    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(document, f, ensure_ascii=False, indent=2)

    print(f"[OK] Converted {len(flows_jsonld)} flows -> {dst}")
    for flow in flows_jsonld:
        step_count = len(flow["meta:hasStep"])
        status = "OK" if step_count <= 12 else "FAIL (>12)"
        print(f"  [{status}] {flow['meta:id']:32s} steps={step_count:2d}  {flow['meta:name']}")


if __name__ == "__main__":
    main()