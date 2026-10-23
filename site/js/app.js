/**
 * POPIA SecureCheck browser UI.
 * Scoring stays in score.js. This file renders the form, stores answers
 * in localStorage only when the visitor asks it to, and builds the download.
 * PR #1 makes no network requests. Domain checks are a locked placeholder.
 */

import { CONDITIONS, QUESTIONS } from "./questions.js";
import { scoreAudit, toMarkdown } from "./score.js";

const STORAGE_KEY = "popia-securecheck.v1";

const auditRoot = document.querySelector("#audit-root");
const resultsRoot = document.querySelector("#results-root");
const live = document.querySelector("#score-live");
const progressLabel = document.querySelector("#progress-label");
const progressBar = document.querySelector("#progressbar");
const progressFill = document.querySelector("#progress-fill");
const businessNameInput = document.querySelector("#business-name");
const rememberInput = document.querySelector("#remember");
const authorisationInput = document.querySelector("#authorisation");
const gateCard = document.querySelector("#gate-card");
const saveStatus = document.querySelector("#save-status");
const exportButton = document.querySelector("#export-markdown");
const printButton = document.querySelector("#print-results");
const clearButton = document.querySelector("#clear-data");

let remember = true;
let announced = false;

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "dataset") {
      for (const [dataKey, dataValue] of Object.entries(value)) node.dataset[dataKey] = dataValue;
    } else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children) {
    if (child == null || child === false) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

function appendTextWithLinks(parent, text) {
  const pattern = /https:\/\/[^\s),.;]+/g;
  let last = 0;
  for (const match of text.matchAll(pattern)) {
    if (match.index > last) parent.append(text.slice(last, match.index));
    const href = match[0];
    parent.append(
      el("a", { href, rel: "noopener noreferrer" }, [href]),
    );
    last = match.index + href.length;
  }
  if (last < text.length) parent.append(text.slice(last));
}

function weightBadge(weight) {
  if (weight >= 4) return "Highest weight";
  if (weight >= 3) return "High weight";
  return "";
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (!data || data.v !== 1) return null;
    return data;
  } catch {
    return null;
  }
}

function readAnswers() {
  const answers = {};
  for (const question of QUESTIONS) {
    const selected = document.querySelector(`input[name="q-${question.id}"]:checked`);
    if (selected) answers[question.id] = selected.value;
  }
  return answers;
}

function currentResult() {
  return scoreAudit(readAnswers());
}

function persist() {
  if (!remember) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ v: 1, remember: false }));
      saveStatus.textContent = "Answers are not being stored on this device.";
    } catch {
      saveStatus.textContent = "This browser blocked local storage. Answers stay on the page until you close it.";
    }
    return;
  }
  const payload = {
    v: 1,
    remember: true,
    businessName: businessNameInput.value.slice(0, 120),
    authorised: authorisationInput.checked,
    answers: readAnswers(),
  };
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    saveStatus.textContent = "Answers are saved in this browser only. They are not sent to a server.";
  } catch {
    saveStatus.textContent = "This browser blocked local storage. Your score still updates until you close the page.";
  }
}

function syncChoiceStyles() {
  for (const label of document.querySelectorAll(".choice")) {
    const input = label.querySelector("input");
    label.classList.toggle("is-selected", Boolean(input && input.checked));
  }
  for (const button of document.querySelectorAll("[data-clear]")) {
    const selected = document.querySelector(`input[name="q-${button.dataset.clear}"]:checked`);
    button.disabled = !selected;
  }
}

function syncGate() {
  gateCard.classList.toggle("is-open", authorisationInput.checked);
}

function answerLabel(answer) {
  if (answer === "yes") return "Yes";
  if (answer === "partly") return "Partly";
  if (answer === "no") return "No";
  return "Not answered";
}

