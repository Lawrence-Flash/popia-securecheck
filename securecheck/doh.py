"""DNS TXT lookups over HTTPS. No extra packages and no system resolver required."""

import json
import urllib.error
import urllib.parse
import urllib.request

from securecheck.constants import DOH_ENDPOINTS, DOH_TIMEOUT_SECONDS, USER_AGENT


class DohError(Exception):
    """A public resolver did not return a usable TXT answer."""


def decode_txt(data: str) -> str:
    """Join the quoted character-strings used in DNS-over-HTTPS JSON."""

    parts = []
    current = []
    quoted = False
    escaped = False
    for character in data:
        if not quoted:
            if character == '"':
                quoted = True
                current = []
            continue
        if escaped:
            current.append(character)
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == '"':
            parts.append("".join(current))
            quoted = False
            continue
        current.append(character)
    if parts:
        return "".join(parts)
    return data.strip().strip('"')


def txt_from_doh(payload) -> list[str]:
    if not isinstance(payload, dict):
        raise DohError("resolver returned an unexpected response")
    status = payload.get("Status")
    if status == 3:
        return []
    if status not in (0, None):
        raise DohError(f"resolver status {status}")
    records = []
    for answer in payload.get("Answer") or []:
        if not isinstance(answer, dict) or answer.get("type") != 16:
            continue
        text = decode_txt(str(answer.get("data", "")))
        if text:
            records.append(text)
    return records


def default_fetch(url: str, timeout: float) -> dict:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/dns-json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(64_000)
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise DohError(str(reason) or "DNS request failed") from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise DohError("resolver returned an unexpected response") from exc


class DohClient:
    def __init__(self, fetch=None, timeout: float = DOH_TIMEOUT_SECONDS, endpoints=DOH_ENDPOINTS):
        self._fetch = fetch or default_fetch
        self.timeout = timeout
        self.endpoints = tuple(endpoints)

    def txt(self, name: str) -> list[str]:
        errors = []
        for endpoint in self.endpoints:
            url = endpoint + "?" + urllib.parse.urlencode({"name": name, "type": "TXT"})
            try:
                return txt_from_doh(self._fetch(url, self.timeout))
            except DohError as exc:
                errors.append(str(exc))
        raise DohError(errors[-1] if errors else "DNS lookup failed")
