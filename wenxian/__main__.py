"""Main entry point for the command line interface."""

from __future__ import annotations

import argparse

from wenxian.from_identifier import from_identifier


def cmd_from(
    *,
    IDENTIFIER: list[str],
    output: str | None = None,
    **kwargs,
):
    """Generate BibTeX from a identifier."""
    buff = []
    references = []
    for identifier in IDENTIFIER:
        ref = from_identifier(identifier)
        if ref is None:
            raise ValueError(f"Failed to fetch reference from {identifier}")
        references.append(ref)
        buff.append(ref.bibtex)
    if output is None:
        return
    if output == 0:
        if len(references) == 1:
            output = f"{references[0].key}.bib"
        else:
            output = "references.bib"
    with open(output, "w") as f:
        f.write("\n".join(buff))


def main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(description="Generate BibTeX.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    parser_from = subparsers.add_parser(
        "from", help="Generate BibTeX from a identifier."
    )
    parser_from.add_argument(
        "IDENTIFIER", type=str, nargs="+", help="Identifier. Only support DOI for now."
    )
    parser_from.add_argument(
        "-o",
        "--output",
        type=str,
        nargs="?",
        const=0,
        default=None,
        help=(
            "Output file. If not specified, print to stdout. If specified without a value, print"
            " to a file with item key (for a single entry) or references.bib (for multiple entries)."
        ),
    )
    parser_from.set_defaults(func=cmd_from)
    return parser


def main():
    """Execute main entry point."""
    parser = main_parser()
    args = parser.parse_args()
    args.func(**vars(args))


if __name__ == "__main__":
    main()
