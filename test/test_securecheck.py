"""Unit tests for the read-only domain checker.

Sockets and HTTP are mocked. These tests must not contact a domain.
"""

import io
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timezone
from unittest import mock

from securecheck.adminpaths import ADMIN_PATHS, assess_admin, check_admin
from securecheck.cli import main
from securecheck.constants import (
    ADMIN_PATHS as PATHS,
    DISCLAIMER,
    DKIM_SELECTORS,
    HEAD_TIMEOUT_SECONDS,
    REFUSAL_MESSAGE,
    SCHEMA,
)
from securecheck.doh import DohClient, DohError, decode_txt, txt_from_doh
from securecheck.domain import DomainError, normalise_domain
from securecheck.emailsec import check_email, is_dkim, spf_view
from securecheck.gate import AuthorisationRequired, require_authorised
from securecheck.headers import assess_headers
from securecheck.http_client import (
    HEAD_TIMEOUT_SECONDS as CLIENT_HEAD_TIMEOUT,
    HttpClient,
    NoRedirect,
    RawReply,
    Response,
    redirect_allowed,
    urllib_open_once,
)
from securecheck.privacy import assess_privacy, find_policy_links
from securecheck.report import build_report
from securecheck.tls import handshake, hostname_matches, interpret_tls, probe_tls
from securecheck.x509lite import parse_certificate

NOW = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
ROOT = pathlib.Path(__file__).resolve().parents[1]


def _cert(**overrides):
    cert = {
        "subject": ((("commonName", "example.com"),),),
        "issuer": ((("organizationName", "Test CA"),),),
        "subjectAltName": (("DNS", "example.com"), ("DNS", "www.example.com")),
        "notBefore": "Jan  1 00:00:00 2026 GMT",
        "notAfter": "Jan  1 00:00:00 2027 GMT",
    }
    cert.update(overrides)
    return cert


def _verified(**overrides):
    observed = {
        "tls_version": "TLSv1.3",
        "cipher_name": "TLS_AES_128_GCM_SHA256",
        "cipher_bits": 128,
        "cert": _cert(),
        "der": b"\x30",
    }
    observed.update(overrides)
    return observed


def _tls(**kwargs):
    defaults = dict(
        verified=_verified(),
        unverified=None,
        verify_error=None,
        verify_code=None,
        connect_error=None,
        now=NOW,
    )
    defaults.update(kwargs)
    return interpret_tls("example.com", **defaults)


def _page(body="<html></html>", status=200, headers=None, **kwargs):
    return Response(
        url=kwargs.pop("url", "https://example.com/"),
        status=status,
        headers=headers or {"content-type": ["text/html; charset=utf-8"]},
        body=body,
        method="GET",
        **kwargs,
    )


class NetworkGuard(unittest.TestCase):
    def setUp(self):
        self.patches = [
            mock.patch("securecheck.tls.socket.create_connection", side_effect=AssertionError("socket")),
            mock.patch("securecheck.doh.urllib.request.urlopen", side_effect=AssertionError("dns")),
            mock.patch("securecheck.http_client.make_opener", side_effect=AssertionError("http")),
        ]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in self.patches:
            patch.stop()


class DomainTests(NetworkGuard):
    def test_accepts_a_bare_domain_and_an_https_url(self):
        self.assertEqual(normalise_domain("Example.COM"), "example.com")
        self.assertEqual(normalise_domain("https://Example.COM:443/"), "example.com")
        self.assertEqual(normalise_domain("http://example.co.za"), "example.co.za")

    def test_encodes_international_names(self):
        self.assertEqual(normalise_domain("bücher.example"), "xn--bcher-kva.example")

    def test_rejects_addresses_paths_and_local_names(self):
        for value in ("192.168.0.1", "https://127.0.0.1/", "localhost", "printer.local", "app.internal"):
            with self.assertRaises(DomainError):
                normalise_domain(value)
        for value in ("https://example.com/admin", "example.com/path", "https://example.com:8443", "user:pass@example.com"):
            with self.assertRaises(DomainError):
                normalise_domain(value)
        with self.assertRaises(DomainError):
            normalise_domain("   ")


