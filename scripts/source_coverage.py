#!/usr/bin/env python3
"""Build and audit a source-to-page content ledger for tutorial books."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ALLOWED_DISPOSITIONS = {
    "verbatim",
    "faithful-edit",
    "visual-plus-text",
    "appendix",
    "user-approved-omit",
}
NOTE_REQUIRED = {"faithful-edit", "visual-plus-text", "appendix"}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def classify(text: str) -> str:
    stripped = text.lstrip()
    if stripped.startswith("```") or stripped.startswith("~~~"):
        return "code"
    if re.match(r"^#{1,6}\s", stripped):
        return "heading"
    if re.match(r"^(?:[-+*]|\d+[.)])\s+", stripped):
        return "list-item"
    if "\n" in stripped and all(
        not line.strip() or line.lstrip().startswith("|") for line in stripped.splitlines()
    ):
        return "table"
    return "paragraph"


def parse_markdown(source: str) -> list[dict[str, str]]:
    """Split Markdown into auditable blocks without merging list items."""
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    raw_blocks: list[str] = []
    paragraph: list[str] = []
    table: list[str] = []
    fence: list[str] = []
    fence_marker: str | None = None

    def flush_paragraph() -> None:
        if paragraph:
            raw_blocks.append("\n".join(paragraph).strip())
            paragraph.clear()

    def flush_table() -> None:
        if table:
            raw_blocks.append("\n".join(table).strip())
            table.clear()

    for line in lines:
        stripped = line.strip()

        if fence_marker is not None:
            fence.append(line)
            if stripped.startswith(fence_marker):
                raw_blocks.append("\n".join(fence).strip())
                fence.clear()
                fence_marker = None
            continue

        if stripped.startswith("```") or stripped.startswith("~~~"):
            flush_paragraph()
            flush_table()
            fence_marker = stripped[:3]
            fence = [line]
            continue

        if not stripped:
            flush_paragraph()
            flush_table()
            continue

        if stripped.startswith("|"):
            flush_paragraph()
            table.append(line)
            continue

        flush_table()

        if re.match(r"^#{1,6}\s", stripped) or re.match(
            r"^(?:[-+*]|\d+[.)])\s+", stripped
        ):
            flush_paragraph()
            raw_blocks.append(line.strip())
            continue

        paragraph.append(line)

    flush_paragraph()
    flush_table()
    if fence:
        raw_blocks.append("\n".join(fence).strip())

    blocks: list[dict[str, str]] = []
    for index, text in enumerate((block for block in raw_blocks if block.strip()), start=1):
        normalized = normalize(text)
        blocks.append(
            {
                "id": f"B{index:04d}",
                "kind": classify(text),
                "text": text,
                "sha256": sha256_text(normalized),
            }
        )
    return blocks


def load_source(path: Path) -> tuple[str, list[dict[str, str]]]:
    source = path.read_text(encoding="utf-8")
    return source, parse_markdown(source)


def init_ledger(source_path: Path, ledger_path: Path) -> None:
    source, blocks = load_source(source_path)
    ledger = {
        "version": 1,
        "source_path": str(source_path),
        "source_sha256": sha256_text(source),
        "blocks": [
            {
                **block,
                "page_ids": [],
                "disposition": None,
                "retention_note": "",
                "approval_note": "",
            }
            for block in blocks
        ],
    }
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Initialized {ledger_path} with {len(blocks)} source blocks.")


def audit_ledger(
    source_path: Path,
    ledger_path: Path,
    allow_approved_omissions: bool,
) -> tuple[dict[str, Any], bool]:
    source, current_blocks = load_source(source_path)
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger_blocks = ledger.get("blocks", [])

    errors: list[dict[str, str]] = []
    source_drift = ledger.get("source_sha256") != sha256_text(source)
    if source_drift:
        errors.append({"id": "SOURCE", "error": "source_sha256 changed"})

    current_by_id = {block["id"]: block for block in current_blocks}
    ledger_by_id = {block.get("id"): block for block in ledger_blocks}
    if set(current_by_id) != set(ledger_by_id):
        errors.append({"id": "SOURCE", "error": "source block IDs changed"})

    disposition_counts = {name: 0 for name in sorted(ALLOWED_DISPOSITIONS)}
    mapped = 0
    approved_omissions = 0

    for block_id, current in current_by_id.items():
        block = ledger_by_id.get(block_id)
        if block is None:
            continue
        if block.get("sha256") != current["sha256"]:
            errors.append({"id": block_id, "error": "block content hash changed"})

        disposition = block.get("disposition")
        page_ids = block.get("page_ids")
        if disposition not in ALLOWED_DISPOSITIONS:
            errors.append({"id": block_id, "error": "invalid or missing disposition"})
            continue
        disposition_counts[disposition] += 1

        if disposition == "user-approved-omit":
            approved_omissions += 1
            if not str(block.get("approval_note", "")).strip():
                errors.append({"id": block_id, "error": "approved omission lacks approval_note"})
            if not allow_approved_omissions:
                errors.append(
                    {"id": block_id, "error": "approved omission requires --allow-approved-omissions"}
                )
            continue

        if not isinstance(page_ids, list) or not page_ids or not all(
            isinstance(page_id, str) and page_id.strip() for page_id in page_ids
        ):
            errors.append({"id": block_id, "error": "retained block lacks page_ids"})
        else:
            mapped += 1

        if disposition in NOTE_REQUIRED and not str(block.get("retention_note", "")).strip():
            errors.append({"id": block_id, "error": "disposition requires retention_note"})

    total = len(current_blocks)
    report: dict[str, Any] = {
        "source": str(source_path),
        "ledger": str(ledger_path),
        "total_blocks": total,
        "mapped_blocks": mapped,
        "approved_omissions": approved_omissions,
        "unmapped_blocks": max(total - mapped - approved_omissions, 0),
        "invalid_blocks": len({error["id"] for error in errors if error["id"] != "SOURCE"}),
        "source_drift": source_drift,
        "coverage_percent": round(((mapped + approved_omissions) / total * 100), 2) if total else 100.0,
        "disposition_counts": disposition_counts,
        "errors": errors,
    }
    return report, not errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a new content ledger")
    init_parser.add_argument("source", type=Path)
    init_parser.add_argument("ledger", type=Path)

    audit_parser = subparsers.add_parser("audit", help="Audit an existing content ledger")
    audit_parser.add_argument("source", type=Path)
    audit_parser.add_argument("ledger", type=Path)
    audit_parser.add_argument("--report", type=Path)
    audit_parser.add_argument("--allow-approved-omissions", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "init":
        init_ledger(args.source, args.ledger)
        return 0

    report, passed = audit_ledger(
        args.source, args.ledger, args.allow_approved_omissions
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())

