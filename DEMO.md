# Three-minute demo

A walkthrough for an interview or a recruiter looking at the project. Use the fictional sample. Do not scan a real site during the demo.

Say this once, near the start: **this is not legal advice and not a POPIA compliance certification.**

## 0:00 — What it is

Open the site (`python3 -m http.server 8000` from the `site` folder, or the GitHub Pages URL).

One sentence: a South African small business can score itself against POPIA's eight conditions in the browser, and can load a read-only domain report for a name it is authorised to check. The page does not upload answers and does not contact the domain.

Point at the amber **Not legal advice** banner.

## 0:45 — Sample domain report

Scroll to **Domain checks**.

1. Tick the confirmation. Say that the tick does not prove ownership, and that the checker refuses to run without `--confirm-authorised` as well.
2. Press **Load sample report**.
3. Walk the five cards for `example-smme.co.za`:
   - **In place** — HTTPS and TLS. Certificate present, name matches, TLS 1.3.
   - **Needs a look** — security headers. Content-Security-Policy and Permissions-Policy were not sent. HSTS and the framing control were.
   - **Not found** — no homepage link whose address or text contains privacy, popia, or paia. Say the notice might still exist on a page this check does not open.
   - **Needs a look** — SPF is a soft fail, DMARC is `p=none`, and no common DKIM selector was found.
   - **Needs a look** — `/wp-admin` answered 200 and `/login` answered 302. That is a hint to review who can open them. The check sent HEAD only and did not try to sign in.

Say the cards are not added up into a POPIA score. Section 19 is the neighbour for the technical checks. The privacy link sits near openness (sections 17 and 18), not section 19.

## 2:00 — Checklist

Scroll to the questionnaire. Answer three questions out loud, including one **No** under security safeguards (breach notification is a strong one: the fix links to the Information Regulator eServices portal).

Show the overall percent move, one condition bar, and the fix at the top of the list. Mention that unanswered questions are left out of the score, and that security safeguards weigh more than the other conditions combined.

## 2:40 — How a real check would run

Do not run it against a domain you do not own. Point at the command:

```bash
python3 -m securecheck domain --confirm-authorised
```

Say you would replace `domain` with a name you are authorised to check, then load `securecheck-report.json` with **Show report**. The same job can be started by hand under **Actions → Domain check**, and it stops if the authorisation box is left unticked.

## 3:00 — Close

- Static site, no backend, no paid API, no account.
- MIT licence. Responsible use: only a business you own or are authorised to assess.
- Honest limit: 27 questions and five passive checks. Not the whole Act, not a certificate, not a port scan.

If you have a few extra seconds, press **Download Markdown** and show that the file stays on the machine.
