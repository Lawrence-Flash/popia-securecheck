/**
 * POPIA SecureCheck question catalogue.
 *
 * Mapped to the eight conditions for lawful processing in section 4 of the
 * Protection of Personal Information Act 4 of 2013. Section citations are
 * the conditions the question is about. Where the Act does not name a
 * specific control, the question describes a generally accepted safeguard
 * a small business can put in place. That is a self-audit judgement, not a
 * court ruling and not a certification.
 */

export const CONDITIONS = [
  {
    id: "accountability",
    title: "Accountability",
    actRef: "Section 8",
    summary:
      "Section 8 says the responsible party must make sure the conditions in this chapter are met when the purpose and means of processing are decided, and for as long as processing continues.",
  },
  {
    id: "processing-limitation",
    title: "Processing limitation",
    actRef: "Sections 9 to 12",
    summary:
      "Use personal information lawfully and reasonably (section 9), keep it adequate, relevant and not excessive (section 10), rely on a ground listed in section 11, and collect it from the person unless a section 12 exception applies.",
  },
  {
    id: "purpose-specification",
    title: "Purpose specification",
    actRef: "Sections 13 and 14",
    summary:
      "Collect personal information for a specific, explicitly defined and lawful purpose (section 13). Do not keep records longer than section 14 allows, and then destroy, delete, or de-identify them so they cannot be reconstructed.",
  },
  {
    id: "further-processing",
    title: "Further processing limitation",
    actRef: "Section 15",
    summary:
      "A later use must be compatible with the purpose of collection, unless a section 15 allowance applies (including consent to that further use).",
  },
  {
    id: "information-quality",
    title: "Information quality",
    actRef: "Section 16",
    summary:
      "Take reasonably practicable steps so personal information is complete, accurate, not misleading, and updated where necessary, having regard to the purpose.",
  },
  {
    id: "openness",
    title: "Openness",
    actRef: "Sections 17 and 18",
    summary:
      "Keep documentation of the processing you are responsible for (section 17, which points to the PAIA manual duties). When you collect personal information, take practical steps so the person knows what section 18 requires them to be told.",
  },
  {
    id: "security-safeguards",
    title: "Security safeguards",
    actRef: "Sections 19 to 22",
    emphasis: true,
    summary:
      "Section 19 requires appropriate, reasonable technical and organisational measures: identify foreseeable risks, put safeguards in place, check that they work, and update them. Sections 20 and 21 cover operators who process personal information for you. Section 22 requires notification of a security compromise to the Information Regulator and to affected people. These questions carry more of the overall score. Where the Act does not name a product or a template, the question is a practical safeguard, not a line quoted from the Act.",
  },
  {
    id: "data-subject-participation",
    title: "Data subject participation",
    actRef: "Sections 23 to 25",
    summary:
      "People may ask you to confirm what you hold about them and to correct or delete it in the cases sections 23 and 24 describe. Section 25 points to the PAIA rules for the manner of access.",
  },
];

