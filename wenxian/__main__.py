"""Main entry point for the command line interface."""

from __future__ import annotations

import argparse
import sys

from wenxian.from_identifier import from_identifier
from wenxian.logger import logger


def cmd_from(
    *,
    IDENTIFIER: list[str],
    output: str | None = None,
    ignore_errors: bool = False,
    output_type: str = "bibtex",
    **kwargs,
):
    """Generate BibTeX from a identifier."""
    buff = []
    references = []
    for identifier in IDENTIFIER:
        try:
            ref = from_identifier(identifier.strip())
        except Exception as e:
            msg = f"Failed to fetch reference from {identifier}: {e}"
            if ignore_errors:
                logger.exception(msg)
                continue
            else:
                raise ValueError(msg) from e
        if ref is None or ref.is_empty():
            msg = f"Failed to fetch reference from {identifier}"
            if ignore_errors:
                logger.error(msg)
                continue
            else:
                raise ValueError(msg)
        references.append(ref)
        if output_type == "bibtex":
            buff.append(ref.bibtex)
        elif output_type == "markdown":
            buff.append(ref.markdown)
        else:
            raise ValueError(f"Unknown output type: {output_type}")
    if output is None:
        sys.stdout.write("\n".join(buff))
        return
    if output == 0:
        extension = {
            "bibtex": ".bib",
            "markdown": ".md",
        }.get(output_type)
        if extension is None:
            raise ValueError(f"Unknown output type: {output_type}")
        if len(references) == 1:
            output = f"{references[0].key}{extension}"
        else:
            output = f"references{extension}"
    with open(output, "w") as f:
        f.write("\n".join(buff))


def main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(description="Generate BibTeX.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    parser_from = subparsers.add_parser(
        "from",
        help="Generate BibTeX from a identifier.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser_from.add_argument(
        "IDENTIFIER",
        type=str,
        nargs="+",
        help="Identifier. Support DOI, PMID, and arXiv ID.",
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
    parser_from.add_argument(
        "--ignore-errors",
        action="store_true",
        help="Ignore errors and continue processing the rest identifiers.",
    )
    parser_from.add_argument(
        "--output_type",
        "--type",
        "-t",
        type=str,
        choices=[
            "bibtex",
            "markdown",
        ],
        default="bibtex",
        help="Output type.",
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
