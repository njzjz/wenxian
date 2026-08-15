"""Tests for the Europe PMC feeder."""

from __future__ import annotations

from wenxian.feeder.europepmc import Europepmc
from wenxian.reference import Author, Reference


class _Response:
    status_code = 200

    def json(self):
        """Return a minimal Europe PMC response."""
        return {
            "resultList": {
                "result": [
                    {
                        "title": "A paper",
                        "pubYear": "2026",
                        "pageInfo": "12-18",
                        "doi": "10.1234/example",
                        "abstractText": "Abstract",
                        "authorList": {
                            "author": [{"firstName": "Ada", "lastName": "Lovelace"}]
                        },
                        "journalInfo": {
                            "volume": "4",
                            "issue": "2",
                            "journal": {"title": "Journal of Tests"},
                        },
                    }
                ]
            }
        }


class _NotFoundResponse:
    status_code = 503


class _EmptyResponse:
    status_code = 200

    def json(self):
        """Return a Europe PMC response without results."""
        return {"resultList": {"result": []}}


def test_from_pmid(monkeypatch):
    """Test converting a Europe PMC result to a reference."""
    monkeypatch.setattr(
        "wenxian.feeder.europepmc.SESSION.get", lambda *args, **kwargs: _Response()
    )

    assert Europepmc().from_pmid("37526163") == Reference(
        author=[Author(first="Ada", last="Lovelace")],
        title="A paper",
        journal="Journal of Tests",
        year=2026,
        volume=4,
        issue=2,
        pages=(12, 18),
        annote="Abstract",
        doi="10.1234/example",
    )


def test_from_pmid_ignores_missing_records(monkeypatch):
    """Test failed and empty Europe PMC responses are ignored."""
    monkeypatch.setattr(
        "wenxian.feeder.europepmc.SESSION.get",
        lambda *args, **kwargs: _NotFoundResponse(),
    )
    assert Europepmc().from_pmid("37526163") is None

    monkeypatch.setattr(
        "wenxian.feeder.europepmc.SESSION.get", lambda *args, **kwargs: _EmptyResponse()
    )
    assert Europepmc().from_pmid("37526163") is None


def test_from_result_uses_full_name_and_journal_fallbacks():
    """Test fallback fields in a Europe PMC result."""
    result = {
        "title": "Fallback metadata",
        "pubYear": "2025",
        "authorList": {"author": [{"fullName": "Grace Hopper"}]},
        "journalTitle": "Journal of Fallbacks",
        "journalInfo": {},
    }

    assert Europepmc()._from_result(result) == Reference(
        author=[Author(first="Grace", last="Hopper")],
        title="Fallback metadata",
        journal="Journal of Fallbacks",
        year=2025,
    )
