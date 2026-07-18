#!/usr/bin/env python3
"""Build a Factorio-ready Advanced Fluid Handling Continued archive."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
INFO = ROOT / "info.json"
MOD_NAME = "advanced-fluid-handling-continued"
LEGACY_NAMESPACE = b"__underground-pipe-pack__/"
CURRENT_NAMESPACE = b"__advanced-fluid-handling-continued__/"

EXCLUDED_TOP_LEVEL = {".git", ".github", "dist"}
EXCLUDED_NAMES = {".DS_Store", "__MACOSX", "__pycache__"}
EXCLUDED_FILES = {
    ".gitignore",
    "scripts/build_release.py",
    "scripts/build_afhc.py",
}

REQUIRED_FILES = {
    "LICENSE.txt",
    "README.md",
    "changelog.txt",
    "control.lua",
    "data.lua",
    "info.json",
    "locale/en/en.cfg",
    "scripts/rotate-and-toggle.lua",
}

FIXED_ZIP_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_metadata() -> dict[str, object]:
    try:
        metadata = json.loads(INFO.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Could not read info.json: {exc}")

    if metadata.get("name") != MOD_NAME:
        fail(f"info.json name must be {MOD_NAME}")
    if metadata.get("factorio_version") != "2.1":
        fail("info.json must target Factorio 2.1")

    version = metadata.get("version")
    if not isinstance(version, str) or not version:
        fail("info.json version is missing")

    dependencies = metadata.get("dependencies", [])
    if not isinstance(dependencies, list) or not any(
        isinstance(dep, str) and dep.startswith("base") and "2.1" in dep
        for dep in dependencies
    ):
        fail("info.json must depend on Factorio base 2.1")

    if "! underground-pipe-pack" not in dependencies:
        fail("info.json must be incompatible with underground-pipe-pack")

    return metadata


def should_package(path: Path) -> bool:
    if not path.is_file():
        return False

    relative = path.relative_to(ROOT)
    if relative.parts and relative.parts[0] in EXCLUDED_TOP_LEVEL:
        return False
    if any(part in EXCLUDED_NAMES for part in relative.parts):
        return False
    if relative.as_posix() in EXCLUDED_FILES:
        return False
    if relative.suffix.lower() in {".zip", ".pyc", ".pyo"}:
        return False
    return True


def packaged_bytes(path: Path) -> bytes:
    # Namespace replacement is deliberately byte based. Some inherited locale
    # files may not be UTF-8, and decoding/re-encoding them can corrupt them or
    # abort the build. Both namespace strings are plain ASCII and safe to
    # replace directly in arbitrary file bytes.
    return path.read_bytes().replace(LEGACY_NAMESPACE, CURRENT_NAMESPACE)


def add_file(archive: zipfile.ZipFile, source: Path, target: PurePosixPath) -> None:
    info = zipfile.ZipInfo(str(target), date_time=FIXED_ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, packaged_bytes(source))


def validate_archive(archive_path: Path, folder_name: str) -> None:
    prefix = f"{folder_name}/"
    expected_info = f"{folder_name}/info.json"

    with zipfile.ZipFile(archive_path, "r") as archive:
        names = archive.namelist()
        if not names:
            fail("Archive is empty")
        if any(not name.startswith(prefix) for name in names):
            fail("Archive contains files outside its Factorio root folder")
        if {PurePosixPath(name).parts[0] for name in names} != {folder_name}:
            fail(f"Archive must contain exactly one root folder named {folder_name}")
        if expected_info not in names:
            fail(f"Archive is missing {expected_info}")
        if len(names) != len(set(names)):
            fail("Archive contains duplicate paths")
        if archive.testzip() is not None:
            fail("Archive integrity test failed")

        stale = []
        for name in names:
            payload = archive.read(name)
            if LEGACY_NAMESPACE in payload:
                stale.append(name)
        if stale:
            fail("Legacy mod namespace remains in: " + ", ".join(stale))

        try:
            packaged_info = json.loads(archive.read(expected_info).decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            fail(f"Packaged info.json is invalid: {exc}")
        if packaged_info.get("name") != MOD_NAME:
            fail("Packaged info.json has the wrong mod name")


def main() -> int:
    metadata = load_metadata()

    missing = sorted(path for path in REQUIRED_FILES if not (ROOT / path).is_file())
    if missing:
        fail("Required files missing: " + ", ".join(missing))

    version = str(metadata["version"])
    folder_name = f"{MOD_NAME}_{version}"
    archive_path = DIST / f"{folder_name}.zip"
    checksum_path = DIST / f"{folder_name}.zip.sha256"

    files = sorted(
        (path for path in ROOT.rglob("*") if should_package(path)),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    with zipfile.ZipFile(
        archive_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for source in files:
            relative = PurePosixPath(source.relative_to(ROOT).as_posix())
            add_file(archive, source, PurePosixPath(folder_name) / relative)

    validate_archive(archive_path, folder_name)

    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    checksum_path.write_text(f"{digest}  {archive_path.name}\n", encoding="utf-8")

    print(f"Mod: {metadata.get('title', MOD_NAME)}")
    print(f"Internal name: {MOD_NAME}")
    print(f"Version: {version}")
    print(f"Packaged files: {len(files)}")
    print(f"Created: {archive_path.relative_to(ROOT)}")
    print(f"Created: {checksum_path.relative_to(ROOT)}")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
