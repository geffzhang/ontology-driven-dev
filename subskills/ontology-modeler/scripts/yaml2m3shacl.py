#!/usr/bin/env python3
"""yaml2m3shacl.py — M3 YAML rules → SHACL shapes (Turtle)

Production translator that replaces the PoC (which inlined business DSL into
SPARQL FILTER — invalid SPARQL). Features:
  * One sh:property per inputParams[] entry (datatype + required → minCount)
  * One sh:sparql per rule, with the DSL expression translated to valid SPARQL
    using BIND + FILTER (negation)
  * sh:targetClass inferred from inputParams[].sourceField entity prefix
    (e.g. Contract.totalAmount → od:Contract)
  * Mixed-entity rules emit rdfs:comment + property shapes but skip
    sh:targetClass and sh:sparql (graceful degrade)
  * IF/THEN/ELSE rules emit rdfs:comment + property shapes but skip sh:sparql
"""
import re
import sys
from pathlib import Path

import yaml

OD_VOCAB = "https://ontology.ontology-driven.dev/v9#"
SH_VOCAB = "http://www.w3.org/ns/shacl#"
XSD_VOCAB = "http://www.w3.org/2001/XMLSchema#"
RDFS_VOCAB = "http://www.w3.org/2000/01/rdf-schema#"

PREFIXES = (
    f"@prefix od: <{OD_VOCAB}> .\n"
    f"@prefix sh: <{SH_VOCAB}> .\n"
    f"@prefix xsd: <{XSD_VOCAB}> .\n"
    f"@prefix rdfs: <{RDFS_VOCAB}> .\n"
)

# ---------------------------------------------------------------------------
# Vocabulary mapping
# ---------------------------------------------------------------------------

# YAML type → XSD datatype
TYPE_MAP = {
    "Decimal": "xsd:decimal",
    "Integer": "xsd:integer",
    "String": "xsd:string",
    "Enum": "xsd:string",
    "Date": "xsd:date",
    "DateTime": "xsd:dateTime",
    "Boolean": "xsd:boolean",
}

# DSL operator → SPARQL operator (== → =, etc.)
OP_MAP = {
    "==": "=",
    "!=": "!=",
    ">=": ">=",
    "<=": "<=",
    ">": ">",
    "<": "<",
}

# ---------------------------------------------------------------------------
# Regex dispatch — order matters
# ---------------------------------------------------------------------------

# Pattern 4: IF/THEN/ELSE  (e.g. "IF x <= 0 THEN '未收款' ELSE ...")
RE_PATTERN4_IF = re.compile(r"^IF\b", re.IGNORECASE)

# Pattern 2: arithmetic comparison  (e.g. "a + b <= c")
RE_PATTERN2_ARITH = re.compile(
    r"^(\w+)\s*([+\-*/])\s*(\w+)\s*(>=|<=|==|!=|>|<)\s*(.+?)\s*$"
)

# Pattern 3: OR-chain  (e.g. "p == 'X' OR p == 'Y'")
RE_PATTERN3_OR = re.compile(
    r"^(\w+)\s*==\s*['\"]([^'\"]+)['\"]\s+OR\s+(\w+)\s*==\s*['\"]([^'\"]+)['\"](?:\s+OR.*)?\s*$"
)

# Pattern 5: AND-chain  (e.g. "a == 0 AND b == 0")
RE_PATTERN5_AND = re.compile(
    r"^(\w+)\s*(==|!=|>=|<=|>|<)\s*(\S+?)\s+AND\s+(\w+)\s*(==|!=|>=|<=|>|<)\s*(\S+?)\s*$"
)

