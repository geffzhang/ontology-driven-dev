#!/usr/bin/env python3
"""
validate_yaml_refs.py — model-validator 跨引用门禁（6 条检查的 Python 移植）

把 OpenClaw ValidateYamlReferencesTool.cs 的 6 条检查语义移植为本地脚本，
供 MetaSkill 步骤 12（skill_exec → scripts/gate.ps1）与 CI 调用。

语义基准：根 SKILL.md 步骤 12 的 6 条 description（绑定语义）
+ ValidateYamlReferencesTool.cs（字段路径 / 违规判定 / 输出信封参考）。
黄金范例 subskills/ontology-modeler/reference-example/ 全部 6 条 PASS。

输入：
  validate_yaml_refs.py <yaml_dir> <manifest> [--check ID]... [--format json|text]

输出契约（与 C# 工具对齐）：
  {
    "status": "OK"|"FAIL"|"ERROR",
    "yaml_dir": ..., "model_files": [...],
    "checks": [{"id", "status": "PASS"|"FAIL"|"SKIP", "message", "violations": [...]}],
    "summary": {"total", "passed", "failed", "skipped"}
  }

退出码：0 = OK（无 FAIL）；1 = 存在 FAIL；2 = 参数/加载错误（ERROR 信封）。
manifest 支持两种形态：model_files 数组（黄金范例 / C# 语义）或 models 对象
（根 SKILL.md 步骤 6 文档形态，取值作文件名）。
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

# Windows GBK stdout 无法输出 →（U+2192）等字符 — 强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 清单文件名 → 规范模型 ID（与 C# ModelKeyByFile 一致；m5-role 为历史别名）
MODEL_KEY_BY_FILE = {
    "m1-object-model.yaml": "M1",
    "m2-behavior-model.yaml": "M2",
    "m3-rule-model.yaml": "M3",
    "m5-actor-model.yaml": "M5",
    "m5-role-model.yaml": "M5",
    "m6-flow-model.yaml": "M6",
    "m7-report-model.yaml": "M7",
    "mu-ui-model.yaml": "MU",
}

# 正式报表类型（check 5 与 C# FormalReportTypes 一致）
FORMAL_REPORT_TYPES = {"LIST_QUERY", "DETAIL_QUERY", "STATISTICAL_QUERY", "REPORT"}

# 条件语气词（check 6 与 C# ConditionalHints 一致，注意 "when "/"if "/"iff " 含尾随空格）
CONDITIONAL_HINTS = ["如果", "若", "若果", "假如", "when ", "if ", "iff "]

# 检查执行顺序 = C# CheckRegistry 注册顺序
CHECK_IDS = [
    "traceability",
    "query_mapping",
    "flow_refs",
    "acyclic_call_graph",
    "query_behavior_bidir",
    "rule_condition_separation",
]


# ──────────────────────────────────────────────────────────────
# 模型加载（容错：缺失 key / 形态不符 → 空集合，绝不让单节畸形中断整体）
# ──────────────────────────────────────────────────────────────

def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _get_list(model, key):
    """model 顶层 key → list[dict]；缺失或形态不符返回 []（对齐 C# GetList）"""
    if not isinstance(model, dict):
        return []
    v = model.get(key)
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def _str(entry, key):
    """dict 取值转 str；None 返回 None（对齐 C# YamlValue.String 语义）"""
    if not isinstance(entry, dict) or entry.get(key) is None:
        return None
    return str(entry[key])


def _str_list(model, key):
    """顶层 list[str]；缺失/形态不符返回 []（对齐 C# StringList）"""
    if not isinstance(model, dict):
        return []
    v = model.get(key)
    return [str(x) for x in v] if isinstance(v, list) else []


