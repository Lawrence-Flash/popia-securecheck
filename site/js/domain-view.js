/**
 * Render a domain report with text nodes only.
 * A report is a local file. It is not trusted as HTML.
 */

import { statusLabel } from "./report.js";

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children) {
    if (child == null || child === false) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

export function clearDomainReport(container) {
  if (container) container.replaceChildren();
}

export function renderDomainReport(container, report) {
  const fragment = document.createDocumentFragment();
  const heading = el("h3", { id: "domain-report-title", tabindex: "-1" }, [`Results for ${report.domain}`]);
  fragment.append(heading);
  fragment.append(el("p", { class: "score-note" }, [report.disclaimer]));
  if (report.sample_note) {
    fragment.append(el("p", { class: "sample-banner" }, [report.sample_note]));
  }
  if (report.generated_at) {
    fragment.append(el("p", { class: "score-note" }, [`Checked: ${report.generated_at}`]));
  }
  if (report.authorisation_note) {
    fragment.append(el("p", {}, [report.authorisation_note]));
  }
  fragment.append(
    el("p", {}, [
      "These are separate read-only observations. They do not add up to a POPIA score, and a tidy report is not a compliance certificate.",
    ]),
  );

  const list = el("div", { class: "check-list" });
  for (const check of report.checks) {
    const card = el("article", { class: `check check-${check.status}` });
    card.append(el("h4", {}, [check.title]));
    card.append(el("p", { class: `check-status band-${statusClass(check.status)}` }, [statusLabel(check.status)]));
    card.append(el("p", {}, [check.summary]));
    if (check.evidence && check.evidence.length) {
      const evidence = el("ul", { class: "detail-list" });
      for (const line of check.evidence) evidence.append(el("li", {}, [line]));
      card.append(evidence);
    }
    if (check.popia_note) {
      card.append(el("p", { class: "popia-label" }, ["Where this sits in POPIA"]));
      card.append(el("p", { class: "popia-note" }, [check.popia_note]));
    }
    list.append(card);
  }
  fragment.append(list);

  if (report.limitations && report.limitations.length) {
    const notes = el("details", { class: "limitations" });
    notes.append(el("summary", {}, ["What this check does not do"]));
    const items = el("ul", { class: "detail-list" });
    for (const line of report.limitations) items.append(el("li", {}, [line]));
    notes.append(items);
    fragment.append(notes);
  }

  container.replaceChildren(fragment);
  heading.focus();
}

function statusClass(status) {
  if (status === "ok") return "strong";
  if (status === "attention") return "partial";
  if (status === "missing") return "urgent";
  return "partial";
}
