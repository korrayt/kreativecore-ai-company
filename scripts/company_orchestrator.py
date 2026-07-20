
#!/usr/bin/env python3
"""Kreative Core deterministic project and task orchestrator."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TEXT_EXTENSIONS = {
    ".md", ".txt", ".toml", ".json", ".yaml", ".yml", ".py", ".js", ".jsx",
    ".ts", ".tsx", ".rs", ".html", ".css", ".scss", ".sql", ".sh"
}
CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".rs", ".java", ".go", ".cs",
    ".cpp", ".c", ".h", ".html", ".css", ".scss", ".sql", ".sh"
}
CREATIVE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".svg", ".psd", ".ai", ".aep",
    ".prproj", ".wav", ".mp3", ".mp4", ".mov", ".mkv", ".blend", ".fbx"
}
HARDWARE_EXTENSIONS = {
    ".step", ".stp", ".iges", ".igs", ".stl", ".obj", ".dwg", ".dxf", ".kicad_pcb"
}

@dataclass
class Department:
    id: str
    name: str
    agent: str
    keywords: list[str]
    capabilities: list[str]

def slugify(value: str) -> str:
    value = value.strip().lower()
    replacements = {
        "ı": "i", "ğ": "g", "ü": "u", "ş": "s", "ö": "o", "ç": "c",
        "İ": "i", "Ğ": "g", "Ü": "u", "Ş": "s", "Ö": "o", "Ç": "c",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-")[:70] or "untitled"

def read_toml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except (tomllib.TOMLDecodeError, OSError) as exc:
        return {"_parse_error": str(exc)}

def safe_text(path: Path, limit: int = 40_000) -> str:
    if not path.is_file() or path.stat().st_size > 500_000:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""

def content_snapshot(folder: Path) -> tuple[str, list[str], set[str]]:
    texts: list[str] = []
    files: list[str] = []
    extensions: set[str] = set()
    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(folder)
        if ".company" in rel.parts or any(part.startswith(".git") for part in rel.parts):
            continue
        files.append(str(rel).replace("\\", "/"))
        extensions.add(path.suffix.lower())
        if path.suffix.lower() in TEXT_EXTENSIONS and len("".join(texts)) < 120_000:
            texts.append(safe_text(path))
    return "\n".join(texts), files, extensions

def load_departments(root: Path) -> list[Department]:
    raw = read_toml(root / "company" / "DEPARTMENTS.toml")
    result: list[Department] = []
    for item in raw.get("departments", []):
        result.append(
            Department(
                id=str(item["id"]),
                name=str(item["name"]),
                agent=str(item["agent"]),
                keywords=[str(x).lower() for x in item.get("keywords", [])],
                capabilities=[str(x) for x in item.get("capabilities", [])],
            )
        )
    if not result:
        raise RuntimeError("company/DEPARTMENTS.toml contains no departments")
    return result

def type_defaults(project_type: str) -> list[str]:
    mapping = {
        "software": [
            "management-strategy", "product-planning", "technology-software",
            "quality-testing", "security-trust", "operations"
        ],
        "ai": [
            "management-strategy", "product-planning", "technology-software",
            "ai-data-analytics", "rnd-innovation", "quality-testing",
            "security-trust", "operations"
        ],
        "creative": [
            "management-strategy", "product-planning", "design-creative",
            "marketing", "quality-testing", "operations"
        ],
        "business": [
            "management-strategy", "product-planning", "marketing", "sales",
            "customer-experience", "operations", "finance", "legal-compliance"
        ],
        "physical": [
            "management-strategy", "product-planning", "rnd-innovation",
            "design-creative", "quality-testing", "security-trust", "operations",
            "finance", "legal-compliance", "hardware-physical-products"
        ],
        "research": [
            "management-strategy", "product-planning", "rnd-innovation",
            "ai-data-analytics", "legal-compliance"
        ],
        "mixed": [
            "management-strategy", "product-planning", "operations"
        ],
    }
    return mapping.get(project_type.lower(), mapping["mixed"])

def route_departments(
    text: str,
    extensions: set[str],
    project_type: str,
    explicit: list[str],
    departments: list[Department],
    maximum: int,
) -> list[tuple[Department, int, list[str]]]:
    by_id = {d.id: d for d in departments}
    if explicit and explicit != ["auto"]:
        selected: list[tuple[Department, int, list[str]]] = []
        for dept_id in explicit:
            if dept_id in by_id:
                selected.append((by_id[dept_id], 100, ["explicit"]))
        return selected

    normalized = text.lower()
    scores: dict[str, int] = {d.id: 0 for d in departments}
    reasons: dict[str, list[str]] = {d.id: [] for d in departments}

    for dept in departments:
        for keyword in dept.keywords:
            count = normalized.count(keyword)
            if count:
                scores[dept.id] += min(count, 5) * 2
                reasons[dept.id].append(keyword)

    for dept_id in type_defaults(project_type):
        if dept_id in scores:
            scores[dept_id] += 8
            reasons[dept_id].append(f"type:{project_type}")

    if extensions & CODE_EXTENSIONS:
        for dept_id in ("technology-software", "quality-testing", "security-trust"):
            scores[dept_id] += 10
            reasons[dept_id].append("code-files")
    if extensions & CREATIVE_EXTENSIONS:
        scores["design-creative"] += 10
        reasons["design-creative"].append("creative-files")
    if extensions & HARDWARE_EXTENSIONS:
        scores["hardware-physical-products"] += 14
        reasons["hardware-physical-products"].append("hardware-files")

    for mandatory in ("management-strategy", "product-planning"):
        scores[mandatory] = max(scores[mandatory], 9)
        reasons[mandatory].append("company-core")

    ranked = sorted(
        (
            (by_id[dept_id], score, sorted(set(reasons[dept_id])))
            for dept_id, score in scores.items()
            if score > 0
        ),
        key=lambda item: (-item[1], item[0].id),
    )
    return ranked[:maximum]

def sha256_payload(*parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8", errors="ignore"))
        digest.update(b"\0")
    return digest.hexdigest()[:16]

def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")

def issue_item(
    *,
    work_id: str,
    title: str,
    body: str,
    labels: list[str],
    agent: str,
    priority: str,
    auto_execute: bool,
    owner_approval: bool,
    source_hash: str,
) -> dict[str, Any]:
    marker = f"<!-- kc-work-id:{work_id} -->"
    execution = (
        "Automatic local AI workflow requested."
        if auto_execute and not owner_approval
        else "Founder approval required before local AI execution."
    )
    full_body = f"""{marker}

