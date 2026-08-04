#!/usr/bin/env python3
"""Generate the GitHub-ready PWA_ROADMAP.md file."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Sequence

import pwa_roadmap_data as data

DEFAULT_OUTPUT = Path("PWA_ROADMAP.md")


class PwaRoadmapFrontendError(RuntimeError):
    pass


def progress_bar(completed: int, total: int, width: int = 30) -> str:
    if total < 0 or completed < 0 or completed > total or width < 1:
        raise PwaRoadmapFrontendError("invalid progress values")
    filled = 0 if total == 0 else round(completed / total * width)
    return "█" * filled + "░" * (width - filled)


def anchor(number: str) -> str:
    return number.lower().replace(".", "")


def branch(root_number: str):
    prefix = root_number + "."
    return tuple(
        item for item in data.MILESTONES
        if item["number"] == root_number or str(item["number"]).startswith(prefix)
    )


def status_icon(status: str) -> str:
    return "✅" if status == "COMPLETED" else "🟦"


def render() -> str:
    total = data.TOTAL_MILESTONES
    completed = data.COMPLETED_MILESTONES
    planned = data.PLANNED_MILESTONES
    percentage = 0.0 if total == 0 else completed / total * 100.0

    lines = [
        '<div align="center">',
        "",
        "# NexiLabs NoveGeo PWA",
        "",
        "## AWS Map Foundation Engineering Roadmap",
        "",
        f"**Version {data.ROADMAP_VERSION}** · **{data.ROADMAP_START} → {data.ROADMAP_END}** · **{total} canonical records**",
        "",
        f"`{progress_bar(completed,total)}` **{percentage:.2f}%**",
        "",
        f"**{completed} completed** · **{planned} planned** · **{len(data.ROOT_MILESTONES)} root milestones**",
        "",
        "</div>",
        "",
        "> [!IMPORTANT]",
        "> This document is generated from `pwa_roadmap_data.py`. Do not edit milestone content here by hand. Run `python pwa_roadmap_frontend.py` after changing the canonical dataset.",
        "",
        "> [!NOTE]",
        "> The runtime product is an AWS-hosted NexiLabs PWA initially focused only on the NoveGeo map. Browser clients must never connect directly to PostgreSQL.",
        "",
        "---",
        "",
        "## Dashboard",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Overall progress | **{percentage:.2f}%** |",
        f"| Completed records | **{completed}** |",
        f"| Planned records | **{planned}** |",
        f"| Total roadmap records | **{total}** |",
        f"| Root milestones | **{len(data.ROOT_MILESTONES)}** |",
        "",
        "## Locked product boundaries",
        "",
        "| Boundary | Decision |",
        "|---|---|",
    ]
    for key, value in data.ROADMAP_BOUNDARIES.items():
        lines.append(f"| {key.replace('_',' ').title()} | {value} |")

    lines += ["", "---", "", "## Roadmap navigation", ""]
    for root in data.ROOT_MILESTONES:
        items = branch(str(root["number"]))
        done = sum(item["status"] == "COMPLETED" for item in items)
        pct = 0 if not items else done / len(items) * 100
        lines.append(
            f"- [{status_icon(str(root['status']))} **{root['number']} — {root['title']}**](#{anchor(str(root['number']))}) — {done}/{len(items)} complete ({pct:.1f}%)"
        )

    lines += ["", "---", "", "## Root milestone overview", "",
              "| Root | Title | Status | Records | Complete | Progress |",
              "|---|---|---:|---:|---:|---:|"]
    for root in data.ROOT_MILESTONES:
        items = branch(str(root["number"]))
        done = sum(item["status"] == "COMPLETED" for item in items)
        pct = 0 if not items else done / len(items) * 100
        lines.append(
            f"| [{root['number']}](#{anchor(str(root['number']))}) | {root['title']} | {status_icon(str(root['status']))} {str(root['status']).title()} | {len(items)} | {done} | {pct:.1f}% |"
        )

    lines += ["", "---", "", "## Complete roadmap", ""]
    for root in data.ROOT_MILESTONES:
        items = branch(str(root["number"]))
        done = sum(item["status"] == "COMPLETED" for item in items)
        pct = 0 if not items else done / len(items) * 100
        lines += [
            f'<a id="{anchor(str(root["number"]))}"></a>',
            f"### {status_icon(str(root['status']))} {root['number']} — {root['title']}",
            "",
            f"`{progress_bar(done,len(items),20)}` **{done}/{len(items)} complete ({pct:.1f}%)**",
            "",
            "<details>",
            f"<summary><strong>Open {root['number']} roadmap records ({len(items)} items)</strong></summary>",
            "",
        ]
        for item in items:
            indent = "&nbsp;" * (int(item["depth"]) * 4)
            lines += [
                f"{indent}{status_icon(str(item['status']))} **`{item['number']}` — {item['title']}**",
                "",
                f"{indent}- **Status:** {str(item['status']).replace('_',' ').title()}",
                f"{indent}- **Priority:** {item['priority']}",
                f"{indent}- **Dependencies:** None",
                f"{indent}- **Record ID:** `{item['record_id']}`",
                f"{indent}- **Semantic path:** `{item['semantic_path']}`",
                f"{indent}- **Verification:** {item['verification_state']}",
                "",
            ]
        lines += [
            "</details>",
            "",
            "[⬆ Back to roadmap navigation](#roadmap-navigation)",
            "",
            "---",
            "",
        ]

    checksum = hashlib.sha256(
        repr(tuple(dict(item) for item in data.MILESTONES)).encode("utf-8")
    ).hexdigest()
    lines += [
        "## Generation information",
        "",
        "| Property | Value |",
        "|---|---|",
        "| Canonical source | `pwa_roadmap_data.py` |",
        "| Generator | `pwa_roadmap_frontend.py` |",
        f"| Roadmap version | `{data.ROADMAP_VERSION}` |",
        f"| Records rendered | `{total}` |",
        f"| Canonical content checksum | `{checksum}` |",
        "",
        "> The generated timestamp is intentionally omitted so unchanged canonical data produces identical output.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write(output: Path = DEFAULT_OUTPUT, *, check: bool = False) -> str:
    rendered = render()
    if check:
        if not output.exists():
            raise PwaRoadmapFrontendError(f"{output} does not exist")
        if output.read_text(encoding="utf-8") != rendered:
            raise PwaRoadmapFrontendError(
                f"{output} is out of date; run pwa_roadmap_frontend.py"
            )
        return rendered
    output.write_text(rendered, encoding="utf-8", newline="\n")
    return rendered


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        rendered = write(args.output, check=args.check)
    except PwaRoadmapFrontendError as exc:
        print(f"ERROR: {exc}")
        return 1
    action = "Verified" if args.check else "Generated"
    print(f"{action} {args.output}")
    print(f"Records: {data.TOTAL_MILESTONES}")
    print(f"SHA-256: {hashlib.sha256(rendered.encode('utf-8')).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