class GateTests(NetworkGuard):
    def test_only_boolean_true_is_confirmation(self):
        require_authorised(True)
        for value in (False, None, "yes", 1, "example.com"):
            with self.assertRaises(AuthorisationRequired):
                require_authorised(value)

    def test_report_does_not_call_clients_without_confirmation(self):
        class Exploding:
            def get(self, url):
                raise AssertionError(url)

            def head(self, url):
                raise AssertionError(url)

            def txt(self, name):
                raise AssertionError(name)

        def tls_probe(*_args, **_kwargs):
            raise AssertionError("tls")

        with self.assertRaises(AuthorisationRequired) as caught:
            build_report(
                "example.com",
                authorised=False,
                http=Exploding(),
                doh=Exploding(),
                tls_probe=tls_probe,
            )
        self.assertIn("confirm-authorised", str(caught.exception))
        self.assertIn(REFUSAL_MESSAGE, str(caught.exception))


class TlsTests(NetworkGuard):
    def test_verified_modern_certificate(self):
        result = _tls()
        self.assertEqual(result["status"], "ok")
        details = result["details"]
        self.assertTrue(details["certificate_present"])
        self.assertFalse(details["expired"])
        self.assertTrue(details["hostname_matches"])
        self.assertTrue(details["trusted"])
        self.assertEqual(details["tls_version"], "TLSv1.3")
        self.assertEqual(details["cipher_name"], "TLS_AES_128_GCM_SHA256")
        self.assertEqual(details["cipher_bits"], 128)
        self.assertIn("not expired", result["summary"])
        self.assertIn("name matches example.com", result["summary"])
        self.assertIn("TLSv1.3", result["summary"])
        self.assertIn("section 19", result["popia_note"].lower())

    def test_expired_certificate_needs_attention(self):
        result = _tls(verified=_verified(cert=_cert(notAfter="Jan  1 00:00:00 2020 GMT")))
        self.assertEqual(result["status"], "attention")
        self.assertTrue(result["details"]["expired"])
        self.assertIn("expired", result["summary"])

    def test_hostname_mismatch_from_unverified_certificate(self):
        result = _tls(
            verified=None,
            unverified=_verified(cert=_cert(subjectAltName=(("DNS", "other.example"),))),
            verify_error="hostname mismatch",
            verify_code=62,
        )
        self.assertEqual(result["status"], "attention")
        self.assertFalse(result["details"]["hostname_matches"])
        self.assertFalse(result["details"]["trusted"])
        self.assertIn("does not match", result["summary"])

    def test_obsolete_tls_and_cipher(self):
        result = _tls(
            verified=_verified(tls_version="TLSv1.0", cipher_name="ECDHE-RSA-DES-CBC3-SHA", cipher_bits=112)
        )
        self.assertEqual(result["status"], "attention")
        self.assertIn("obsolete", result["summary"])

    def test_connection_failure_is_an_error_and_not_a_missing_grade(self):
        result = _tls(verified=None, connect_error="timed out")
        self.assertEqual(result["status"], "error")
        self.assertFalse(result["details"]["certificate_present"])
        self.assertIn("port 443", result["summary"])

    def test_hostname_rules(self):
        self.assertTrue(hostname_matches("www.example.com", ["*.example.com"]))
        self.assertFalse(hostname_matches("example.com", ["*.example.com"]))
        self.assertFalse(hostname_matches("a.b.example.com", ["*.example.com"]))
        self.assertTrue(hostname_matches("Example.COM", ["example.com"]))
        self.assertFalse(hostname_matches("example.com", ["www.example.com"]))

    def test_handshake_uses_port_443_and_the_hostname(self):
        captured = {}

        class FakeSocket:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        class FakeTls:
            def version(self):
                return "TLSv1.3"

            def cipher(self):
                return ("TLS_AES_128_GCM_SHA256", "TLSv1.3", 128)

            def getpeercert(self, binary_form=False):
                if binary_form:
                    return b"der"
                return _cert()

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        class Context:
            def wrap_socket(self, _sock, server_hostname=None):
                captured["sni"] = server_hostname
                return FakeTls()

        def connect(address, timeout):
            captured["address"] = address
            captured["timeout"] = timeout
            return FakeSocket()

        observed = handshake("example.com", 5, Context(), connect=connect)
        self.assertEqual(captured["address"], ("example.com", 443))
        self.assertEqual(captured["timeout"], 5)
        self.assertEqual(captured["sni"], "example.com")
        self.assertEqual(observed["cipher_bits"], 128)
        self.assertNotIn(22, captured["address"])

    def test_probe_does_not_open_a_second_connection_on_timeout(self):
        calls = []

        def fake_handshake(host, timeout, context):
            calls.append((host, timeout, context.check_hostname))
            raise TimeoutError("timed out")

        result = probe_tls("example.com", handshake_fn=fake_handshake, now=NOW)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["status"], "error")


