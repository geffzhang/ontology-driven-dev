#!/usr/bin/env python3
"""
validate.py — ontology-modeler 统一验证入口

把以下三类验证统一在一个 CLI 入口：
1. JSON-LD (meta: vocab)  →  validate_m6jsonld.py  (PoC 阶段验证)
2. JSON-LD (od: vocab)    →  validate_od_jsonld.py  (PoC 阶段验证)
3. YAML                    →  暂 SKIPPED，交给 OpenClaw ValidateYamlReferencesTool.cs

设计：
- 按文件后缀路由（.jsonld / .yaml）
- 按 @context IRI 进一步路由（meta: vs od:）
- 聚合输出 text 或 json
- 退出码：0=PASS；1=FAIL；2=SKIPPED with --strict

用法：
  validate.py <dir|file>                # 默认 text
  validate.py <dir> --format json
  validate.py <dir> --strict            # 把 SKIPPED 也当失败

示例：
  $ python tools/validate.py reference-example/
  [PASS] reference-example/m1-object-model.jsonld
  [PASS] reference-example/m5-actor-model.jsonld
  [PASS] reference-example/m6-flow-model.jsonld
  [PASS] reference-example/m7-report-model.jsonld
  [SKIP] reference-example/m1-object-model.yaml
  [SKIP] reference-example/m5-actor-model.yaml
  [SKIP] reference-example/m6-flow-model.yaml
  [SKIP] reference-example/m7-query-model.yaml
  [SKIP] reference-example/m7-report-model.yaml
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from rdflib import Graph, Namespace, RDF

# 词表 IRI → 子验证器映射
META_IRI = "https://openclaw.dev/meta/v1#"
OD_IRI = "https://ontology.ontology-driven.dev/v9#"

TOOLS_DIR = Path(__file__).resolve().parent


def detect_vocab(jsonld_path: Path) -> str | None:
    """读 @context，识别 vocab：'meta' / 'od' / None"""
    try:
        with open(jsonld_path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    ctx = doc.get("@context")
    if not isinstance(ctx, dict):
        return None
    if ctx.get("meta") == META_IRI:
        return "meta"
    if ctx.get("od") == OD_IRI:
        return "od"
    return None


def validate_jsonld(jsonld_path: Path) -> dict:
    """根据 @context 路由到对应 PoC 验证脚本（subprocess）"""
    vocab = detect_vocab(jsonld_path)
    if vocab == "meta":
        cmd = [sys.executable, str(TOOLS_DIR / "validate_m6jsonld.py"), str(jsonld_path)]
    elif vocab == "od":
        cmd = [sys.executable, str(TOOLS_DIR / "validate_od_jsonld.py"), str(jsonld_path)]
    else:
        return {
            "passed": False,
            "skipped": False,
            "error": f"无法识别 @context vocab（既不是 meta: 也不是 od:）",
        }

    proc = subprocess.run(cmd, capture_output=True, text=True)
    stdout_lines = proc.stdout.strip().splitlines() if proc.stdout else []
    passed = proc.returncode == 0
    fail_lines = [l for l in stdout_lines if l.startswith("[FAIL]")]
    return {
        "passed": passed,
        "skipped": False,
        "exit_code": proc.returncode,
        "stdout_lines": stdout_lines,
        "fail_lines": fail_lines,
        "stderr": proc.stderr.strip() if proc.stderr else "",
    }


def validate_yaml(yaml_path: Path) -> dict:
    """YAML 验证不在 ontology-modeler 职责内，由 ValidateYamlReferencesTool.cs 接管"""
    return {
        "passed": True,
        "skipped": True,
        "stdout_lines": [
            "[SKIP] YAML 验证归 OpenClaw ValidateYamlReferencesTool.cs（ITool）"
        ],
    }


def validate_manifest(jsonld_path: Path) -> dict:
    """manifest.jsonld 顶层入口验证：rdflib 解析 + 7 个 ModelManifestEntry"""
    try:
        with open(jsonld_path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return {"passed": False, "error": str(e)}

    g = Graph()
    try:
        g.parse(data=json.dumps(doc), format="json-ld")
    except Exception as e:
        return {"passed": False, "error": f"parse: {e}"}

    OD = Namespace("https://ontology.ontology-driven.dev/v9#")
    entries = list(g.subjects(RDF.type, OD.ModelManifestEntry))
    return {
        "passed": len(entries) == 7,
        "stdout_lines": [f"[OK] manifest.jsonld: {len(entries)} ModelManifestEntry"],
    }


def collect_targets(target: Path) -> list:
    """展开 target 为待验证文件列表"""
    if target.is_file():
        return [target]
    if target.is_dir():
        files = sorted(p for p in target.iterdir() if p.suffix in (".yaml", ".yml", ".jsonld"))
        manifest = target / "manifest.jsonld"
        if manifest.exists():
            files.append(manifest)
        return files
    return []


def render_text(results: list) -> None:
    """text 格式输出"""
    for r in results:
        if r.get("skipped"):
            tag = "SKIP"
        elif r.get("passed"):
            tag = "PASS"
        else:
            tag = "FAIL"
        print(f"[{tag}] {r['path']}")
        for line in r.get("stdout_lines", []):
            print(f"  {line}")
        if not r.get("passed") and not r.get("skipped") and r.get("stderr"):
            print(f"  [STDERR] {r['stderr']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ontology-modeler 统一验证入口"
    )
    parser.add_argument("path", help="目录或文件")
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="输出格式"
    )
    parser.add_argument(
        "--strict", action="store_true", help="把 SKIPPED 当作失败"
    )
    args = parser.parse_args()

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"[ERROR] 路径不存在: {target}", file=sys.stderr)
        return 2

    targets = collect_targets(target)
    if not targets:
        print(f"[WARN] 未发现 .yaml / .jsonld 文件: {target}")
        return 0

    results = []
    for f in targets:
        if f.name == "manifest.jsonld":
            r = validate_manifest(f)
        elif f.suffix == ".jsonld":
            r = validate_jsonld(f)
        elif f.suffix in (".yaml", ".yml"):
            r = validate_yaml(f)
        else:
            continue
        r["path"] = str(f)
        r["kind"] = f.name
        results.append(r)

    if args.format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        render_text(results)
        print()
        passed = sum(1 for r in results if r.get("passed") and not r.get("skipped"))
        failed = sum(1 for r in results if not r.get("passed") and not r.get("skipped"))
        skipped = sum(1 for r in results if r.get("skipped"))
        print(
            f"summary: {passed} passed, {failed} failed, {skipped} skipped"
        )

    failed = sum(1 for r in results if not r.get("passed") and not r.get("skipped"))
    skipped = sum(1 for r in results if r.get("skipped"))

    if args.strict and skipped > 0:
        return 2
    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())