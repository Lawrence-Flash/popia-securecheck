"""SPF and DMARC TXT records, plus DKIM at a short list of common selectors."""

import re

from securecheck.constants import DKIM_SELECTORS
from securecheck.doh import DohError

EMAIL_NOTE = (
    "SPF, DKIM, and DMARC are not named in the Act. They make it harder for "
    "someone else to send mail that looks as if it came from this domain. That "
    "supports the section 19 confidentiality duty where the business sends "
    "personal information by email. A missing record is something to fix with "
    "the email host. It is not proof of a security compromise, and section 22 "
    "(breach notification) is a separate duty this check does not measure."
)

_ALL = re.compile(r"(?:^|\s)([+\-~?])?all(?=\s|$)", re.IGNORECASE)
_DMARC_P = re.compile(r"(?:^|;)\s*p\s*=\s*(none|quarantine|reject)\b", re.IGNORECASE)
_DKIM_KEY = re.compile(r"(?:^|;)p=[A-Za-z0-9+/=]{8,}")


def _shorten(text: str | None, limit: int = 180) -> str | None:
    if text is None:
        return None
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def spf_view(records: list[str]) -> dict:
    found = [record for record in records if record.lower().startswith("v=spf1")]
    if not found:
        return {
            "state": "missing",
            "record": None,
            "qualifier": None,
            "sentence": "No SPF TXT record (v=spf1) was published on this domain.",
        }
    if len(found) > 1:
        return {
            "state": "attention",
            "record": found[0],
            "qualifier": None,
            "sentence": "More than one SPF record was published. Receivers may treat that as no SPF.",
        }
    match = _ALL.search(found[0])
    qualifier = (match.group(1) or "+") if match else None
    sentences = {
        "-": "SPF is present and ends with -all, which tells receivers to reject mail from hosts the record does not list.",
        "~": "SPF is present and ends with ~all (a soft fail). Receivers can treat unlisted hosts as suspicious. This is a common setting.",
        "?": "SPF is present but ends with ?all, which is neutral and does not tell receivers to reject unlisted hosts.",
        "+": "SPF is present but ends with +all, which treats every host as allowed to send mail for this domain.",
    }
    sentence = sentences.get(
        qualifier,
        "SPF is present but has no all mechanism, so it does not say what to do with other hosts.",
    )
    state = "ok" if qualifier in {"-", "~"} else "attention"
    return {"state": state, "record": found[0], "qualifier": qualifier, "sentence": sentence}


def dmarc_view(records: list[str] | None, domain: str, error: str | None = None) -> dict:
    if error:
        return {
            "state": "error",
            "record": None,
            "policy": None,
            "sentence": f"The DMARC lookup failed ({error}).",
        }
    found = [record for record in records or [] if "v=dmarc1" in record.lower().replace(" ", "")]
    if not found:
        return {
            "state": "missing",
            "record": None,
            "policy": None,
            "sentence": f"No DMARC TXT record was published at _dmarc.{domain}.",
        }
    match = _DMARC_P.search(found[0])
    policy = match.group(1).lower() if match else None
    if policy == "reject":
        sentence = "DMARC is present with p=reject. Receivers are asked to reject mail that fails DMARC."
        state = "ok"
    elif policy == "quarantine":
        sentence = "DMARC is present with p=quarantine. Receivers are asked to treat failing mail as suspicious."
        state = "ok"
    elif policy == "none":
        sentence = "DMARC is present with p=none. That asks for reports and does not ask receivers to quarantine or reject mail."
        state = "attention"
    else:
        sentence = "DMARC is present but no p= policy was found."
        state = "attention"
    return {"state": state, "record": found[0], "policy": policy, "sentence": sentence}


def is_dkim(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    if "v=dkim1" in compact.lower():
        return True
    return _DKIM_KEY.search(compact) is not None


def check_email(domain: str, doh, selectors=DKIM_SELECTORS) -> dict:
    try:
        root_txt = doh.txt(domain)
    except DohError as exc:
        message = f"The DNS TXT lookup failed ({exc}). SPF, DMARC, and DKIM were not checked."
        return _result("error", message, [message], {"error": str(exc), "selectors_checked": list(selectors)})

    spf = spf_view(root_txt)
    dmarc_error = None
    dmarc_txt: list[str] | None = []
    try:
        dmarc_txt = doh.txt(f"_dmarc.{domain}")
    except DohError as exc:
        dmarc_error = str(exc)
        dmarc_txt = None
    dmarc = dmarc_view(dmarc_txt, domain, dmarc_error)

    found = []
    dkim_errors = []
    for selector in selectors:
        try:
            rows = doh.txt(f"{selector}._domainkey.{domain}")
        except DohError as exc:
            dkim_errors.append(f"{selector}: {exc}")
            continue
        for row in rows:
            if is_dkim(row):
                found.append({"selector": selector, "record": _shorten(row)})
                break

    if found:
        names = ", ".join(item["selector"] for item in found)
        label = "selectors" if len(found) > 1 else "selector"
        dkim_sentence = f"DKIM TXT records were found for {label}: {names}."
        dkim_state = "ok"
    else:
        dkim_sentence = (
            "No DKIM TXT record was found at the common selectors this check tries. "
            "A selector that is not in that list can still exist, so this is not proof that DKIM is absent."
        )
        dkim_state = "attention"
    if dkim_errors and not found:
        dkim_sentence += " Some selector lookups failed."

    parts = [spf, dmarc]
    if dmarc["state"] == "error" or (dkim_errors and not found and spf["state"] == "missing"):
        status = "attention"
    elif spf["state"] == "missing" and dmarc["state"] == "missing":
        status = "missing"
    elif spf["state"] == "ok" and dmarc["state"] == "ok" and dkim_state == "ok":
        status = "ok"
    else:
        status = "attention"

    summary = " ".join([spf["sentence"], dmarc["sentence"], dkim_sentence])
    evidence = [
        spf["sentence"],
        dmarc["sentence"],
        dkim_sentence,
        "Selectors checked: " + ", ".join(selectors),
    ]
    if spf["record"]:
        evidence.append("SPF record: " + (_shorten(spf["record"]) or ""))
    if dmarc["record"]:
        evidence.append("DMARC record: " + (_shorten(dmarc["record"]) or ""))
    details = {
        "spf": {"state": spf["state"], "qualifier": spf["qualifier"], "record": _shorten(spf["record"], 450)},
        "dmarc": {"state": dmarc["state"], "policy": dmarc["policy"], "record": _shorten(dmarc["record"], 450)},
        "dkim": {"state": dkim_state, "found": found, "errors": dkim_errors},
        "selectors_checked": list(selectors),
    }
    return _result(status, summary, evidence, details)


def _result(status: str, summary: str, evidence: list[str], details: dict) -> dict:
    return {
        "id": "email",
        "title": "SPF, DMARC, and DKIM",
        "status": status,
        "summary": summary,
        "popia_note": EMAIL_NOTE,
        "evidence": evidence,
        "details": details,
    }
