import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { CONDITIONS, QUESTIONS } from "../site/js/questions.js";
import { DISCLAIMER, bandFor, normaliseAnswer, scoreAudit, toMarkdown } from "../site/js/score.js";

const yes = Object.fromEntries(QUESTIONS.map((question) => [question.id, "yes"]));
const no = Object.fromEntries(QUESTIONS.map((question) => [question.id, "no"]));
const partly = Object.fromEntries(QUESTIONS.map((question) => [question.id, "partly"]));

describe("answer handling", () => {
  it("accepts only yes, partly, and no", () => {
    assert.equal(normaliseAnswer("yes"), "yes");
    assert.equal(normaliseAnswer("partly"), "partly");
    assert.equal(normaliseAnswer("no"), "no");
    assert.equal(normaliseAnswer("YES"), null);
    assert.equal(normaliseAnswer(""), null);
    assert.equal(normaliseAnswer(null), null);
    assert.equal(normaliseAnswer(1), null);
  });

  it("gives no score when nothing has been answered", () => {
    const result = scoreAudit({});
    assert.equal(result.percent, null);
    assert.equal(result.band, null);
    assert.equal(result.answered, 0);
    assert.equal(result.total, QUESTIONS.length);
    assert.equal(result.complete, false);
    assert.equal(result.earned, 0);
    assert.equal(result.possible, 0);
    assert.equal(result.fixes.length, 0);
    assert.ok(result.byCondition.every((condition) => condition.percent === null));
  });

  it("ignores unknown ids and invalid values", () => {
    const result = scoreAudit({ "not-a-question": "no", "accountability-named": "YES" });
    assert.equal(result.percent, null);
    assert.equal(result.answered, 0);
  });

  it("treats a non-object answer map as empty", () => {
    assert.equal(scoreAudit(null).percent, null);
    assert.equal(scoreAudit("yes").percent, null);
  });
});

describe("weights", () => {
  it("scores yes as full marks, partly as half, and no as zero", () => {
    const allYes = scoreAudit(yes);
    const allNo = scoreAudit(no);
    const allPartly = scoreAudit(partly);
    assert.equal(allYes.percent, 100);
    assert.equal(allYes.earned, allYes.possible);
    assert.equal(allYes.band.id, "strong");
    assert.equal(allYes.complete, true);
    assert.equal(allYes.fixes.length, 0);
    assert.equal(allNo.percent, 0);
    assert.equal(allNo.earned, 0);
    assert.equal(allNo.possible, allYes.possible);
    assert.equal(allNo.band.id, "urgent");
    assert.equal(allNo.fixes.length, QUESTIONS.length);
    assert.equal(allPartly.percent, 50);
    assert.equal(allPartly.earned, allYes.possible / 2);
    assert.equal(allPartly.band.id, "partial");
    assert.ok(allPartly.fixes.every((fix) => fix.action.startsWith("Finish what you have started.")));
  });

  it("leaves unanswered questions out of the denominator", () => {
    const result = scoreAudit({ "security-mfa": "yes", "security-patches": "no" });
    assert.equal(result.answered, 2);
    assert.equal(result.earned, 3);
    assert.equal(result.possible, 5);
    assert.equal(result.percent, 60);
    const security = result.byCondition.find((condition) => condition.id === "security-safeguards");
    assert.equal(security.answered, 2);
    assert.equal(security.total, 14);
    assert.equal(security.percent, 60);
    const accountability = result.byCondition.find((condition) => condition.id === "accountability");
    assert.equal(accountability.percent, null);
    assert.equal(accountability.answered, 0);
  });

  it("uses half weights without rounding each question first", () => {
    const conditions = [{ id: "c", title: "C", actRef: "Section 1", summary: "S" }];
    const questions = [
      { id: "a", conditionId: "c", weight: 3, sectionRef: "Section 1", prompt: "A", why: "w", fix: "Fix A." },
      { id: "b", conditionId: "c", weight: 3, sectionRef: "Section 1", prompt: "B", why: "w", fix: "Fix B." },
    ];
    const result = scoreAudit({ a: "yes", b: "partly" }, questions, conditions);
    assert.equal(result.earned, 4.5);
    assert.equal(result.possible, 6);
    assert.equal(result.percent, 75);
  });
});

describe("priority", () => {
  it("lists higher weight first, then a No above a Partly, then questionnaire order", () => {
    const conditions = [{ id: "c", title: "Condition C", actRef: "Section 1", summary: "S" }];
    const questions = [
      { id: "low-no", conditionId: "c", weight: 1, sectionRef: "Section 1", prompt: "Low", why: "w", fix: "Fix low." },
      { id: "high-partly", conditionId: "c", weight: 5, sectionRef: "Section 1", prompt: "High partial", why: "w", fix: "Fix high." },
      { id: "high-no", conditionId: "c", weight: 5, sectionRef: "Section 1", prompt: "High gap", why: "w", fix: "Fix high no." },
    ];
    const result = scoreAudit(
      { "low-no": "no", "high-partly": "partly", "high-no": "no" },
      questions,
      conditions,
    );
    assert.deepEqual(
      result.fixes.map((fix) => fix.id),
      ["high-no", "high-partly", "low-no"],
    );
    assert.equal(result.fixes[0].rank, 1);
    assert.equal(result.fixes[1].action, "Finish what you have started. Fix high.");
    assert.equal(result.percent, 23);
  });

  it("puts the section 22 questions first when every answer is no", () => {
    const result = scoreAudit(no);
    assert.deepEqual(
      result.fixes.slice(0, 3).map((fix) => fix.id),
      ["security-breach-notify", "security-breach-content", "security-loss"],
    );
    assert.equal(result.fixes[0].weight, 4);
    assert.equal(result.fixes[2].weight, 3);
  });
});

