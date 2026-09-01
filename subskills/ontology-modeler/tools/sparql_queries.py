#!/usr/bin/env python3
"""
sparql_queries.py — 跨 JSON-LD 文件 SPARQL 查询演示

演示双轨制 JSON-LD 的核心增量价值：跨文件链接数据查询
（YAML 时代只能 grep 字符串）。

加载：
  reference-example/{m1,m5,m6,m7}-*-model.jsonld
  （m2,m3,mU 暂无 JSON-LD，跳过）

示例：
  python tools/sparql_queries.py --list
  python tools/sparql_queries.py --query Q1
  python tools/sparql_queries.py --all
"""

import argparse
import sys
from pathlib import Path

from rdflib import Graph, Namespace

REFERENCE_DIR = Path(__file__).resolve().parent.parent / "reference-example"

OD = Namespace("https://ontology.ontology-driven.dev/v9#")
META = Namespace("https://openclaw.dev/meta/v1#")

QUERIES = {}


def register(name, description):
    """装饰器：注册查询"""
    def decorator(fn):
        QUERIES[name] = {"fn": fn, "description": description}
        return fn
    return decorator


def load_graph() -> Graph:
    """加载所有 JSON-LD 到一个 rdflib Graph（跨文件）"""
    g = Graph()
    files = sorted(REFERENCE_DIR.glob("m*-*-model.jsonld"))
    for f in files:
        with open(f, encoding="utf-8") as fh:
            g.parse(data=fh.read(), format="json-ld")
        print(f"[load] {f.name}", file=sys.stderr)
    return g


# ── Q1：M6 步骤用了哪个 role + 哪个 M2 behavior？─────────────────
@register("Q1", "M6 步骤中带 permissionRef / skill 引用的 step 详情")
def q1(g: Graph) -> None:
    q = """
    PREFIX meta: <https://openclaw.dev/meta/v1#>
    PREFIX od: <https://ontology.ontology-driven.dev/v9#>

    SELECT ?flowId ?stepId ?label ?kind ?permRef ?skillRef
    WHERE {
      ?flow a meta:Flow ; meta:id ?flowId ; meta:hasStep ?step .
      ?step meta:id ?stepId ; meta:kind ?kind .
      OPTIONAL { ?step meta:label ?label }
      OPTIONAL { ?step meta:permissionRef ?permRef }
      OPTIONAL { ?step meta:skill ?skillRef }
      FILTER (?kind IN ("user_input", "agent", "skill_exec"))
    }
    ORDER BY ?flowId ?stepId
    """
    rows = list(g.query(q))
    print(f"\n# Q1: {len(rows)} M6 steps with role/behavior references")
    print(f"{'flowId':<28} {'stepId':<6} {'kind':<14} {'label':<20} permRef / skillRef")
    print("-" * 100)
    for r in rows:
        label = str(r.label)[:18] if r.label else ""
        perm = str(r.permRef).rsplit(":", 1)[-1] if r.permRef else "-"
        skill = str(r.skillRef).rsplit(":", 1)[-1] if r.skillRef else "-"
        print(f"{str(r.flowId):<28} {str(r.stepId):<6} {str(r.kind):<14} {label:<20} {perm} / {skill}")


# ── Q2：M7 报表 → 主 aggregate → 引用字典 → 所有字典项 ──────────
@register("Q2", "M7 报表 → 主 aggregate → 引用字典 → 所有字典项")
def q2(g: Graph) -> None:
    q = """
    PREFIX od: <https://ontology.ontology-driven.dev/v9#>

    SELECT ?reportId ?aggId ?dictId ?typeName ?itemCode ?itemLabel ?sortOrder
    WHERE {
      ?report a od:Report ; od:id "REP-CONTRACT-LIST" ;
              od:sourceObject ?src .
      ?src od:primary true ; od:objectRef ?aggRef .
      ?aggRef a od:AggregateRoot ; od:id ?aggId .
      ?aggRef od:hasAttribute ?attr .
      ?attr od:dictionaryRef ?dref .
      ?dref od:dictionaryId ?dictId ; od:typeCode ?typeCode .
      ?dict od:id ?dictId ; od:hasType ?dtype .
      ?dtype od:typeCode ?typeCode ; od:typeName ?typeName ; od:hasItem ?ditem .
      ?ditem od:code ?itemCode ; od:label ?itemLabel ; od:sortOrder ?sortOrder .
    }
    ORDER BY ?dictId ?sortOrder
    LIMIT 40
    """
    rows = list(g.query(q))
    print(f"\n# Q2: {len(rows)} dict items reachable from REP-CONTRACT-LIST")
    print(f"{'report':<22} {'agg':<20} {'dictId':<24} {'typeName':<12} {'code':<12} {'label':<20}")
    print("-" * 110)
    for r in rows:
        print(
            f"{'REP-CONTRACT-LIST':<22} {str(r.aggId):<20} {str(r.dictId):<24} "
            f"{str(r.typeName):<12} {str(r.itemCode):<12} {str(r.itemLabel):<20}"
        )


