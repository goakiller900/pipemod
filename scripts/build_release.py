#!/usr/bin/env python3
"""Validate and build a deterministic Factorio-ready AFHC release archive."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import NoReturn

ROOT = Path(__file__).resolve().parents[1]
INFO_PATH = ROOT / "info.json"
CHANGELOG_PATH = ROOT / "changelog.txt"
DIST_DIR = ROOT / "dist"

MOD_NAME = "advanced-fluid-handling-continued"
LEGACY_MOD_NAME = "underground-pipe-pack"
LEGACY_NAMESPACE = f"__{LEGACY_MOD_NAME}__/"
CURRENT_NAMESPACE = f"__{MOD_NAME}__/"

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
EXCLUDED_TOP_LEVEL = {".git", ".github", "dist"}
EXCLUDED_NAMES = {".DS_Store", "__MACOSX", "__pycache__"}
EXCLUDED_FILES = {".gitignore", "scripts/build_release.py"}
TEXT_EXTENSIONS = {".lua", ".cfg", ".json", ".md", ".txt", ".yml", ".yaml"}
NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
CHANGELOG_VERSION_PATTERN = re.compile(r"^Version:\s*(\d+\.\d+\.\d+)\s*$", re.MULTILINE)
REQUIRE_PATTERN = re.compile(r"require\s*\(?\s*[\"']([^\"']+)[\"']\s*\)?")
ASSET_PATTERN = re.compile(r"[\"']__(?P<mod>[A-Za-z0-9_-]+)__/(?P<path>[^\"']+)[\"']")
FIXED_ZIP_TIMESTAMP = (2020, 1, 1, 0, 0, 0)

FORBIDDEN_SOURCE_PATTERNS = {
    r"\bhardness\s*=": "obsolete MinableProperties.hardness field",
    r"\bbase_area\s*=": "obsolete FluidBox.base_area field",
    r"\btwo_direction_only\s*=": "unsupported ValvePrototype.two_direction_only field",
    r"fluid_box\s*\.\s*hide_connection_info\s*=": "FluidBox.hide_connection_info belongs on PipeConnectionDefinition",
    r"\bpipe\s*\.\s*underground_collision_mask\s*=": "unsupported PipePrototype.underground_collision_mask field",
    r"\bpipe\s*\.\s*auto_recycle\s*=": "unsupported PipePrototype.auto_recycle field",
}


def fail(message: str) -> NoReturn:
    raise SystemExit(f"ERROR: {message}")


def load_metadata() -> dict[str, object]:
    try:
        metadata = json.loads(INFO_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail("Missing info.json")
    except json.JSONDecodeError as exc:
        fail(f"Invalid info.json: {exc}")

    for field in ("name", "version", "title", "factorio_version", "author"):
        value = metadata.get(field)
        if not isinstance(value, str) or not value.strip():
            fail(f"info.json field '{field}' must be a non-empty string")

    name = str(metadata["name"])
    version = str(metadata["version"])
    if not NAME_PATTERN.fullmatch(name):
        fail("info.json name may contain only letters, digits, underscores and hyphens")
    if name != MOD_NAME:
        fail(f"AFHC internal mod name must be {MOD_NAME}")
    if not VERSION_PATTERN.fullmatch(version):
        fail("info.json version must use MAJOR.MINOR.PATCH")
    if metadata["factorio_version"] != "2.1":
        fail("AFHC must target Factorio 2.1")

    dependencies = metadata.get("dependencies")
    if not isinstance(dependencies, list):
        fail("info.json dependencies must be an array")
    if not any(isinstance(v, str) and re.match(r"^base\s*>=\s*2\.1(?:\D|$)", v) for v in dependencies):
        fail("info.json must depend on base >= 2.1")
    if f"! {LEGACY_MOD_NAME}" not in dependencies:
        fail(f"AFHC must declare incompatibility with {LEGACY_MOD_NAME} to avoid prototype collisions")
    if len(dependencies) != len(set(dependencies)):
        fail("info.json contains duplicate dependencies")
    return metadata


def validate_changelog(version: str) -> None:
    try:
        text = CHANGELOG_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail("Missing changelog.txt")
    match = CHANGELOG_VERSION_PATTERN.search(text)
    if not match:
        fail("changelog.txt does not contain a Version entry")
    if match.group(1) != version:
        fail(f"Top changelog version {match.group(1)} does not match info.json {version}")


def strip_lua_comments(text: str) -> str:
    text = re.sub(r"--\[(=*)\[.*?\]\1\]", "", text, flags=re.DOTALL)
    return re.sub(r"--[^\n]*", "", text)


def resolve_module(source: Path, module: str) -> bool:
    if module.startswith("__") or module == "util":
        return True
    relative = Path(*module.replace(".", "/").split("/"))
    candidates = (
        ROOT / relative.with_suffix(".lua"),
        ROOT / relative / "init.lua",
        source.parent / relative.with_suffix(".lua"),
        source.parent / relative / "init.lua",
    )
    return any(candidate.is_file() for candidate in candidates)


def validate_lua_requires() -> None:
    missing: list[str] = []
    for lua_path in sorted(ROOT.rglob("*.lua")):
        text = strip_lua_comments(lua_path.read_text(encoding="utf-8"))
        for module in REQUIRE_PATTERN.findall(text):
            if not resolve_module(lua_path, module):
                missing.append(f"{lua_path.relative_to(ROOT)}: {module}")
    if missing:
        fail("Missing Lua modules: " + ", ".join(missing))


def validate_removed_fields() -> None:
    failures: list[str] = []
    for lua_path in sorted(ROOT.rglob("*.lua")):
        text = strip_lua_comments(lua_path.read_text(encoding="utf-8"))
        for pattern, description in FORBIDDEN_SOURCE_PATTERNS.items():
            if re.search(pattern, text):
                failures.append(f"{lua_path.relative_to(ROOT)}: {description}")
    if failures:
        fail("Factorio 2.1 source checks failed: " + "; ".join(failures))


def transformed_text(source: Path) -> str:
    text = source.read_text(encoding="utf-8")
    return text.replace(LEGACY_NAMESPACE, CURRENT_NAMESPACE)


def validate_asset_paths() -> None:
    missing: list[str] = []
    for source in sorted(ROOT.rglob("*")):
        if not source.is_file() or source.suffix.lower() not in TEXT_EXTENSIONS or ".git" in source.parts:
            continue
        text = transformed_text(source)
        for match in ASSET_PATTERN.finditer(text):
            if match.group("mod") != MOD_NAME:
                continue
            referenced_path = match.group("path")
            asset_path = PurePosixPath(referenced_path)
            if referenced_path.endswith("/") or ".." in asset_path.parts:
                continue
            if asset_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".ogg", ".wav", ".flac", ".json", ".lua"}:
                continue
            if not (ROOT / asset_path).is_file():
                missing.append(f"{source.relative_to(ROOT)} -> {referenced_path}")
    if missing:
        fail("Missing self-referenced assets: " + ", ".join(missing))


def validate_source(metadata: dict[str, object]) -> None:
    missing = sorted(path for path in REQUIRED_FILES if not (ROOT / path).is_file())
    if missing:
        fail("Required mod files are missing: " + ", ".join(missing))
    validate_lua_requires()
    validate_removed_fields()
    validate_asset_paths()


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


def package_bytes(source: Path) -> bytes:
    if source.suffix.lower() not in TEXT_EXTENSIONS:
        return source.read_bytes()
    return transformed_text(source).encode("utf-8")


def add_file_to_zip(archive: zipfile.ZipFile, source: Path, archive_path: PurePosixPath) -> None:
    info = zipfile.ZipInfo(str(archive_path), date_time=FIXED_ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, package_bytes(source))


def validate_archive(archive_path: Path, folder_name: str) -> None:
    expected_prefix = f"{folder_name}/"
    expected_info = f"{folder_name}/info.json"
    stale: list[str] = []
    with zipfile.ZipFile(archive_path, mode="r") as archive:
        names = archive.namelist()
        if not names:
            fail("Archive is empty")
        if any(not name.startswith(expected_prefix) for name in names):
            fail("Archive contains entries outside the required root folder")
        if {PurePosixPath(name).parts[0] for name in names} != {folder_name}:
            fail(f"Archive must contain exactly one root folder named {folder_name}")
        if expected_info not in names:
            fail(f"Archive does not contain {expected_info}")
        if len(names) != len(set(names)):
            fail("Archive contains duplicate paths")
        for name in names:
            if PurePosixPath(name).suffix.lower() in TEXT_EXTENSIONS:
                text = archive.read(name).decode("utf-8", errors="replace")
                if LEGACY_NAMESPACE in text:
                    stale.append(name)
        if stale:
            fail("Packaged archive still contains legacy asset namespaces: " + ", ".join(stale))
        bad_file = archive.testzip()
        if bad_file is not None:
            fail(f"Archive integrity check failed at {bad_file}")


def build_archive(metadata: dict[str, object]) -> tuple[Path, Path, str, int]:
    name = str(metadata["name"])
    version = str(metadata["version"])
    folder_name = f"{name}_{version}"
    archive_path = DIST_DIR / f"{folder_name}.zip"
    checksum_path = DIST_DIR / f"{folder_name}.zip.sha256"
    source_files = sorted((p for p in ROOT.rglob("*") if should_package(p)), key=lambda p: p.relative_to(ROOT).as_posix())

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source in source_files:
            relative = PurePosixPath(source.relative_to(ROOT).as_posix())
            add_file_to_zip(archive, source, PurePosixPath(folder_name) / relative)

    validate_archive(archive_path, folder_name)
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    checksum_path.write_text(f"{digest}  {archive_path.name}\n", encoding="utf-8")
    return archive_path, checksum_path, digest, len(source_files)


def main() -> int:
    metadata = load_metadata()
    version = str(metadata["version"])
    validate_changelog(version)
    validate_source(metadata)
    archive_path, checksum_path, digest, count = build_archive(metadata)
    print(f"Mod name: {metadata['name']}")
    print(f"Title: {metadata['title']}")
    print(f"Version: {version}")
    print(f"Factorio version: {metadata['factorio_version']}")
    print(f"Packaged files: {count}")
    print(f"Created: {archive_path.relative_to(ROOT)}")
    print(f"Created: {checksum_path.relative_to(ROOT)}")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
