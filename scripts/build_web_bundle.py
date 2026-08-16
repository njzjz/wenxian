"""Build the self-contained pure-Python bundle used by the web app."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tarfile
import tempfile
from importlib.metadata import PathDistribution
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_REQUIREMENTS_IN = ROOT / "web-requirements.in"
WEB_REQUIREMENTS_LOCK = ROOT / "web-requirements.lock"


def _locked_requirements(lock: Path = WEB_REQUIREMENTS_LOCK) -> list[str]:
    """Return the exact package pins recorded by the uv-generated lock file."""
    requirements = []
    for raw_line in lock.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            requirements.append(line)
    return requirements


def _sync_locked_dependencies(target: Path) -> None:
    """Install exactly the locked browser dependencies into ``target`` with uv."""
    subprocess.run(
        [
            "uv",
            "pip",
            "sync",
            str(WEB_REQUIREMENTS_LOCK),
            "--target",
            str(target),
        ],
        check=True,
    )


def _install_wenxian_wheel(target: Path, wheel: Path) -> None:
    """Overlay the current wenxian wheel without resolving dependencies again."""
    subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--target",
            str(target),
            "--no-deps",
            str(wheel),
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

        _sync_locked_dependencies(target)
        _install_wenxian_wheel(target, wheel)

        for cache in target.rglob("__pycache__"):
            shutil.rmtree(cache)
        for compiled in target.rglob("*.pyc"):
            compiled.unlink()
        shutil.rmtree(target / "bin", ignore_errors=True)

        manifest = {
            "format": 1,
            "packages": _versions(target),
            "requirements": _locked_requirements(),
            "requirements_lock": WEB_REQUIREMENTS_LOCK.name,
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
    """Build a web bundle from command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build_bundle(args.wheel, args.output)


if __name__ == "__main__":
    main()
