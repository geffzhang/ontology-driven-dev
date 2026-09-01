#!/usr/bin/env python3
"""drift_check.py — YAML <-> JSON-LD ID set consistency check (spec § 八 CI gate).

Deviations from brief (pre-flagged defects in brief, fixed per task instructions):

1. Filename derivation bug: brief's chained `.replace('m1-', 'm1-object-')` etc.
   turns `m1-object-model.jsonld` into `m1-object-object-model.yaml` (double-prefix),
   so the YAML file never resolves and `continue` fires silently. Fix: derive the
   yaml name directly from the model id (`M1` -> `m1-object-model.yaml`, etc.) using
   a small explicit map.

2. URN key bug: brief's `yaml_ids` builds URNs as
   `urn:od:contract-mgmt:{yaml_section_key}:{id}` (e.g. `:aggregates:AGG-...`), but
   every JSON-LD in this repo uses the *model id* as the second segment
   (`:M1:AGG-...`). With the brief's URN key the two sets never intersect. Fix:
   pass `m_id` (M1/M5/M7) and use it as the URN segment.

3. M5 actor field bug: brief reads `item['id']` for every YAML section, but
   `actors[]` items use `actorId` and `roles[]` items use `roleId`. Fix: per-model
   YAML id extractor that knows each section's id field.

Output: exit 0 on no drift, 1 on drift, prints the symmetric-difference summary.
"""
import json
import sys
from pathlib import Path

import yaml
from rdflib import Graph

# Map: model_id -> (jsonld_filename, yaml_filename, [(yaml_section, id_field, urn_prefix)])
MODELS = [
    (
        "M1",
        "m1-object-model.jsonld",
        "m1-object-model.yaml",
        [("aggregates", "id", "AGG-")],
    ),
    (
        "M5",
        "m5-actor-model.jsonld",
        "m5-actor-model.yaml",
        [("actors", "actorId", "ACTOR-"), ("roles", "roleId", "ROLE-")],
    ),
    (
        "M7",
        "m7-report-model.jsonld",
        "m7-report-model.yaml",
        [("query_reports", "id", "REP-")],
    ),
]


def yaml_ids(path, sections):
    """Collect id-typed entities from a YAML model.

    `sections` is a list of (yaml_section_key, id_field_name, urn_prefix) tuples.
    Only items whose `id_field` value starts with `urn_prefix` are emitted.
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    out = set()
    for section, field, prefix in sections:
        for item in data.get(section, []) or []:
            value = item.get(field)
            if value and value.startswith(prefix):
                out.add(value)
    return out


def jsonld_ids(path):
    """Collect all URN subjects from a JSON-LD file."""
    g = Graph()
    g.parse(data=path.read_text(encoding="utf-8"), format="json-ld")
    return {str(s) for s in g.subjects() if str(s).startswith("urn:od:")}


def main():
    yaml_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "yaml/")
    if not yaml_dir.exists():
        print(f"[SKIP] {yaml_dir} not found")
        return 0

    drifts = []
    for m_id, jsonld_name, yaml_name, sections in MODELS:
        yaml_file = yaml_dir / yaml_name
        jsonld_file = yaml_dir / jsonld_name
        if not yaml_file.exists() or not jsonld_file.exists():
            continue
        y_local = yaml_ids(yaml_file, sections)
        j_all = jsonld_ids(jsonld_file)
        # Build expected YAML-side URNs by prefixing model id
        y_urns = {f"urn:od:contract-mgmt:{m_id}:{v}" for v in y_local}
        # Restrict JSON-LD set to URNs carrying the same model id AND one of
        # the tracked prefixes (AGG-/ACTOR-/ROLE-/REP-). JSON-LD also contains
        # derived/secondary entities (ASSOC-, DICT-, BIZ_TYPE, PERM-, ...) that
        # are produced from YAML by the upstream transformer; those are not
        # in scope for this drift check.
        tracked_prefixes = tuple(p for _, _, p in sections)
        j_for_model = {
            u for u in j_all
            if u.startswith(f"urn:od:contract-mgmt:{m_id}:")
            and u.split(f"urn:od:contract-mgmt:{m_id}:", 1)[1].startswith(tracked_prefixes)
        }
        only_y = y_urns - j_for_model
        only_j = j_for_model - y_urns
        if only_y or only_j:
            drifts.append((m_id, only_y, only_j))

    if drifts:
        print("[FAIL] drift detected:")
        for m, only_y, only_j in drifts:
            if only_y:
                print(f"  {m}: YAML-only = {sorted(only_y)}")
            if only_j:
                print(f"  {m}: JSONLD-only = {sorted(only_j)}")
        return 1
    print("[OK] no drift")
    return 0


if __name__ == "__main__":
    sys.exit(main())