function renderQuestionnaire() {
  const form = el("form", { id: "audit-form" });
  form.addEventListener("submit", (event) => event.preventDefault());

  for (const condition of CONDITIONS) {
    const questions = QUESTIONS.filter((question) => question.conditionId === condition.id);
    const headingId = `condition-${condition.id}`;
    const section = el("section", {
      class: condition.emphasis ? "condition condition-emphasis" : "condition",
      "aria-labelledby": headingId,
    });
    section.append(
      el("h3", { id: headingId }, [condition.title]),
      el("p", { class: "act-ref" }, [condition.actRef]),
      el("p", { class: "condition-summary" }, [condition.summary]),
    );
    if (condition.emphasis) {
      section.append(
        el("p", { class: "weight-note" }, [
          "These questions carry more of the overall score, because security safeguards and breach notification are the focus of this self-audit.",
        ]),
      );
    }
    for (const question of questions) {
      const badge = weightBadge(question.weight);
      const fieldset = el("fieldset", { class: "question" });
      fieldset.append(el("legend", {}, [question.prompt]));
      const kicker = el("p", { class: "kicker" }, [question.sectionRef]);
      if (badge) kicker.append(document.createTextNode(` · ${badge}`));
      fieldset.append(kicker);
      fieldset.append(
        el("details", {}, [
          el("summary", {}, ["Why this is asked"]),
          el("p", {}, [question.why]),
        ]),
      );
      const choices = el("div", { class: "choices" });
      for (const value of ["yes", "partly", "no"]) {
        const inputId = `${question.id}-${value}`;
        const input = el("input", { type: "radio", name: `q-${question.id}`, id: inputId, value });
        input.addEventListener("change", onAnswerChange);
        choices.append(
          el("label", { class: "choice", dataset: { value } }, [input, answerLabel(value)]),
        );
      }
      const clear = el(
        "button",
        { type: "button", class: "text-button", dataset: { clear: question.id } },
        ["Clear answer"],
      );
      clear.disabled = true;
      clear.addEventListener("click", () => {
        for (const input of document.querySelectorAll(`input[name="q-${question.id}"]`)) {
          input.checked = false;
        }
        onAnswerChange();
      });
      fieldset.append(choices, clear);
      section.append(fieldset);
    }
    form.append(section);
  }
  auditRoot.replaceChildren(form);
}

function renderResults() {
  const result = currentResult();
  const businessName = businessNameInput.value.trim();
  const fragment = document.createDocumentFragment();

  const scoreCard = el("div", { class: "score-card" });
  if (result.percent === null) {
    scoreCard.append(
      el("p", { class: "score-number" }, ["–"]),
      el("p", { class: "band" }, ["No score yet"]),
      el("p", {}, [
        "Answer at least one question. Unanswered questions are left out of the score until you answer them.",
      ]),
    );
  } else {
    scoreCard.append(
      el("p", { class: "score-number" }, [`${result.percent}%`]),
      el("p", { class: `band band-${result.band.id}` }, [result.band.label]),
      el("p", {}, [
        `${formatPoint(result.earned)} of ${formatPoint(result.possible)} weighted points, from ${result.answered} of ${result.total} answers.`,
      ]),
      el("p", { class: "score-note" }, [
        result.complete
          ? "Every question is answered. A high score is still not a POPIA compliance certification."
          : "Unanswered questions are excluded. The score will change when you answer the rest. A high score is not a POPIA compliance certification.",
      ]),
    );
  }
  scoreCard.append(
    el("p", { class: "band-key" }, [
      "85–100 strong self-assessed baseline · 70–84 workable baseline · 40–69 partial · 0–39 needs urgent attention",
    ]),
  );
  fragment.append(scoreCard);

  const conditionList = el("ol", { class: "condition-scores" });
  for (const condition of result.byCondition) {
    const item = el("li", {});
    const head = el("div", { class: "condition-score-head" });
    head.append(
      el("p", { class: "condition-name" }, [condition.title]),
      el("p", { class: "act-ref" }, [condition.actRef]),
    );
    if (condition.percent === null) {
      head.append(el("p", { class: "condition-percent" }, ["Not started"]));
      item.append(head);
      item.append(el("p", { class: "score-note" }, [`0 of ${condition.total} answered.`]));
    } else {
      head.append(el("p", { class: `condition-percent band-${condition.band.id}` }, [`${condition.percent}%`]));
      const meter = el("div", {
        class: `meter band-${condition.band.id}`,
        role: "meter",
        "aria-valuemin": "0",
        "aria-valuemax": "100",
        "aria-valuenow": String(condition.percent),
        "aria-label": `${condition.title}, ${condition.percent} percent, ${condition.band.label}`,
      });
      const fill = el("span", {});
      fill.style.width = `${condition.percent}%`;
      meter.append(fill);
      const note =
        condition.answered === condition.total
          ? `${condition.answered} of ${condition.total} answered.`
          : `${condition.answered} of ${condition.total} answered. Unanswered questions are not in this percent.`;
      item.append(head, meter, el("p", { class: "score-note" }, [note]));
    }
    conditionList.append(item);
  }
  fragment.append(el("h3", { id: "by-condition" }, ["Scores by condition"]), conditionList);

  fragment.append(el("h3", { id: "fixes-title" }, ["Prioritised fixes"]));
  fragment.append(
    el("p", {}, [
      "Higher-weighted gaps come first. A No ranks above a Partly of the same weight. Partly scores half the question weight.",
    ]),
  );
  if (result.fixes.length === 0) {
    fragment.append(
      el("p", {}, [
        "No gaps in the answers you have given. Unanswered questions are not listed. This is still not a compliance certificate.",
      ]),
    );
  } else {
    const fixList = el("ol", { class: "fixes" });
    for (const fix of result.fixes) {
      const gap = fix.answer === "no" ? "Gap" : "Partial";
      const item = el("li", { class: `fix fix-${fix.answer}` });
      item.append(el("p", { class: "kicker" }, [`${gap} · weight ${fix.weight} · ${fix.sectionRef}`]));
      item.append(el("p", { class: "fix-prompt" }, [fix.prompt]));
      const action = el("p", { class: "fix-action" });
      appendTextWithLinks(action, fix.action);
      item.append(action);
      fixList.append(item);
    }
    fragment.append(fixList);
  }

  const printBlock = el("div", { class: "print-only" });
  printBlock.append(el("h2", {}, ["Answers"]));
  if (businessName) printBlock.append(el("p", {}, [`Business: ${businessName}`]));
  const answerList = el("ul", { class: "print-answers" });
  for (const row of result.rows) {
    answerList.append(
      el("li", {}, [`${row.prompt} — ${answerLabel(row.answer)} (${row.sectionRef})`]),
    );
  }
  printBlock.append(answerList);
  fragment.append(printBlock);

  resultsRoot.replaceChildren(fragment);
  updateProgress(result);
  updateLive(result);
}

