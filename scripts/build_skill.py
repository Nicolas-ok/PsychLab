#!/usr/bin/env python3
"""Build and check a portable PsychLab skill archive using the standard library."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "psychlab-skill-v1.2.zip"
DOCS = [
    "01_REASONING_REFERENCE.md",
    "02_INTERVENTIONS_REFERENCE.md",
    "03_ADVERSARIAL_EXAMPLES.md",
    "04_CLINICAL_REFERENCE.md",
    "05_CAREGIVER_AND_CONTINUITY_REFERENCE.md",
]
FRONTMATTER = """---
name: psychlab
description: Agente experimental de razonamiento psicologico. Usar ante consultas sobre emociones, patrones, decisiones, seguimiento longitudinal, dudas clinicas y apoyo a familiares; priorizar evidencia, incertidumbre, autonomia y seguridad.
---

"""
FOLDER = "psychlab/"


def files_to_package() -> dict[str, bytes]:
    core = (ROOT / "CORE_INSTRUCTIONS.md").read_text(encoding="utf-8")
    contents = {FOLDER + "SKILL.md": (FRONTMATTER + core).encode("utf-8")}
    for document in DOCS:
        contents[FOLDER + "references/" + document] = (ROOT / document).read_bytes()
    index = {
        "files": [{"name": p, "path": "references/" + p} for p in DOCS],
        "guidelines": (
            "Interpret paths relative to the folder containing SKILL.md; only use "
            "genuinely available context, and treat all example cases as synthetic."
        ),
    }
    contents[FOLDER + "lookup/knowledge-index.json"] = (
        json.dumps(index, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    return contents


def build() -> None:
    contents = files_to_package()
    with ZipFile(OUT, "w", compression=ZIP_STORED) as archive:
        for filename, data in contents.items():
            entry = ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_STORED
            archive.writestr(entry, data)
    print(f"Built {OUT.name} ({OUT.stat().st_size} bytes)")


def verify() -> None:
    expected = files_to_package()
    with ZipFile(OUT, "r") as archive:
        assert archive.testzip() is None, "Archive CRC check failed"
        actual = set(archive.namelist())
        assert actual == set(expected), f"Missing/extra entries: {actual ^ set(expected)}"
        for filename, data in expected.items():
            assert archive.read(filename) == data, f"Unexpected contents: {filename}"
    core = (ROOT / "CORE_INSTRUCTIONS.md").read_text(encoding="utf-8")
    clinical = (ROOT / "04_CLINICAL_REFERENCE.md").read_text(encoding="utf-8")
    examples = (ROOT / "03_ADVERSARIAL_EXAMPLES.md").read_text(encoding="utf-8")
    assert "05_CAREGIVER_AND_CONTINUITY_REFERENCE.md" in core
    assert "Time-aware safety formulation" in clinical
    assert all(f"CASE {i} " in examples for i in range(26, 33))
    print("Verified archive integrity, source correspondence and regression coverage")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="Check current ZIP")
    args = parser.parse_args()
    verify() if args.verify else build()
