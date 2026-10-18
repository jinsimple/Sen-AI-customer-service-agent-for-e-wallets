"use client";

import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { DEFAULT_LANG_NO_PROVIDER, LANG_COOKIE, localeOf, makeT, type Lang, type TFn } from "./core";

type Ctx = { lang: Lang; t: TFn; locale: string; setLang: (l: Lang) => void };

const I18nContext = createContext<Ctx | null>(null);

export function I18nProvider({ lang, children }: { lang: Lang; children: ReactNode }) {
  const router = useRouter();
  const setLang = useCallback(
    (next: Lang) => {
      // One year, whole site. Not httpOnly: it is a UI preference, not a credential.
      document.cookie = `${LANG_COOKIE}=${next}; path=/; max-age=31536000; samesite=lax`;
      document.documentElement.lang = next;
      // Re-render server components (layouts, server pages) in the new language.
      router.refresh();
    },
    [router],
  );
  const value = useMemo<Ctx>(() => ({ lang, t: makeT(lang), locale: localeOf(lang), setLang }), [lang, setLang]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

const FALLBACK: Ctx = {
  lang: DEFAULT_LANG_NO_PROVIDER,
  t: makeT(DEFAULT_LANG_NO_PROVIDER),
  locale: localeOf(DEFAULT_LANG_NO_PROVIDER),
  setLang: () => {},
};

/**
 * Client-component translator. Outside a provider (unit tests, isolated renders) it falls back to
 * Vietnamese, so existing tests that assert Vietnamese UI text keep working unchanged.
 */
export function useI18n(): Ctx {
  return useContext(I18nContext) ?? FALLBACK;
}
