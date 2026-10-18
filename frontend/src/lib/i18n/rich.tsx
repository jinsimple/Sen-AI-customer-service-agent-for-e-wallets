import { Fragment, type ReactNode } from "react";

/**
 * Render a dictionary string containing a tiny markup subset: <b>…</b>, <strong>…</strong>, <i>…</i>.
 * Keeps one layout for both languages while letting translators place emphasis naturally.
 * `bStyle` is applied to <b> (the landing page highlights bold fragments in the main text colour).
 * Tags do not nest; that is all the UI copy needs.
 */
export function rich(text: string, bStyle?: React.CSSProperties): ReactNode {
  const parts = text.split(/(<b>[\s\S]*?<\/b>|<strong>[\s\S]*?<\/strong>|<i>[\s\S]*?<\/i>)/g);
  return parts.map((p, i) => {
    if (p.startsWith("<b>")) return <b key={i} style={bStyle}>{p.slice(3, -4)}</b>;
    if (p.startsWith("<strong>")) return <strong key={i}>{p.slice(8, -9)}</strong>;
    if (p.startsWith("<i>")) return <i key={i}>{p.slice(3, -4)}</i>;
    return <Fragment key={i}>{p}</Fragment>;
  });
}
