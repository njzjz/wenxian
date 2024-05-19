"""Identifier type and regex."""

from __future__ import annotations

import re
from enum import Enum


class Identifier(Enum):
    """Identifier type."""

    DOI = "DOI"
    PMID = "PMID"
    ARXIV = "arXiv"


REGEX: dict[Identifier, re.Pattern] = {
    Identifier.DOI: re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE),
    Identifier.PMID: re.compile(r"\b\d{8}\b"),
    Identifier.ARXIV: re.compile(r"\d{4}\.\d{4,5}(v\d+)?"),
}
"""Regex for identifiers."""


def get_identifier_type(identifier: str) -> Identifier | None:
    """Get the type of an identifier."""
    for id_type, regex in REGEX.items():
        if regex.match(identifier):
            return id_type
    return None
