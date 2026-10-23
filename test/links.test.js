import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { splitHttpsLinks } from "../site/js/links.js";

describe("https links in fix text", () => {
  it("keeps the Information Regulator eServices path intact", () => {
    const text =
      "Report a compromise at https://eservices.inforegulator.org.za/compromises/default.aspx. Check the Regulator's site if that process changes.";
    const parts = splitHttpsLinks(text);
    assert.equal(parts.map((part) => part.value).join(""), text);
    assert.deepEqual(
      parts.filter((part) => part.kind === "link").map((part) => part.value),
      ["https://eservices.inforegulator.org.za/compromises/default.aspx"],
    );
  });

  it("leaves a closing parenthesis and a following sentence outside the link", () => {
    const text = "Use the portal (https://eservices.inforegulator.org.za/compromises/default.aspx). Then stop.";
    const parts = splitHttpsLinks(text);
    assert.equal(parts.map((part) => part.value).join(""), text);
    assert.equal(parts[1].kind, "link");
    assert.equal(parts[1].value, "https://eservices.inforegulator.org.za/compromises/default.aspx");
    assert.match(parts[2].value, /^\)\. Then stop\.$/);
  });
});
