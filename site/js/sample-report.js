/**
 * Fictional domain report for the Load sample report button.
 * Canonical copy: examples/sample-securecheck-report.json
 * test/sample-report.test.js fails if the two diverge.
 * Embedded so the static site can show it without a network request.
 */
export const SAMPLE_REPORT = {
  "schema": "popia-securecheck.domain-report.v1",
  "disclaimer": "Not legal advice and not a POPIA compliance certification.",
  "sample_note": "Fictional sample for example-smme.co.za. No domain was contacted to create this file. Loading it does not scan a website.",
  "tool": "popia-securecheck",
  "tool_version": "2",
  "generated_at": "2026-10-23T09:00:00Z",
  "domain": "example-smme.co.za",
  "authorised": true,
  "authorisation_note": "This file is a fictional sample, not a live check. A real run requires the operator to confirm they own the domain or are authorised to assess it. That confirmation does not prove ownership.",
  "limitations": [
    "Read-only. The checker does not scan ports, try passwords, crawl the site, or attempt to break in.",
    "HTTPS, headers, admin addresses, and the privacy-policy check use port 443 only.",
    "Admin hints are HEAD requests to /admin, /wp-admin, /administrator, and /login. Redirects are not followed.",
    "DKIM is looked up only at a short fixed list of common selectors.",
    "DNS answers come from public DNS-over-HTTPS (Cloudflare, then Quad9 if Cloudflare does not answer).",
    "The privacy check reads homepage HTML only. It does not run JavaScript and does not open the linked page.",
    "Nothing here is legal advice or a POPIA compliance certification."
  ],
  "checks": [
    {
      "id": "tls",
      "title": "HTTPS and TLS",
      "status": "ok",
      "summary": "example-smme.co.za presented a certificate. The certificate is not expired. The name matches example-smme.co.za. The certificate chain verified. The connection negotiated TLSv1.3 with TLS_AES_128_GCM_SHA256, 128 bits.",
      "popia_note": "Section 19 of the Protection of Personal Information Act 4 of 2013 requires appropriate, reasonable technical and organisational measures to protect the integrity and confidentiality of personal information. Encrypting a website people use to send that information is a generally accepted technical measure. The Act does not name a TLS version or a cipher. This check does not show whether this site collects personal information, and it is not the whole of the section 19 duty. It is not a finding by the Information Regulator.",
      "evidence": [
        "Certificate present: yes",
        "Expired: no. Valid until 2027-01-01T00:00:00Z.",
        "Hostname matches: yes",
        "Certificate chain verified: yes",
        "TLS version: TLSv1.3",
        "Cipher: TLS_AES_128_GCM_SHA256 (128 bits)",
        "Subject name: example-smme.co.za",
        "DNS names: example-smme.co.za, www.example-smme.co.za"
      ],
      "details": {
        "certificate_present": true,
        "expired": false,
        "not_yet_valid": false,
        "hostname_matches": true,
        "trusted": true,
        "tls_version": "TLSv1.3",
        "cipher_name": "TLS_AES_128_GCM_SHA256",
        "cipher_bits": 128,
        "subject_cn": "example-smme.co.za",
        "issuer": "Example CA",
        "not_before": "2026-01-01T00:00:00Z",
        "not_after": "2027-01-01T00:00:00Z",
        "days_remaining": 69,
        "sans": [
          "example-smme.co.za",
          "www.example-smme.co.za"
        ],
        "verification_error": null
      }
    },
    {
      "id": "headers",
      "title": "Security headers",
      "status": "attention",
      "summary": "The homepage HTTPS response is missing Content-Security-Policy and Permissions-Policy.",
      "popia_note": "Section 19 does not name HSTS, Content-Security-Policy, X-Content-Type-Options, framing controls, Referrer-Policy, or Permissions-Policy. They are widely used browser safeguards for a site that serves personal information. A missing header is a gap in this read-only check. It is not, by itself, a breach of POPIA.",
      "evidence": [
        "URL: https://example-smme.co.za/",
        "HTTPS status: 200",
        "HSTS is present.",
        "No content security policy was sent.",
        "X-Content-Type-Options is nosniff.",
        "A framing control is present (X-Frame-Options: SAMEORIGIN).",
        "Referrer-Policy is present (strict-origin-when-cross-origin).",
        "Permissions-Policy is not set."
      ],
      "details": {
        "url": "https://example-smme.co.za/",
        "status_code": 200,
        "items": [
          {
            "id": "hsts",
            "name": "Strict-Transport-Security (HSTS)",
            "state": "present",
            "value": "max-age=15552000",
            "sentence": "HSTS is present."
          },
          {
            "id": "csp",
            "name": "Content-Security-Policy",
            "state": "missing",
            "value": null,
            "sentence": "No content security policy was sent."
          },
          {
            "id": "nosniff",
            "name": "X-Content-Type-Options",
            "state": "present",
            "value": "nosniff",
            "sentence": "X-Content-Type-Options is nosniff."
          },
          {
            "id": "framing",
            "name": "X-Frame-Options or CSP frame-ancestors",
            "state": "present",
            "value": "SAMEORIGIN",
            "sentence": "A framing control is present (X-Frame-Options: SAMEORIGIN)."
          },
          {
            "id": "referrer",
            "name": "Referrer-Policy",
            "state": "present",
            "value": "strict-origin-when-cross-origin",
            "sentence": "Referrer-Policy is present (strict-origin-when-cross-origin)."
          },
          {
            "id": "permissions",
            "name": "Permissions-Policy",
            "state": "missing",
            "value": null,
            "sentence": "Permissions-Policy is not set."
          }
        ]
      }
    },
    {
      "id": "privacy",
      "title": "Privacy, POPIA, or PAIA link",
      "status": "missing",
      "summary": "The homepage HTML had no link whose address or text contains privacy, popia, or paia. The notice may still exist on a page this check does not open. This check does not run JavaScript.",
      "popia_note": "Section 18 requires reasonably practicable steps so a person is aware of the particulars listed in that section when their personal information is collected. A page called a privacy policy is a common way to do that. The Act does not require that title. Section 17 requires documentation of processing as referred to in the Promotion of Access to Information Act. A homepage link whose address or text contains privacy, popia, or paia only shows that a link is present. It does not show that the notice or the manual is complete.",
      "evidence": [
        "The homepage HTML had no link whose address or text contains privacy, popia, or paia. The notice may still exist on a page this check does not open. This check does not run JavaScript."
      ],
      "details": {
        "links": []
      }
    },
    {
      "id": "email",
      "title": "SPF, DMARC, and DKIM",
      "status": "attention",
      "summary": "SPF is present and ends with ~all (a soft fail). Receivers can treat unlisted hosts as suspicious. This is a common setting. DMARC is present with p=none. That asks for reports and does not ask receivers to quarantine or reject mail. No DKIM TXT record was found at the common selectors this check tries. A selector that is not in that list can still exist, so this is not proof that DKIM is absent.",
      "popia_note": "SPF, DKIM, and DMARC are not named in the Act. They make it harder for someone else to send mail that looks as if it came from this domain. That supports the section 19 confidentiality duty where the business sends personal information by email. A missing record is something to fix with the email host. It is not proof of a security compromise, and section 22 (breach notification) is a separate duty this check does not measure.",
      "evidence": [
        "SPF is present and ends with ~all (a soft fail). Receivers can treat unlisted hosts as suspicious. This is a common setting.",
        "DMARC is present with p=none. That asks for reports and does not ask receivers to quarantine or reject mail.",
        "No DKIM TXT record was found at the common selectors this check tries. A selector that is not in that list can still exist, so this is not proof that DKIM is absent.",
        "Selectors checked: google, selector1, selector2, k1, s1, s2, default, dkim, mail, smtp",
        "SPF record: v=spf1 include:_spf.example-mail.test ~all",
        "DMARC record: v=DMARC1; p=none; rua=mailto:dmarc@example-smme.co.za"
      ],
      "details": {
        "spf": {
          "state": "ok",
          "qualifier": "~",
          "record": "v=spf1 include:_spf.example-mail.test ~all"
        },
        "dmarc": {
          "state": "attention",
          "policy": "none",
          "record": "v=DMARC1; p=none; rua=mailto:dmarc@example-smme.co.za"
        },
        "dkim": {
          "state": "attention",
          "found": [],
          "errors": []
        },
        "selectors_checked": [
          "google",
          "selector1",
          "selector2",
          "k1",
          "s1",
          "s2",
          "default",
          "dkim",
          "mail",
          "smtp"
        ]
      }
    },
    {
      "id": "admin_paths",
      "title": "Exposed-admin hint",
      "status": "attention",
      "summary": "This check sent HEAD only to /admin, /wp-admin, /administrator, and /login. At least one of those addresses answered. That is a hint to review who can open it, not a weakness by itself. Redirects were not followed and no sign-in was attempted.",
      "popia_note": "Section 19 expects a responsible party to identify reasonably foreseeable risks. An answer from /admin, /wp-admin, /administrator, or /login is only a hint that a sign-in page may be reachable. Many businesses publish those addresses on purpose. This check does not try passwords and does not show whether the page is safe.",
      "evidence": [
        "HEAD /admin returned 404.",
        "HEAD /wp-admin returned 200.",
        "HEAD /administrator returned 404.",
        "HEAD /login returned 302."
      ],
      "details": {
        "paths": [
          {
            "path": "/admin",
            "url": "https://example-smme.co.za/admin",
            "status": 404,
            "error": null,
            "sentence": "HEAD /admin returned 404."
          },
          {
            "path": "/wp-admin",
            "url": "https://example-smme.co.za/wp-admin",
            "status": 200,
            "error": null,
            "sentence": "HEAD /wp-admin returned 200."
          },
          {
            "path": "/administrator",
            "url": "https://example-smme.co.za/administrator",
            "status": 404,
            "error": null,
            "sentence": "HEAD /administrator returned 404."
          },
          {
            "path": "/login",
            "url": "https://example-smme.co.za/login",
            "status": 302,
            "error": null,
            "sentence": "HEAD /login returned 302."
          }
        ],
        "timeout_seconds": 4
      }
    }
  ]
};
