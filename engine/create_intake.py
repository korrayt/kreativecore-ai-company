from __future__ import annotations

import argparse
from pathlib import Path


def slug(value: str) -> str:
    import re
    replacements = {"ı": "i", "ğ": "g", "ü": "u", "ş": "s", "ö": "o", "ç": "c"}
    value = value.lower().strip()
    for old, new in replacements.items():
        value = value.replace(old, new)
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9._-]+", "-", value)).strip("-")[:70]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["project", "task"])
    parser.add_argument("name")
    parser.add_argument("description")
    parser.add_argument("--type", default="mixed")
    parser.add_argument("--priority", default="P2")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    key = slug(args.name)
    if args.kind == "project":
        folder = root / "tasks" / "projects" / key
        folder.mkdir(parents=True, exist_ok=True)
        toml = f"""[project]\nname = {args.name!r}\nobjective = {args.description!r}\ndesired_outcome = "TBD"\ntype = {args.type!r}\npriority = {args.priority!r}\nstage = "idea"\nowner = "@korrayt"\ndepartments = ["auto"]\nauto_execute = false\nrequires_owner_approval = false\n\n[context]\ntarget_user = ""\nproblem = {args.description!r}\nconstraints = ""\nsuccess_signal = ""\n"""
        (folder / "PROJECT.toml").write_text(toml, encoding="utf-8")
        (folder / "BRIEF.md").write_text(f"# {args.name}\n\n{args.description}\n", encoding="utf-8")
        (folder / "input").mkdir(exist_ok=True)
        (folder / "input" / ".gitkeep").touch()
    else:
        folder = root / "tasks" / "inbox" / key
        folder.mkdir(parents=True, exist_ok=True)
        toml = f"""[task]\ntitle = {args.name!r}\nrequest = {args.description!r}\nproject = ""\npriority = {args.priority!r}\ndepartment = "auto"\nagent = "coder"\nauto_execute = false\nrequires_owner_approval = false\n\n[context]\nexpected_output = "TBD"\nacceptance_criteria = "TBD"\nconstraints = ""\n"""
        (folder / "TASK.toml").write_text(toml, encoding="utf-8")
        (folder / "REQUEST.md").write_text(f"# {args.name}\n\n{args.description}\n", encoding="utf-8")
    print(folder.relative_to(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
