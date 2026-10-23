"""HTTPS certificate, hostname, expiry, and a TLS version/cipher summary."""

import socket
import ssl
from datetime import datetime, timezone

from securecheck.x509lite import Asn1Error, parse_certificate

TLS_NOTE = (
    "Section 19 of the Protection of Personal Information Act 4 of 2013 requires "
    "appropriate, reasonable technical and organisational measures to protect the "
    "integrity and confidentiality of personal information. Encrypting a website "
    "people use to send that information is a generally accepted technical measure. "
    "The Act does not name a TLS version or a cipher. This check does not show "
    "whether this site collects personal information, and it is not the whole of "
    "the section 19 duty. It is not a finding by the Information Regulator."
)

_MODERN = {"TLSv1.2", "TLSv1.3"}
_WEAK_CIPHER_MARKERS = ("NULL", "EXPORT", "RC4", "ANON", "RC2", "DES-CBC3", "3DES", "IDEA")
_EXPIRED = 10
_NOT_YET_VALID = 9
_HOSTNAME_MISMATCH = 62


def handshake(host: str, timeout: float, context: ssl.SSLContext, connect=None) -> dict:
    if connect is None:
        connect = socket.create_connection
    with connect((host, 443), timeout=timeout) as raw:
        with context.wrap_socket(raw, server_hostname=host) as tls:
            cipher = tls.cipher() or ("", "", None)
            certificate = tls.getpeercert() or {}
            der = tls.getpeercert(binary_form=True)
            return {
                "tls_version": tls.version(),
                "cipher_name": cipher[0] or None,
                "cipher_bits": cipher[2] if len(cipher) > 2 else None,
                "cert": certificate,
                "der": der,
            }


def hostname_matches(host: str, names: list[str]) -> bool:
    """True when ``host`` equals a DNS name, or a single leftmost wildcard label."""

    try:
        wanted = host.lower().rstrip(".").encode("idna").decode("ascii")
    except UnicodeError:
        return False
    for name in names:
        try:
            candidate = name.lower().rstrip(".").encode("idna").decode("ascii")
        except UnicodeError:
            continue
        if candidate == wanted:
            return True
        if candidate.startswith("*."):
            suffix = candidate[1:]
            if wanted.endswith(suffix):
                label = wanted[: -len(suffix)]
                if label and "." not in label:
                    return True
    return False


def _openssl_time(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith(" GMT"):
        text = text[: -len(" GMT")].strip()
    try:
        parsed = datetime.strptime(text, "%b %d %H:%M:%S %Y")
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc)


def _rdn(rdns, key: str) -> str | None:
    for group in rdns or ():
        for item in group:
            if len(item) >= 2 and item[0] == key and item[1]:
                return item[1]
    return None


def _cipher_is_weak(name: str | None) -> bool:
    if not name:
        return False
    upper = name.upper()
    return any(marker in upper for marker in _WEAK_CIPHER_MARKERS)


