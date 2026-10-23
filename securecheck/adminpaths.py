"""HEAD-only hints for four common admin paths. Status codes only."""

from securecheck.constants import ADMIN_PATHS, HEAD_TIMEOUT_SECONDS

ADMIN_NOTE = (
    "Section 19 expects a responsible party to identify reasonably foreseeable "
    "risks. An answer from /admin, /wp-admin, /administrator, or /login is only "
    "a hint that a sign-in page may be reachable. Many businesses publish those "
    "addresses on purpose. This check does not try passwords and does not show "
    "whether the page is safe."
)

_QUIET = {404, 410}


def assess_admin(domain: str, rows: list[dict]) -> dict:
    evidence = [row["sentence"] for row in rows]
    errors = [row for row in rows if row["status"] is None]
    answered = [row for row in rows if row["status"] is not None and row["status"] not in _QUIET]
    quiet = [row for row in rows if row["status"] in _QUIET]
    if len(errors) == len(rows):
        status = "error"
        summary = "None of the four admin addresses could be checked."
    elif not answered and not errors:
        status = "ok"
        summary = (
            "None of /admin, /wp-admin, /administrator, or /login returned a page. "
            "This check only asked those four addresses."
        )
    elif answered:
        status = "attention"
        summary = (
            "This check sent HEAD only to /admin, /wp-admin, /administrator, and /login. "
            "At least one of those addresses answered. That is a hint to review who can open it, "
            "not a weakness by itself. Redirects were not followed and no sign-in was attempted."
        )
    else:
        status = "attention"
        summary = "Some of the four admin addresses could not be checked. The others did not return a page."
    if quiet and answered:
        pass
    return _result(
        status,
        summary,
        evidence,
        {"paths": rows, "timeout_seconds": HEAD_TIMEOUT_SECONDS},
    )


def check_admin(domain: str, http, paths=ADMIN_PATHS) -> dict:
    rows = []
    for path in paths:
        url = f"https://{domain}{path}"
        try:
            response = http.head(url)
        except Exception as exc:
            response = None
            error = str(exc)
            status = None
        else:
            error = response.error
            status = response.status
        if error and status is None:
            sentence = f"HEAD {path} could not be completed ({error})."
        elif status is None:
            sentence = f"HEAD {path} could not be completed."
        else:
            sentence = f"HEAD {path} returned {status}."
        rows.append({"path": path, "url": url, "status": status, "error": error, "sentence": sentence})
    return assess_admin(domain, rows)


def _result(status: str, summary: str, evidence: list[str], details: dict) -> dict:
    return {
        "id": "admin_paths",
        "title": "Exposed-admin hint",
        "status": status,
        "summary": summary,
        "popia_note": ADMIN_NOTE,
        "evidence": evidence,
        "details": details,
    }
