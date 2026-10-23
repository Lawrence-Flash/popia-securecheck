/**
 * Load a domain-check JSON report in the browser.
 * The page does not contact the domain. The checker writes the file.
 */

export const REPORT_SCHEMA = "popia-securecheck.domain-report.v1";

const MAX_TEXT = 1000000;

export function statusLabel(status) {
  if (status === "ok") return "In place";
  if (status === "attention") return "Needs a look";
  if (status === "missing") return "Not found";
  if (status === "error") return "Could not check";
  return "Could not check";
}

function clip(value, max) {
  const text = typeof value === "string" ? value : "";
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

export function parseDomainReport(text) {
  if (typeof text !== "string" || text.trim() === "") {
    return { ok: false, error: "Paste a JSON report, or choose the file the checker wrote." };
  }
  const source = text.replace(/^\uFEFF/, "");
  if (source.length > MAX_TEXT) {
    return { ok: false, error: "That report is too large to show here." };
  }
  let data;
  try {
    data = JSON.parse(source);
  } catch {
    return { ok: false, error: "That text is not JSON." };
  }
  if (!data || typeof data !== "object" || Array.isArray(data) || data.schema !== REPORT_SCHEMA) {
    return { ok: false, error: "That JSON is not a POPIA SecureCheck domain report." };
  }
  if (typeof data.domain !== "string" || data.domain.trim() === "") {
    return { ok: false, error: "That report does not name a domain." };
  }
  if (!Array.isArray(data.checks) || data.checks.length === 0) {
    return { ok: false, error: "That report does not contain any checks." };
  }
  const checks = [];
  for (const check of data.checks.slice(0, 20)) {
    if (!check || typeof check !== "object" || typeof check.title !== "string" || typeof check.summary !== "string") {
      return { ok: false, error: "That report contains a check this page cannot show." };
    }
    checks.push({
      id: clip(check.id, 40),
      title: clip(check.title, 120),
      status: ["ok", "attention", "missing", "error"].includes(check.status) ? check.status : "error",
      summary: clip(check.summary, 2000),
      popia_note: clip(check.popia_note, 2000),
      evidence: Array.isArray(check.evidence)
        ? check.evidence.filter((line) => typeof line === "string").slice(0, 30).map((line) => clip(line, 500))
        : [],
    });
  }
  const limitations = Array.isArray(data.limitations)
    ? data.limitations.filter((line) => typeof line === "string").slice(0, 20).map((line) => clip(line, 500))
    : [];
  const disclaimer =
    typeof data.disclaimer === "string" && data.disclaimer.includes("Not legal advice")
      ? clip(data.disclaimer, 400)
      : "Not legal advice and not a POPIA compliance certification.";
  return {
    ok: true,
    report: {
      schema: REPORT_SCHEMA,
      disclaimer,
      domain: clip(data.domain.trim(), 253),
      generated_at: clip(typeof data.generated_at === "string" ? data.generated_at : "", 40),
      authorisation_note: clip(typeof data.authorisation_note === "string" ? data.authorisation_note : "", 500),
      sample_note: clip(typeof data.sample_note === "string" ? data.sample_note : "", 500),
      limitations,
      checks,
    },
  };
}

export function reportForDisplay(authorised, parsed) {
  if (authorised !== true) {
    return {
      ok: false,
      error: "Tick the confirmation before a domain report can be shown. The tick does not prove ownership.",
    };
  }
  return parsed;
}

export function domainReportMarkdown(report) {
  if (!report) return "";
  const lines = ["## Domain checks", "", report.disclaimer, ""];
  if (report.sample_note) lines.push(report.sample_note, "");
  lines.push(`Domain: ${report.domain}`, "");
  if (report.generated_at) lines.push(`Checked: ${report.generated_at}`, "");
  for (const check of report.checks) {
    lines.push(`### ${check.title}`, "", `${statusLabel(check.status)}. ${check.summary}`, "");
    for (const line of check.evidence || []) lines.push(`- ${line}`);
    if (check.popia_note) lines.push("", check.popia_note);
    lines.push("");
  }
  if (report.limitations && report.limitations.length) {
    lines.push("### What this check does not do", "");
    for (const line of report.limitations) lines.push(`- ${line}`);
    lines.push("");
  }
  lines.push("Loaded from a JSON report on this device. This page did not contact the domain.", "");
  return lines.join("\n");
}
