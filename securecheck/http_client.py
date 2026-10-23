"""HTTPS reads for the homepage and four fixed admin paths.

GET follows a few same-site HTTPS redirects. HEAD does not follow any.
Neither method looks at any port except 443, which is in the URL.
"""

import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

from securecheck.constants import (
    HEAD_TIMEOUT_SECONDS,
    HTTP_TIMEOUT_SECONDS,
    MAX_HTML_BYTES,
    MAX_REDIRECTS,
    USER_AGENT,
)

REDIRECT_CODES = {301, 302, 303, 307, 308}


@dataclass
class Response:
    url: str
    status: int | None
    headers: dict[str, list[str]] = field(default_factory=dict)
    body: str = ""
    error: str | None = None
    method: str = "GET"
    stopped_redirect: str | None = None

    def values(self, name: str) -> list[str]:
        return self.headers.get(name.lower(), [])

    @property
    def content_type(self) -> str:
        values = self.values("content-type")
        return values[0] if values else ""


@dataclass
class RawReply:
    url: str
    status: int | None
    headers: dict[str, list[str]]
    body: bytes
    error: str | None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Surface the redirect status instead of fetching the next URL."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)


def same_site(left: str, right: str) -> bool:
    a = (left or "").lower().rstrip(".")
    b = (right or "").lower().rstrip(".")
    if not a or not b:
        return False
    return a == b or a == f"www.{b}" or b == f"www.{a}"


def redirect_allowed(current: str, new: str) -> bool:
    old = urllib.parse.urlparse(current)
    nxt = urllib.parse.urlparse(new)
    if nxt.scheme != "https" or not old.hostname or not nxt.hostname:
        return False
    return same_site(old.hostname, nxt.hostname)


def header_map(headers) -> dict[str, list[str]]:
    mapped: dict[str, list[str]] = {}
    if headers is None:
        return mapped
    for key, value in headers.items():
        mapped.setdefault(str(key).lower(), []).append(str(value))
    return mapped


def _charset(content_type: str) -> str:
    for part in content_type.split(";")[1:]:
        name, _, value = part.strip().partition("=")
        if name.lower() == "charset" and value:
            return value.strip().strip('"')
    return "utf-8"


def decode_body(body: bytes, headers: dict[str, list[str]]) -> str:
    content_type = headers.get("content-type", [""])[0]
    charset = _charset(content_type)
    try:
        return body.decode(charset, "replace")
    except LookupError:
        return body.decode("utf-8", "replace")


def short_error(exc: BaseException) -> str:
    reason = getattr(exc, "reason", exc)
    text = str(reason).strip() or exc.__class__.__name__
    if len(text) > 300:
        return text[:299] + "…"
    return text


def make_opener():
    context = ssl.create_default_context()
    return urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=context),
        NoRedirect(),
    )


def urllib_open_once(url: str, method: str, timeout: float, opener=None) -> RawReply:
    if opener is None:
        opener = make_opener()
    request = urllib.request.Request(
        url,
        method=method,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read(MAX_HTML_BYTES) if method == "GET" else b""
            headers = header_map(response.headers)
            return RawReply(response.geturl() or url, response.status, headers, body, None)
    except urllib.error.HTTPError as exc:
        body = b""
        if method == "GET":
            try:
                body = exc.read(MAX_HTML_BYTES)
            except Exception:
                body = b""
        try:
            exc.close()
        except Exception:
            pass
        return RawReply(getattr(exc, "url", None) or url, exc.code, header_map(exc.headers), body, None)
    except urllib.error.URLError as exc:
        return RawReply(url, None, {}, b"", short_error(exc))


def _to_response(raw: RawReply, method: str) -> Response:
    return Response(
        url=raw.url,
        status=raw.status,
        headers=raw.headers,
        body=decode_body(raw.body, raw.headers) if raw.body else "",
        error=raw.error,
        method=method,
    )


class HttpClient:
    def __init__(self, open_once=None, timeout=HTTP_TIMEOUT_SECONDS, head_timeout=HEAD_TIMEOUT_SECONDS):
        self._open_once = open_once or urllib_open_once
        self.timeout = timeout
        self.head_timeout = head_timeout

    def get(self, url: str) -> Response:
        current = url
        for hop in range(MAX_REDIRECTS + 1):
            raw = self._open_once(current, "GET", self.timeout)
            response = _to_response(raw, "GET")
            if response.error or response.status not in REDIRECT_CODES:
                return response
            location = response.values("location")
            if not location:
                return response
            nxt = urllib.parse.urljoin(current, location[0].strip())
            if not redirect_allowed(current, nxt):
                response.stopped_redirect = nxt
                return response
            if hop == MAX_REDIRECTS:
                response.error = "The homepage redirected too many times."
                return response
            current = nxt
        response = Response(url=url, status=None, error="The homepage redirected too many times.", method="GET")
        return response

    def head(self, url: str) -> Response:
        raw = self._open_once(url, "HEAD", self.head_timeout)
        return _to_response(raw, "HEAD")