export const QUESTIONS = [
  {
    id: "accountability-named",
    conditionId: "accountability",
    weight: 2,
    sectionRef: "Section 8",
    prompt:
      "Is one person in the business clearly responsible for checking that the POPIA conditions are met?",
    why:
      "Section 8 requires the responsible party to ensure the Chapter 3 conditions are complied with. The Act does not, in this section, prescribe a job title. Naming a person is how a small business makes that duty real.",
    fix:
      "Choose one owner or manager. Write down their name and tell staff that this person checks how the business handles personal information.",
  },
  {
    id: "accountability-timing",
    conditionId: "accountability",
    weight: 2,
    sectionRef: "Section 8",
    prompt:
      "Does that person check the conditions both when you decide why and how personal information will be used, and again while you are still using it?",
    why:
      "Section 8 applies at the time the purpose and means of the processing are determined, and during the processing itself.",
    fix:
      "Add two checks to that person's work: one before you start using a new kind of personal information, and a regular look at the information you already hold.",
  },
  {
    id: "limitation-minimal",
    conditionId: "processing-limitation",
    weight: 2,
    sectionRef: "Section 10",
    prompt:
      "Do you use only personal information that is enough for the purpose, relevant to it, and not more than you need?",
    why:
      "Section 10 says personal information may be processed only if, given the purpose for which it is processed, it is adequate, relevant and not excessive.",
    fix:
      "Look at each form, inbox, and spreadsheet. Stop collecting fields you do not use, such as an ID number or a home address when a name and a phone number will do.",
  },
  {
    id: "limitation-lawful",
    conditionId: "processing-limitation",
    weight: 2,
    sectionRef: "Sections 9 and 11",
    prompt:
      "Before you use someone's personal information, can you point to a lawful reason, such as consent, a contract, a legal duty, or another ground listed in section 11?",
    why:
      "Section 9 requires processing to be lawful and reasonable. Section 11 allows processing only on a listed ground. Consent is one of those grounds, not the only one. If you rely on consent, section 11(2) says you bear the burden of proof.",
    fix:
      "For each main use (sales, payroll, deliveries, marketing), write the section 11 ground you rely on. If the ground is consent, keep a record of it, and remember consent can be withdrawn.",
  },
  {
    id: "limitation-direct",
    conditionId: "processing-limitation",
    weight: 2,
    sectionRef: "Section 12",
    prompt:
      "Do you collect personal information from the person it is about, unless a section 12 exception applies?",
    why:
      "Section 12 says personal information must be collected directly from the data subject, except in the cases the section lists. Those include information in a public record, consent to collect it elsewhere, and cases where direct collection is not reasonably practicable.",
    fix:
      "Where you can, ask the person yourself. If you receive information from someone else, note which section 12 exception you are relying on.",
  },
  {
    id: "purpose-specific",
    conditionId: "purpose-specification",
    weight: 2,
    sectionRef: "Section 13",
    prompt:
      "Is personal information collected for a specific purpose you can state in plain language, and is that purpose lawful and related to what the business does?",
    why:
      "Section 13 requires collection for a specific, explicitly defined and lawful purpose related to a function or activity of the responsible party.",
    fix:
      "Write one sentence for each kind of record: who it is about, what you collect, and the purpose. Stop purposes you cannot explain in a sentence.",
  },
  {
    id: "purpose-retention",
    conditionId: "purpose-specification",
    weight: 2,
    sectionRef: "Section 14",
    prompt:
      "When you no longer have a lawful reason to keep a record of personal information, do you delete, destroy, or de-identify it so that it cannot be reconstructed?",
    why:
      "Section 14 says records must not be retained longer than necessary for the purpose, unless a listed reason applies, such as a law, a contract, or consent. When you may no longer keep the record, section 14(4) and (5) require you to destroy or delete it, or de-identify it, in a manner that prevents its reconstruction in an intelligible form.",
    fix:
      "Set a keep-until date for customer, supplier, and staff records. When the date passes, delete the copies you no longer have a reason to keep, including downloads and old spreadsheets, in a way that stops the record being rebuilt.",
  },
  {
    id: "further-compatible",
    conditionId: "further-processing",
    weight: 2,
    sectionRef: "Section 15",
    prompt:
      "Before you use personal information for a new purpose, do you check that the new use fits the original purpose, or that a section 15 allowance applies?",
    why:
      "Section 15 says further processing must be compatible with the purpose for which the information was collected. Section 15(3) lists cases that are not incompatible, including where the person has consented to the further processing.",
    fix:
      "When someone suggests a new use, such as marketing to people on old invoices, pause. Write down the original purpose and why the new use does or does not fit. If it does not fit, get a fresh lawful ground before you continue.",
  },
  {
    id: "quality-accurate",
    conditionId: "information-quality",
    weight: 2,
    sectionRef: "Section 16",
    prompt:
      "Do you take practical steps to keep personal information complete, accurate, not misleading, and updated where that matters for the purpose?",
    why:
      "Section 16 requires reasonably practicable steps to that effect. In taking them, you must have regard to the purpose for which the information is collected or further processed.",
    fix:
      "Once or twice a year, ask customers and staff to confirm the details you still use. Correct errors when someone tells you about them. Do not keep two conflicting versions of the same record.",
  },
  {
    id: "openness-documentation",
    conditionId: "openness",
    weight: 2,
    sectionRef: "Section 17",
    prompt:
      "Do you keep documentation of the personal-information processing your business is responsible for?",
    why:
      "Section 17 requires a responsible party to maintain the documentation of all processing operations under its responsibility, as referred to in section 14 or section 51 of the Promotion of Access to Information Act.",
    fix:
      "Write down what you collect, why, who you share it with, and how long you keep it. Check whether your business must also publish that documentation as a PAIA manual, and update it when the processing changes.",
  },
  {
    id: "openness-notice",
    conditionId: "openness",
    weight: 2,
    sectionRef: "Section 18",
    prompt:
      "When you collect personal information, do you take practical steps so the person knows what is being collected, who you are, why you need it, and whether they are required to provide it?",
    why:
      "Section 18 requires reasonably practicable steps so the data subject is aware of the information being collected, your name and address, the purpose, and whether supply is voluntary or mandatory, plus other matters the section lists where they apply. Section 18(4) sets out exceptions. When you collect directly from the person, the steps are taken before collection unless they already know.",
    fix:
      "Add a short notice to forms, quotes, and sign-up sheets: your business name, what you are collecting, the purpose, whether it is voluntary or mandatory, and how to contact you.",
  },
  {
    id: "security-loss",
    conditionId: "security-safeguards",
    weight: 3,
    sectionRef: "Section 19(1)(a)",
    prompt:
      "Do you protect personal information against loss, damage, and unauthorised destruction, including a backup you have tested by restoring it?",
    why:
      "Section 19(1)(a) requires appropriate, reasonable technical and organisational measures to prevent loss of, damage to, or unauthorised destruction of personal information. The Act does not name a backup product. A backup you have never restored is a weak safeguard.",
    fix:
      "Keep a backup of the records you would struggle to recreate, store it somewhere separate from the original, and restore a test file so you know the backup works. Lock cupboards that hold paper files such as IDs and bank letters.",
  },
  {
    id: "security-access",
    conditionId: "security-safeguards",
    weight: 3,
    sectionRef: "Section 19(1)(b)",
    prompt:
      "Is access to personal information limited to people who need it for their work, with each person using their own login?",
    why:
      "Section 19(1)(b) requires appropriate, reasonable measures to prevent unlawful access to or processing of personal information. Separate logins are a generally accepted way to do that. The Act does not name a particular system.",
    fix:
      "Stop shared passwords. Give each person their own account, and limit customer lists, payroll, and inboxes to the people who actually need them.",
  },
  {
    id: "security-mfa",
    conditionId: "security-safeguards",
    weight: 3,
    sectionRef: "Section 19(1)(b)",
    prompt:
      "Is multi-factor authentication turned on for email and for other accounts that can open personal information?",
    why:
      "Section 19 requires reasonable measures against unlawful access, and section 19(3) says you must have due regard to generally accepted information security practices. A second sign-in step is one of those practices. The Act does not name a product, and this question is not a finding that every account in every business must use a particular app.",
    fix:
      "Turn on multi-factor authentication for business email first, then for banking, payroll, cloud storage, and the website host. Save the backup codes somewhere offline.",
  },
  {
    id: "security-leavers",
    conditionId: "security-safeguards",
    weight: 3,
    sectionRef: "Section 19(1)(b)",
    prompt:
      "Do you remove or change access when someone leaves the business, or when they no longer need it for their work?",
    why:
      "Old accounts are a foreseeable route to unlawful access. Section 19(1)(b) requires reasonable measures to prevent unlawful access. The Act does not set a number of hours. Same-day removal is the practical version of that duty.",
    fix:
      "Keep a list of systems that hold personal information. On the day someone leaves or changes role, remove their email, shared drives, shop system, and social accounts. Change any password they knew.",
  },
  {
    id: "security-patches",
    conditionId: "security-safeguards",
    weight: 2,
    sectionRef: "Section 19(3)",
    prompt:
      "Do you install security updates for the phones, computers, and software that store or send personal information?",
    why:
      "Section 19(3) says the responsible party must have due regard to generally accepted information security practices and procedures, including industry or professional rules that apply. Installing known security fixes is one of those practices. The Act does not name a vendor.",
    fix:
      "Turn on automatic updates for phones, laptops, and the software you use for email, accounting, and the website. Once a month, check that the updates actually installed.",
  },
  {
    id: "security-staff",
    conditionId: "security-safeguards",
    weight: 2,
    sectionRef: "Section 19(1)",
    prompt:
      "Have staff been told, in plain language, how to handle personal information and not to share passwords or act on unexpected payment and login requests?",
    why:
      "Section 19(1) calls for organisational measures as well as technical ones. People who handle personal information need to know the basic rules. A briefing is a practical measure, not a form prescribed by the Act.",
    fix:
      "Give every person who sees customer or staff information a one-page briefing: no shared passwords, no personal information in an open chat group, and how to pause before paying or logging in from an unexpected message.",
  },
  {
    id: "security-risks",
    conditionId: "security-safeguards",
    weight: 3,
    sectionRef: "Section 19(2)(a)",
    prompt:
      "Have you identified the main internal and external risks to personal information in the business's possession or under its control?",
    why:
      "Section 19(2)(a) requires reasonable measures to identify all reasonably foreseeable internal and external risks to personal information in your possession or under your control.",
    fix:
      "List the places personal information sits: email, the till, payroll, paper files, phones, and the bookkeeper. Next to each, write how it could be lost or seen by the wrong person. Include staff mistakes, a lost phone, and a break-in.",
  },
  {
    id: "security-verify",
    conditionId: "security-safeguards",
    weight: 3,
    sectionRef: "Section 19(2)(b) and (c)",
    prompt:
      "Have you put safeguards in place for those risks, and do you check from time to time that the safeguards are actually being followed?",
    why:
      "Section 19(2)(b) requires appropriate safeguards against the risks identified. Section 19(2)(c) requires you to regularly verify that the safeguards are effectively implemented.",
    fix:
      "For each risk on your list, write the safeguard you use. Twice a year, check a sample: are former staff off the accounts, can a backup be restored, and are paper files still locked?",
  },
  {
    id: "security-update",
    conditionId: "security-safeguards",
    weight: 3,
    sectionRef: "Section 19(2)(d)",
    prompt: "When you find a new risk or a gap in a safeguard, do you update the safeguard?",
    why:
      "Section 19(2)(d) requires safeguards to be continually updated in response to new risks or deficiencies in safeguards already implemented.",
    fix:
      "After a near miss, a new system, or a staff change, update the written safeguards. Give each known gap an owner and a date. Do not leave it only on a list.",
  },
  {
    id: "security-operator-authority",
    conditionId: "security-safeguards",
    weight: 2,
    sectionRef: "Section 20",
    prompt:
      "Do suppliers and other people who process personal information for you do so only with your knowledge or authorisation, and do they keep it confidential?",
    why:
      "Section 20 says an operator, or anyone processing personal information on behalf of a responsible party or an operator, must process it only with the knowledge or authorisation of the responsible party, and must treat it as confidential, unless the law or the proper performance of their duties requires otherwise.",
    fix:
      "List every bookkeeper, payroll bureau, mailing tool, website host, and freelancer who can see personal information. Confirm you asked them to do that work, and that they know not to use the information for their own purposes or to pass it on.",
  },
  {
    id: "security-operator-contract",
    conditionId: "security-safeguards",
    weight: 3,
    sectionRef: "Section 21",
    prompt:
      "Is there a written contract that requires each operator to keep the section 19 security measures, and to tell you immediately if they reasonably believe an unauthorised person accessed or acquired the personal information?",
    why:
      "Section 21(1) requires a written contract between the responsible party and the operator so that the operator establishes and maintains the section 19 security measures. Section 21(2) requires the operator to notify the responsible party immediately where there are reasonable grounds to believe personal information has been accessed or acquired by an unauthorised person.",
    fix:
      "For each supplier who processes personal information for you, put those two duties in a signed contract or a signed addendum. A verbal understanding does not meet section 21(1).",
  },
  {
    id: "security-breach-notify",
    conditionId: "security-safeguards",
    weight: 4,
    sectionRef: "Section 22(1) and (2)",
    prompt:
      "If you had reasonable grounds to believe an unauthorised person had accessed or acquired personal information, would you notify the Information Regulator and, unless you cannot identify them, the people affected, as soon as reasonably possible?",
    why:
      "Section 22(1) requires notification of the Information Regulator and of the data subject, unless the data subject's identity cannot be established. Section 22(2) says notification must be made as soon as reasonably possible after discovery, taking into account the legitimate needs of law enforcement or measures reasonably necessary to determine the scope and to restore the integrity of the system. Section 22(3) allows a delay in telling the data subject only if a public body responsible for the prevention, detection or investigation of offences, or the Regulator, determines that notification will impede a criminal investigation.",
    fix:
      "Decide now who will notify the Information Regulator and who will contact affected customers or staff. Do not wait for a perfect investigation before you start. Section 22 is the legal duty. Separately, the Regulator has directed organisations to report security compromises through its eServices portal from 1 April 2025 (https://eservices.inforegulator.org.za/compromises/default.aspx). Check the Regulator's website in case that process changes.",
  },
  {
    id: "security-breach-content",
    conditionId: "security-safeguards",
    weight: 4,
    sectionRef: "Section 22(4) and (5)",
    prompt:
      "Would the notice to affected people be in writing, and would it describe the possible consequences, what you are doing about the compromise, what they can do to protect themselves, and the identity of the unauthorised person if you know it?",
    why:
      "Section 22(4) requires the notification to a data subject to be in writing and communicated by at least one listed method, such as post, email, a prominent notice on the responsible party's website, or the news media, or as the Regulator directs. Section 22(5) requires enough information for the person to take protective measures, including the possible consequences, the measures you intend to take or have taken, a recommendation of what the person can do, and, if known, the identity of the unauthorised person.",
    fix:
      "Draft a one-page notice now, with blanks for the date, what was involved, the possible harm, the steps you are taking, and the steps the person should take. Keep it where more than one person can find it during an incident.",
  },
  {
    id: "security-breach-plan",
    conditionId: "security-safeguards",
    weight: 3,
    sectionRef: "Section 22",
    prompt:
      "Do you have a short written plan for the first hours of a suspected compromise: who to call, how to stop further access, and what to record?",
    why:
      "POPIA does not prescribe a named internal template. Section 22 does require notification as soon as reasonably possible once there are reasonable grounds to believe personal information was accessed or acquired by an unauthorised person. A short plan is how a small business makes that duty workable. It is a practical aid, not a form the Act requires by name.",
    fix:
      "On one page, write who decides that a compromise may have happened, who to contact (including any operator, under section 21(2)), how you stop further access without wiping what you may need to understand the incident, and where you record times and facts.",
  },
  {
    id: "participation-access",
    conditionId: "data-subject-participation",
    weight: 2,
    sectionRef: "Section 23",
    prompt:
      "If a person proves who they are and asks, can you confirm free of charge whether you hold personal information about them, and provide the record or a description of it within a reasonable time?",
    why:
      "Section 23(1) gives a data subject who has provided adequate proof of identity the right to request confirmation, free of charge, of whether you hold personal information about them, and to request the record or a description of it, including third parties who have had access, within a reasonable time. A prescribed fee may apply to the copy, and section 23(3) requires a written estimate before you provide a service you will charge for. Section 23(2) says that if you communicate the information, you must advise the person of the right to request correction under section 24. Section 25 says the manner of access follows sections 18 and 53 of the Promotion of Access to Information Act.",
    fix:
      "Choose one inbox for these requests. Agree who checks identity, confirms whether you hold information (free of charge), and responds. If you charge a fee for the copy, give a written estimate first. When you release information, tell the person they may ask for a correction under section 24.",
  },
  {
    id: "participation-correction",
    conditionId: "data-subject-participation",
    weight: 2,
    sectionRef: "Section 24",
    prompt:
      "If someone asks you to correct or delete personal information that is inaccurate, irrelevant, excessive, out of date, incomplete, misleading, unlawfully obtained, or no longer allowed to be kept, can you act as soon as reasonably practicable and tell them what you did?",
    why:
      "Section 24 lets a data subject request correction or deletion of personal information in those cases, and destruction or deletion of a record the responsible party is no longer authorised to retain under section 14. On receipt, the responsible party must, as soon as reasonably practicable, correct, destroy or delete the information, or provide credible evidence in support of it, or attach a note that a correction was requested but not made where agreement cannot be reached. Section 24(4) requires you to notify the data subject of the action taken.",
    fix:
      "Write a three-step routine: log the request, correct or delete the record including the working copies, and reply to the person with what you did. If you disagree, follow the alternatives in section 24(2), including the option to attach a note that a correction was requested but not made.",
  },
];
