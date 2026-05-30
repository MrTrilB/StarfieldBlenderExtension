from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
import tokenize
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
RELEASE_TEMPLATE = ROOT / "SFGBDocs" / "ReleaseTemplate"
SOURCE_MAIN = ROOT / "scripts" / "starfield_blender_extension"
SOURCE_BATCH = ROOT / "scripts" / "tool_batch_process"
SOURCE_PHYSICS = ROOT / "scripts" / "tool_physics_editor"
SOURCE_PROFILER = ROOT / "profiler"
OUTPUT = ROOT / "temp_check_dist" / "starfield_blender_extension"

PHYSICS_DATA_FILES = (
    ROOT / "physics_data.bin",
    ROOT / "physics_data_debug.bin",
)

IGNORE_PATTERNS = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")


def log(message: str) -> None:
    print(f"[build-temp] {message}")


def ensure_exists(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {description}: {path}")


def copy_tree(src: Path, dst: Path) -> None:
    ensure_exists(src, "directory")
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=IGNORE_PATTERNS)


def copy_file(src: Path, dst: Path) -> None:
    ensure_exists(src, "file")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _remove_readonly(func, path, _exc_info) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clean_output() -> None:
    if OUTPUT.exists():
        log(f"Cleaning output directory: {OUTPUT}")
        shutil.rmtree(OUTPUT, onerror=_remove_readonly)
    OUTPUT.mkdir(parents=True, exist_ok=True)


def build_distribution() -> None:
    ensure_exists(RELEASE_TEMPLATE, "ReleaseTemplate directory")
    ensure_exists(SOURCE_MAIN, "main source directory")
    ensure_exists(SOURCE_BATCH, "batch tool source directory")
    ensure_exists(SOURCE_PHYSICS, "physics tool source directory")

    clean_output()

    # Main addon Python source (canonical source-of-truth)
    log("Copying primary addon source")
    copy_tree(SOURCE_MAIN, OUTPUT)

    # Runtime baseline from ReleaseTemplate (non-Python contract)
    log("Copying runtime baseline from ReleaseTemplate")
    copy_tree(RELEASE_TEMPLATE / "3rdparty", OUTPUT / "3rdparty")
    copy_tree(RELEASE_TEMPLATE / "Assets", OUTPUT / "assets")
    copy_tree(RELEASE_TEMPLATE / "Result", OUTPUT / "Result")
    copy_tree(RELEASE_TEMPLATE / "Temp", OUTPUT / "Temp")
    copy_file(RELEASE_TEMPLATE / "MeshConverter.dll", OUTPUT / "MeshConverter.dll")
    copy_file(RELEASE_TEMPLATE / "CALUMI.Animation.dll", OUTPUT / "CALUMI.Animation.dll")

    # Additional tool directories requested for inclusion in the test distribution
    log("Copying additional tool sources")
    copy_tree(SOURCE_BATCH, OUTPUT / "tool_batch_process")
    copy_tree(SOURCE_PHYSICS, OUTPUT / "tool_physics_editor")

    # Additional runtime files requested for inclusion
    log("Copying profiler and physics data files")
    copy_tree(SOURCE_PROFILER, OUTPUT / "profiler")
    for file_path in PHYSICS_DATA_FILES:
        copy_file(file_path, OUTPUT / file_path.name)


def python_files(root: Path) -> Iterable[Path]:
    return sorted(
        path
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def compile_python(output_root: Path) -> list[tuple[Path, Exception]]:
    errors: list[tuple[Path, Exception]] = []
    for file_path in python_files(output_root):
        try:
            with tokenize.open(str(file_path)) as source_file:
                source = source_file.read()
            compile(source, str(file_path), "exec")
        except Exception as exc:  # pragma: no cover - CLI helper
            errors.append((file_path, exc))
    return errors


def validate_distribution(compile_check: bool) -> None:
    ensure_exists(OUTPUT, "output directory")

    required_paths = [
        OUTPUT / "__init__.py",
        OUTPUT / "ui",
        OUTPUT / "operators",
        OUTPUT / "types",
        OUTPUT / "utils",
        OUTPUT / "assets",
        OUTPUT / "3rdparty",
        OUTPUT / "MeshConverter.dll",
        OUTPUT / "CALUMI.Animation.dll",
        OUTPUT / "profiler",
        OUTPUT / "physics_data.bin",
        OUTPUT / "physics_data_debug.bin",
        OUTPUT / "Result",
        OUTPUT / "Temp",
        OUTPUT / "tool_batch_process",
        OUTPUT / "tool_physics_editor",
    ]

    forbidden_nested = [
        OUTPUT / "3rdparty" / "3rdparty",
        OUTPUT / "assets" / "Assets",
        OUTPUT / "profiler" / "profiler",
    ]

    missing = [path for path in required_paths if not path.exists()]
    if missing:
        raise RuntimeError(
            "Missing required output paths:\n" + "\n".join(f" - {path}" for path in missing)
        )

    duplicates = [path for path in forbidden_nested if path.exists()]
    if duplicates:
        raise RuntimeError(
            "Found forbidden nested directories:\n"
            + "\n".join(f" - {path}" for path in duplicates)
        )

    if compile_check:
        log("Running recursive Python syntax validation")
        compile_errors = compile_python(OUTPUT)
        if compile_errors:
            formatted = "\n".join(
                f" - {path}: {exc}" for path, exc in compile_errors
            )
            raise RuntimeError(f"Python compile validation failed:\n{formatted}")

    log("Validation passed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and validate temp_check_dist/starfield_blender_extension"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Clean and rebuild temp distribution")
    build_parser.add_argument(
        "--compile",
        action="store_true",
        help="Run recursive py_compile validation after build",
    )

    validate_parser = subparsers.add_parser("validate", help="Validate existing temp distribution")
    validate_parser.add_argument(
        "--compile",
        action="store_true",
        help="Run recursive py_compile validation",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if args.command == "build":
            build_distribution()
            validate_distribution(compile_check=args.compile)
            log("Build completed successfully")
        elif args.command == "validate":
            validate_distribution(compile_check=args.compile)
            log("Validation completed successfully")
        else:  # pragma: no cover - argparse guards this
            raise RuntimeError(f"Unsupported command: {args.command}")
    except Exception as exc:  # pragma: no cover - CLI helper
        log(f"ERROR: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
