#!/usr/bin/env python3
"""merge_rdf.py — 逐模型派生 RDF 并成单一图（打包产物）

定位：yaml2* 转换器之后的**打包派生步骤**。逐模型 JSON-LD（od:/meta:）与
M3 的 SHACL TTL（sh:）本就是同一 RDF 数据模型，此处输出一个单图文件
`ontology-merged.ttl` 供交换 / 外部消费（自包含 SHACL bundle：拿它自己
既当数据图又当形状图可直接校验）。

**旧产物保持不变**：本产物是新增，不替代任何既有文件——逐模型
JSON-LD / SHACL、manifest.jsonld、门禁消费路径全部原样。

输入：目录内已派生的 m1/m2/m5/m6/m7-*.jsonld + m3-rule-model.shacl.ttl
      （缺哪个跳过哪个；manifest.jsonld 与 m3-*-fixture.jsonld 不在清单内，
       fixtures 属测试数据不并入）
输出：<dir>/ontology-merged.ttl（Turtle 单图，含 od: + meta: + sh: 全部三元组）
退出：0 成功；2 输入错误（目录不存在 / 无任何可并源文件）

用法：
  merge_rdf.py <dir> [--out <path>] [--format json|text]
"""

import argparse
import json
import sys
from pathlib import Path

from rdflib import Graph, Namespace
from rdflib.compare import to_canonical_graph

# Windows GBK stdout 无法输出 →（U+2192）等字符 — 强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 显式词表前缀绑定（序列化前 bind）：否则 rdflib 对未绑定命名空间自动
# 生成 ns1/ns2，其分配顺序受进程内 hash 顺序影响，两次运行可能互换 —
# CI 逐字节确定性 diff 会误报。bind 顺序即输出前缀顺序。
BINDINGS = [
    ("od", "https://ontology.ontology-driven.dev/v9#"),
    ("meta", "https://openclaw.dev/meta/v1#"),
    ("sh", "http://www.w3.org/ns/shacl#"),
]

# 固定源清单：顺序即并入顺序（输出确定性）；显式列举，天然排除
# manifest.jsonld（索引元数据）与 m3-fixture*.jsonld（测试数据）
SOURCES = [
    "m1-object-model.jsonld",
    "m2-behavior-model.jsonld",
    "m3-rule-model.shacl.ttl",
    "m5-actor-model.jsonld",
    "m6-flow-model.jsonld",
    "m7-report-model.jsonld",
]


def load_source(path: Path) -> Graph:
    """单文件 → 独立 Graph（rdflib 逐文件解析，bnode 不跨文件碰撞）"""
    g = Graph()
    fmt = "turtle" if path.suffix == ".ttl" else "json-ld"
    g.parse(data=path.read_text(encoding="utf-8"), format=fmt)
    return g


def main() -> int:
    parser = argparse.ArgumentParser(description="并图打包：逐模型 RDF → ontology-merged.ttl")
    parser.add_argument("dir", help="含派生 RDF 的目录")
    parser.add_argument("--out", help="输出路径（默认 <dir>/ontology-merged.ttl）")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    d = Path(args.dir).resolve()
    if not d.is_dir():
        print(f"[ERROR] 目录不存在: {d}", file=sys.stderr)
        return 2

    merged = Graph()
    report, skipped = [], []
    for name in SOURCES:
        p = d / name
        if not p.exists():
            skipped.append(name)
            continue
        g = load_source(p)
        merged += g
        report.append({"file": name, "triples": len(g)})

    if not report:
        print(f"[ERROR] 无任何可并源文件: {d}", file=sys.stderr)
        return 2

    # 确定性输出：to_canonical_graph 按结构哈希重标 bnode（跨进程稳定），
    # 再按 (s,p,o) 排序重建图。直接序列化 merged 时，Memory store 对
    # bnode 列表项（如 od:attributes / od:SourceObject）的迭代顺序受进程
    # hash 顺序影响，两次运行会重排 — 排序重建后逐字节可复现。
    canonical = to_canonical_graph(merged)
    ordered = Graph()
    for t in sorted(canonical):
        ordered.add(t)
    for prefix, iri in BINDINGS:
        ordered.bind(prefix, Namespace(iri), replace=True)

    out = Path(args.out) if args.out else d / "ontology-merged.ttl"
    out.write_text(ordered.serialize(format="turtle"), encoding="utf-8")

    payload = {
        "out": str(out.resolve()),
        "sources": report,
        "skipped": skipped,
        "total_triples": len(merged),
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for s in report:
            print(f"[OK] {s['file']}: {s['triples']} triples")
        for name in skipped:
            print(f"[SKIP] {name} (not derived)")
        print(f"[OK] merged → {payload['out']} ({payload['total_triples']} triples)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