{body.rstrip()}

## Local AI execution

- Custom agent: `{agent}`
- Priority: `{priority}`
- Auto execute requested: `{str(auto_execute).lower()}`
- Owner approval required: `{str(owner_approval).lower()}`
- Mode: {execution}

Mobile action: use **Actions → Mobile Company Control** and select agent `{agent}`.

## Source fingerprint

`{source_hash}`
"""
    all_labels = sorted(set(labels + [f"agent:{agent}", priority]))
    if owner_approval:
        all_labels.append("needs-owner-approval")
    else:
        all_labels.append("local-ai:ready")
    if auto_execute and not owner_approval:
        all_labels.append("local-ai:auto")
    return {
        "work_id": work_id,
        "title": title,
        "body": full_body,
        "labels": sorted(set(all_labels)),
        "agent": agent,
        "priority": priority,
        "auto_execute": auto_execute and not owner_approval,
        "owner_approval": owner_approval,
        "source_hash": source_hash,
    }

def project_roadmap(name: str, objective: str, departments: list[tuple[Department, int, list[str]]]) -> str:
    rows = [
        ("0. Intake", "Analyst", "Dosya ve brief analizi; eksik bilgilerin çıkarılması", "Analiz raporu"),
        ("1. Definition", "Product + Planner", "Problem, kullanıcı, kapsam ve kabul kriterleri", "Onaylı proje tanımı"),
        ("2. Architecture", "Architect + ilgili departmanlar", "Çözüm yapısı ve bağımlılıklar", "Uygulama planı"),
        ("3. Execution", "Departman ajanları", "Aşamalı üretim", "Çalışan/teslim edilebilir çıktı"),
        ("4. Independent QA", "Reviewer + Quality", "Test, güvenlik ve kullanılabilirlik", "Doğrulama raporu"),
        ("5. Release / Handover", "Operator + Executive", "Yayın, teslim veya sonraki karar", "Kapanış ve öğrenme"),
    ]
    lines = [
        f"# {name} — Roadmap",
        "",
        f"**Objective:** {objective or 'TBD'}",
        "",
        "| Phase | Owner | Work | Exit evidence |",
        "|---|---|---|---|",
    ]
    lines += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows]
    lines += ["", "## Routed departments", ""]
    for dept, score, reasons in departments:
        lines.append(f"- **{dept.name}** — score {score}; reasons: {', '.join(reasons) or 'core'}")
    return "\n".join(lines)

def process_project(
    root: Path,
    folder: Path,
    departments: list[Department],
    maximum: int,
    approval_ids: set[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest_raw = read_toml(folder / "PROJECT.toml")
    manifest = manifest_raw.get("project", {})
    context = manifest_raw.get("context", {})
    parse_error = manifest_raw.get("_parse_error")

    folder_slug = slugify(folder.name)
    name = str(manifest.get("name") or folder.name)
    objective = str(manifest.get("objective") or context.get("problem") or "")
    desired = str(manifest.get("desired_outcome") or "")
    project_type = str(manifest.get("type") or "mixed").lower()
    priority = str(manifest.get("priority") or "P2").upper()
    if priority not in {"P0", "P1", "P2", "P3"}:
        priority = "P2"
    auto_execute = bool(manifest.get("auto_execute", False))
    explicit_departments = [str(x) for x in manifest.get("departments", ["auto"])]
    owner_approval = bool(manifest.get("requires_owner_approval", False))

    text, files, extensions = content_snapshot(folder)
    combined = "\n".join([
        name, objective, desired, str(context), text, " ".join(files)
    ])
    routed = route_departments(
        combined,
        extensions,
        project_type,
        explicit_departments,
        departments,
        maximum,
    )
    routed_ids = [dept.id for dept, _, _ in routed]
    if approval_ids.intersection(routed_ids):
        owner_approval = True

    source_hash = sha256_payload(
        json.dumps(manifest_raw, ensure_ascii=False, sort_keys=True),
        combined,
    )
    company_dir = folder / ".company"

    state = {
        "kind": "project",
        "slug": folder_slug,
        "name": name,
        "path": str(folder.relative_to(root)).replace("\\", "/"),
        "objective": objective,
        "desired_outcome": desired,
        "type": project_type,
        "priority": priority,
        "stage": str(manifest.get("stage") or "intake"),
        "owner": str(manifest.get("owner") or "@korrayt"),
        "auto_execute": auto_execute,
        "owner_approval": owner_approval,
        "manifest_present": (folder / "PROJECT.toml").is_file(),
        "manifest_parse_error": parse_error,
        "source_hash": source_hash,
        "file_count": len(files),
        "files": files[:300],
        "departments": [
            {
                "id": dept.id,
                "name": dept.name,
                "agent": dept.agent,
                "score": score,
                "reasons": reasons,
            }
            for dept, score, reasons in routed
        ],
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    write_json(company_dir / "PROJECT_STATE.json", state)

    analysis_lines = [
        f"# {name} — Initial Analysis",
        "",
        f"- **Path:** `{state['path']}`",
        f"- **Type:** `{project_type}`",
        f"- **Priority:** `{priority}`",
        f"- **Manifest:** {'present' if state['manifest_present'] else 'missing'}",
        f"- **Files discovered:** {len(files)}",
        f"- **Auto execution:** `{str(auto_execute).lower()}`",
        f"- **Owner approval:** `{str(owner_approval).lower()}`",
        "",
        "## Objective",
        "",
        objective or "TBD — PROJECT.toml veya BRIEF.md içinde netleştirilmeli.",
        "",
        "## Desired outcome",
        "",
        desired or "TBD",
        "",
        "## Missing / uncertain information",
        "",
    ]
    missing: list[str] = []
    if not state["manifest_present"]:
        missing.append("PROJECT.toml bulunamadı; `_template` dosyasını kopyala.")
    if parse_error:
        missing.append(f"PROJECT.toml parse error: {parse_error}")
    if not objective:
        missing.append("Objective / problem tanımı eksik.")
    if not desired:
        missing.append("Somut bitiş çıktısı eksik.")
    if not context.get("target_user"):
        missing.append("Hedef kullanıcı tanımı eksik.")
    if not context.get("success_signal"):
        missing.append("Başarı sinyali eksik.")
    analysis_lines += [f"- {item}" for item in missing] or ["- İlk analiz için yeterli temel bilgi var."]
    analysis_lines += ["", "## Routed departments", ""]
    for dept, score, reasons in routed:
        analysis_lines.append(f"- **{dept.name}** (`{dept.agent}`) — {score}: {', '.join(reasons)}")
    write_text(company_dir / "ANALYSIS.md", "\n".join(analysis_lines))
    write_text(company_dir / "ROADMAP.md", project_roadmap(name, objective, routed))

    department_lines = [
        f"# {name} — Department Plan",
        "",
        "| Department | Agent | First responsibility | Approval |",
        "|---|---|---|---|",
    ]
    for dept, _, _ in routed:
        first = dept.capabilities[0] if dept.capabilities else "Department review"
        approval = "Founder" if dept.id in approval_ids else "Normal gate"
        department_lines.append(f"| {dept.name} | `{dept.agent}` | {first} | {approval} |")
    write_text(company_dir / "DEPARTMENT_PLAN.md", "\n".join(department_lines))

    path_label = f"project:{folder_slug}"[:50]
    common_labels = ["kc:company", "kc:project", path_label]
    dispatch: list[dict[str, Any]] = []

    dispatch.append(issue_item(
        work_id=f"project:{folder_slug}:analysis",
        title=f"[ANALYSIS] {name}",
        body=f"""## Project