class HeaderTests(NetworkGuard):
    def _headers(self, **extra):
        headers = {
            "content-type": ["text/html"],
            "strict-transport-security": ["max-age=31536000"],
            "content-security-policy": ["default-src 'self'; frame-ancestors 'none'"],
            "x-content-type-options": ["nosniff"],
            "referrer-policy": ["strict-origin-when-cross-origin"],
            "permissions-policy": ["camera=()"],
        }
        headers.update(extra)
        return headers

    def test_all_six_controls_present(self):
        result = assess_headers(_page(headers=self._headers()))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["details"]["items"]), 6)
        self.assertTrue(all(item["state"] == "present" for item in result["details"]["items"]))

    def test_frame_ancestors_covers_the_framing_control(self):
        headers = self._headers()
        headers.pop("x-frame-options", None)
        result = assess_headers(_page(headers=headers))
        framing = next(item for item in result["details"]["items"] if item["id"] == "framing")
        self.assertEqual(framing["state"], "present")
        self.assertEqual(result["status"], "ok")

    def test_missing_and_weak_headers(self):
        result = assess_headers(
            _page(
                headers={
                    "content-type": ["text/html"],
                    "x-frame-options": ["SAMEORIGIN"],
                    "x-content-type-options": ["sniff"],
                    "strict-transport-security": ["max-age=0"],
                    "referrer-policy": ["unsafe-url"],
                }
            )
        )
        self.assertEqual(result["status"], "attention")
        states = {item["id"]: item["state"] for item in result["details"]["items"]}
        self.assertEqual(states["csp"], "missing")
        self.assertEqual(states["permissions"], "missing")
        self.assertEqual(states["nosniff"], "weak")
        self.assertEqual(states["hsts"], "weak")
        self.assertEqual(states["referrer"], "weak")
        self.assertEqual(states["framing"], "present")

    def test_no_headers_is_missing_and_a_failed_fetch_is_an_error(self):
        empty = assess_headers(_page(headers={"content-type": ["text/html"]}))
        self.assertEqual(empty["status"], "missing")
        failed = assess_headers(Response(url="https://example.com/", status=None, error="timed out"))
        self.assertEqual(failed["status"], "error")

    def test_off_site_redirect_is_not_described_as_the_final_page(self):
        result = assess_headers(_page(status=302, stopped_redirect="https://elsewhere.example/"))
        self.assertEqual(result["status"], "attention")
        self.assertIn("did not follow", result["summary"])


