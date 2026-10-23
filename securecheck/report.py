"""Build the JSON report. The authorisation gate runs before any check."""

from datetime import datetime, timezone

from securecheck.adminpaths import check_admin
from securecheck.constants import AUTHORISATION_NOTE, DISCLAIMER, LIMITATIONS, SCHEMA, TOOL_VERSION
from securecheck.domain import normalise_domain
from securecheck.emailsec import check_email
from securecheck.gate import require_authorised
from securecheck.headers import assess_headers
from securecheck.http_client import Response
from securecheck.privacy import assess_privacy
from securecheck.tls import probe_tls


def build_report(domain: str, *, authorised: bool, http, doh, tls_probe=probe_tls, now=None) -> dict:
    """Run the passive checks and return a JSON-ready report.

    ``authorised`` must be ``True``. Anything else raises before a client is used.
    """

    require_authorised(authorised)
    ascii_domain = normalise_domain(domain)
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)

    checks = [
        _guard("tls", "HTTPS and TLS", lambda: tls_probe(ascii_domain, now=moment)),
    ]
    try:
        page = http.get(f"https://{ascii_domain}/")
    except Exception as exc:
        page = Response(
            url=f"https://{ascii_domain}/",
            status=None,
            error=str(exc),
            method="GET",
        )
    checks.append(_guard("headers", "Security headers", lambda: assess_headers(page)))
    checks.append(_guard("privacy", "Privacy, POPIA, or PAIA link", lambda: assess_privacy(f"https://{ascii_domain}/", page)))
    checks.append(_guard("email", "SPF, DMARC, and DKIM", lambda: check_email(ascii_domain, doh)))
    checks.append(_guard("admin_paths", "Exposed-admin hint", lambda: check_admin(ascii_domain, http)))

    return {
        "schema": SCHEMA,
        "disclaimer": DISCLAIMER,
        "tool": "popia-securecheck",
        "tool_version": TOOL_VERSION,
        "generated_at": moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "domain": ascii_domain,
        "authorised": True,
        "authorisation_note": AUTHORISATION_NOTE,
        "limitations": list(LIMITATIONS),
        "checks": checks,
    }


def _guard(check_id: str, title: str, function):
    try:
        return function()
    except Exception as exc:
        message = f"This check could not be completed ({exc})."
        return {
            "id": check_id,
            "title": title,
            "status": "error",
            "summary": message,
            "popia_note": "",
            "evidence": [message],
            "details": {"error": str(exc)},
        }
