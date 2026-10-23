/**
 * Pure scoring and Markdown export for POPIA SecureCheck.
 * The browser UI and the Node tests both import this file.
 * There is no network access and no storage here.
 */

import { CONDITIONS, QUESTIONS } from "./questions.js";

export const ANSWERS = Object.freeze(["yes", "partly", "no"]);

export const DISCLAIMER =
  "Not legal advice and not a POPIA compliance certification. This self-audit only reflects the answers entered in the browser. It does not measure every duty in the Protection of Personal Information Act 4 of 2013. Consult the Information Regulator's guidance or a qualified professional before relying on it.";

const HALF = Object.freeze({ yes: 2, partly: 1, no: 0 });

export function normaliseAnswer(value) {
  return ANSWERS.includes(value) ? value : null;
}

export function bandFor(percent) {
  if (typeof percent !== "number" || Number.isNaN(percent)) return null;
  if (percent >= 85) return { id: "strong", label: "Strong self-assessed baseline" };
  if (percent >= 70) return { id: "workable", label: "Workable baseline" };
  if (percent >= 40) return { id: "partial", label: "Partial: important gaps remain" };
  return { id: "urgent", label: "Needs urgent attention" };
}

function toPercent(earnedHalf, possibleHalf) {
  if (possibleHalf <= 0) return null;
  return Math.round((earnedHalf / possibleHalf) * 100);
}

function conditionTitle(conditions, conditionId) {
  return conditions.find((condition) => condition.id === conditionId)?.title ?? conditionId;
}

/**
 * Score a set of answers.
 * Yes earns the full weight, partly earns half, and no earns zero.
 * Unanswered questions are left out of both the points earned and the points available.
 * The overall percent uses question weights. It is not an average of the eight condition scores.
 *
 * @param {Record<string, string>} rawAnswers
 * @param {typeof QUESTIONS} [questions]
 * @param {typeof CONDITIONS} [conditions]
 */
export function scoreAudit(rawAnswers = {}, questions = QUESTIONS, conditions = CONDITIONS) {
  const answers = rawAnswers && typeof rawAnswers === "object" ? rawAnswers : {};
  const rows = questions.map((question, order) => {
    const answer = normaliseAnswer(answers[question.id]);
    const weight = question.weight;
    return {
      ...question,
      order,
      answer,
      earnedHalf: answer ? HALF[answer] * weight : 0,
      possibleHalf: answer ? 2 * weight : 0,
    };
  });

  const earnedHalf = rows.reduce((sum, row) => sum + row.earnedHalf, 0);
  const possibleHalf = rows.reduce((sum, row) => sum + row.possibleHalf, 0);
  const answered = rows.filter((row) => row.answer).length;
  const percent = toPercent(earnedHalf, possibleHalf);

  const byCondition = conditions.map((condition) => {
    const subset = rows.filter((row) => row.conditionId === condition.id);
    const subsetEarned = subset.reduce((sum, row) => sum + row.earnedHalf, 0);
    const subsetPossible = subset.reduce((sum, row) => sum + row.possibleHalf, 0);
    const conditionAnswered = subset.filter((row) => row.answer).length;
    const conditionPercent = toPercent(subsetEarned, subsetPossible);
    return {
      id: condition.id,
      title: condition.title,
      actRef: condition.actRef,
      summary: condition.summary,
      emphasis: Boolean(condition.emphasis),
      answered: conditionAnswered,
      total: subset.length,
      earned: subsetEarned / 2,
      possible: subsetPossible / 2,
      percent: conditionPercent,
      band: bandFor(conditionPercent),
    };
  });

  const fixes = rows
    .filter((row) => row.answer === "no" || row.answer === "partly")
    .map((row) => ({
      id: row.id,
      conditionId: row.conditionId,
      conditionTitle: conditionTitle(conditions, row.conditionId),
      sectionRef: row.sectionRef,
      weight: row.weight,
      answer: row.answer,
      prompt: row.prompt,
      action: row.answer === "partly" ? `Finish what you have started. ${row.fix}` : row.fix,
      order: row.order,
    }))
    .sort((a, b) => {
      if (a.weight !== b.weight) return b.weight - a.weight;
      if (a.answer !== b.answer) return a.answer === "no" ? -1 : 1;
      return a.order - b.order;
    })
    .map((fix, index) => ({ ...fix, rank: index + 1 }));

  return {
    answered,
    total: rows.length,
    complete: rows.length > 0 && answered === rows.length,
    earned: earnedHalf / 2,
    possible: possibleHalf / 2,
    percent,
    band: bandFor(percent),
    byCondition,
    fixes,
    rows: rows.map((row) => ({
      id: row.id,
      conditionId: row.conditionId,
      conditionTitle: conditionTitle(conditions, row.conditionId),
      sectionRef: row.sectionRef,
      weight: row.weight,
      prompt: row.prompt,
      answer: row.answer,
    })),
  };
}

