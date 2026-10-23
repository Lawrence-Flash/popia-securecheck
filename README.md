# POPIA SecureCheck

A free security self-audit for South African small businesses. You answer plain-language questions in your browser, get a score against POPIA's eight conditions for lawful processing, and leave with a prioritised list of fixes. The page is static. It can be hosted on GitHub Pages at no cost.

**Not legal advice and not a POPIA compliance certification.** SecureCheck does not measure every duty in the Protection of Personal Information Act 4 of 2013, it does not know facts you do not enter, and a high score does not mean the Information Regulator would agree. Use the [Information Regulator's](https://inforegulator.org.za/) guidance, or ask a qualified professional, before you rely on a result. This project is not published by the Regulator.

## What you can do in this version

- Answer 27 yes / partly / no questions mapped to the eight conditions in section 4 of the Act.
- See an overall score, a score for each condition, and a prioritised list of plain-language fixes.
- Keep the calculation on your own device. Nothing is uploaded.
- Optionally remember answers in this browser's `localStorage`, and clear them with **Clear saved answers**.
- Download the results as Markdown, or print them.
- Confirm, with a checkbox, that you own the business or are authorised to assess it. Domain checks stay closed until that box is ticked, and the checker itself will not run without the same confirmation.
- Run read-only checks against a domain you own or are authorised to test, then load the JSON report into the page. The page does not contact the domain.

There is no backend, no Google Cloud project, no Gemini or other paid API, and no build step. The domain checker uses the Python 3 standard library only.

## Run it locally

From the `site` folder:

```bash
cd site
python3 -m http.server 8000
```

Open <http://127.0.0.1:8000>. Serve the folder over HTTP. Opening `index.html` as a file will not load the questionnaire, because the page uses ES modules.

## Check a domain locally (including WSL)

Run this from the repository folder, the one that contains the `securecheck` package. In Ubuntu on WSL that is the same command as on any other Linux terminal. Python 3 is enough. There is no `pip install`.

```bash
cd /path/to/popia-securecheck
python3 -m securecheck your-domain.co.za --confirm-authorised
```

Pass `--confirm-authorised` only if you own that domain or the owner has authorised you to assess it. The flag does not prove ownership. Without it, the command stops before it contacts the domain.

The command writes `securecheck-report.json` in the current directory. It is gitignored. Then:

1. Start the site with `python3 -m http.server` from the `site` folder, as above.
2. Tick the ownership confirmation.
3. Choose `securecheck-report.json`, or paste it, and press **Show report**.

Use `-o -` to print the JSON to the terminal instead of a file. `python3 -m securecheck --help` lists the options.

The checker is passive:

- HTTPS on port 443 only: is a certificate present, is it unexpired, does the name match, and which TLS version and cipher were negotiated.
- Security headers on the homepage response: HSTS, Content-Security-Policy, X-Content-Type-Options, X-Frame-Options or CSP `frame-ancestors`, Referrer-Policy, and Permissions-Policy.
- SPF and DMARC TXT records, plus DKIM at a short fixed list of common selectors. DNS uses DNS-over-HTTPS to Cloudflare, then Quad9 if Cloudflare does not answer.
- HEAD requests, and only HEAD, to `/admin`, `/wp-admin`, `/administrator`, and `/login`. The report contains status codes. It does not follow those redirects or try to sign in.
- Whether the homepage HTML contains a link whose address or text contains privacy, popia, or paia.

It does not scan ports, run nmap, try passwords, crawl the site, query Have I Been Pwned, or call a paid API. A missing header or a missing DNS record is a gap in this check. It is not a finding by the Information Regulator, and it is not a POPIA compliance certification.

On the page, each result is written in plain language. Where a result honestly relates to a POPIA duty, the card says so: TLS, headers, email authentication, and the admin hint sit near section 19 (security safeguards). A privacy or PAIA link sits near sections 17 and 18 (openness), not section 19. The Act does not name TLS versions, header names, SPF, DKIM, or DMARC.

## Run the same check in GitHub Actions

[`.github/workflows/domain-check.yml`](.github/workflows/domain-check.yml) runs the same `python3 -m securecheck` command. It does not run on push. You start it by hand:

1. Open **Actions → Domain check → Run workflow**.
2. Enter the domain.
3. Tick **I own this domain or I am authorised to check it**. Leave it unticked and the job stops before any check.
4. Download the `securecheck-report` artifact and load that JSON on the site.

GitHub's runner sees the public HTTPS and DNS view of the domain. A name that only resolves inside your WSL network will not check the same way there. Use the local command for that.

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
python3 -m unittest discover -s test -p 'test_*.py'
```

`npm test` runs both. Node.js 20 or newer is required for the questionnaire tests. The domain-check tests use Python 3 and mocked sockets and responses, so they do not contact a domain. [`.github/workflows/test.yml`](.github/workflows/test.yml) runs both on push and on pull requests.

## Roadmap

- **PR #2 — read-only domain checks.** HTTPS/TLS, security headers, SPF, DKIM and DMARC, an exposed-admin hint, and whether a privacy policy link appears on the homepage. The ownership confirmation on the page, and `--confirm-authorised` on the command, both have to be given before a check is shown or run.
- **PR #3 — polish.** Sharper wording, reporting, and small-business usability now that the checks exist.

## Responsible use

Use SecureCheck only for a business you own or are authorised to assess. The confirmation checkbox does not prove ownership, and neither does `--confirm-authorised`. Do not use the domain checker to probe someone else's systems.

Answers can describe real weaknesses. The Markdown download stays on your machine unless you move it. Treat that file as sensitive. On a shared computer, use **Clear saved answers** before you leave. Untick **Remember my answers on this device** if you do not want them written to `localStorage`.

## Licence

[MIT](LICENSE). Copyright (c) 2026 Lawrence-Flash.
