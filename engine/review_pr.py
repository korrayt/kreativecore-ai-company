from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.config import model_config
from engine.github_api import GitHub
from engine.json_protocol import extract_json
from engine.runtime import client, read_agent


def review(root: Path, number: int) -> dict:
    github = GitHub()
    pr = github.pull(number)
    files = github.pull_files(number)
    blocks = []
    for item in files[:40]:
        blocks.append(f"===== {item['filename']} =====\nstatus={item['status']} additions={item['additions']} deletions={item['deletions']}\n{item.get('patch') or '[patch unavailable]'}")
    diff = "\n\n".join(blocks)[:70000]
    model = model_config(root)
    result = extract_json(client(root).chat(
        system=read_agent(root, "reviewer") + "\nReturn only JSON with verdict, summary and findings. verdict must be approve, comment or request_changes.",
        user=f"PR #{number}\nTITLE: {pr['title']}\nBODY: {pr.get('body') or ''}\nDIFF:\n{diff}",
        max_tokens=model.max_tokens_review,
    ))
    findings = result.get("findings", [])
    body = f"## Local AI Review\n\n**Verdict:** `{result.get('verdict', 'comment')}`\n\n### Summary\n\n{result.get('summary', '')}\n\n### Findings\n\n" + ("\n".join(f"- {x}" for x in findings) if isinstance(findings, list) and findings else "- No specific findings") + "\n\n> Human review remains required."
    github.comment(number, body)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("number", type=int)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    print(json.dumps(review(Path(args.root).resolve(), args.number), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