# Pattern 1: simple comparison  (e.g. "x >= 1000")
RE_PATTERN1_SIMPLE = re.compile(
    r"^(\w+)\s*(>=|<=|==|!=|>|<)\s*(.+?)\s*$"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def first_lower(name):
    """Lowercase first letter (used to derive sh:path from param name)."""
    return name[0].lower() + name[1:] if name else name


def extract_entities(input_params):
    """Distinct entity prefixes (preserving first-seen order) from sourceField."""
    seen = []
    for p in input_params:
        sf = p.get("sourceField", "")
        if "." in sf:
            ent = sf.split(".", 1)[0]
            if ent not in seen:
                seen.append(ent)
    return seen


def render_rhs(rhs):
    """Render a right-hand-side token as a SPARQL literal/variable."""
    rhs = rhs.strip()
    if rhs == "true":
        return "true"
    if rhs == "false":
        return "false"
    if (rhs.startswith("'") and rhs.endswith("'")) or (
        rhs.startswith('"') and rhs.endswith('"')
    ):
        inner = rhs[1:-1].replace('"', '\\"')
        return f'"{inner}"'
    try:
        float(rhs)
        return rhs
    except ValueError:
        pass
    return f"?{rhs}"


# ---------------------------------------------------------------------------
# Property shape emission
# ---------------------------------------------------------------------------


def emit_property_block(param, rule_name):
    """Emit one sh:property [ ... ] block (Turtle).

    The inner statements of an anonymous blank node terminate with `;` and the
    closing `]` is preceded by NO terminator (the blank-node-closing punctuation
    is implicit). The blank node is itself a predicate-object on the parent,
    so it is followed by `;` to continue the property list.
    """
    name = param["name"]
    ptype = param.get("type", "String")
    required = param.get("required", True)
    xsd_type = TYPE_MAP.get(ptype, "xsd:string")
    path = f"od:{first_lower(name)}"

    lines = [
        "    sh:property [",
        f"        sh:path {path} ;",
        f"        sh:datatype {xsd_type} ;",
    ]
    if required:
        lines.append("        sh:minCount 1 ;")
    lines.append(
        f'        sh:message "{rule_name}: requires valid {name} ({ptype})" ;'
    )
    lines.append("    ] ;")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# DSL → SPARQL translator
# ---------------------------------------------------------------------------


def dsl_to_sparql(expr, input_params):
    """Translate a rule's DSL expression to SPARQL WHERE body lines.

    Returns (where_body_lines_or_None, pattern_label).
    """
    expr = expr.strip()

    # Build property bindings (always emitted so FILTER vars are bound)
    bindings = [
        f"            ?this od:{first_lower(p['name'])} ?{first_lower(p['name'])} ."
        for p in input_params
    ]

    # Pattern 4 — IF/THEN/ELSE — graceful degrade
    if RE_PATTERN4_IF.match(expr):
        return None, "Pattern4-IF/THEN/ELSE"

    # Pattern 2 — arithmetic
    m = RE_PATTERN2_ARITH.match(expr)
    if m:
        a, op, b, cmp_op, rhs = m.groups()
        sum_var = f"?_sum_{a}_{b}"
        rhs_sparql = render_rhs(rhs)
        body = bindings + [
            f"            BIND((xsd:decimal(?{a}) {op} xsd:decimal(?{b})) AS {sum_var}) .",
            f"            FILTER ({sum_var} {OP_MAP[cmp_op]} {rhs_sparql})",
        ]
        return body, "Pattern2-Arithmetic"

    # Pattern 3 — OR-chain
    m = RE_PATTERN3_OR.match(expr)
    if m:
        a, va, b, vb = m.groups()
        body = bindings + [
            f'            FILTER (!(?{a} = "{va}" || ?{b} = "{vb}"))',
        ]
        return body, "Pattern3-OR-chain"

    # Pattern 5 — AND-chain
    m = RE_PATTERN5_AND.match(expr)
    if m:
        a, cmp_a, va, b, cmp_b, vb = m.groups()
        body = bindings + [
            f"            FILTER (!(?{a} {OP_MAP[cmp_a]} {render_rhs(va)} && ?{b} {OP_MAP[cmp_b]} {render_rhs(vb)}))",
        ]
        return body, "Pattern5-AND-chain"

    # Pattern 1 — simple comparison
    m = RE_PATTERN1_SIMPLE.match(expr)
    if m:
        left, cmp_op, right = m.groups()
        body = bindings + [
            f"            FILTER (?{left} {OP_MAP[cmp_op]} {render_rhs(right)})",
        ]
        return body, "Pattern1-Simple"

    return None, "Unrecognized-degraded"


# ---------------------------------------------------------------------------
# NodeShape assembly
# ---------------------------------------------------------------------------


def to_shape(rule, stats):
    rid = rule["id"]
    description = rule.get("description", rid)
    name = rule.get("name", rid)
    expr = " ".join(rule.get("expression", "true").split())
    severity = rule.get("severity", "sh:Violation").replace("sh:", "")
    input_params = rule.get("inputParams", [])

    entities = extract_entities(input_params)
    single_entity = len(entities) == 1
    mixed_entities = len(entities) > 1

    # Property blocks (one per inputParam)
    property_blocks = "\n".join(
        emit_property_block(p, name) for p in input_params
    )

    # targetClass
    target_class_ttl = ""
    if single_entity:
        target_class_ttl = f"    sh:targetClass od:{entities[0]} ;\n"
    elif mixed_entities:
        print(
            f"[WARN] {rid}: mixed entities {entities} — skipping sh:targetClass and sh:sparql",
            file=sys.stderr,
        )

    # sh:sparql (DSL → SPARQL, negated)
    sparql_ttl = ""
    pattern_label = None
    if single_entity:
        sparql_body, pattern_label = dsl_to_sparql(expr, input_params)
        if sparql_body is not None:
            where_block = "\n".join(sparql_body)
            sparql_ttl = (
                "    sh:sparql [\n"
                '        sh:select """\n'
                "            SELECT ?this WHERE {\n"
                f"{where_block}\n"
                "            }\n"
                '        """ ;\n'
                "    ] ;\n"
            )
        else:
            # Pattern 4 or unrecognized — graceful degrade (rdfs:comment only)
            pass

    # Record stats (per-rule)
    bucket = pattern_label if pattern_label else "degraded"
    stats[bucket] = stats.get(bucket, 0) + 1

    # rdfs:comment documenting the rule + pattern
    comment_ttl = (
        f'    rdfs:comment """Rule: {name}. DSL: {expr} (pattern: '
        f'{pattern_label or "degraded"})""" ;\n'
    )

    # Assemble Turtle — predicates end with ';' except the final '.'
    parts = [
        f"od:{rid}Shape",
        "    a sh:NodeShape ;",
        target_class_ttl,
        sparql_ttl,
        property_blocks,
        comment_ttl,
        f"    sh:severity sh:{severity} ;",
        f'    sh:message "{description}" .',
    ]
    return "\n".join(p for p in parts if p) + "\n"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main():
    if len(sys.argv) < 2:
        print("Usage: yaml2m3shacl.py <yaml-path> [<ttl-path>]", file=sys.stderr)
        sys.exit(1)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".shacl.ttl")
    data = yaml.safe_load(src.read_text(encoding="utf-8"))
    rules = data.get("rules", [])

    stats = {}
    body = "\n".join(to_shape(r, stats) for r in rules)
    dst.write_text(PREFIXES + body, encoding="utf-8")

    print(f"[OK] {src.name} -> {dst.name} ({len(rules)} SHACL shapes)")
    print("[STATS] Pattern distribution:")
    for pname, count in sorted(stats.items()):
        print(f"  - {pname}: {count}")


if __name__ == "__main__":
    main()