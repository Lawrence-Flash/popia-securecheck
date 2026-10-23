"""Security headers on one homepage HTTPS response."""

from securecheck.http_client import Response

HEADERS_NOTE = (
    "Section 19 does not name HSTS, Content-Security-Policy, X-Content-Type-Options, "
    "framing controls, Referrer-Policy, or Permissions-Policy. They are widely used "
    "browser safeguards for a site that serves personal information. A missing header "
    "is a gap in this read-only check. It is not, by itself, a breach of POPIA."
)


def _clip(value: str, limit: int = 180) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _has_frame_ancestors(values: list[str]) -> bool:
    for value in values:
        for directive in value.split(";"):
            tokens = directive.strip().split()
            if tokens and tokens[0].lower() == "frame-ancestors":
                return True
    return False


def _hsts_disabled(value: str) -> bool:
    for part in value.split(";"):
        name, separator, number = part.strip().partition("=")
        if separator and name.lower() == "max-age" and number.strip() == "0":
            return True
    return False


def assess_headers(response: Response) -> dict:
    if response.error and response.status is None:
        return _result(
            "error",
            "The homepage could not be read over HTTPS, so the security headers were not checked.",
            [f"Connection: {response.error}"],
            {"error": response.error},
        )
    if response.error == "The homepage redirected too many times.":
        return _result(
            "error",
            "The homepage redirected too many times, so the security headers were not checked.",
            [response.error],
            {"error": response.error, "url": response.url, "status_code": response.status},
        )

    items = _items(response)
    weak = [item for item in items if item["state"] == "weak"]
    missing = [item for item in items if item["state"] == "missing"]
    if response.stopped_redirect:
        status = "attention"
        summary = (
            "The homepage redirected to a different site, and this check did not follow it. "
            "The header notes below are for that redirect response only."
        )
    elif not missing and not weak:
        status = "ok"
        summary = "The homepage HTTPS response included all six header controls this check looks for."
    elif len(missing) == len(items) and not weak:
        status = "missing"
        summary = "The homepage HTTPS response did not include any of the six header controls this check looks for."
    else:
        status = "attention"
        names = [item["name"] for item in missing]
        summary = "The homepage HTTPS response is missing " + _join(names) + "." if names else (
            "The homepage HTTPS response includes a header this check treats as weak."
        )
        if weak and names:
            summary += " Another header is present but weak."
        elif weak and not names:
            summary = "The homepage HTTPS response includes a header this check treats as weak."

    evidence = []
    if response.stopped_redirect:
        evidence.append(f"Redirect to another site was not followed: {response.stopped_redirect}")
    evidence.append(f"URL: {response.url}")
    if response.status is not None:
        evidence.append(f"HTTPS status: {response.status}")
    evidence.extend(item["sentence"] for item in items)
    return _result(status, summary, evidence, {"url": response.url, "status_code": response.status, "items": items})


def _items(response: Response) -> list[dict]:
    hsts = response.values("strict-transport-security")
    csp = response.values("content-security-policy")
    nosniff = response.values("x-content-type-options")
    frame = response.values("x-frame-options")
    referrer = response.values("referrer-policy")
    permissions = response.values("permissions-policy")
    items = [
        _hsts_item(hsts),
        _csp_item(csp),
        _nosniff_item(nosniff),
        _framing_item(frame, csp),
        _referrer_item(referrer),
        _permissions_item(permissions, response.values("feature-policy")),
    ]
    return items


def _hsts_item(values: list[str]) -> dict:
    if not values:
        return _item("hsts", "Strict-Transport-Security (HSTS)", "missing", None, "HSTS is not set, so browsers are not told to keep using HTTPS for this site.")
    shown = _clip(values[0])
    if _hsts_disabled(values[0]):
        return _item("hsts", "Strict-Transport-Security (HSTS)", "weak", shown, "HSTS is present but max-age is 0, which turns it off.")
    return _item("hsts", "Strict-Transport-Security (HSTS)", "present", shown, "HSTS is present.")


def _csp_item(values: list[str]) -> dict:
    if not values:
        return _item("csp", "Content-Security-Policy", "missing", None, "No content security policy was sent.")
    return _item("csp", "Content-Security-Policy", "present", _clip(values[0]), "A content security policy is present.")


def _nosniff_item(values: list[str]) -> dict:
    if not values:
        return _item("nosniff", "X-Content-Type-Options", "missing", None, "X-Content-Type-Options is missing.")
    shown = _clip(values[0])
    if values[0].strip().lower() == "nosniff":
        return _item("nosniff", "X-Content-Type-Options", "present", shown, "X-Content-Type-Options is nosniff.")
    return _item("nosniff", "X-Content-Type-Options", "weak", shown, f"X-Content-Type-Options is {shown!r}, not nosniff.")


def _framing_item(frame: list[str], csp: list[str]) -> dict:
    if frame:
        shown = _clip(frame[0])
        return _item(
            "framing",
            "X-Frame-Options or CSP frame-ancestors",
            "present",
            shown,
            f"A framing control is present (X-Frame-Options: {shown}).",
        )
    if _has_frame_ancestors(csp):
        return _item(
            "framing",
            "X-Frame-Options or CSP frame-ancestors",
            "present",
            "frame-ancestors",
            "A framing control is present (CSP frame-ancestors).",
        )
    return _item(
        "framing",
        "X-Frame-Options or CSP frame-ancestors",
        "missing",
        None,
        "Neither X-Frame-Options nor CSP frame-ancestors was set.",
    )


def _referrer_item(values: list[str]) -> dict:
    if not values:
        return _item("referrer", "Referrer-Policy", "missing", None, "Referrer-Policy is missing.")
    shown = _clip(values[0])
    if shown.lower() == "unsafe-url":
        return _item(
            "referrer",
            "Referrer-Policy",
            "weak",
            shown,
            "Referrer-Policy is unsafe-url, which sends the full page address to other sites.",
        )
    return _item("referrer", "Referrer-Policy", "present", shown, f"Referrer-Policy is present ({shown}).")


def _permissions_item(values: list[str], feature_policy: list[str]) -> dict:
    if values:
        return _item("permissions", "Permissions-Policy", "present", _clip(values[0]), "Permissions-Policy is present.")
    sentence = "Permissions-Policy is not set."
    if feature_policy:
        sentence += " An older Feature-Policy header is present. This check looks for Permissions-Policy."
    return _item("permissions", "Permissions-Policy", "missing", None, sentence)


def _item(item_id: str, name: str, state: str, value: str | None, sentence: str) -> dict:
    return {"id": item_id, "name": name, "state": state, "value": value, "sentence": sentence}


def _join(names: list[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def _result(status: str, summary: str, evidence: list[str], details: dict) -> dict:
    return {
        "id": "headers",
        "title": "Security headers",
        "status": status,
        "summary": summary,
        "popia_note": HEADERS_NOTE,
        "evidence": evidence,
        "details": details,
    }
