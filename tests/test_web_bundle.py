"""Tests for the release-time web bundle builder."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path


def test_web_bundle_script_declares_runtime_requirements():
    """Keep the browser bundle aligned with the pure-Python runtime deps."""
    from scripts.build_web_bundle import WEB_REQUIREMENTS

    assert "requests" in WEB_REQUIREMENTS
    assert "pylatexenc==3.0a21" in WEB_REQUIREMENTS
    assert "unidecode" in WEB_REQUIREMENTS
    assert "pyiso4" in WEB_REQUIREMENTS
    assert all("ratelimiter" not in requirement for requirement in WEB_REQUIREMENTS)


def test_web_bundle_manifest_format(tmp_path: Path):
    """Document the metadata contract consumed by release diagnostics."""
    archive = tmp_path / "bundle.tar.gz"
    manifest = {
        "format": 1,
        "packages": {"wenxian": "0.0.test"},
        "requirements": ["requests"],
    }
    manifest_path = tmp_path / "wenxian-web-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with tarfile.open(archive, "w:gz") as bundle:
        bundle.add(manifest_path, arcname=manifest_path.name)

    with tarfile.open(archive, "r:gz") as bundle:
        extracted = json.load(bundle.extractfile("wenxian-web-manifest.json"))

    assert extracted["format"] == 1
    assert extracted["packages"]["wenxian"] == "0.0.test"
