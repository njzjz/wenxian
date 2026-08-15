"""Tests for the DataCite feeder."""

from __future__ import annotations

from wenxian.feeder.datacite import Datacite
from wenxian.reference import Author, Reference


class _Response:
    status_code = 200

    def json(self):
        return {
            "data": {
                "attributes": {
                    "doi": "10.48550/arXiv.2304.09409",
                    "creators": [
                        {"givenName": "Ada", "familyName": "Lovelace"}
                    ],
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
