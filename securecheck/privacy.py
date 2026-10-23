"""Look for homepage links whose address or text mentions privacy, POPIA, or PAIA."""

import urllib.parse
from html.parser import HTMLParser

from securecheck.http_client import Response

PRIVACY_NOTE = (
    "Section 18 requires reasonably practicable steps so a person is aware of "
    "the particulars listed in that section when their personal information is "
    "collected. A page called a privacy policy is a common way to do that. The "
    "Act does not require that title. Section 17 requires documentation of "
    "processing as referred to in the Promotion of Access to Information Act. "
    "A homepage link whose address or text contains privacy, popia, or paia only "
    "shows that a link is present. It does not show that the notice or the manual is complete."
)

_TERMS = ("privacy", "popia", "paia")


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.base = None
        self.links = []
        self._href = None
        self._text: list[str] = []
        self._in_anchor = False

    def handle_starttag(self, tag, attrs):
        attributes = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "base" and not self.base and attributes.get("href"):
            self.base = attributes["href"]
        if tag.lower() != "a":
            return
        self._in_anchor = True
        self._href = attributes.get("href", "")
        self._text = []

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._in_anchor:
            self.links.append((self._href or "", "".join(self._text)))
            self._in_anchor = False
            self._href = None

    def handle_data(self, data):
        if self._in_anchor:
            self._text.append(data)


def _is_html(content_type: str) -> bool:
    if not content_type:
        return True
    media = content_type.split(";", 1)[0].strip().lower()
    return media in {"text/html", "application/xhtml+xml"}


def _terms_in(href: str, text: str) -> list[str]:
    parsed = urllib.parse.urlparse(href)
    path = urllib.parse.unquote(parsed.path or "")
    haystack = f"{parsed.netloc} {path} {text}".lower()
    return [term for term in _TERMS if term in haystack]


def find_policy_links(html: str, page_url: str, limit: int = 8) -> list[dict]:
    parser = _LinkParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return []
    base = urllib.parse.urljoin(page_url, parser.base) if parser.base else page_url
    found = []
    seen = set()
    for href, text in parser.links:
        cleaned = " ".join(text.split())
        if href.lower().startswith(("javascript:", "data:")):
            continue
        matched = _terms_in(href, cleaned)
        if not matched:
            continue
        absolute = urllib.parse.urljoin(base, href) if href else ""
        key = (absolute, cleaned, tuple(matched))
        if key in seen:
            continue
        seen.add(key)
        found.append({"href": absolute or href, "text": cleaned, "matched": matched})
        if len(found) >= limit:
            break
    return found


def assess_privacy(page_url: str, response: Response) -> dict:
    if response.error and response.status is None:
        summary = "The homepage HTML could not be fetched, so this check did not look for a privacy, POPIA, or PAIA link."
        return _result("error", summary, [f"Connection: {response.error}"], {"error": response.error, "links": []})
    if response.stopped_redirect:
        summary = (
            "The homepage redirected to another site and this check did not follow it, "
            "so a privacy link was not looked for there."
        )
        return _result(
            "attention",
            summary,
            [f"Redirect not followed: {response.stopped_redirect}"],
            {"stopped_redirect": response.stopped_redirect, "links": []},
        )
    if not _is_html(response.content_type):
        summary = "The homepage response was not HTML, so no privacy, POPIA, or PAIA link was read from it."
        return _result("attention", summary, [f"Content type: {response.content_type}"], {"content_type": response.content_type, "links": []})

    links = find_policy_links(response.body, response.url or page_url)
    if links:
        bits = []
        for link in links:
            label = link["text"] or link["href"]
            bits.append(label)
        shown = ", ".join(bits[:4])
        summary = (
            f"The homepage links to a page whose address or text contains privacy, popia, or paia ({shown}). "
            "That shows a link is present. It does not show that the notice meets section 18."
        )
        evidence = [f"{link['text'] or '(no link text)'} — {link['href']} (matched {', '.join(link['matched'])})" for link in links]
        return _result("ok", summary, evidence, {"links": links})

    summary = (
        "The homepage HTML had no link whose address or text contains privacy, popia, or paia. "
        "The notice may still exist on a page this check does not open. This check does not run JavaScript."
    )
    return _result("missing", summary, [summary], {"links": []})


def _result(status: str, summary: str, evidence: list[str], details: dict) -> dict:
    return {
        "id": "privacy",
        "title": "Privacy, POPIA, or PAIA link",
        "status": status,
        "summary": summary,
        "popia_note": PRIVACY_NOTE,
        "evidence": evidence,
        "details": details,
    }
