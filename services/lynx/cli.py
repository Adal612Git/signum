from __future__ import annotations

import json
import sys

from .plan import generate_plan


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print(json.dumps({"status": "failed", "error": "Missing project_id"}))
        raise SystemExit(1)
    project_id = args[0]
    _ = generate_plan(project_id)
    print(json.dumps({"status": "ok", "path": "automation/codex_plan.json"}))


if __name__ == "__main__":
    main()
