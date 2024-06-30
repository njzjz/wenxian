"""Feeder base class."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from xml.etree import ElementTree

    from wenxian.reference import Reference


class Feeder:
    """Feeder base class."""

    def from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI."""

    def from_arxiv(self, arxiv: str) -> Reference | None:
        """Fetch a reference from an arXiv identifier."""

    def from_pmid(self, pmid: str | int) -> Reference | None:
        """Fetch a reference from a PubMed identifier."""

    @overload
    def _int(self, string: int) -> int: ...

    @overload
    def _int(self, string: str) -> int | str: ...

    @overload
    def _int(self, string: None) -> None: ...

    def _int(self, string: str | int | None) -> int | str | None:
        """Convert string to int if it is a digit, return None if string is None."""
        if string is None:
            return None
        elif isinstance(string, int):
            return string
        elif isinstance(string, str):
            return int(string) if string.isdigit() else string
        raise ValueError(f"Invalid string: {string}")

    @overload
    def _pages(self, string: str) -> tuple[int]: ...

    @overload
    def _pages(self, string: None) -> None: ...

    def _pages(
        self, string: str | None
    ) -> tuple[int | str] | tuple[int | str, int | str] | None:
        """Convert a page string to a tuple of integers."""
        if string is None:
            return None
        page_list = tuple(self._int(s) for s in string.split("-"))
        if len(page_list) == 1 or len(page_list) == 2:
            return page_list
        raise ValueError(f"Invalid page string: {string}")

    @overload
    def _text(self, node: ElementTree.Element) -> str: ...

    @overload
    def _text(self, node: None) -> None: ...

    def _text(self, node: ElementTree.Element | None) -> str | None:
        """Read text from XML node, return None if node is None."""
        return "".join(node.itertext()).strip() if node is not None else None