`{state['path']}`

## Mission

Read the entire project folder and generated `.company` files. Replace the deterministic first
pass with a deeper analysis. Clarify the problem, desired outcome, missing information, risks,
opportunities, required departments and the next decision.

Update project documentation in the same folder and open a focused pull request.""",
        labels=common_labels + ["stage:intake", "dept:management-strategy"],
        agent="analyst",
        priority=priority,
        auto_execute=auto_execute,
        owner_approval=False,
        source_hash=source_hash,
    ))

    dispatch.append(issue_item(
        work_id=f"project:{folder_slug}:roadmap",
        title=f"[PLAN] {name} — roadmap and work breakdown",
        body=f"""## Project

`{state['path']}`

## Mission

Use the project brief and analysis to create a realistic milestone roadmap, dependencies,
acceptance criteria, risks, work packages and review gates. Keep the plan small enough to
execute and update `.company/ROADMAP.md`.""",
        labels=common_labels + ["stage:planning", "dept:management-strategy"],
        agent="planner",
        priority=priority,
        auto_execute=False,
        owner_approval=False,
        source_hash=source_hash,
    ))

    for dept, score, reasons in routed:
        dept_owner_approval = owner_approval or dept.id in approval_ids
        dispatch.append(issue_item(
            work_id=f"project:{folder_slug}:department:{dept.id}",
            title=f"[DEPT] {name} — {dept.name}",
            body=f"""## Project

