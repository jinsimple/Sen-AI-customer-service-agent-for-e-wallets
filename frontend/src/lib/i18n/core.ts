// Shared i18n primitives — safe to import from both server and client components.
//
// Design (portfolio edition):
//   · Two languages, `vi` (the product's native language) and `en`.
//   · The choice lives in the `lang` cookie (set by <LanguageToggle/>). With no cookie, the server
//     falls back to the browser's Accept-Language: Vietnamese browsers get `vi`, everyone else `en`.
//   · Components rendered WITHOUT a provider (unit tests, isolated renders) default to `vi`, so the
//     existing Vietnamese test assertions keep their meaning.
//   · Only UI chrome is translated. Conversation content (the agent's replies, ticket descriptions
//     typed by customers) and backend-generated messages stay in the language they were written in.
import { DICT, type DictKey } from "./dict";

export type Lang = "vi" | "en";
export const LANGS: Lang[] = ["vi", "en"];
export const LANG_COOKIE = "lang";
export const DEFAULT_LANG_NO_PROVIDER: Lang = "vi";

export function isLang(v: unknown): v is Lang {
  return v === "vi" || v === "en";
}

/** Resolve the language from an explicit cookie value, else from an Accept-Language header. */
export function resolveLang(cookieValue: string | undefined, acceptLanguage: string | null | undefined): Lang {
  if (isLang(cookieValue)) return cookieValue;
  const first = (acceptLanguage ?? "").split(",")[0]?.trim().toLowerCase() ?? "";
  return first.startsWith("vi") ? "vi" : "en";
}

export type Vars = Record<string, string | number>;

/** Look up a key and interpolate `{name}` placeholders. Unknown keys fall back to the key itself. */
export function translate(lang: Lang, key: DictKey, vars?: Vars): string {
  const entry = DICT[key];
  let s: string = entry ? entry[lang] : key;
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.split(`{${k}}`).join(String(v));
  return s;
}

export type TFn = (key: DictKey, vars?: Vars) => string;
export function makeT(lang: Lang): TFn {
  return (key, vars) => translate(lang, key, vars);
}

/** The language the current page was rendered in (`<html lang>`), for non-React client code such
 *  as the fetch wrapper. Falls back to the no-provider default outside a browser. */
export function docLang(): Lang {
  if (typeof document === "undefined") return DEFAULT_LANG_NO_PROVIDER;
  const l = document.documentElement.lang;
  return isLang(l) ? l : DEFAULT_LANG_NO_PROVIDER;
}

/** BCP-47 locale used for number/date formatting in each UI language. */
export function localeOf(lang: Lang): string {
  return lang === "en" ? "en-US" : "vi-VN";
}
