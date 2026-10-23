# POPIA SecureCheck

A free security self-audit for South African small businesses. You answer plain-language questions in your browser, get a score against POPIA's eight conditions for lawful processing, and leave with a prioritised list of fixes. The page is static. It can be hosted on GitHub Pages at no cost.

**Not legal advice and not a POPIA compliance certification.** SecureCheck does not measure every duty in the Protection of Personal Information Act 4 of 2013, it does not know facts you do not enter, and a high score does not mean the Information Regulator would agree. Use the [Information Regulator's](https://inforegulator.org.za/) guidance, or ask a qualified professional, before you rely on a result. This project is not published by the Regulator.

## What you can do in this version

- Answer 27 yes / partly / no questions mapped to the eight conditions in section 4 of the Act.
- See an overall score, a score for each condition, and a prioritised list of plain-language fixes.
- Keep the calculation on your own device. Nothing is uploaded.
- Optionally remember answers in this browser's `localStorage`, and clear them with **Clear saved answers**.
- Download the results as Markdown, or print them.
- Confirm, with a checkbox, that you own the business or are authorised to assess it. That gate is what later domain checks will require. The checks themselves are not in this version.

There is no backend, no Google Cloud project, no Gemini or other paid API, and no build step.

## Run it locally

From the `site` folder:

```bash
cd site
python3 -m http.server 8000
```

Open <http://127.0.0.1:8000>. Serve the folder over HTTP. Opening `index.html` as a file will not load the questionnaire, because the page uses ES modules.

## Enable GitHub Pages

The site is the `site` directory. [`.github/workflows/pages.yml`](.github/workflows/pages.yml) publishes that directory with GitHub Actions. It runs when changes land on `main`.

1. Merge this project to the `main` branch.
2. In the repository, open **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. Push to `main`, or run the **Deploy GitHub Pages** workflow by hand.
5. The site is published at `https://<user>.github.io/<repository>/`. For this repository that is <https://lawrence-flash.github.io/popia-securecheck/>.

Paths are relative, so the same files work at the project-site subpath and on a local server. The first deployment can take a minute. GitHub may ask you to approve the `github-pages` environment once.

## How scoring works

Each question has a weight. **Yes** earns the full weight, **Partly** earns half, and **No** earns zero. Partly means the practice exists but is incomplete or inconsistent.

Unanswered questions are left out of both the points earned and the points available. The overall percentage is `100 × earned / available`, rounded to the nearest whole number. It uses question weights. It is not an average of the eight condition scores.

Security-safeguard questions (sections 19 to 22) carry more weight than the other seven conditions combined, so those gaps move the overall score more. Where the Act does not name a product or a template, the question describes a generally accepted safeguard a small business can put in place. Answering "No" means that safeguard is missing from your answers. It is not a court finding about your business.

| Score | Band |
| --- | --- |
| 85–100 | Strong self-assessed baseline |
| 70–84 | Workable baseline |
| 40–69 | Partial: important gaps remain |
| 0–39 | Needs urgent attention |

Fixes are sorted by weight, highest first. A **No** ranks above a **Partly** of the same weight. A high score is still not a certificate.

## What the questions follow

Section 4 of Act 4 of 2013 lists eight conditions. The questionnaire uses these section numbers:

| Condition | Sections |
| --- | --- |
| Accountability | 8 |
| Processing limitation | 9 to 12 |
| Purpose specification | 13 and 14 |
| Further processing limitation | 15 |
| Information quality | 16 |
| Openness | 17 and 18 |
| Security safeguards | 19 to 22 |
| Data subject participation | 23 to 25 |

Section 19 requires appropriate, reasonable technical and organisational measures to protect the integrity and confidentiality of personal information, including identifying foreseeable risks, putting safeguards in place, checking them, and updating them. Section 22 requires notification of a security compromise to the Information Regulator and, unless the person cannot be identified, to the data subject. The notice to the person must be in writing and must give them enough information to take protective measures. Sections 20 and 21 cover operators who process personal information for a responsible party.

The consolidated Act text is available from [SAFLII](https://www.saflii.org/za/legis/consol_act/popia4o2013399/). Section numbers in the tool are limited to the duty the question is about.

## Tests

Scoring is plain JavaScript in [`site/js/score.js`](site/js/score.js), shared by the page and the tests. No packages are installed.

```bash
node --test
```

`npm test` runs the same command. Node.js 20 or newer is required. [`.github/workflows/test.yml`](.github/workflows/test.yml) runs the tests on push and on pull requests.

## Roadmap

- **PR #2 — read-only domain checks.** Behind the ownership confirmation already on the page: HTTPS/TLS, security headers, SPF/DMARC/DKIM, an exposed-admin hint, and whether a privacy policy appears to be present. Checks stay read-only. They are not in this pull request, and this version does not contact a domain or a server.
- **PR #3 — polish.** Sharper wording, reporting, and small-business usability after the checks exist.

## Responsible use

Use SecureCheck only for a business you own or are authorised to assess. The confirmation checkbox does not prove ownership. Do not use it, or the domain checks planned for later, to probe someone else's systems.

Answers can describe real weaknesses. The Markdown download stays on your machine unless you move it. Treat that file as sensitive. On a shared computer, use **Clear saved answers** before you leave. Untick **Remember my answers on this device** if you do not want them written to `localStorage`.

## Licence

[MIT](LICENSE). Copyright (c) 2026 Lawrence-Flash.