class EmailTests(NetworkGuard):
    def test_spf_qualifiers_are_plain_language(self):
        strict = spf_view(["v=spf1 include:_spf.example.com -all"])
        self.assertEqual(strict["qualifier"], "-")
        self.assertEqual(strict["state"], "ok")
        soft = spf_view(["v=spf1 ~all"])
        self.assertEqual(soft["state"], "ok")
        open_relay = spf_view(["v=spf1 +all"])
        self.assertEqual(open_relay["state"], "attention")
        self.assertNotIn("critical", open_relay["sentence"].lower())
        bare = spf_view(["v=spf1 all"])
        self.assertEqual(bare["qualifier"], "+")
        self.assertIsNone(spf_view(["v=spf1 include:all.example.net"])["qualifier"])
        self.assertEqual(spf_view(["google-site-verification=abc"])["state"], "missing")

    def test_dmarc_dkim_and_selector_list(self):
        class FakeDoh:
            def __init__(self):
                self.calls = []

            def txt(self, name):
                self.calls.append(name)
                if name == "example.com":
                    return ["v=spf1 -all"]
                if name == "_dmarc.example.com":
                    return ["v=DMARC1; p=reject; rua=mailto:dmarc@example.com"]
                if name == "google._domainkey.example.com":
                    return ["v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG"]
                return []

        doh = FakeDoh()
        result = check_email("example.com", doh)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["details"]["dmarc"]["policy"], "reject")
        self.assertEqual(result["details"]["dkim"]["found"][0]["selector"], "google")
        self.assertEqual(
            doh.calls,
            ["example.com", "_dmarc.example.com"]
            + [f"{selector}._domainkey.example.com" for selector in DKIM_SELECTORS],
        )
        self.assertIn("section 19", result["popia_note"].lower())
        self.assertIn("section 22", result["popia_note"].lower())

    def test_missing_spf_and_dmarc_still_reports_the_dkim_limit(self):
        class FakeDoh:
            def txt(self, _name):
                return []

        result = check_email("example.com", FakeDoh())
        self.assertEqual(result["status"], "missing")
        self.assertIn("not proof that DKIM is absent", result["summary"])

    def test_monitoring_only_dmarc_needs_a_look(self):
        result = check_email("example.com", _dmarc_none())
        self.assertEqual(result["status"], "attention")
        self.assertIn("p=none", result["summary"])

    def test_dns_failure_does_not_keep_querying(self):
        class FakeDoh:
            def __init__(self):
                self.calls = []

            def txt(self, name):
                self.calls.append(name)
                raise DohError("resolver did not answer")

        doh = FakeDoh()
        result = check_email("example.com", doh)
        self.assertEqual(result["status"], "error")
        self.assertEqual(doh.calls, ["example.com"])

    def test_dkim_recognition(self):
        self.assertTrue(is_dkim("v=DKIM1; p=AAAA"))
        self.assertTrue(is_dkim("k=rsa; p=MIIBIjANBgkqhkiG"))
        self.assertFalse(is_dkim("hello"))


class DohTests(NetworkGuard):
    def test_joins_quoted_txt_chunks_and_treats_nxdomain_as_empty(self):
        self.assertEqual(decode_txt('"v=spf1 " "-all"'), "v=spf1 -all")
        self.assertEqual(txt_from_doh({"Status": 3}), [])
        records = txt_from_doh(
            {"Status": 0, "Answer": [{"type": 16, "data": '"v=spf1 -all"'}, {"type": 5, "data": "cname"}]}
        )
        self.assertEqual(records, ["v=spf1 -all"])
        with self.assertRaises(DohError):
            txt_from_doh({"Status": 2})

    def test_uses_the_first_resolver_that_answers(self):
        calls = []

        def fetch(url, timeout):
            calls.append((url, timeout))
            if "cloudflare" in url:
                raise DohError("down")
            return {"Status": 0, "Answer": [{"type": 16, "data": '"v=spf1 -all"'}]}

        client = DohClient(fetch=fetch, timeout=4)
        self.assertEqual(client.txt("example.com"), ["v=spf1 -all"])
        self.assertEqual(len(calls), 2)
        self.assertIn("name=example.com", calls[0][0])
        self.assertIn("type=TXT", calls[0][0])
        self.assertIn("cloudflare-dns.com", calls[0][0])
        self.assertIn("dns.quad9.net", calls[1][0])
        self.assertEqual(calls[0][1], 4)


class AdminTests(NetworkGuard):
    def test_paths_are_the_fixed_list_and_only_status_codes_are_reported(self):
        self.assertEqual(PATHS, ("/admin", "/wp-admin", "/administrator", "/login"))

        class FakeHttp:
            def __init__(self):
                self.urls = []

            def head(self, url):
                self.urls.append(url)
                status = 200 if url.endswith("/wp-admin") else 404
                return Response(url=url, status=status, method="HEAD", body="")

        http = FakeHttp()
        result = check_admin("example.com", http)
        self.assertEqual(
            http.urls,
            [f"https://example.com{path}" for path in ADMIN_PATHS],
        )
        self.assertEqual(result["status"], "attention")
        self.assertIn("HEAD /wp-admin returned 200.", result["evidence"])
        self.assertNotIn("vulnerable", result["summary"].lower())
        self.assertNotIn("exposed", result["summary"].lower())
        self.assertNotIn("body", json.dumps(result["details"]["paths"]))

    def test_all_404_is_in_place_and_total_failure_is_an_error(self):
        quiet = assess_admin(
            "example.com",
            [{"path": path, "status": 404, "error": None, "sentence": f"HEAD {path} returned 404."} for path in PATHS],
        )
        self.assertEqual(quiet["status"], "ok")
        failed = assess_admin(
            "example.com",
            [{"path": path, "status": None, "error": "timed out", "sentence": f"HEAD {path} could not be completed."} for path in PATHS],
        )
        self.assertEqual(failed["status"], "error")