function clean(value) {
  return String(value).replace(/[\r\n]+/g, " ").trim().slice(0, 200);
}

function formatPoints(value) {
  if (Number.isInteger(value)) return String(value);
  return value.toFixed(1);
}

/**
 * Build a Markdown report. `details.generatedAt` and `details.businessName`
 * are printed as given, with newlines removed, so tests stay stable.
 */
export function toMarkdown(result, details = {}) {
  const lines = ["# POPIA SecureCheck results", "", DISCLAIMER, ""];
  const businessName = clean(details.businessName || "");
  const generatedAt = clean(details.generatedAt || "");
  if (businessName) {
    lines.push(`Business: ${businessName}`, "");
  }
  if (generatedAt) {
    lines.push(`Generated: ${generatedAt}`, "");
  }

  lines.push("## Overall score", "");
  if (result.percent === null) {
    lines.push(
      "No score yet. Answer at least one question. Unanswered questions are excluded from the score.",
    );
  } else {
    lines.push(`${result.percent}% — ${result.band.label}`);
    lines.push("");
    lines.push(
      `Points: ${formatPoints(result.earned)} of ${formatPoints(result.possible)} weighted points, from ${result.answered} of ${result.total} answers.`,
    );
    lines.push("");
    lines.push(
      "Unanswered questions are excluded from the score. The overall score uses question weights, not an average of the condition scores. A high score is not a certificate of compliance.",
    );
  }

  lines.push("", "## Scores by condition", "");
  for (const condition of result.byCondition) {
    const score =
      condition.percent === null ? "Not started" : `${condition.percent}% — ${condition.band.label}`;
    lines.push(
      `- **${condition.title}** (${condition.actRef}): ${score}. ${condition.answered} of ${condition.total} answered.`,
    );
  }

  lines.push("", "## Prioritised fixes", "");
  if (result.fixes.length === 0) {
    lines.push("No gaps in the answers given. Unanswered questions are not listed as fixes.");
  } else {
    lines.push(
      "Higher-weighted gaps come first. A No ranks above a Partly of the same weight.",
    );
    lines.push("");
    for (const fix of result.fixes) {
      const gapLabel = fix.answer === "no" ? "Gap" : "Partial";
      lines.push(`### ${fix.rank}. ${gapLabel} — ${fix.conditionTitle} — ${fix.sectionRef}`);
      lines.push("");
      lines.push(fix.prompt);
      lines.push("");
      lines.push(fix.action);
      lines.push("");
    }
  }

  lines.push("## Answers", "");
  for (const row of result.rows) {
    const value = row.answer ?? "unanswered";
    lines.push(`- ${row.prompt} — **${value}** (${row.sectionRef}, weight ${row.weight})`);
  }
  lines.push(
    "",
    "Stored only where you save this file. SecureCheck does not send answers to a server.",
    "",
  );
  return lines.join("\n");
}
