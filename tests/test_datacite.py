"""Tests for the DataCite feeder."""

from __future__ import annotations

from wenxian.feeder.datacite import Datacite
from wenxian.reference import Author, Reference


class _Response:
    status_code = 200

    def json(self):
        """Return a minimal DataCite response."""
        return {
            "data": {
                "attributes": {
                    "doi": "10.48550/arXiv.2304.09409",
                    "creators": [{"givenName": "Ada", "familyName": "Lovelace"}],
                    "titles": [{"title": "A preprint"}],
                    "publisher": "arXiv",
                    "publicationYear": 2023,
                    "types": {"bibtex": "article"},
                    "descriptions": [
                        {"descriptionType": "Abstract", "description": "Abstract"}
                    ],
                    "container": {},
                }
            }
        }


class _NotFoundResponse:
    status_code = 404


class _EmptyResponse:
    status_code = 200

    def json(self):
        """Return a DataCite response without DOI attributes."""
        return {"data": {}}


def test_from_arxiv(monkeypatch):
    """Test converting an arXiv DataCite record to a reference."""
    monkeypatch.setattr(
        "wenxian.feeder.datacite.SESSION.get", lambda *args, **kwargs: _Response()
    )

    assert Datacite().from_arxiv("2304.09409") == Reference(
        author=[Author(first="Ada", last="Lovelace")],
        title="A preprint",
        journal="arXiv",
        year=2023,
        pages="2304.09409",
        annote="Abstract",
        doi="10.48550/arXiv.2304.09409",
    )


def test_from_doi_ignores_missing_records(monkeypatch):
    """Test missing and empty DataCite records are ignored."""
    monkeypatch.setattr(
        "wenxian.feeder.datacite.SESSION.get",
        lambda *args, **kwargs: _NotFoundResponse(),
    )
    assert Datacite().from_doi("10.1234/missing") is None

    monkeypatch.setattr(
        "wenxian.feeder.datacite.SESSION.get", lambda *args, **kwargs: _EmptyResponse()
    )
    assert Datacite().from_doi("10.1234/empty") is None


def test_from_attributes_handles_name_and_type_fallbacks():
    """Test fallback creator names, pages, and unknown BibTeX types."""
    data = {
        "doi": "10.1234/example",
        "creators": [
            {"name": "Lovelace, Ada"},
            {"name": "Grace Hopper"},
        ],
        "titles": [{"title": "Fallback metadata"}],
        "publisher": "Example Publisher",
        "publicationYear": "2024",
        "types": {"bibtex": "unknown"},
        "descriptions": [{"descriptionType": "Other", "description": "Ignored"}],
        "container": {
            "volume": "2",
            "issue": "1",
            "firstPage": "10",
            "lastPage": "12",
        },
    }

    assert Datacite()._from_attributes(data, doi="10.1234/example") == Reference(
        author=[
            Author(first="Ada", last="Lovelace"),
            Author(first="Grace", last="Hopper"),
        ],
        title="Fallback metadata",
        journal="Example Publisher",
        year=2024,
        volume=2,
        issue=1,
        pages=(10, 12),
        doi="10.1234/example",
    )