class PrivacyTests(NetworkGuard):
    def test_finds_privacy_popia_and_paia_links_without_crawling(self):
        html = """
        <html><head><base href="https://example.com/docs/"></head>
        <body>
          <a href="/privacy-policy">Privacy</a>
          <a href="notice.html">POPIA notice</a>
          <a href="https://example.com/paia-manual">Manual</a>
          <a href="/search?q=privacy">Search</a>
          <a href="javascript:alert('privacy')">Skip</a>
          <a href="/about">About</a>
        </body></html>
        """
        links = find_policy_links(html, "https://example.com/")
        hrefs = [link["href"] for link in links]
        self.assertIn("https://example.com/privacy-policy", hrefs)
        self.assertIn("https://example.com/docs/notice.html", hrefs)
        self.assertIn("https://example.com/paia-manual", hrefs)
        self.assertTrue(all("search" not in href for href in hrefs))
        self.assertTrue(all(not href.startswith("javascript:") for href in hrefs))
        result = assess_privacy("https://example.com/", _page(body=html))
        self.assertEqual(result["status"], "ok")
        self.assertIn("section 18", result["summary"])
        self.assertIn("section 17", result["popia_note"].lower())

    def test_missing_link_and_failed_fetch(self):
        missing = assess_privacy("https://example.com/", _page(body="<a href='/about'>About</a>"))
        self.assertEqual(missing["status"], "missing")
        self.assertIn("JavaScript", missing["summary"])
        failed = assess_privacy("https://example.com/", Response(url="https://example.com/", status=None, error="timed out"))
        self.assertEqual(failed["status"], "error")
        other = assess_privacy(
            "https://example.com/",
            _page(headers={"content-type": ["image/png"]}, body=""),
        )
        self.assertEqual(other["status"], "attention")


class HttpTests(NetworkGuard):
    def test_head_does_not_follow_or_read_a_body(self):
        seen = {}

        class Headers:
            def items(self):
                return []

        class FakeResponse:
            headers = Headers()
            status = 200

            def read(self, _count):
                raise AssertionError("HEAD must not read a body")

            def geturl(self):
                return "https://example.com/admin"

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        class Opener:
            def open(self, request, timeout=None):
                seen["method"] = request.get_method()
                seen["url"] = request.full_url
                seen["timeout"] = timeout
                seen["agent"] = request.get_header("User-agent")
                return FakeResponse()

        raw = urllib_open_once("https://example.com/admin", "HEAD", 4, opener=Opener())
        self.assertEqual(raw.status, 200)
        self.assertEqual(raw.body, b"")
        self.assertEqual(seen["method"], "HEAD")
        self.assertEqual(seen["url"], "https://example.com/admin")
        self.assertEqual(seen["timeout"], 4)

        def open_once(url, method, timeout):
            seen["client"] = (url, method, timeout)
            return RawReply(url, 404, {}, b"", None)

        client = HttpClient(open_once=open_once)
        response = client.head("https://example.com/login")
        self.assertEqual(seen["client"], ("https://example.com/login", "HEAD", CLIENT_HEAD_TIMEOUT))
        self.assertEqual(response.status, 404)
        self.assertEqual(response.body, "")
        self.assertEqual(HEAD_TIMEOUT_SECONDS, 4)

    def test_get_follows_www_and_stops_for_another_site_or_http(self):
        def same_site(url, method, timeout):
            if url == "https://example.com/":
                return RawReply(url, 301, {"location": ["https://www.example.com/home"]}, b"", None)
            self.assertEqual(url, "https://www.example.com/home")
            return RawReply(url, 200, {"content-type": ["text/html"]}, b"<p>ok</p>", None)

        response = HttpClient(open_once=same_site).get("https://example.com/")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.url, "https://www.example.com/home")
        self.assertIn("ok", response.body)

        def off_site(url, method, timeout):
            return RawReply(url, 302, {"location": ["https://elsewhere.example/go"]}, b"", None)

        stopped = HttpClient(open_once=off_site).get("https://example.com/")
        self.assertEqual(stopped.stopped_redirect, "https://elsewhere.example/go")
        self.assertFalse(redirect_allowed("https://example.com/", "http://example.com/"))
        self.assertFalse(redirect_allowed("https://example.com/", "https://shop.example.com/"))
        self.assertTrue(redirect_allowed("https://example.com/", "https://www.example.com/"))

    def test_redirect_handler_does_not_fetch_the_next_url(self):
        request = urllib.request.Request("https://example.com/")
        with self.assertRaises(urllib.error.HTTPError) as caught:
            NoRedirect().redirect_request(request, None, 302, "Found", {}, "https://elsewhere.example/")
        self.assertEqual(caught.exception.code, 302)


