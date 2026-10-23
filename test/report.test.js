import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

import {
  REPORT_SCHEMA,
  domainReportMarkdown,
  parseDomainReport,
  reportForDisplay,
  statusLabel,
} from "../site/js/report.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function report(overrides = {}) {
  return {
    schema: REPORT_SCHEMA,
    disclaimer: "Not legal advice and not a POPIA compliance certification.",
    domain: "example.co.za",
    generated_at: "2026-06-15T12:00:00Z",
    authorisation_note: "Confirmed by the operator. That confirmation does not prove ownership.",
    limitations: ["Read-only."],
    checks: [
      {
        id: "tls",
        title: "HTTPS and TLS",
        status: "ok",
        summary: "The certificate is in place.",
        popia_note: "Section 19 describes this kind of technical measure.",
        evidence: ["Certificate present: yes"],
      },
    ],
    ...overrides,
  };
}

describe("domain report loader", () => {
  it("uses the same schema name as the Python checker", () => {
    const python = readFileSync(path.join(root, "securecheck/constants.py"), "utf8");
    assert.match(python, new RegExp(REPORT_SCHEMA.replaceAll(".", "\\.")));
  });

  it("rejects a report until the ownership box is confirmed", () => {
    const parsed = parseDomainReport(JSON.stringify(report()));
    assert.equal(parsed.ok, true);
    const blocked = reportForDisplay(false, parsed);
    assert.equal(blocked.ok, false);
    assert.match(blocked.error, /Tick the confirmation/);
    assert.match(blocked.error, /does not prove ownership/);
    assert.equal(reportForDisplay(true, parsed).ok, true);
    assert.equal(reportForDisplay("yes", parsed).ok, false);
  });

  it("rejects empty, non-JSON, and foreign reports", () => {
    assert.match(parseDomainReport("").error, /Paste a JSON report/);
    assert.match(parseDomainReport("{").error, /not JSON/);
    assert.match(parseDomainReport(JSON.stringify({ schema: "other", domain: "example.com", checks: [{}] })).error, /not a POPIA SecureCheck/);
    assert.match(parseDomainReport("x".repeat(1000001)).error, /too large/);
  });

  it("keeps text as text and drops unexpected statuses", () => {
    const parsed = parseDomainReport(
      JSON.stringify(
        report({
          checks: [
            {
              id: "tls",
              title: "<script>alert(1)</script>",
              status: "pwned",
              summary: "Fine",
              popia_note: "Section 19.",
              evidence: ["line", 12, "<b>bold</b>"],
            },
          ],
        }),
      ),
    );
    assert.equal(parsed.ok, true);
    assert.equal(parsed.report.checks[0].title, "<script>alert(1)</script>");
    assert.equal(parsed.report.checks[0].status, "error");
    assert.deepEqual(parsed.report.checks[0].evidence, ["line", "<b>bold</b>"]);
    assert.equal(statusLabel("ok"), "In place");
    assert.equal(statusLabel("attention"), "Needs a look");
    assert.equal(statusLabel("missing"), "Not found");
    assert.equal(statusLabel("error"), "Could not check");
  });

  it("builds a markdown section without calling the network", () => {
    const parsed = reportForDisplay(true, parseDomainReport(JSON.stringify(report())));
    const markdown = domainReportMarkdown(parsed.report);
    assert.match(markdown, /## Domain checks/);
    assert.match(markdown, /Not legal advice/);
    assert.match(markdown, /example\.co\.za/);
    assert.match(markdown, /HTTPS and TLS/);
    assert.match(markdown, /In place/);
    assert.match(markdown, /Certificate present: yes/);
    assert.match(markdown, /did not contact the domain/);
  });
});
