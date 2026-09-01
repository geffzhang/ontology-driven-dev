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