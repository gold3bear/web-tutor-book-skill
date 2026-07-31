#!/usr/bin/env python3
"""Generate a technical candidate-issue report for a tutorial PDF.

This script is intentionally not a final publication judge. Visual review,
source coverage, task completion, and time-sensitive fact checks remain
mandatory.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import statistics
import sys
from pathlib import Path


def load_dependencies():
    try:
        import pdfplumber
        from pypdf import PdfReader
    except ImportError as error:
        raise SystemExit(
            "audit_pdf.py requires pypdf and pdfplumber. Install them in the "
            "current Agent runtime, or perform equivalent PDF inspection with "
            "the tools already available in that environment."
        ) from error
    return PdfReader, pdfplumber


def flatten_outline_count(items) -> int:
    total = 0
    for item in items or []:
        if isinstance(item, list):
            total += flatten_outline_count(item)
        else:
            total += 1
    return total


def main() -> int:
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    parser = argparse.ArgumentParser(
        description="Create a technical quality audit JSON for a tutorial PDF."
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--min-body-font", type=float, default=9.0)
    parser.add_argument("--screenshot-text-threshold", type=int, default=160)
    args = parser.parse_args()

    if not args.pdf.is_file():
        parser.error(f"PDF not found: {args.pdf}")

    PdfReader, pdfplumber = load_dependencies()
    reader = PdfReader(str(args.pdf))
    root = reader.trailer["/Root"]
    metadata = {str(key): str(value) for key, value in (reader.metadata or {}).items()}
    pages = []
    candidates = []

    with pdfplumber.open(str(args.pdf)) as plumber_pdf:
        for index, (page, plumber_page) in enumerate(
            zip(reader.pages, plumber_pdf.pages), start=1
        ):
            text = page.extract_text() or ""
            sizes = [
                float(char["size"])
                for char in plumber_page.chars
                if char.get("size") is not None
            ]
            resources = page.get("/Resources") or {}
            xobjects = resources.get("/XObject") or {}
            image_count = 0
            for reference in xobjects.values():
                try:
                    if reference.get_object().get("/Subtype") == "/Image":
                        image_count += 1
                except Exception:
                    continue

            links = []
            for reference in page.get("/Annots") or []:
                try:
                    annotation = reference.get_object()
                    if annotation.get("/Subtype") != "/Link":
                        continue
                    action = annotation.get("/A") or {}
                    links.append(str(action.get("/URI") or annotation.get("/Dest") or ""))
                except Exception:
                    continue

            text_chars = len(text.strip())
            row = {
                "page": index,
                "text_chars": text_chars,
                "image_count": image_count,
                "link_count": len(links),
                "links": links,
                "min_font": round(min(sizes), 2) if sizes else None,
                "median_font": round(statistics.median(sizes), 2) if sizes else None,
                "max_font": round(max(sizes), 2) if sizes else None,
                "replacement_character_count": text.count("\ufffd"),
                "visible_markdown_candidates": sorted(
                    set(re.findall(r"```|\*\*|\[[^\]]+\]\([^)]+\)", text))
                ),
                "sample": re.sub(r"\s+", " ", text).strip()[:240],
            }
            pages.append(row)

            if text_chars == 0 and image_count == 0:
                candidates.append(
                    {"severity": "P0-candidate", "page": index, "issue": "blank-page"}
                )
            if image_count > 0 and text_chars < args.screenshot_text_threshold:
                candidates.append(
                    {
                        "severity": "P0-candidate",
                        "page": index,
                        "issue": "screenshot-dependent-content",
                        "note": "Visually confirm whether key instructions exist only inside images.",
                    }
                )
            if sizes and min(sizes) < args.min_body_font:
                candidates.append(
                    {
                        "severity": "P1-candidate",
                        "page": index,
                        "issue": "small-extractable-font",
                        "minimum_points": round(min(sizes), 2),
                    }
                )
            if text.count("\ufffd"):
                candidates.append(
                    {
                        "severity": "P0-candidate",
                        "page": index,
                        "issue": "replacement-characters",
                    }
                )
            if row["visible_markdown_candidates"]:
                candidates.append(
                    {
                        "severity": "P1-candidate",
                        "page": index,
                        "issue": "visible-markdown-syntax",
                        "matches": row["visible_markdown_candidates"],
                    }
                )

    try:
        outline_count = flatten_outline_count(reader.outline)
    except Exception:
        outline_count = 0

    title = metadata.get("/Title", "").strip()
    if not title:
        candidates.append(
            {"severity": "P1-candidate", "page": None, "issue": "missing-title-metadata"}
        )
    if len(reader.pages) > 3 and outline_count == 0:
        candidates.append(
            {"severity": "P2-candidate", "page": None, "issue": "missing-bookmarks"}
        )

    result = {
        "file": str(args.pdf.resolve()),
        "page_count": len(reader.pages),
        "metadata": metadata,
        "document": {
            "tagged": bool(root.get("/StructTreeRoot")),
            "language": str(root.get("/Lang") or ""),
            "outline_count": outline_count,
            "named_destination_count": len(reader.named_destinations),
            "attachment_names": list(reader.attachments.keys()),
        },
        "pages": pages,
        "candidate_issues": candidates,
        "requires_visual_review": True,
        "requires_task_completion_review": True,
        "requires_source_coverage_review": True,
        "requires_time_sensitive_fact_check": True,
        "verdict": "not-computed",
        "verdict_note": (
            "Use references/DOCUMENT-QUALITY-AUDIT.md. Automated candidates "
            "cannot establish publication fitness or content fidelity."
        ),
    }

    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(args.output)
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