class ReportTests(NetworkGuard):
    def test_report_shape_and_call_order(self):
        calls = []

        class Http:
            def get(self, url):
                calls.append(("get", url))
                return _page(body="<a href='/privacy'>Privacy</a>", headers={
                    "content-type": ["text/html"],
                    "strict-transport-security": ["max-age=100"],
                    "content-security-policy": ["default-src 'self'"],
                    "x-content-type-options": ["nosniff"],
                    "x-frame-options": ["DENY"],
                    "referrer-policy": ["no-referrer"],
                    "permissions-policy": ["geolocation=()"],
                })

            def head(self, url):
                calls.append(("head", url))
                return Response(url=url, status=404, method="HEAD")

        class Doh:
            def txt(self, name):
                calls.append(("txt", name))
                if name == "example.com":
                    return ["v=spf1 -all"]
                if name == "_dmarc.example.com":
                    return ["v=DMARC1; p=quarantine"]
                if name == "selector1._domainkey.example.com":
                    return ["v=DKIM1; p=AAAAAAAABBBB"]
                return []

        def tls_probe(host, now=None):
            calls.append(("tls", host))
            return _tls()

        report = build_report(
            "https://example.com/",
            authorised=True,
            http=Http(),
            doh=Doh(),
            tls_probe=tls_probe,
            now=NOW,
        )
        json.dumps(report)
        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["disclaimer"], DISCLAIMER)
        self.assertTrue(report["authorised"])
        self.assertEqual(report["domain"], "example.com")
        self.assertEqual(report["generated_at"], "2026-06-15T12:00:00Z")
        self.assertEqual([item["id"] for item in report["checks"]], ["tls", "headers", "privacy", "email", "admin_paths"])
        self.assertEqual(calls[0], ("tls", "example.com"))
        self.assertIn(("get", "https://example.com/"), calls)
        head_urls = [url for method, url in calls if method == "head"]
        self.assertEqual(head_urls, [f"https://example.com{path}" for path in PATHS])
        self.assertNotIn("critical vulnerability", json.dumps(report).lower())


class CliTests(NetworkGuard):
    def test_help_mentions_the_confirmation_flag(self):
        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout):
            with self.assertRaises(SystemExit) as caught:
                main(["--help"])
        self.assertEqual(caught.exception.code, 0)
        help_text = stdout.getvalue()
        self.assertIn("--confirm-authorised", help_text)
        self.assertIn("POPIA compliance certification", help_text)

    def test_refuses_before_building_a_report(self):
        with mock.patch("securecheck.cli.build_report") as build:
            code = main(["example.com"])
        self.assertEqual(code, 2)
        build.assert_not_called()

    def test_bad_domain_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "out.json"
            code = main(["https://example.com/secret", "--confirm-authorised", "--output", str(path)])
            self.assertEqual(code, 2)
            self.assertFalse(path.exists())

    def test_writes_the_json_report(self):
        report = {"schema": SCHEMA, "disclaimer": DISCLAIMER, "domain": "example.com"}
        with mock.patch("securecheck.cli.build_report", return_value=report) as build:
            with tempfile.TemporaryDirectory() as tmp:
                path = pathlib.Path(tmp) / "out.json"
                code = main(["example.com", "--confirm-authorised", "--output", str(path)])
                self.assertEqual(code, 0)
                self.assertEqual(json.loads(path.read_text(encoding="utf-8")), report)
        self.assertIs(build.call_args.kwargs["authorised"], True)