describe("bands", () => {
  it("matches the published cutoffs", () => {
    assert.equal(bandFor(0).id, "urgent");
    assert.equal(bandFor(39).id, "urgent");
    assert.equal(bandFor(40).id, "partial");
    assert.equal(bandFor(69).id, "partial");
    assert.equal(bandFor(70).id, "workable");
    assert.equal(bandFor(84).id, "workable");
    assert.equal(bandFor(85).id, "strong");
    assert.equal(bandFor(100).id, "strong");
    assert.equal(bandFor(null), null);
    assert.equal(bandFor(undefined), null);
    assert.equal(bandFor(Number.NaN), null);
    assert.equal(bandFor("85"), null);
  });
});

describe("markdown", () => {
  it("includes the disclaimer, scores, and fixes without calling the result a certificate", () => {
    const result = scoreAudit({
      "security-breach-notify": "no",
      "accountability-named": "partly",
    });
    const markdown = toMarkdown(result, {
      businessName: "Acme Stores\n## Injected",
      generatedAt: "1 January 2026",
    });
    assert.match(markdown, new RegExp(DISCLAIMER.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
    assert.match(markdown, /not a POPIA compliance certification/);
    assert.match(markdown, /Business: Acme Stores ## Injected/);
    assert.doesNotMatch(markdown, /\n## Injected/);
    assert.match(markdown, /Generated: 1 January 2026/);
    assert.match(markdown, /Security safeguards/);
    assert.match(markdown, /Section 22\(1\) and \(2\)/);
    assert.match(markdown, /Decide now who will notify the Information Regulator/);
    assert.match(markdown, /Finish what you have started\./);
    assert.doesNotMatch(markdown, /you are compliant/i);
    assert.doesNotMatch(markdown, /certified compliant/i);
    assert.match(markdown, /does not send answers to a server/);
  });

  it("says there is no score when nothing has been answered", () => {
    const markdown = toMarkdown(scoreAudit({}));
    assert.match(markdown, /No score yet/);
    assert.match(markdown, /Not started/);
  });
});

describe("catalogue", () => {
  it("covers the eight POPIA conditions with 27 weighted questions", () => {
    assert.deepEqual(
      CONDITIONS.map((condition) => condition.id),
      [
        "accountability",
        "processing-limitation",
        "purpose-specification",
        "further-processing",
        "information-quality",
        "openness",
        "security-safeguards",
        "data-subject-participation",
      ],
    );
    assert.equal(QUESTIONS.length, 27);
    assert.ok(QUESTIONS.length >= 20 && QUESTIONS.length <= 30);
    const counts = Object.fromEntries(CONDITIONS.map((condition) => [condition.id, 0]));
    const seen = new Set();
    for (const question of QUESTIONS) {
      assert.equal(seen.has(question.id), false);
      seen.add(question.id);
      assert.equal(Number.isInteger(question.weight), true);
      assert.ok(question.weight > 0);
      assert.match(question.sectionRef, /^Sections? /);
      assert.ok(question.prompt.length > 20);
      assert.ok(question.why.length > 20);
      assert.ok(question.fix.length > 20);
      assert.ok(counts[question.conditionId] !== undefined);
      counts[question.conditionId] += 1;
    }
    assert.deepEqual(counts, {
      accountability: 2,
      "processing-limitation": 3,
      "purpose-specification": 2,
      "further-processing": 1,
      "information-quality": 1,
      openness: 2,
      "security-safeguards": 14,
      "data-subject-participation": 2,
    });
  });

  it("gives security safeguards more weight than the other conditions combined", () => {
    const security = QUESTIONS.filter((question) => question.conditionId === "security-safeguards");
    const rest = QUESTIONS.filter((question) => question.conditionId !== "security-safeguards");
    const sum = (items) => items.reduce((total, question) => total + question.weight, 0);
    assert.equal(sum(security), 41);
    assert.equal(sum(rest), 26);
    assert.ok(sum(security) > sum(rest));
    const refs = security.map((question) => question.sectionRef).join(" ");
    assert.match(refs, /19\(1\)/);
    assert.match(refs, /19\(2\)/);
    assert.match(refs, /19\(3\)/);
    assert.match(refs, /Section 20/);
    assert.match(refs, /Section 21/);
    assert.match(refs, /Section 22/);
    assert.equal(CONDITIONS.find((condition) => condition.id === "security-safeguards").emphasis, true);
  });
});