def _stamp(moment: datetime | None) -> str | None:
    if moment is None:
        return None
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clip(text: str | None, limit: int = 300) -> str | None:
    if not text:
        return None
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def interpret_tls(
    host: str,
    *,
    verified: dict | None,
    unverified: dict | None,
    verify_error: str | None,
    verify_code: int | None,
    connect_error: str | None,
    now: datetime,
) -> dict:
    observed = verified or unverified
    if observed is None:
        return _check(
            host,
            status="error",
            summary=(
                f"No HTTPS certificate could be read for {host}. "
                "The check looks only at TLS on port 443, and that connection did not succeed."
            ),
            details=_details(
                present=False,
                expired=None,
                not_yet_valid=None,
                hostname_ok=None,
                trusted=None,
                version=None,
                cipher=None,
                bits=None,
                subject_cn=None,
                issuer=None,
                not_before=None,
                not_after=None,
                days=None,
                sans=[],
                verification_error=connect_error,
            ),
            evidence=[
                "Certificate present: no",
                f"Connection: {connect_error or 'did not succeed'}",
            ],
        )

    cert = observed.get("cert") or {}
    subject_cn = None
    issuer = None
    sans: list[str] = []
    not_before = None
    not_after = None
    if cert:
        subject_cn = _rdn(cert.get("subject"), "commonName")
        issuer = _rdn(cert.get("issuer"), "organizationName") or _rdn(cert.get("issuer"), "commonName")
        sans = [value for kind, value in cert.get("subjectAltName", ()) if kind == "DNS"]
        not_before = _openssl_time(cert.get("notBefore"))
        not_after = _openssl_time(cert.get("notAfter"))
    elif observed.get("der"):
        try:
            parsed = parse_certificate(observed["der"])
        except Asn1Error:
            parsed = None
        if parsed:
            subject_cn = parsed["subject_cn"]
            issuer = parsed["issuer"]
            sans = parsed["sans"]
            not_before = parsed["not_before"]
            not_after = parsed["not_after"]

    present = bool(cert) or bool(observed.get("der"))
    trusted = verified is not None
    if trusted:
        hostname_ok = True
    elif sans or subject_cn:
        names = sans or ([subject_cn] if subject_cn else [])
        hostname_ok = hostname_matches(host, names)
    else:
        hostname_ok = None
    if verify_code == _HOSTNAME_MISMATCH:
        hostname_ok = False

    expired = None
    not_yet_valid = None
    if not_after is not None:
        expired = now >= not_after
    elif verify_code == _EXPIRED:
        expired = True
    elif trusted:
        expired = False
    if not_before is not None:
        not_yet_valid = now < not_before
    elif verify_code == _NOT_YET_VALID:
        not_yet_valid = True
    elif trusted:
        not_yet_valid = False

    version = observed.get("tls_version")
    cipher = observed.get("cipher_name")
    bits = observed.get("cipher_bits")
    weak = _cipher_is_weak(cipher)
    days = None if not_after is None else (not_after - now).days
    details = _details(
        present=present,
        expired=expired,
        not_yet_valid=not_yet_valid,
        hostname_ok=hostname_ok,
        trusted=trusted,
        version=version,
        cipher=cipher,
        bits=bits,
        subject_cn=subject_cn,
        issuer=issuer,
        not_before=not_before,
        not_after=not_after,
        days=days,
        sans=sans[:8],
        verification_error=None if trusted else verify_error,
    )
    problems = (
        not present
        or expired is True
        or not_yet_valid is True
        or hostname_ok is False
        or trusted is False
        or expired is None
        or hostname_ok is None
        or (version is not None and version not in _MODERN)
        or version is None
        or weak
    )
    status = "missing" if not present else ("attention" if problems else "ok")
    return _check(host, status=status, summary=_summary(host, details, weak), details=details, evidence=_evidence(details, weak))


def _details(**kwargs) -> dict:
    present = kwargs["present"]
    return {
        "certificate_present": present,
        "expired": kwargs["expired"],
        "not_yet_valid": kwargs["not_yet_valid"],
        "hostname_matches": kwargs["hostname_ok"],
        "trusted": kwargs["trusted"],
        "tls_version": kwargs["version"],
        "cipher_name": kwargs["cipher"],
        "cipher_bits": kwargs["bits"],
        "subject_cn": kwargs["subject_cn"],
        "issuer": kwargs["issuer"],
        "not_before": _stamp(kwargs["not_before"]),
        "not_after": _stamp(kwargs["not_after"]),
        "days_remaining": kwargs["days"],
        "sans": kwargs["sans"],
        "verification_error": _clip(kwargs["verification_error"]),
    }


def _yes_no(value) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "could not tell"