class CertificateParserTests(NetworkGuard):
    def test_reads_a_synthetic_certificate(self):
        parsed = parse_certificate(_synthetic_cert())
        self.assertEqual(parsed["subject_cn"], "example.com")
        self.assertEqual(parsed["issuer"], "Test CA")
        self.assertEqual(parsed["sans"], ["example.com", "www.example.com"])
        self.assertEqual(parsed["not_before"], datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(parsed["not_after"], datetime(2027, 1, 1, tzinfo=timezone.utc))

    def test_reads_an_openssl_certificate_when_available(self):
        if shutil.which("openssl") is None:
            self.skipTest("openssl is not installed")
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            certificate = directory / "cert.pem"
            der = directory / "cert.der"
            command = [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-keyout",
                str(directory / "key.pem"),
                "-out",
                str(certificate),
                "-days",
                "30",
                "-nodes",
                "-subj",
                "/CN=example.com/O=Test CA",
                "-addext",
                "subjectAltName=DNS:example.com,DNS:www.example.com",
            ]
            subprocess.run(command, check=True, capture_output=True)
            subprocess.run(
                ["openssl", "x509", "-in", str(certificate), "-outform", "DER", "-out", str(der)],
                check=True,
                capture_output=True,
            )
            parsed = parse_certificate(der.read_bytes())
        self.assertEqual(parsed["subject_cn"], "example.com")
        self.assertIn("example.com", parsed["sans"])
        self.assertIn("www.example.com", parsed["sans"])
        self.assertIsNotNone(parsed["not_after"])
        self.assertGreater(parsed["not_after"], datetime.now(timezone.utc))


class SourceGuardTests(NetworkGuard):
    def test_checker_stays_passive(self):
        text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "securecheck").rglob("*.py")).lower()
        for banned in ("nmap", "haveibeenpwned", "have i been pwned", "gemini", "shodan", "import requests", "import dns"):
            self.assertNotIn(banned, text)
        self.assertNotIn("critical vulnerability", text)
        workflow = (ROOT / ".github" / "workflows" / "domain-check.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch", workflow)
        self.assertIn("confirm_authorised", workflow)
        self.assertNotIn("push:", workflow)


def _dmarc_none():
    class FakeDoh:
        def txt(self, name):
            if name == "example.com":
                return ["v=spf1 ~all"]
            if name == "_dmarc.example.com":
                return ["v=DMARC1; p=none"]
            return []

    return FakeDoh()


def _tl(tag: int, content: bytes) -> bytes:
    return bytes([tag]) + _der_len(len(content)) + content


def _der_len(length: int) -> bytes:
    if length < 128:
        return bytes([length])
    raw = length.to_bytes((length.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(raw)]) + raw


def _seq(*parts: bytes) -> bytes:
    return _tl(0x30, b"".join(parts))


def _name(oid: bytes, text: str) -> bytes:
    attribute = _seq(_tl(0x06, oid), _tl(0x13, text.encode()))
    return _seq(_tl(0x31, attribute))


def _synthetic_cert() -> bytes:
    version = _tl(0xA0, _tl(0x02, b"\x02"))
    serial = _tl(0x02, b"\x01")
    signature = _seq(_tl(0x06, b"\x2a\x86\x48\x86\xf7\x0d\x01\x01\x0b"))
    issuer = _seq(
        _tl(0x31, _seq(_tl(0x06, b"\x55\x04\x0a"), _tl(0x13, b"Test CA"))),
        _tl(0x31, _seq(_tl(0x06, b"\x55\x04\x03"), _tl(0x13, b"Ignored CN"))),
    )
    validity = _seq(_tl(0x17, b"260101000000Z"), _tl(0x17, b"270101000000Z"))
    subject = _name(b"\x55\x04\x03", "example.com")
    public_key = _seq(_seq(_tl(0x06, b"\x2a")), _tl(0x03, b"\x00\x00"))
    general_names = _seq(_tl(0x82, b"example.com"), _tl(0x82, b"www.example.com"))
    extension = _seq(_tl(0x06, b"\x55\x1d\x11"), _tl(0x04, general_names))
    extensions = _tl(0xA3, _seq(extension))
    tbs = _seq(version, serial, signature, issuer, validity, subject, public_key, extensions)
    return _seq(tbs, signature, _tl(0x03, b"\x00\x00"))


if __name__ == "__main__":
    unittest.main()
