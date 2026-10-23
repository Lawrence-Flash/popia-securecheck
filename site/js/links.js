/**
 * Split plain text into text and https links.
 * A link stops at whitespace or ")", and trailing sentence punctuation
 * stays outside the address so hosts with dots are not cut short.
 */

export function splitHttpsLinks(text) {
  const source = typeof text === "string" ? text : "";
  const pattern = /https:\/\/[^\s)]+/g;
  const parts = [];
  let last = 0;
  for (const match of source.matchAll(pattern)) {
    const raw = match[0];
    const href = raw.replace(/[.,;:]+$/, "");
    if (!href) continue;
    if (match.index > last) parts.push({ kind: "text", value: source.slice(last, match.index) });
    parts.push({ kind: "link", value: href });
    last = match.index + href.length;
  }
  if (last < source.length) parts.push({ kind: "text", value: source.slice(last) });
  return parts;
}