def load_models(yaml_dir: Path, manifest_raw: str):
    """按 manifest 加载全部模型 YAML。返回 (models: dict[M1..MU → dict], loaded_files)。

    抛 LoadError（携带 error_code）：
      manifest_not_found / invalid_manifest / model_file_not_found / yaml_parse_error
    """
    # manifest 定位：绝对路径 > 相对 CWD > 相对 yaml_dir
    manifest_path = Path(manifest_raw)
    if not manifest_path.is_absolute():
        cwd_candidate = Path.cwd() / manifest_path
        yamldir_candidate = yaml_dir / manifest_path
        manifest_path = (
            cwd_candidate if cwd_candidate.exists() else yamldir_candidate
        )

    if not manifest_path.exists():
        raise LoadError(
            "manifest_not_found", f"manifest not found: {manifest_path}"
        )

    try:
        with open(manifest_path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise LoadError("invalid_manifest", f"manifest parse failed: {e}") from e

    # 双形态兼容：model_files 数组（黄金范例 / C#）或 models 对象（步骤 6 文档）
    if isinstance(doc, dict) and isinstance(doc.get("model_files"), list):
        model_files = [str(x) for x in doc["model_files"] if str(x).strip()]
    elif isinstance(doc, dict) and isinstance(doc.get("models"), dict):
        model_files = [
            str(v) for v in doc["models"].values() if str(v).strip()
        ]
    else:
        raise LoadError(
            "invalid_manifest",
            f"manifest.model_files missing or not an array: {manifest_path}",
        )

    if not model_files:
        raise LoadError(
            "invalid_manifest", f"manifest.model_files is empty: {manifest_path}"
        )

    models = {}
    for fname in model_files:
        fpath = yaml_dir / fname
        if not fpath.exists():
            raise LoadError("model_file_not_found", f"model file not found: {fpath}")
        try:
            data = yaml.safe_load(fpath.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as e:
            raise LoadError("yaml_parse_error", f"YAML parse failed {fname}: {e}") from e
        if not isinstance(data, dict):
            raise LoadError(
                "yaml_parse_error", f"YAML root of {fname} is not a mapping"
            )
        key = MODEL_KEY_BY_FILE.get(fname, Path(fname).stem)
        models[key] = data

    return models, model_files


class LoadError(Exception):
    def __init__(self, error_code: str, message: str):
        super().__init__(message)
        self.error_code = error_code


# ──────────────────────────────────────────────────────────────
# ID 集合提取（对齐 C# ExtractIdSets）
# ──────────────────────────────────────────────────────────────

def extract_id_sets(models):
    s = {}
    s["M1Objects"] = {e["id"] for e in _get_list(models.get("M1"), "aggregates") if _str(e, "id") is not None}
    s["M2Behaviors"] = set()
    s["M2UserActionBehaviors"] = set()
    s["M2QueryBehaviors"] = set()
    s["M2QueryReportRefs"] = set()
    for b in _get_list(models.get("M2"), "behaviors"):
        bid = _str(b, "id")
        if bid is None:
            continue
        s["M2Behaviors"].add(bid)
        if _str(b, "triggerType") == "USER_ACTION":
            s["M2UserActionBehaviors"].add(bid)
        if _str(b, "behaviorType") == "QUERY":
            s["M2QueryBehaviors"].add(bid)
        qref = _str(b, "queryReportRef")
        if qref is not None:
            s["M2QueryReportRefs"].add(qref)
    s["M3Rules"] = {e["id"] for e in _get_list(models.get("M3"), "rules") if _str(e, "id") is not None}
    s["M5Roles"] = {e["roleId"] for e in _get_list(models.get("M5"), "roles") if _str(e, "roleId") is not None}
    s["M5Permissions"] = {e["permissionId"] for e in _get_list(models.get("M5"), "permissions") if _str(e, "permissionId") is not None}
    s["M6Flows"] = {e["id"] for e in _get_list(models.get("M6"), "flows") if _str(e, "id") is not None}
    s["M7Reports"] = {e["id"] for e in _get_list(models.get("M7"), "query_reports") if _str(e, "id") is not None}
    s["MuTools"] = set()
    s["MuToolBehaviorRefs"] = set()
    for t in _get_list(models.get("MU"), "tools"):
        tname = _str(t, "toolName")
        if tname is not None:
            s["MuTools"].add(tname)
        bref = _str(t, "behaviorRef")
        if bref is not None:
            s["MuToolBehaviorRefs"].add(bref)
    return s


def _violation(model, path, ref, detail):
    return {"model": model, "path": path, "ref": ref, "detail": detail}


def _result(cid, status, message, violations=None):
    return {"id": cid, "status": status, "message": message, "violations": violations or []}


def _group_by_value(pairs):
    """[(key, value)] → {value: [key...]}（对齐 C# GroupKeys 用法）"""
    groups = {}
    for k, v in pairs:
        groups.setdefault(v, []).append(k)
    return groups


# ──────────────────────────────────────────────────────────────
# Check 1: traceability（V9 §1.3 decision 7）
# ──────────────────────────────────────────────────────────────

def check_traceability(ids, models):
    violations = []

    # 正向：每个 USER_ACTION 行为必须被至少一个 MU tool 引用
    for bid in sorted(ids["M2UserActionBehaviors"] - ids["MuToolBehaviorRefs"]):
        violations.append(_violation(
            "M2/MU", f"M2.behaviors[id={bid}]", bid,
            "M2 USER_ACTION behavior has no MU tool reference"))

    # 反向：每个 MU tool 的 behaviorRef 必须存在于 M2
    for bref in sorted(ids["MuToolBehaviorRefs"] - ids["M2Behaviors"]):
        violations.append(_violation(
            "MU", f"MU.tools[behaviorRef={bref}]", bref,
            "MU tool references non-existent M2 behavior"))

    if violations:
        return _result("traceability", "FAIL",
                       f"{len(violations)} traceability violation(s)", violations)
    return _result("traceability", "PASS",
                   f"all {len(ids['M2UserActionBehaviors'])} USER_ACTION behaviors covered; "
                   f"all {len(ids['MuToolBehaviorRefs'])} MU tool refs valid")


# ──────────────────────────────────────────────────────────────
# Check 2: query_mapping（M7.behaviorRef ↔ M2.queryReportRef，严格 1:1）
# ──────────────────────────────────────────────────────────────

def check_query_mapping(ids, models):
    violations = []

    m7_to_beh = {}
    for rep in _get_list(models.get("M7"), "query_reports"):
        rid, bref = _str(rep, "id"), _str(rep, "behaviorRef")
        if rid is not None and bref is not None:
            m7_to_beh[rid] = bref

    m2_to_rep = {}
    for b in _get_list(models.get("M2"), "behaviors"):
        qref = _str(b, "queryReportRef")
        bid = _str(b, "id")
        if qref is not None and bid is not None:
            m2_to_rep[bid] = qref

    if not m7_to_beh and not m2_to_rep:
        return _result("query_mapping", "SKIP",
                       "no M7 reports and no M2 QUERY behaviors")

    # 正向：M7 → M2 存在性
    for rid, bref in m7_to_beh.items():
        if bref not in ids["M2Behaviors"]:
            violations.append(_violation(
                "M7", f"M7.query_reports[id={rid}].behaviorRef", bref,
                "M7 references non-existent M2 behavior"))

    # 反向：M2 → M7 存在性
    for bid, qref in m2_to_rep.items():
        if qref not in ids["M7Reports"]:
            violations.append(_violation(
                "M2", f"M2.behaviors[id={bid}].queryReportRef", qref,
                "M2 references non-existent M7 report"))

    # 严格 1:1 — 一个行为绑定多个报表
    for bref, rids in _group_by_value(m7_to_beh.items()).items():
        if len(rids) > 1:
            violations.append(_violation(
                "M7", f"M7.query_reports[].behaviorRef={bref}", bref,
                f"M2 behavior bound to multiple reports: {', '.join(sorted(rids))}"))

    # 严格 1:1 — 一个报表绑定多个行为
    for qref, bids in _group_by_value(m2_to_rep.items()).items():
        if len(bids) > 1:
            violations.append(_violation(
                "M2", f"M2.behaviors[].queryReportRef={qref}", qref,
                f"M7 report bound to multiple behaviors: {', '.join(sorted(bids))}"))

    if violations:
        return _result("query_mapping", "FAIL",
                       f"{len(violations)} query_mapping violation(s)", violations)
    return _result("query_mapping", "PASS",
                   f"{len(m7_to_beh)} M7 report↔M2 behavior mapping(s) strict 1:1")


# ──────────────────────────────────────────────────────────────
# Check 3: flow_refs
# ──────────────────────────────────────────────────────────────

def check_flow_refs(ids, models):
    flows = _get_list(models.get("M6"), "flows")
    if not flows:
        return _result("flow_refs", "SKIP", "no M6 flows defined")

    violations = []
    for flow in flows:
        fid = _str(flow, "id") or "<unknown>"

        for obj in _str_list(flow, "businessObjectRefs"):
            if obj and obj not in ids["M1Objects"]:
                violations.append(_violation(
                    "M6", f"M6.flows[id={fid}].businessObjectRefs", obj,
                    "M6 references non-existent M1 object"))

        for role in _str_list(flow, "roleRefs"):
            if role and role not in ids["M5Roles"]:
                violations.append(_violation(
                    "M6", f"M6.flows[id={fid}].roleRefs", role,
                    "M6 references non-existent M5 role"))

        for act in _get_list(flow, "activities"):
            aid = _str(act, "activityId") or "<unknown>"

            bref = _str(act, "behaviorRef")
            if bref is not None and bref not in ids["M2Behaviors"]:
                violations.append(_violation(
                    "M6", f"M6.flows[id={fid}].activities[id={aid}].behaviorRef",
                    bref, "M6 activity references non-existent M2 behavior"))

            rref = _str(act, "roleRef")
            if rref is not None and rref not in ids["M5Roles"]:
                violations.append(_violation(
                    "M6", f"M6.flows[id={fid}].activities[id={aid}].roleRef",
                    rref, "M6 activity references non-existent M5 role"))

            sref = _str(act, "subFlowRef")
            if sref is not None and sref not in ids["M6Flows"]:
                violations.append(_violation(
                    "M6", f"M6.flows[id={fid}].activities[id={aid}].subFlowRef",
                    sref, "M6 activity references non-existent M6 flow"))

            # ruleRef 位于 GATEWAY 分支内
            for br in _get_list(act, "branches"):
                rr = _str(br, "ruleRef")
                if rr is not None and rr not in ids["M3Rules"]:
                    violations.append(_violation(
                        "M6", f"M6.flows[id={fid}].activities[id={aid}].branches[].ruleRef",
                        rr, "M6 gateway branch references non-existent M3 rule"))

    if violations:
        return _result("flow_refs", "FAIL",
                       f"{len(violations)} flow_ref violation(s)", violations)
    return _result("flow_refs", "PASS",
                   f"all {len(flows)} M6 flow references resolve")


# ──────────────────────────────────────────────────────────────
# Check 4: acyclic_call_graph（SUB_FLOW_CALL 调用图三色 DFS）
# ──────────────────────────────────────────────────────────────

def check_acyclic_call_graph(ids, models):
    flows = _get_list(models.get("M6"), "flows")
    if not flows:
        return _result("acyclic_call_graph", "SKIP", "no M6 flows defined")

    edges = {}
    for flow in flows:
        fid = _str(flow, "id")
        if fid is None:
            continue
        callees = set()
        for act in _get_list(flow, "activities"):
            if _str(act, "activityType") == "SUB_FLOW_CALL":
                sref = _str(act, "subFlowRef")
                if sref is not None:
                    callees.add(sref)
        edges[fid] = callees

    color = {node: 0 for node in edges}  # 0 白 / 1 灰 / 2 黑
    stack = []
    cycle_path = None

    def dfs(node):
        nonlocal cycle_path
        color[node] = 1
        stack.append(node)
        for nxt in edges[node]:
            if nxt not in color:
                continue  # 未知流 — 由 flow_refs 捕获
            if color[nxt] == 1:
                idx = stack.index(nxt)
                cycle_path = stack[idx:] + [nxt]
                return True
            if color[nxt] == 0 and dfs(nxt):
                return True
        stack.pop()
        color[node] = 2
        return False

    for node in list(edges):
        if color[node] == 0 and dfs(node):
            break

    if cycle_path is not None:
        path = " → ".join(cycle_path)
        return _result("acyclic_call_graph", "FAIL",
                       f"SUB_FLOW_CALL cycle detected: {path}",
                       [_violation("M6", "flows[].activities[subFlowRef]", path, "cycle")])
    return _result("acyclic_call_graph", "PASS",
                   f"{len(edges)} M6 flows, no SUB_FLOW_CALL cycles")


# ──────────────────────────────────────────────────────────────
# Check 5: query_behavior_bidir（正式报表 ↔ QUERY 行为，严格 1:1）
# ──────────────────────────────────────────────────────────────

def check_query_behavior_bidir(ids, models):
    violations = []

    formal_reports = {}
    for rep in _get_list(models.get("M7"), "query_reports"):
        if _str(rep, "objectType") in FORMAL_REPORT_TYPES:
            rid, bref = _str(rep, "id"), _str(rep, "behaviorRef")
            if rid is not None and bref is not None:
                formal_reports[rid] = bref

    formal_behaviors = {}
    for b in _get_list(models.get("M2"), "behaviors"):
        if _str(b, "behaviorType") == "QUERY":
            qref = _str(b, "queryReportRef")
            bid = _str(b, "id")
            if qref is not None and bid is not None:
                formal_behaviors[bid] = qref

    if not formal_reports and not formal_behaviors:
        return _result("query_behavior_bidir", "SKIP",
                       "no formal M7 reports and no M2 QUERY behaviors")

    # 基数 — 行为绑定多个正式报表
    for bref, rids in _group_by_value(formal_reports.items()).items():
        if len(rids) > 1:
            violations.append(_violation(
                "M7", f"M7.query_reports[].behaviorRef={bref}", bref,
                f"formal M2 QUERY bound to multiple reports: {', '.join(sorted(rids))}"))

    # 基数 — 报表绑定多个行为
    for qref, bids in _group_by_value(formal_behaviors.items()).items():
        if len(bids) > 1:
            violations.append(_violation(
                "M2", f"M2.behaviors[].queryReportRef={qref}", qref,
                f"formal M7 report bound to multiple behaviors: {', '.join(sorted(bids))}"))

    # 交叉 — 正式报表的行为必须是 QUERY 类型
    for rid, bref in formal_reports.items():
        if bref not in formal_behaviors:
            violations.append(_violation(
                "M7", f"M7.query_reports[id={rid}].behaviorRef", bref,
                "formal M7 report's behavior is not M2 QUERY type"))

    # 交叉 — QUERY 行为必须指向正式报表
    for bid, qref in formal_behaviors.items():
        if qref not in formal_reports:
            violations.append(_violation(
                "M2", f"M2.behaviors[id={bid}].queryReportRef", qref,
                "M2 QUERY behavior references non-formal M7 report"))

    if violations:
        return _result("query_behavior_bidir", "FAIL",
                       f"{len(violations)} bidirectional violation(s)", violations)
    return _result("query_behavior_bidir", "PASS",
                   f"{len(formal_reports)} formal report(s) ↔ "
                   f"{len(formal_behaviors)} M2 QUERY behavior(s), strict 1:1")


# ──────────────────────────────────────────────────────────────
# Check 6: rule_condition_separation（syncTrigger 描述只写结论）
# ──────────────────────────────────────────────────────────────

def check_rule_condition_separation(ids, models):
    behaviors = _get_list(models.get("M2"), "behaviors")
    if not behaviors:
        return _result("rule_condition_separation", "SKIP",
                       "no M2 behaviors defined")

    violations = []
    total_triggers = 0

    for b in behaviors:
        bid = _str(b, "id") or "<unknown>"
        triggers = _get_list(b, "syncTriggers")
        total_triggers += len(triggers)
        for idx, trig in enumerate(triggers):
            desc = (_str(trig, "description") or "").strip()
            lower = desc.lower()
            has_condition = any(h in lower for h in CONDITIONAL_HINTS)
            if has_condition:
                violations.append(_violation(
                    "M2", f"M2.behaviors[id={bid}].syncTriggers[{idx}].description",
                    _str(trig, "behaviorRef") or "",
                    "syncTrigger description embeds conditional logic; "
                    "move condition to an M3 rule and reference it from appliedRules"))

    if violations:
        return _result("rule_condition_separation", "FAIL",
                       f"{len(violations)} syncTrigger description(s) encode conditions inline "
                       f"(out of {total_triggers})", violations)
    return _result("rule_condition_separation", "PASS",
                   f"all {total_triggers} syncTrigger descriptions are conclusion-only")


# ──────────────────────────────────────────────────────────────
# 输出与入口
# ──────────────────────────────────────────────────────────────

CHECK_HANDLERS = {
    "traceability": check_traceability,
    "query_mapping": check_query_mapping,
    "flow_refs": check_flow_refs,
    "acyclic_call_graph": check_acyclic_call_graph,
    "query_behavior_bidir": check_query_behavior_bidir,
    "rule_condition_separation": check_rule_condition_separation,
}


def error_envelope(error_code, message):
    """与 C# SerializeError 对齐的 ERROR 信封"""
    return {
        "status": "ERROR",
        "yaml_dir": "",
        "model_files": [],
        "checks": [],
        "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0},
        "error_code": error_code,
        "error": message,
    }


def render_text(payload):
    """text 输出：逐检查一行 + violation 明细 + summary"""
    print(f"status: {payload['status']}")
    for r in payload["checks"]:
        tag = r["status"]
        print(f"[{tag}] {r['id']} — {r['message']}")
        for v in r["violations"]:
            print(f"  [{v['model']}] {v['path']} ref={v['ref']} — {v['detail']}")
    s = payload["summary"]
    print(f"summary: {s['passed']} passed, {s['failed']} failed, {s['skipped']} skipped")
    if payload.get("error_code"):
        print(f"error: [{payload['error_code']}] {payload['error']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="model-validator 6 条跨引用门禁")
    parser.add_argument("yaml_dir", help="7 模型 YAML 所在目录")
    parser.add_argument("manifest", help="manifest.json 路径（绝对或相对 yaml_dir）")
    parser.add_argument("--check", action="append", choices=CHECK_IDS,
                        help="只跑指定检查（可重复）")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    yaml_dir = Path(args.yaml_dir).resolve()
    if not yaml_dir.is_dir():
        payload = error_envelope("invalid_arguments", f"yaml_dir not found: {yaml_dir}")
    else:
        try:
            models, loaded_files = load_models(yaml_dir, args.manifest)
        except LoadError as e:
            payload = error_envelope(e.error_code, str(e))
        else:
            ids = extract_id_sets(models)
            check_ids = args.check or CHECK_IDS
            results = []
            for cid in check_ids:
                try:
                    results.append(CHECK_HANDLERS[cid](ids, models))
                except Exception as e:  # 单检查异常不得中断整体（对齐 C# try/catch per check）
                    results.append(_result(
                        cid, "FAIL",
                        f"check '{cid}' threw {type(e).__name__}: {e}"))
            passed = sum(1 for r in results if r["status"] == "PASS")
            failed = sum(1 for r in results if r["status"] == "FAIL")
            skipped = sum(1 for r in results if r["status"] == "SKIP")
            payload = {
                "status": "FAIL" if failed else "OK",
                "yaml_dir": str(yaml_dir),
                "model_files": loaded_files,
                "checks": results,
                "summary": {"total": len(results), "passed": passed,
                            "failed": failed, "skipped": skipped},
            }

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False))
    else:
        render_text(payload)

    if payload["status"] == "ERROR":
        return 2
    if payload["status"] == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