function formatPoint(value) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function updateProgress(result) {
  progressLabel.textContent = result.complete
    ? `All ${result.total} answered`
    : `${result.answered} of ${result.total} answered`;
  progressBar.setAttribute("aria-valuemax", String(result.total));
  progressBar.setAttribute("aria-valuenow", String(result.answered));
  progressBar.setAttribute("aria-valuetext", progressLabel.textContent);
  const ratio = result.total === 0 ? 0 : (result.answered / result.total) * 100;
  progressFill.style.width = `${ratio}%`;
}

function updateLive(result) {
  if (!announced) return;
  if (result.percent === null) {
    live.textContent = "No score yet. No questions answered.";
    return;
  }
  live.textContent = `Overall score ${result.percent} percent. ${result.band.label}. ${result.answered} of ${result.total} answered. ${result.fixes.length} fixes listed.`;
}

function onAnswerChange() {
  announced = true;
  syncChoiceStyles();
  renderResults();
  persist();
}

function applyState(state) {
  if (!state) return;
  remember = state.remember !== false;
  rememberInput.checked = remember;
  if (!remember) return;
  if (typeof state.businessName === "string") businessNameInput.value = state.businessName.slice(0, 120);
  authorisationInput.checked = Boolean(state.authorised);
  const answers = state.answers && typeof state.answers === "object" ? state.answers : {};
  for (const question of QUESTIONS) {
    const value = answers[question.id];
    if (value !== "yes" && value !== "partly" && value !== "no") continue;
    const input = document.querySelector(`input[name="q-${question.id}"][value="${value}"]`);
    if (input) input.checked = true;
  }
}

function generatedAt() {
  return new Date().toLocaleString("en-ZA", { dateStyle: "long", timeStyle: "short" });
}

function bindActions() {
  businessNameInput.addEventListener("input", () => {
    announced = true;
    renderResults();
    persist();
  });
  rememberInput.addEventListener("change", () => {
    remember = rememberInput.checked;
    if (!remember) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ v: 1, remember: false }));
      } catch {
        /* persist() reports the failure */
      }
    }
    persist();
  });
  authorisationInput.addEventListener("change", () => {
    syncGate();
    persist();
  });
  exportButton.addEventListener("click", () => {
    const markdown = toMarkdown(currentResult(), {
      businessName: businessNameInput.value,
      generatedAt: generatedAt(),
    });
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = el("a", { href: url, download: "popia-securecheck-results.md" });
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    saveStatus.textContent = "Markdown file downloaded to this device. It was not uploaded.";
  });
  printButton.addEventListener("click", () => {
    window.print();
  });
  clearButton.addEventListener("click", () => {
    const hasAnswers = Object.keys(readAnswers()).length > 0 || businessNameInput.value.trim() !== "";
    let stored = null;
    try {
      stored = localStorage.getItem(STORAGE_KEY);
    } catch {
      stored = null;
    }
    if (hasAnswers || authorisationInput.checked || stored) {
      const confirmed = window.confirm(
        "Clear the business name, answers, and authorisation tick stored in this browser?",
      );
      if (!confirmed) return;
    }
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* still clear the page */
    }
    remember = true;
    rememberInput.checked = true;
    businessNameInput.value = "";
    authorisationInput.checked = false;
    for (const input of document.querySelectorAll('#audit-form input[type="radio"]')) input.checked = false;
    syncChoiceStyles();
    syncGate();
    announced = true;
    renderResults();
    saveStatus.textContent = stored || hasAnswers
      ? "Saved answers were cleared from this browser."
      : "There were no saved answers to clear.";
  });
}

renderQuestionnaire();
applyState(loadState());
syncChoiceStyles();
syncGate();
bindActions();
renderResults();
saveStatus.textContent = remember
  ? "Answers are saved in this browser only after you change them. They are not sent to a server."
  : "Answers are not being stored on this device.";
if (Object.keys(readAnswers()).length > 0) {
  announced = true;
  updateLive(currentResult());
}
