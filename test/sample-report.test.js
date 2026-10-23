import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

import { SAMPLE_REPORT } from "../site/js/sample-report.js";
import { REPORT_SCHEMA, parseDomainReport, reportForDisplay } from "../site/js/report.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const samplePath = path.join(root, "examples/sample-securecheck-report.json");

describe("committed sample domain report", () => {
  it("matches the report embedded for the demo button", () => {
    const file = JSON.parse(readFileSync(samplePath, "utf8"));
    assert.deepEqual(SAMPLE_REPORT, file);
  });

  it("is a fictional mixed result the page can show", () => {
    const text = readFileSync(samplePath, "utf8");
    const parsed = parseDomainReport(text);
    assert.equal(parsed.ok, true);
    assert.equal(parsed.report.schema, REPORT_SCHEMA);
    assert.equal(parsed.report.domain, "example-smme.co.za");
    assert.match(parsed.report.disclaimer, /Not legal advice/);
    assert.match(parsed.report.sample_note, /Fictional sample/);
    assert.match(parsed.report.sample_note, /does not scan a website/);
    assert.match(parsed.report.authorisation_note, /does not prove ownership/);
    const byId = Object.fromEntries(parsed.report.checks.map((check) => [check.id, check.status]));
    assert.equal(byId.tls, "ok");
    assert.equal(byId.headers, "attention");
    assert.equal(byId.privacy, "missing");
    assert.equal(byId.email, "attention");
    assert.equal(byId.admin_paths, "attention");
    const blocked = reportForDisplay(false, parsed);
    assert.equal(blocked.ok, false);
    assert.equal(reportForDisplay(true, parsed).report.domain, "example-smme.co.za");
  });
});
