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
  $ python scripts/validate.py reference-example/
  [PASS] reference-example/m1-object-model.jsonld
  [PASS] reference-example/m5-actor-model.jsonld
  [PASS] reference-example/m6-flow-model.jsonld
  [PASS] reference-example/m7-report-model.jsonld
  [SKIP] reference-example/m1-object-model.yaml
  [SKIP] reference-example/m5-actor-model.yaml
  [SKIP] reference-example/m6-flow-model.yaml
  [SKIP] reference-example/m7-report-model.yaml
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml
from rdflib import Graph, Namespace, RDF

# Windows GBK stdout can't encode ↔ (U+2194) — force UTF-8 for M2 alignment output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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


def validate_m2_yaml_jsonld_alignment(yaml_path: Path, jsonld_path: Path) -> dict:
    """M2 双层对账 + yamlPointer 反向链接验证

    两层校验：
    1. ID 集对称 — YAML behaviors[].id 与 JSON-LD od:Behavior/od:id 一一对应
    2. yamlPointer 反向 — JSON-LD 每条 od:yamlPointer 形如
       #yaml/<filename>#behaviors[<id>]，<id> 必须真实存在于传入的 yaml_path 中
       （filename 字段也需与 yaml_path.basename 一致，否则记为一致性问题但仍用 yaml_path 校验）
    """
    # ── 加载 yaml_path（后续 ID 对称 & 反向链接都依赖它）
    try:
        yaml_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        return {
            "passed": False,
            "stdout_lines": [
                f"[FAIL] M2 yamlPointer 解析失败: {yaml_path.name} — {e}"
            ],
        }

    yaml_by_id = {
        b["id"]: b
        for b in yaml_data.get("behaviors", [])
        if isinstance(b, dict) and "id" in b
    }
    yaml_ids = set(yaml_by_id.keys())

    g = Graph()
    with open(jsonld_path, encoding="utf-8") as f:
        g.parse(data=f.read(), format="json-ld")
    OD = Namespace("https://ontology.ontology-driven.dev/v9#")
    jsonld_ids = {str(g.value(s, OD.id)) for s in g.subjects(RDF.type, OD.Behavior)}

    stdout_lines = []
    passed = True

    # ── 检查 1：ID 集对称
    missing_in_jsonld = yaml_ids - jsonld_ids
    missing_in_yaml = jsonld_ids - yaml_ids
    if missing_in_jsonld or missing_in_yaml:
        stdout_lines.append(
            f"[FAIL] M2 ID 漂移: yaml-仅={sorted(missing_in_jsonld)}, jsonld-仅={sorted(missing_in_yaml)}"
        )
        passed = False
    else:
        stdout_lines.append(f"[OK] M2 双层对账: {len(yaml_ids)} behaviors 一致")

    # ── 检查 2：yamlPointer 反向链接解析
    resolved_count = 0
    pointer_fails = []

    for s in g.subjects(RDF.type, OD.Behavior):
        yp = g.value(s, OD.yamlPointer)
        if yp is None:
            pointer_fails.append(f"[FAIL] M2 yamlPointer 缺失: subject={s}")
            continue
        yp_str = str(yp)
        # 解析 #yaml/<filename>#behaviors[<id>]
        try:
            tail = yp_str.split("#yaml/", 1)[1]
            yaml_filename, rest = tail.split("#behaviors[", 1)
            behavior_id = rest.split("]", 1)[0]
        except (IndexError, ValueError):
            pointer_fails.append(f"[FAIL] M2 yamlPointer 格式错误: {yp_str}")
            continue

        # 一致性检查：yamlPointer 文件名 vs 传入 yaml_path.basename
        if yaml_filename != yaml_path.name:
            pointer_fails.append(
                f"[FAIL] M2 yamlPointer 文件不一致: 指向 {yaml_filename}，传入 {yaml_path.name}"
            )
            # 仍按 yaml_path 校验 behavior_id
            if behavior_id not in yaml_by_id:
                pointer_fails.append(f"[FAIL] M2 yamlPointer 断裂: {behavior_id}")
            else:
                resolved_count += 1
            continue

        if behavior_id not in yaml_by_id:
            pointer_fails.append(f"[FAIL] M2 yamlPointer 断裂: {behavior_id}")
            continue
        resolved_count += 1

    if not pointer_fails:
        stdout_lines.append(
            f"[OK] M2 yamlPointer: {resolved_count} reverse-links resolved"
        )
    else:
        stdout_lines.extend(pointer_fails)
        passed = False

    return {"passed": passed, "stdout_lines": stdout_lines}


def collect_targets(target: Path) -> list:
    """展开 target 为待验证文件列表"""
    if target.is_file():
        return [target]
    if target.is_dir():
        files = sorted(p for p in target.iterdir() if p.suffix in (".yaml", ".yml", ".jsonld") and p.name != "manifest.jsonld")
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
    # 在 collect_targets 后，对 M2 YAML 触发对账
    m2_yaml = target / "m2-behavior-model.yaml"
    m2_jsonld = target / "m2-behavior-model.jsonld"
    if m2_yaml.exists() and m2_jsonld.exists():
        r = validate_m2_yaml_jsonld_alignment(m2_yaml, m2_jsonld)
        r["path"] = f"{m2_yaml.name} ↔ {m2_jsonld.name}"
        results.append(r)
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
        r["kind"] = f.suffix
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