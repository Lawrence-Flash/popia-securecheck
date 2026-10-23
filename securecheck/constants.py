"""Shared limits for the read-only domain checker.

The checker contacts port 443 only, plus public DNS-over-HTTPS resolvers.
It does not scan ports or try passwords.
"""

SCHEMA = "popia-securecheck.domain-report.v1"
DISCLAIMER = "Not legal advice and not a POPIA compliance certification."
TOOL_VERSION = "2"

TLS_TIMEOUT_SECONDS = 5
HTTP_TIMEOUT_SECONDS = 5
HEAD_TIMEOUT_SECONDS = 4
DOH_TIMEOUT_SECONDS = 4
MAX_HTML_BYTES = 512_000
MAX_REDIRECTS = 3

ADMIN_PATHS = ("/admin", "/wp-admin", "/administrator", "/login")

# A short fixed list. A selector that is not here can still exist.
DKIM_SELECTORS = (
    "google",
    "selector1",
    "selector2",
    "k1",
    "s1",
    "s2",
    "default",
    "dkim",
    "mail",
    "smtp",
)

DOH_ENDPOINTS = (
    "https://cloudflare-dns.com/dns-query",
    "https://dns.quad9.net/dns-query",
)

USER_AGENT = "POPIA-SecureCheck/2 (read-only authorised domain check)"

AUTHORISATION_NOTE = (
    "The person who ran this check confirmed they own this domain or are "
    "authorised to assess it. That confirmation does not prove ownership."
)

REFUSAL_MESSAGE = (
    "Refusing to run checks. Pass --confirm-authorised only if you own this "
    "domain or the owner has authorised you to assess it. The flag does not "
    "prove ownership, and this tool will not contact the domain without it."
)

LIMITATIONS = [
    "Read-only. The checker does not scan ports, try passwords, crawl the site, or attempt to break in.",
    "HTTPS, headers, admin addresses, and the privacy-policy check use port 443 only.",
    "Admin hints are HEAD requests to /admin, /wp-admin, /administrator, and /login. Redirects are not followed.",
    "DKIM is looked up only at a short fixed list of common selectors.",
    "DNS answers come from public DNS-over-HTTPS (Cloudflare, then Quad9 if Cloudflare does not answer).",
    "The privacy check reads homepage HTML only. It does not run JavaScript and does not open the linked page.",
    "Nothing here is legal advice or a POPIA compliance certification.",
]
