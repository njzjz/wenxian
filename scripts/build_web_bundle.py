"""Build the self-contained pure-Python bundle used by the web app."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from importlib.metadata import PathDistribution
from pathlib import Path

WEB_REQUIREMENTS = (
    "requests",
    "pylatexenc==3.0a21",
    "unidecode",
    "pyiso4",
)


def _install(target: Path, requirements: list[str]) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-compile",
            "--target",
            str(target),
            *requirements,
        ],
        check=True,
    )


def _versions(target: Path) -> dict[str, str]:
    versions = {}
    for metadata in target.glob("*.dist-info"):
        distribution = PathDistribution(metadata)
        name = distribution.metadata.get("Name")
        if name:
            versions[name] = distribution.version
    return dict(sorted(versions.items(), key=lambda item: item[0].lower()))


def build_bundle(wheel: Path, output: Path) -> None:
    """Build a gzipped site-packages archive from a wenxian wheel."""
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "site-packages"
        target.mkdir()

        _install(target, list(WEB_REQUIREMENTS))
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-compile",
                "--no-deps",
                "--target",
                str(target),
                str(wheel),
            ],
            check=True,
        )

        for cache in target.rglob("__pycache__"):
            shutil.rmtree(cache)
        for compiled in target.rglob("*.pyc"):
            compiled.unlink()
        shutil.rmtree(target / "bin", ignore_errors=True)

        manifest = {
            "format": 1,
            "packages": _versions(target),
            "requirements": list(WEB_REQUIREMENTS),
        }
        (target / "wenxian-web-manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        output.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(output, "w:gz", compresslevel=9) as archive:
            for path in sorted(target.rglob("*")):
                if path.is_file():
                    archive.add(path, arcname=path.relative_to(target))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build_bundle(args.wheel, args.output)


if __name__ == "__main__":
    main()
