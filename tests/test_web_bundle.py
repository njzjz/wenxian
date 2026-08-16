"""Tests for the web bundle builder."""

from __future__ import annotations

import json
import tarfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def test_web_bundle_uses_uv_locked_runtime_requirements():
    """Keep the browser bundle aligned with the pinned pure-Python runtime deps."""
    from scripts.build_web_bundle import (
        WEB_REQUIREMENTS_IN,
        WEB_REQUIREMENTS_LOCK,
        _locked_requirements,
    )

    declared = {
        line.strip()
        for line in WEB_REQUIREMENTS_IN.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert declared == {
        "requests",
        "pylatexenc==3.0a21",
        "unidecode",
        "pyiso4",
    }

    locked = _locked_requirements(WEB_REQUIREMENTS_LOCK)
    assert "requests==2.34.2" in locked
    assert "pylatexenc==3.0a21" in locked
    assert "unidecode==1.4.0" in locked
    assert "pyiso4==0.1.6" in locked
    assert "certifi==2026.7.22" in locked
    assert "charset-normalizer==3.5.1" in locked
    assert "idna==3.18" in locked
    assert "urllib3==2.7.0" in locked
    assert all("==" in requirement for requirement in locked)
    assert all("ratelimiter" not in requirement for requirement in locked)


def test_web_bundle_manifest_format(tmp_path: Path):
    """Document the metadata contract consumed by release diagnostics."""
    archive = tmp_path / "bundle.tar.gz"
    manifest = {
        "format": 1,
        "packages": {"wenxian": "0.0.test"},
        "requirements": ["requests==2.34.2"],
        "requirements_lock": "web-requirements.lock",
    }
    manifest_path = tmp_path / "wenxian-web-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with tarfile.open(archive, "w:gz") as bundle:
        bundle.add(manifest_path, arcname=manifest_path.name)

    with tarfile.open(archive, "r:gz") as bundle:
        extracted_file = bundle.extractfile("wenxian-web-manifest.json")
        assert extracted_file is not None
        extracted = json.load(extracted_file)

    assert extracted["format"] == 1
    assert extracted["packages"]["wenxian"] == "0.0.test"
    assert extracted["requirements_lock"] == "web-requirements.lock"
