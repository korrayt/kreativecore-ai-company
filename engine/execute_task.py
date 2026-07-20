from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from engine.checks import run_checks
from engine.config import engine_settings, model_config
from engine.github_api import GitHub
from engine.json_protocol import extract_json, validate_code_actions
from engine.runtime import client, read_agent, repo_context
from engine.safety import apply_actions


def resolve(root: Path, reference: str) -> tuple[str, str]:
    if reference.isdigit():
        issue = GitHub().issue(int(reference))
        return str(issue["title"]), str(issue.get("body") or "")
    folder = root / "tasks" / "inbox" / reference
    if folder.is_dir():
        manifest = (folder / "TASK.toml").read_text(encoding="utf-8", errors="ignore") if (folder / "TASK.toml").is_file() else ""
        request = (folder / "REQUEST.md").read_text(encoding="utf-8", errors="ignore") if (folder / "REQUEST.md").is_file() else ""
        return reference, manifest + "\n\n" + request
    markdown = root / "tasks" / "inbox" / f"{reference}.md"
    if markdown.is_file():
        return reference, markdown.read_text(encoding="utf-8", errors="ignore")
    raise FileNotFoundError(f"Task not found: {reference}")


def execute(root: Path, reference: str, agent: str) -> dict:
    title, request = resolve(root, reference)
    context = repo_context(root, title + "\n" + request)
    llm, model = client(root), model_config(root)
    protocol = """Return only one JSON object:
{"summary":"...","actions":[{"op":"write","path":"relative/path","content":"complete content"},{"op":"delete","path":"relative/path"}],"notes":[]}
Never return shell commands. Never edit protected paths."""
    payload = extract_json(llm.chat(
        system=read_agent(root, agent) + "\n" + protocol,
        user=f"TASK TITLE:\n{title}\n\nREQUEST:\n{request}\n\nSELECTED REPOSITORY CONTEXT:\n{context}",
        max_tokens=model.max_tokens_code,
    ))
    actions = validate_code_actions(payload)
    settings = engine_settings(root)
    changed = apply_actions(
        root,
        actions,
        protected_prefixes=list(settings["safety"]["protected_prefixes"]),
        max_files=int(settings["engine"]["max_write_files"]),
        max_bytes=int(settings["engine"]["max_write_bytes"]),
    )
    checks = run_checks(root)
    passed = all(item["returncode"] == 0 for item in checks)
    report = {"reference": reference, "agent": agent, "summary": payload.get("summary", ""), "changed_files": changed, "checks": checks, "passed": passed, "notes": payload.get("notes", [])}
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", reference)
    (reports / f"task-{safe}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (reports / f"task-{safe}.md").write_text(f"# AI Task Report — {reference}\n\n- Agent: `{agent}`\n- Checks passed: `{passed}`\n\n## Summary\n\n{payload.get('summary', '')}\n\n## Changed files\n\n" + "\n".join(f"- `{x}`" for x in changed) + "\n\n## Checks\n\n```json\n" + json.dumps(checks, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    if not passed:
        raise RuntimeError("Generated changes failed repository checks")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("--agent", default="coder")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    print(json.dumps(execute(Path(args.root).resolve(), args.reference, args.agent), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
