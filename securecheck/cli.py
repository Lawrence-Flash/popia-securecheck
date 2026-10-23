"""Command line for ``python3 -m securecheck``."""

import argparse
import json
import pathlib
import sys

from securecheck.constants import DISCLAIMER, REFUSAL_MESSAGE
from securecheck.doh import DohClient
from securecheck.domain import DomainError
from securecheck.gate import AuthorisationRequired
from securecheck.http_client import HttpClient
from securecheck.report import build_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="securecheck",
        description=(
            "Read-only checks for a domain you own or are authorised to assess. "
            + DISCLAIMER
        ),
    )
    parser.add_argument("domain", help="Domain name, for example example.co.za")
    parser.add_argument(
        "--confirm-authorised",
        action="store_true",
        help=(
            "Confirm you own this domain or the owner has authorised you to check it. "
            "Required. Does not prove ownership."
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        default="securecheck-report.json",
        help="Where to write the JSON report. Use - for stdout. Default: securecheck-report.json",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.confirm_authorised is not True:
        print(REFUSAL_MESSAGE, file=sys.stderr)
        return 2
    try:
        report = build_report(
            args.domain,
            authorised=True,
            http=HttpClient(),
            doh=DohClient(),
        )
    except AuthorisationRequired as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except DomainError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output == "-":
        sys.stdout.write(text)
        return 0
    path = pathlib.Path(args.output)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        print(f"Could not write the report: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {path}", file=sys.stderr)
    return 0
