"use client";

import { LANGS } from "@/lib/i18n/core";
import { useI18n } from "@/lib/i18n/client";

/** EN | VI segmented switch. Stores the choice in the `lang` cookie and re-renders the page. */
export default function LanguageToggle({ className = "" }: { className?: string }) {
  const { lang, setLang, t } = useI18n();
  return (
    <div className={`lang-toggle ${className}`} role="group" aria-label={t("lang.switchLabel")}>
      {LANGS.map((l) => (
        <button
          key={l}
          type="button"
          className={`lang-toggle-btn${l === lang ? " active" : ""}`}
          aria-pressed={l === lang}
          onClick={() => l !== lang && setLang(l)}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