# ── Q3：M5 actor SALES → role → permissions → M1 objects ─────────
@register("Q3", "M5 SALES actor → ROLE-SALES → 所有 permission 覆盖的 object")
def q3(g: Graph) -> None:
    q = """
    PREFIX od: <https://ontology.ontology-driven.dev/v9#>

    SELECT ?actorName ?roleName ?permId ?targetType ?targetRef
    WHERE {
      ?actor a od:Actor ; od:id "ACTOR-SALES" ; od:name ?actorName ;
             od:hasRole ?roleRef .
      ?roleRef a od:Role ; od:name ?roleName ; od:hasPermission ?permRef .
      ?permRef a od:Permission ; od:id ?permId ;
               od:targetType ?targetType ; od:targetRef ?targetRef .
    }
    ORDER BY ?permId
    LIMIT 30
    """
    rows = list(g.query(q))
    print(f"\n# Q3: {len(rows)} permissions held by ACTOR-SALES")
    print(f"{'actor':<10} {'role':<14} {'permission':<26} {'targetType':<10} targetRef")
    print("-" * 100)
    for r in rows:
        actor = str(r.actorName)[:8] if r.actorName else ""
        role = str(r.roleName)[:12] if r.roleName else ""
        target = str(r.targetRef or "").rsplit(":", 1)[-1]
        print(f"{actor:<10} {role:<14} {str(r.permId):<26} {str(r.targetType):<10} {target}")


# ── Q4：所有 meta:Step 的 kind 分布 ──────────────────────────────
@register("Q4", "M6 所有 step 的 kind 分布统计")
def q4(g: Graph) -> None:
    q = """
    PREFIX meta: <https://openclaw.dev/meta/v1#>

    SELECT ?kind (COUNT(?step) AS ?count)
    WHERE {
      ?step a meta:Step ; meta:kind ?kind .
    }
    GROUP BY ?kind
    ORDER BY DESC(?count)
    """
    rows = list(g.query(q))
    print(f"\n# Q4: step kind distribution")
    print(f"{'kind':<14} count")
    print("-" * 30)
    total = 0
    for r in rows:
        c = r["count"]  # bracket access (避 ResultRow.count builtin 冲突)
        print(f"{str(r.kind):<14} {str(c)}")
        total += int(c)
    print(f"{'TOTAL':<14} {total}")


# ── Q5：GATEWAY (llm_classify) routes 的 choice/target ────────────
@register("Q5", "M6 所有 GATEWAY step 的 routes（choice / target / isDefault）")
def q5(g: Graph) -> None:
    q = """
    PREFIX meta: <https://openclaw.dev/meta/v1#>

    SELECT ?flowId ?stepId ?choice ?target ?isDefault ?branchName
    WHERE {
      ?step a meta:Step ; meta:kind "llm_classify" ;
            meta:id ?stepId ; meta:routes ?route .
      ?route a meta:Route ; meta:choice ?choice ; meta:target ?target .
      OPTIONAL { ?route meta:isDefault ?isDefault }
      OPTIONAL { ?route meta:branchName ?branchName }
      ?flow meta:hasStep ?step ; meta:id ?flowId .
    }
    ORDER BY ?flowId ?stepId
    """
    rows = list(g.query(q))
    print(f"\n# Q5: {len(rows)} GATEWAY routes across all flows")
    print(f"{'flow':<28} {'step':<6} {'choice':<14} {'target':<10} {'default':<8} branchName")
    print("-" * 100)
    for r in rows:
        default = "YES" if r.isDefault and str(r.isDefault) == "true" else ""
        branch = str(r.branchName) if r.branchName else ""
        print(f"{str(r.flowId):<28} {str(r.stepId):<6} {str(r.choice):<14} {str(r.target):<10} {default:<8} {branch}")


def main() -> int:
    parser = argparse.ArgumentParser(description="跨 JSON-LD 文件 SPARQL 查询")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--list", action="store_true", help="列出所有查询")
    grp.add_argument("--query", choices=QUERIES.keys(), help="运行指定查询")
    grp.add_argument("--all", action="store_true", help="运行全部查询")
    args = parser.parse_args()

    if args.list:
        print("# Available SPARQL queries\n")
        for name, info in QUERIES.items():
            print(f"{name}: {info['description']}")
        return 0

    g = load_graph()

    if args.all:
        for name, info in QUERIES.items():
            info["fn"](g)
            print()
    else:
        QUERIES[args.query]["fn"](g)

    return 0


if __name__ == "__main__":
    sys.exit(main())