`{state['path']}`

## Department

**{dept.name}**

Routing score: {score}  
Routing reasons: {', '.join(reasons)}

## Mission

Review the project from this department's perspective. Produce the department-specific plan,
required inputs, dependencies, acceptance criteria, risks and the smallest next executable
task. Do not implement unrelated departments' work.""",
            labels=common_labels + [f"dept:{dept.id}"],
            agent=dept.agent,
            priority=priority,
            auto_execute=auto_execute,
            owner_approval=dept_owner_approval,
            source_hash=source_hash,
        ))

    return state, dispatch

def process_task(
    root: Path,
    path: Path,
    departments: list[Department],
    maximum: int,
    approval_ids: set[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    is_folder = path.is_dir()
    manifest_raw = read_toml(path / "TASK.toml") if is_folder else {}
    manifest = manifest_raw.get("task", {})
    context = manifest_raw.get("context", {})
    parse_error = manifest_raw.get("_parse_error")

    slug = slugify(path.stem if path.is_file() else path.name)
    title = str(manifest.get("title") or path.stem if path.is_file() else manifest.get("title") or path.name)
    request = str(manifest.get("request") or "")
    if path.is_file():
        request = safe_text(path)
        text, files, extensions = request, [path.name], {path.suffix.lower()}
    else:
        text, files, extensions = content_snapshot(path)
        request = request or safe_text(path / "REQUEST.md")

    priority = str(manifest.get("priority") or "P2").upper()
    if priority not in {"P0", "P1", "P2", "P3"}:
        priority = "P2"
    department_choice = str(manifest.get("department") or "auto")
    agent_choice = str(manifest.get("agent") or "auto")
    auto_execute = bool(manifest.get("auto_execute", False))
    owner_approval = bool(manifest.get("requires_owner_approval", False))

    explicit = [] if department_choice == "auto" else [department_choice]
    routed = route_departments(
        "\n".join([title, request, str(context), text, " ".join(files)]),
        extensions,
        "mixed",
        explicit,
        departments,
        maximum,
    )
    primary = routed[0][0] if routed else next(d for d in departments if d.id == "management-strategy")
    agent = primary.agent if agent_choice == "auto" else agent_choice
    if primary.id in approval_ids:
        owner_approval = True

    source_hash = sha256_payload(
        json.dumps(manifest_raw, ensure_ascii=False, sort_keys=True),
        request,
        text,
    )
    state = {
        "kind": "task",
        "slug": slug,
        "title": title,
        "path": str(path.relative_to(root)).replace("\\", "/"),
        "request": request[:10_000],
        "priority": priority,
        "department": primary.id,
        "department_name": primary.name,
        "agent": agent,
        "auto_execute": auto_execute,
        "owner_approval": owner_approval,
        "manifest_parse_error": parse_error,
        "source_hash": source_hash,
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }

    if is_folder:
        company_dir = path / ".company"
        write_json(company_dir / "TASK_STATE.json", state)
        write_text(
            company_dir / "ROUTING.md",
            f"""# {title} — Routing

- Department: **{primary.name}**
- Agent: `{agent}`
- Priority: `{priority}`
- Auto execute: `{str(auto_execute).lower()}`
- Owner approval: `{str(owner_approval).lower()}`
- Reasons: {', '.join(routed[0][2]) if routed else 'fallback'}
""",
        )

    dispatch = [issue_item(
        work_id=f"task:{slug}",
        title=f"[TASK] {title}",
        body=f"""## Source

`{state['path']}`

## Request

{request or 'Read the source folder/file and clarify the requested outcome.'}

## Expected output

{context.get('expected_output') or 'TBD'}

## Acceptance criteria

{context.get('acceptance_criteria') or 'Define measurable acceptance criteria before implementation.'}

## Routed department

**{primary.name}**
""",
        labels=["kc:company", "kc:task", f"dept:{primary.id}"],
        agent=agent,
        priority=priority,
        auto_execute=auto_execute,
        owner_approval=owner_approval,
        source_hash=source_hash,
    )]
    return state, dispatch

def render_portfolio(projects: list[dict[str, Any]]) -> str:
    lines = [
        "# Project Portfolio",
        "",
        "| Project | Type | Stage | Priority | Departments | Auto | Approval |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in sorted(projects, key=lambda x: (x["priority"], x["name"].lower())):
        depts = ", ".join(d["name"] for d in item["departments"][:5])
        if len(item["departments"]) > 5:
            depts += f" +{len(item['departments']) - 5}"
        lines.append(
            f"| [{item['name']}](../projects/{item['slug']}/) | {item['type']} | "
            f"{item['stage']} | {item['priority']} | {depts} | "
            f"{item['auto_execute']} | {item['owner_approval']} |"
        )
    if not projects:
        lines.append("| — | — | — | — | — | — | — |")
    return "\n".join(lines)

def render_queue(dispatch: list[dict[str, Any]]) -> str:
    lines = [
        "# Company Queue",
        "",
        "| Priority | Work | Agent | Auto | Approval | ID |",
        "|---|---|---|---|---|---|",
    ]
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    for item in sorted(dispatch, key=lambda x: (order.get(x["priority"], 9), x["title"])):
        lines.append(
            f"| {item['priority']} | {item['title']} | `{item['agent']}` | "
            f"{item['auto_execute']} | {item['owner_approval']} | `{item['work_id']}` |"
        )
    if not dispatch:
        lines.append("| — | — | — | — | — | — |")
    return "\n".join(lines)

def run(root: Path) -> dict[str, Any]:
    departments = load_departments(root)
    policies = read_toml(root / "company" / "POLICIES.toml")
    maximum = int(policies.get("automation", {}).get("max_departments_per_project", 12))
    approval_ids = set(policies.get("approval", {}).get("always_require_owner", []))

    projects_dir = root / "tasks" / "projects"
    inbox_dir = root / "tasks" / "inbox"
    project_states: list[dict[str, Any]] = []
    task_states: list[dict[str, Any]] = []
    dispatch: list[dict[str, Any]] = []

    if projects_dir.is_dir():
        for folder in sorted(projects_dir.iterdir()):
            if not folder.is_dir() or folder.name.startswith(("_", ".")):
                continue
            state, items = process_project(root, folder, departments, maximum, approval_ids)
            project_states.append(state)
            dispatch.extend(items)

    if inbox_dir.is_dir():
        for path in sorted(inbox_dir.iterdir()):
            if path.name.startswith(("_", ".")):
                continue
            if not path.is_dir() and path.suffix.lower() != ".md":
                continue
            state, items = process_task(root, path, departments, maximum, approval_ids)
            task_states.append(state)
            dispatch.extend(items)

    registry = {
        "version": 2,
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "projects": project_states,
        "tasks": task_states,
        "dispatch_count": len(dispatch),
    }
    write_json(root / "tasks" / ".company" / "registry.json", registry)
    write_json(root / "tasks" / ".company" / "dispatch.json", {"items": dispatch})
    write_text(root / "tasks" / ".company" / "PORTFOLIO.md", render_portfolio(project_states))
    write_text(root / "tasks" / ".company" / "QUEUE.md", render_queue(dispatch))
    return registry

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    registry = run(root)
    print(
        f"Company scan complete: {len(registry['projects'])} projects, "
        f"{len(registry['tasks'])} tasks, {registry['dispatch_count']} work items."
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())
