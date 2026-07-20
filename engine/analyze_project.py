from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.config import model_config
from engine.json_protocol import extract_json
from engine.runtime import client, read_agent, repo_context


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def analyze(root: Path, slug: str) -> None:
    project = root / "tasks" / "projects" / slug
    if not project.is_dir():
        raise FileNotFoundError(f"Project not found: {slug}")
    manifest, brief = text(project / "PROJECT.toml"), text(project / "BRIEF.md")
    context = repo_context(root, f"{slug}\n{manifest}\n{brief}")
    llm = client(root)
    model = model_config(root)

    analyst = extract_json(llm.chat(
        system=read_agent(root, "analyst") + "\nReturn only JSON with keys analysis, opportunities, unknowns, departments, first_decision, success_signal.",
        user=f"PROJECT: {slug}\nPROJECT TOML:\n{manifest}\nBRIEF:\n{brief}\nCONTEXT:\n{context}",
        max_tokens=model.max_tokens_analysis,
    ))
    planner = extract_json(llm.chat(
        system=read_agent(root, "planner") + "\nReturn only JSON with keys objective, milestones, dependencies, acceptance_criteria, risks, next_action.",
        user=json.dumps({"project": slug, "analysis": analyst, "brief": brief}, ensure_ascii=False),
        max_tokens=model.max_tokens_analysis,
    ))
    architect = extract_json(llm.chat(
        system=read_agent(root, "architect") + "\nReturn only JSON with keys architecture, components, data_flow, technical_risks, validation.",
        user=json.dumps({"project": slug, "analysis": analyst, "roadmap": planner, "context": context}, ensure_ascii=False),
        max_tokens=model.max_tokens_analysis,
    ))

    company = project / ".company"
    company.mkdir(parents=True, exist_ok=True)
    for name, value in [("AI_ANALYSIS", analyst), ("AI_ROADMAP", planner), ("AI_ARCHITECTURE", architect)]:
        (company / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (company / "AI_REPORT.md").write_text(
        f"# {slug} — Local AI Company Report\n\n## Analysis\n```json\n{json.dumps(analyst, ensure_ascii=False, indent=2)}\n```\n\n## Roadmap\n```json\n{json.dumps(planner, ensure_ascii=False, indent=2)}\n```\n\n## Architecture\n```json\n{json.dumps(architect, ensure_ascii=False, indent=2)}\n```\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("slug")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    analyze(Path(args.root).resolve(), args.slug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
