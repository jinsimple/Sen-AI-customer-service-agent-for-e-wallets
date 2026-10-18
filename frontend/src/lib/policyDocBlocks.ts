// ADR-065 polish (Sep 5, caught by the PO from a shoot screenshot) — `full_text` is read from the
// docx via raw extraction: a SECTION/ARTICLE heading often STICKS right onto the end of the
// previous section's last sentence, with NO line break (real example, MoMo_FAQ_Giao_dich.docx:
// "...the transaction will fail.67. How to withdraw from MoMo to a linked bank account\n") —
// dumping `full_text` straight into one `pre-wrap` block turns the whole page into one flat
// paragraph, each section stuck to the previous one's tail.
//
// This module ONLY computes block COORDINATES (start/end within the ORIGINAL `full_text` itself, no
// slicing/joining of strings) — deliberately not mutating the text so the backend's `highlight`
// offset (original ADR-065) stays exactly correct, with no recomputation needed.
export type PolicyDocBlockType = "heading" | "url" | "para" | "blank";

export interface PolicyDocBlock {
  type: PolicyDocBlockType;
  text: string; // already trimmed, used ONLY for RENDERING — the start/end coordinates still point into the ORIGINAL full_text
  start: number;
  end: number;
}

// An end-of-sentence punctuation mark, IMMEDIATELY FOLLOWED by a list number (FAQ "67. " or a ToS
// "1.1. ") and then an UPPERCASE letter — the REAL signature of a heading stuck to a tail (not a
// monetary amount like "30,000,000đ", because that form has no space after its final dot). `\p{Lu}`
// (Unicode uppercase) instead of hand-listing every accented Vietnamese uppercase letter — a hand
// list is easy to miss some; `\p{Lu}` matches EVERY Unicode uppercase letter (Á/Đ/Ơ/Ư... are all in
// the Lu category).
// `(?<!\d)` blocks a FALSE SELF-MATCH inside a multi-level ToS number like "1.1." — without it, the
// regex would read "1" + "." (middle) + "1. " as a fake heading, splitting "1.1." in two as "1." +
// "1. ...". A REAL end-of-sentence mark never sits right after a digit that is part of that very
// list number.
const GLUED_HEADING_RE = /(?<!\d)[.!?](\d+(?:\.\d+)*\.\s+)(?=\p{Lu})/gu;
// A heading that's already on its own line (doesn't need the stuck-tail fix) — FAQ "N. question",
// ToS "N.N. clause name". Can't be told apart from a numbered sub-item inside one answer (accepted
// — the sub-item gets bolded a bit more than it should, NOT the "stuck text" bug the PO caught;
// this trade-off buys a simpler, easier-to-audit rule).
const HEADING_LINE_RE = /^\d+(?:\.\d+)*\.\s+\S/;
const URL_LINE_RE = /^https?:\/\//;

export function splitPolicyDocBlocks(fullText: string): PolicyDocBlock[] {
  const boundaries = new Set<number>([0, fullText.length]);
  let idx = fullText.indexOf("\n");
  while (idx !== -1) {
    boundaries.add(idx + 1);
    idx = fullText.indexOf("\n", idx + 1);
  }
  for (const m of fullText.matchAll(GLUED_HEADING_RE)) {
    // m.index points at the end-of-sentence punctuation — the split point is RIGHT AFTER that mark
    // (the start of the list number), not taken from group 1 (a group's offset drifts from m.index
    // depending on the length of whatever matched before it; using m.index + 1 because the
    // punctuation mark is always exactly 1 character).
    boundaries.add(m.index + 1);
  }

  const sorted = [...boundaries].sort((a, b) => a - b);
  const blocks: PolicyDocBlock[] = [];
  for (let i = 0; i < sorted.length - 1; i++) {
    const start = sorted[i];
    const end = sorted[i + 1];
    const trimmed = fullText.slice(start, end).trim();
    let type: PolicyDocBlockType;
    if (!trimmed) type = "blank";
    else if (URL_LINE_RE.test(trimmed)) type = "url";
    else if (HEADING_LINE_RE.test(trimmed)) type = "heading";
    else type = "para";
    blocks.push({ type, text: trimmed, start, end });
  }
  return blocks;
}

/**
 * Whether a block overlaps [hlStart, hlEnd) — using a standard interval overlap, not requiring an
 * exact match (the backend computes the highlight offset against exactly 1 chunk, which can drift a
 * few characters from the block boundary due to trimming).
 */
export function blockOverlapsHighlight(block: PolicyDocBlock, hlStart: number, hlEnd: number): boolean {
  return block.end > hlStart && block.start < hlEnd;
}
