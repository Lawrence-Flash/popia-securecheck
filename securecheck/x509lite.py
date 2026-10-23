"""Read a few fields from a certificate, using only the standard library.

This is enough to report expiry and DNS names when the TLS handshake did
not verify. It is not a full X.509 implementation.
"""

from datetime import datetime, timezone


class Asn1Error(ValueError):
    """The bytes were not a certificate this parser understands."""


CN_OID = bytes((0x55, 0x04, 0x03))
ORG_OID = bytes((0x55, 0x04, 0x0A))
SAN_OID = bytes((0x55, 0x1D, 0x11))


def read_tlv(data: bytes, offset: int = 0) -> tuple[int, bytes, int]:
    if offset >= len(data):
        raise Asn1Error("truncated certificate")
    tag = data[offset]
    offset += 1
    if offset >= len(data):
        raise Asn1Error("truncated length")
    first = data[offset]
    offset += 1
    if first < 0x80:
        length = first
    else:
        count = first & 0x7F
        if count == 0 or count > 4 or offset + count > len(data):
            raise Asn1Error("bad length")
        length = int.from_bytes(data[offset : offset + count], "big")
        offset += count
    end = offset + length
    if end > len(data):
        raise Asn1Error("value overflows")
    return tag, data[offset:end], end


def iter_tlvs(data: bytes):
    offset = 0
    while offset < len(data):
        tag, value, offset = read_tlv(data, offset)
        yield tag, value


def _decode_string(tag: int, value: bytes) -> str:
    if tag in (0x0C, 0x12, 0x13, 0x14, 0x16):
        return value.decode("utf-8", "replace")
    if tag == 0x1E:
        return value.decode("utf-16-be", "replace")
    if tag == 0x1C and len(value) % 4 == 0:
        return "".join(chr(int.from_bytes(value[index : index + 4], "big")) for index in range(0, len(value), 4))
    return ""


def _attributes(name_body: bytes) -> list[tuple[bytes, str]]:
    found = []
    for _tag, rdn in iter_tlvs(name_body):
        for _inner, attribute in iter_tlvs(rdn):
            parts = list(iter_tlvs(attribute))
            if len(parts) >= 2 and parts[0][0] == 0x06:
                found.append((parts[0][1], _decode_string(parts[1][0], parts[1][1])))
    return found


def _parse_time(tag: int, value: bytes) -> datetime | None:
    text = value.decode("ascii", "replace").strip().rstrip("Z")
    try:
        if tag == 0x17 and len(text) >= 12:
            year = int(text[0:2])
            year += 2000 if year < 50 else 1900
            return datetime(
                year,
                int(text[2:4]),
                int(text[4:6]),
                int(text[6:8]),
                int(text[8:10]),
                int(text[10:12]),
                tzinfo=timezone.utc,
            )
        if tag == 0x18 and len(text) >= 14:
            return datetime(
                int(text[0:4]),
                int(text[4:6]),
                int(text[6:8]),
                int(text[8:10]),
                int(text[10:12]),
                int(text[12:14]),
                tzinfo=timezone.utc,
            )
    except ValueError:
        return None
    return None


def _dns_names(extension_value: bytes) -> list[str]:
    """``extension_value`` is the explicit [3] contents (a SEQUENCE TLV)."""

    body = extension_value
    if body[:1] == b"\x30":
        _tag, body, _next = read_tlv(body, 0)
    names: list[str] = []
    for _tag, extension in iter_tlvs(body):
        parts = list(iter_tlvs(extension))
        if not parts or parts[0][0] != 0x06 or parts[0][1] != SAN_OID:
            continue
        octet = next((value for tag, value in parts if tag == 0x04), b"")
        general = octet
        if general[:1] == b"\x30":
            _tag, general, _next = read_tlv(general, 0)
        for tag, value in iter_tlvs(general):
            if tag == 0x82:
                names.append(value.decode("ascii", "replace"))
            elif tag == 0xA2:
                for inner_tag, inner in iter_tlvs(value):
                    if inner_tag in (0x16, 0x0C, 0x13):
                        names.append(inner.decode("ascii", "replace"))
    return names


def parse_certificate(der: bytes) -> dict:
    """Return subject CN, issuer, validity, and DNS subject-alternative names."""

    _tag, certificate, _next = read_tlv(der, 0)
    _tag, tbs, _next = read_tlv(certificate, 0)
    fields = list(iter_tlvs(tbs))
    if not fields:
        raise Asn1Error("empty certificate")
    index = 1 if fields[0][0] == 0xA0 else 0
    if len(fields) <= index + 4:
        raise Asn1Error("certificate is missing validity")

    issuer = _attributes(fields[index + 2][1])
    validity = list(iter_tlvs(fields[index + 3][1]))
    subject = _attributes(fields[index + 4][1])
    not_before = _parse_time(*validity[0]) if validity else None
    not_after = _parse_time(*validity[1]) if len(validity) > 1 else None
    sans: list[str] = []
    for tag, value in fields:
        if tag == 0xA3:
            sans.extend(_dns_names(value))

    issuer_name = next((value for oid, value in issuer if oid == ORG_OID and value), None)
    if not issuer_name:
        issuer_name = next((value for oid, value in issuer if oid == CN_OID and value), None)
    return {
        "subject_cn": next((value for oid, value in subject if oid == CN_OID and value), None),
        "issuer": issuer_name,
        "not_before": not_before,
        "not_after": not_after,
        "sans": sans,
    }
