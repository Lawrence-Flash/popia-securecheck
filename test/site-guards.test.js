import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function read(relativePath) {
  return readFileSync(path.join(root, relativePath), "utf8");
}

function walk(directory) {
  const files = [];
  for (const entry of readdirSync(directory)) {
    const fullPath = path.join(directory, entry);
    if (statSync(fullPath).isDirectory()) files.push(...walk(fullPath));
    else files.push(fullPath);
  }
  return files;
}

const networkApis = [
  { name: "fetch", re: /\bfetch\s*\(/ },
  { name: "XMLHttpRequest", re: /\bXMLHttpRequest\b/ },
  { name: "WebSocket", re: /\bWebSocket\b/ },
  { name: "sendBeacon", re: /\bsendBeacon\s*\(/ },
  { name: "EventSource", re: /\bEventSource\b/ },
  { name: "importScripts", re: /\bimportScripts\s*\(/ },
];

describe("site stays local", () => {
  it("does not call the network from the site source", () => {
    const files = walk(path.join(root, "site")).filter((file) => /\.(js|html|css|svg)$/.test(file));
    assert.ok(files.length >= 4);
    for (const file of files) {
      const source = readFileSync(file, "utf8");
      for (const api of networkApis) {
        assert.equal(api.re.test(source), false, `${path.relative(root, file)} contains ${api.name}`);
      }
    }
  });

  it("loads no remote scripts or stylesheets", () => {
    const html = read("site/index.html");
    const css = read("site/css/styles.css");
    assert.doesNotMatch(html, /<script[^>]+src\s*=\s*["']https?:/i);
    assert.doesNotMatch(html, /<link[^>]+href\s*=\s*["']https?:/i);
    assert.doesNotMatch(css, /url\(\s*["']?https?:/i);
    assert.match(html, /<script type="module" src="js\/app\.js"><\/script>/);
  });
});

describe("required copy", () => {
  it("shows the disclaimer, the authorisation gate, and the report loader", () => {
    const html = read("site/index.html");
    const app = read("site/js/app.js");
    assert.match(html, /Not legal advice and not a POPIA compliance certification/);
    assert.match(html, /authorised me to assess its systems and domain names/);
    assert.match(html, /does not prove ownership/);
    assert.match(html, /--confirm-authorised/);
    assert.doesNotMatch(html, /Domain checks coming in PR #2/);
    assert.match(html, /id="report-file"/);
    assert.match(html, /id="report-paste"/);
    assert.match(html, /id="show-report"/);
    assert.match(html, /id="load-sample"/);
    assert.match(html, /Load sample report/);
    assert.match(html, /example-smme\.co\.za/);
    assert.match(html, /examples\/sample-securecheck-report\.json/);
    assert.match(app, /loadSampleReport/);
    assert.match(app, /splitHttpsLinks/);
    assert.match(html, /Clear saved answers/);
    assert.match(html, /Remember my answers on this device/);
    assert.match(html, /id="authorisation"/);
    assert.match(app, /reportForDisplay\(/);
  });

  it("documents local use, Pages, scope, and the MIT licence", () => {
    const readme = read("README.md");
    const licence = read("LICENSE");
    assert.match(readme, /python3 -m http\.server/);
    assert.match(readme, /python3 -m securecheck domain --confirm-authorised/);
    assert.match(readme, /examples\/sample-securecheck-report\.json/);
    assert.match(readme, /Load sample report/);
    assert.match(readme, /GitHub Pages/);
    assert.match(readme, /GitHub Actions/);
    assert.match(readme, /`site` folder/);
    assert.match(readme, /HTTPS\/TLS|HTTPS and TLS/);
    assert.match(readme, /security headers/);
    assert.match(readme, /SPF/);
    assert.match(readme, /DKIM/);
    assert.match(readme, /DMARC/);
    assert.match(readme, /privacy policy/i);
    assert.match(readme, /What's next/);
    assert.match(readme, /popia, cybersecurity, south-africa, smme, security-checklist/);
    assert.doesNotMatch(readme, /PR #2/);
    assert.doesNotMatch(readme, /PR #3/);
    assert.doesNotMatch(readme, /coming in/i);
    assert.match(readme, /Not legal advice/);
    assert.match(readme, /not a POPIA compliance certification/i);
    assert.match(readme, /Information Regulator/);
    assert.match(readme, /MIT/);
    assert.match(readme, /Responsible use/);
    assert.match(readme, /localStorage/);
    assert.match(licence, /MIT License/);
    assert.match(licence, /Copyright \(c\) 2026 Lawrence-Flash/);
  });
});
