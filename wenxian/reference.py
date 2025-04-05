"""Reference class for generating BibTeX entries."""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass

import unidecode
from pyiso4.ltwa import Abbreviate
from pylatexenc.latexencode import unicode_to_latex

abbreviator = Abbreviate.create()
XML_CLEANER = re.compile(r"<\/?[^<>]+>")
"""Regex to remove XML tags."""


def remove_xml_tags(text: str) -> str:
    """Remove XML tags.

    Parameters
    ----------
    text : str
        A text string.

    Returns
    -------
    str
        A text string without XML tags.
    """
    return XML_CLEANER.sub("", text)


@dataclass
class Author:
    """Author name."""

    first: str | None
    last: str | None
    suffix: str | None = None

    def __str__(self) -> str:
        """Generate a name string."""
        if self.first is None or self.last is None:
            raise ValueError(
                f"First name ({self.first}) or last name ({self.last}) is missing."
            )
        if self.suffix is not None:
            return f"{self.first} {{{self.last} {self.suffix}}}"
        elif " " in self.last:
            return f"{self.first} {{{self.last}}}"
        return f"{self.first} {self.last}"


@dataclass
class Reference:
    """A reference to a scholarly article."""

    author: list[Author] | None = None
    title: str | None = None
    journal: str | None = None
    year: int | None = None
    volume: int | str | None = None
    issue: int | str | None = None
    pages: tuple[int] | tuple[int, int] | str | None = None
    annote: str | None = None
    doi: str | None = None

    @property
    def journal_abbr(self) -> str | None:
        """Abbreviated journal name."""
        if self.journal is None:
            return None
        if self.journal in {"arXiv", "ChemRxiv"}:
            # special case
            return self.journal
        journal_title = self.journal.title()
        if journal_title.startswith("Npj"):
            # special case
            journal_title = journal_title.replace("Npj", "npj")
        abbr = abbreviator(journal_title, remove_part=True)
        # workaround to fix the missing E, e.g. Phys. Rev. E
        # https://github.com/pierre-24/pyiso4/issues/13
        # Example: 10.1103/PhysRevE.108.055310
        if self.journal.title().endswith(" E") and not abbr.endswith(" E"):
            abbr += " E"
        if abbr.replace(",", ".") == self.journal.title():
            # assume it is already abbreviated, cannot handle cases like "J. Chem. Phys."
            # https://github.com/pierre-24/pyiso4/issues/11
            # Example: 10.1021/acs.jpcc.3c05522
            # when it contains ., it may not be abbreviated
            # Example: 10.1021/acs.jpcb.3c05928
            return self.journal.title()
        return abbr

    @property
    def key(self) -> str:
        """Generate a BibTeX key."""
        if self.author is None or len(self.author) == 0:
            # 10.1126/science.288.5473.1950
            last = "NoAuthor"
        elif self.author[0].last is None:
            last = "NoLastName"
        else:
            last = unidecode.unidecode(self.author[0].last).replace(" ", "")
        journal_abbr = self.journal_abbr
        if journal_abbr is None:
            raise ValueError("No journal is found.")
        if self.pages is None:
            first_page: str | int | None = None
        elif isinstance(self.pages, tuple):
            first_page = self.pages[0]
        else:
            first_page = self.pages
        key = "{last}_{journal}".format(
            last=last,
            journal=re.sub(r"[\ \-\.:,]", "", journal_abbr),
        )
        if self.year is not None:
            key += f"_{self.year}"
        if self.volume is not None:
            key += f"_v{self.volume}"
        if first_page is not None:
            key += f"_p{first_page}"
        # special characters are not allowed anywhere in the key, not only in journal
        # https://tex.stackexchange.com/a/96918/262109
        key = re.sub(r"""[\ "#%'\(\),\=\{\}]""", "", key)
        return key

    @property
    def bibtex(self) -> str:
        """Generate a BibTeX entry."""
        if self.author is None:
            author_string = None
        else:
            author_string = " and ".join(str(aa) for aa in self.author)
        if self.pages is None:
            page_string = None
        elif isinstance(self.pages, tuple):
            page_string = "--".join(str(x) for x in self.pages)
        else:
            page_string = str(self.pages)

        # See https://us.mirrors.cicku.me/ctan/macros/latex/contrib/biblatex/doc/biblatex.pdf
        data = {
            "author": author_string,
            "title": self.title,
            "journal": self.journal_abbr,
            "year": self.year,
            "volume": self.volume,
            "number": self.issue,
            "pages": page_string,
            "doi": self.doi,
            "abstract": self.annote,
        }
        start = f"@Article{{{self.key},"
        end = "}\n"
        items = [start]
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                valuestr = str(value)
            else:
                valuestr = ("\n" + " " * 13).join(
                    textwrap.wrap(
                        unidecode.unidecode(
                            unicode_to_latex(
                                remove_xml_tags(value),
                                non_ascii_only=False,
                                replacement_latex_protection="braces-all",
                            )
                        ),
                        70,
                    )
                )
                if key == "author":
                    # prevent {} in author that is used to split first and last name
                    # be escaped
                    valuestr = valuestr.replace(r"{\{}", r"{").replace(r"{\}}", r"}")
                if key == "title":
                    valuestr = f"{{{{{valuestr}}}}}"
                else:
                    valuestr = f"{{{valuestr}}}"
            valuestr += ","
            keystr = " " * 4 + (key + " =").ljust(11, " ")
            items.append(keystr + valuestr)
        items.append(end)
        return "\n".join(items)

    def __or__(self, other: Reference | None) -> Reference:
        """Combine two references."""
        if other is None:
            return self
        return Reference(
            author=self.author or other.author,
            title=self.title or other.title,
            journal=self.journal or other.journal,
            year=self.year or other.year,
            volume=self.volume or other.volume,
            issue=self.issue or other.issue,
            pages=self.pages or other.pages,
            annote=self.annote or other.annote,
            doi=self.doi or other.doi,
        )

    def is_empty(self) -> bool:
        """Check if the reference is empty."""
        return all(
            (
                self.author is None,
                self.title is None,
                self.journal is None,
                self.year is None,
                self.volume is None,
                self.issue is None,
                self.pages is None,
                self.annote is None,
                self.doi is None,
            )
        )
