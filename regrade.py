"""
Re-apply the current grade() function to an already-collected results file.

No API calls -- the response text is already on disk. This exists because
grade() has changed since some result files were generated (the minor-audience
check was added after results.live.json's run), which leaves stored verdicts
silently stale. Re-running the model would cost quota for no reason when the
fix is just re-grading text that's already sitting there.

    python regrade.py results/results.live.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil

from runner import Scaffold, Probe, SCAFFOLD_DIR, PROBE_FILE, grade, find_deltas, control_health, Result
import yaml


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    args = ap.parse_args()

    path = pathlib.Path(args.path)
    backup = path.with_suffix(path.suffix + ".pre-regrade.bak")
    shutil.copy2(path, backup)

    scaffolds = {s.id: s for s in (Scaffold.load(p) for p in sorted(SCAFFOLD_DIR.glob("*.yaml")))}
    raw = yaml.safe_load(PROBE_FILE.read_text(encoding="utf-8"))["probes"]
    probes = {d["id"]: Probe(id=d["id"], category=d["category"], severity=d["severity"],
                              fields=d.get("fields", {}), direct_intent=d["direct_intent"])
              for d in raw}

    payload = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for r in payload["results"]:
        if r["condition"] == "direct":
            continue  # direct uses the bare-model sentinel scaffold; grade() output for it doesn't depend on the changed branch
        s = scaffolds.get(r["scaffold_id"])
        p = probes.get(r["probe_id"])
        if s is None or p is None:
            continue
        new_verdict, new_rationale = grade(r["response_excerpt"], p, s, r["condition"])
        if new_verdict != r["verdict"]:
            changed += 1
            r["verdict"] = new_verdict
            r["rationale"] = new_rationale

    results = [Result(**{k: v for k, v in r.items() if k in Result.__dataclass_fields__}) for r in payload["results"]]
    payload["deltas"] = find_deltas(results)
    payload["failed_controls"] = control_health(results)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"re-graded {path}: {changed} verdicts changed (backup at {backup})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
