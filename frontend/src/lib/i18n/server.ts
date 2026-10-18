import "server-only";
import { cookies, headers } from "next/headers";
import { LANG_COOKIE, makeT, resolveLang, type Lang, type TFn } from "./core";

/** The UI language for the current request (cookie first, then Accept-Language). */
export async function getLang(): Promise<Lang> {
  const [c, h] = await Promise.all([cookies(), headers()]);
  return resolveLang(c.get(LANG_COOKIE)?.value, h.get("accept-language"));
}

/** Server-component translator bound to the current request's language. */
export async function getT(): Promise<{ lang: Lang; t: TFn }> {
  const lang = await getLang();
  return { lang, t: makeT(lang) };
}
