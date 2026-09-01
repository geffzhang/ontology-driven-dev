#!/usr/bin/env python3
"""
run_shacl.py — 用 pyshacl 校验 JSON-LD

用法：
  run_shacl.py <data.jsonld> <shape.ttl> [--format text|json]

示例：
  run_shacl.py reference-example/m6-flow-model.jsonld shacl/m6_flow_shape.ttl
  run_shacl.py reference-example/m1-object-model.jsonld shacl/m1_aggregate_shape.ttl

退出码：0=conforms；1=violations；3=错误
"""

import argparse
import json
import sys
from pathlib import Path

from rdflib import Graph
from pyshacl import validate


def run(data_path: Path, shape_path: Path) -> dict:
    """运行 SHACL 校验，返回 {conforms, violations[], text}"""
    data_graph = Graph()
    with open(data_path, encoding="utf-8") as f:
        data_graph.parse(data=f.read(), format="json-ld")

    shape_graph = Graph()
    shape_graph.parse(str(shape_path), format="turtle")

    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shape_graph,
        inference="none",
        debug=False,
        meta_shacl=False,
    )

    # 提取 violation 列表
    violations = []
    if not conforms:
        from rdflib.namespace import RDF, Namespace
        SH = Namespace("http://www.w3.org/ns/shacl#")
        for v in results_graph.subjects(RDF.type, SH.ValidationResult):
            violations.append(
                {
                    "focusNode": str(results_graph.value(v, SH.focusNode) or ""),
                    "path": str(results_graph.value(v, SH.resultPath) or ""),
                    "message": str(results_graph.value(v, SH.resultMessage) or ""),
                    "severity": str(results_graph.value(v, SH.resultSeverity) or ""),
                }
            )

    return {
        "conforms": bool(conforms),
        "violations": violations,
        "text": results_text,
    }


def render_text(data_path: Path, shape_path: Path, result: dict) -> None:
    if result["conforms"]:
        print(f"[OK] {data_path.name} conforms to {shape_path.name}")
        return
    print(f"[FAIL] {data_path.name} violates {shape_path.name}")
    print(f"  {len(result['violations'])} violation(s):")
    for v in result["violations"]:
        msg = v["message"] or "(no message)"
        node = v["focusNode"].split("/")[-1] or v["focusNode"]
        path = v["path"].split("/")[-1] or v["path"]
        print(f"  - {node} / {path}: {msg}")


def main() -> int:
    parser = argparse.ArgumentParser(description="SHACL 校验器")
    parser.add_argument("data", help="JSON-LD 数据文件")
    parser.add_argument("shape", help="SHACL 形状 .ttl 文件")
    parser.add_argument(
        "--format", choices=["text", "json"], default="text"
    )
    args = parser.parse_args()

    data_path = Path(args.data).resolve()
    shape_path = Path(args.shape).resolve()

    if not data_path.exists():
        print(f"[ERROR] data not found: {data_path}", file=sys.stderr)
        return 3
    if not shape_path.exists():
        print(f"[ERROR] shape not found: {shape_path}", file=sys.stderr)
        return 3

    try:
        result = run(data_path, shape_path)
    except Exception as e:
        print(f"[ERROR] SHACL validation failed: {e}", file=sys.stderr)
        return 3

    if args.format == "json":
        out = {
            "data": str(data_path),
            "shape": str(shape_path),
            "conforms": result["conforms"],
            "violation_count": len(result["violations"]),
            "violations": result["violations"],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        render_text(data_path, shape_path, result)

    return 0 if result["conforms"] else 1


if __name__ == "__main__":
    sys.exit(main())