def _evidence(details: dict, weak: bool) -> list[str]:
    expiry = "Expiry: could not be read"
    if details["expired"] is True:
        expiry = f"Expired: yes (not after {details['not_after'] or 'an unknown date'})"
    elif details["expired"] is False:
        extra = f" Valid until {details['not_after']}." if details["not_after"] else ""
        expiry = f"Expired: no.{extra}"
    cipher = details["cipher_name"] or "unknown"
    if details["cipher_bits"]:
        cipher = f"{cipher} ({details['cipher_bits']} bits)"
    if weak:
        cipher += " — obsolete"
    lines = [
        f"Certificate present: {_yes_no(details['certificate_present'])}",
        expiry,
        f"Hostname matches: {_yes_no(details['hostname_matches'])}",
        f"Certificate chain verified: {_yes_no(details['trusted'])}",
        f"TLS version: {details['tls_version'] or 'unknown'}",
        f"Cipher: {cipher}",
    ]
    if details["subject_cn"]:
        lines.append(f"Subject name: {details['subject_cn']}")
    if details["sans"]:
        lines.append("DNS names: " + ", ".join(details["sans"]))
    if details["verification_error"]:
        lines.append(f"Verification note: {details['verification_error']}")
    return lines


def _summary(host: str, details: dict, weak: bool) -> str:
    sentences = [f"{host} presented a certificate." if details["certificate_present"] else f"{host} did not present a certificate."]
    if details["expired"] is True:
        when = details["not_after"] or "an unknown date"
        sentences.append(f"The certificate is expired (not after {when}).")
    elif details["not_yet_valid"] is True:
        sentences.append("The certificate is not valid yet.")
    elif details["expired"] is False:
        sentences.append("The certificate is not expired.")
    else:
        sentences.append("The expiry date could not be read.")
    if details["hostname_matches"] is True:
        sentences.append(f"The name matches {host}.")
    elif details["hostname_matches"] is False:
        sentences.append(f"The name does not match {host}.")
    else:
        sentences.append("The name on the certificate could not be checked.")
    if details["trusted"] is True:
        sentences.append("The certificate chain verified.")
    elif details["trusted"] is False:
        sentences.append("The certificate chain did not verify.")
    version = details["tls_version"] or "an unknown TLS version"
    cipher = details["cipher_name"] or "an unnamed cipher"
    bits = f", {details['cipher_bits']} bits" if details["cipher_bits"] else ""
    sentences.append(f"The connection negotiated {version} with {cipher}{bits}.")
    if details["tls_version"] and details["tls_version"] not in _MODERN:
        sentences.append("That TLS version is obsolete.")
    if weak:
        sentences.append("That cipher is obsolete.")
    return " ".join(sentences)


def _check(host: str, *, status: str, summary: str, details: dict, evidence: list[str]) -> dict:
    return {
        "id": "tls",
        "title": "HTTPS and TLS",
        "status": status,
        "summary": summary,
        "popia_note": TLS_NOTE,
        "evidence": evidence,
        "details": details,
    }


def probe_tls(host: str, *, timeout: float = 5, now: datetime | None = None, handshake_fn=handshake) -> dict:
    """Connect once on port 443. On a certificate error, read the cert without trusting it."""

    moment = now or datetime.now(timezone.utc)
    verified = None
    unverified = None
    verify_error = None
    verify_code = None
    connect_error = None
    try:
        verified = handshake_fn(host, timeout, ssl.create_default_context())
    except ssl.SSLCertVerificationError as exc:
        verify_error = getattr(exc, "verify_message", None) or str(exc)
        verify_code = getattr(exc, "verify_code", None)
        loose = ssl.create_default_context()
        loose.check_hostname = False
        loose.verify_mode = ssl.CERT_NONE
        try:
            unverified = handshake_fn(host, timeout, loose)
        except OSError as exc2:
            connect_error = short_connect_error(exc2)
    except OSError as exc:
        connect_error = short_connect_error(exc)
    return interpret_tls(
        host,
        verified=verified,
        unverified=unverified,
        verify_error=verify_error,
        verify_code=verify_code,
        connect_error=connect_error,
        now=moment,
    )


def short_connect_error(exc: BaseException) -> str:
    text = str(exc).strip() or exc.__class__.__name__
    if len(text) > 300:
        return text[:299] + "…"
    return text
