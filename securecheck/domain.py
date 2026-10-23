"""Turn user input into one public domain name. Never an address to scan."""

import ipaddress
import re
import urllib.parse

_DOMAIN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


class DomainError(ValueError):
    """The input is not a single domain this checker will accept."""


def normalise_domain(raw: str) -> str:
    """Return a lowercase ASCII domain, or raise DomainError.

    ``https://example.co.za`` and ``example.co.za`` are both accepted.
    IP addresses, page paths, other ports, and local names are not.
    """

    if raw is None or not str(raw).strip():
        raise DomainError("Enter a domain name.")
    text = str(raw).strip()
    if any(character in text for character in " \t\r\n"):
        raise DomainError("Enter one domain name, without spaces.")

    if "://" in text or text.startswith("//"):
        parsed = urllib.parse.urlparse(text if "://" in text else f"https:{text}")
        if parsed.username or parsed.password or "@" in (parsed.netloc or ""):
            raise DomainError("Remove the username from the address.")
        if parsed.scheme not in ("http", "https"):
            raise DomainError("Pass a domain name.")
        if parsed.port not in (None, 443):
            raise DomainError("This check only uses HTTPS on port 443.")
        if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            raise DomainError("Pass the domain only, not a page path.")
        host = parsed.hostname or ""
    else:
        if any(character in text for character in "/?#@"):
            raise DomainError("Pass the domain only, not a page path.")
        if ":" in text:
            raise DomainError("Pass the domain only. This check uses port 443.")
        host = text

    host = host.strip(".").lower()
    if not host:
        raise DomainError("Enter a domain name.")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise DomainError(
            "Pass a domain name, not an IP address. This check does not scan addresses."
        )

    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise DomainError("That does not look like a domain name.") from exc

    if not _DOMAIN.fullmatch(ascii_host):
        raise DomainError("That does not look like a domain name.")
    if (
        ascii_host == "localhost"
        or ascii_host.endswith(".localhost")
        or ascii_host.endswith(".local")
        or ascii_host.endswith(".internal")
    ):
        raise DomainError(
            "This check is for a public domain name you are authorised to assess."
        )
    return ascii_host
