export const locales = ["it", "en"] as const;
export type Locale = (typeof locales)[number];

export const strings = {
  it: {
    site_title: "Scarti",
    site_tagline: "Anomalie settimanali nell'economia italiana",
    latest_reports: "Ultimi report",
    archive: "Archivio",
    method: "Metodo",
    subscribe: "Iscriviti",
    week_of: "Settimana del",
    read_time: "4 minuti di lettura",
    source: "Fonte",
    view_english: "English",
    anomalies_found: (n: number) =>
      n === 1 ? "1 anomalia rilevata" : `${n} anomalie rilevate`,
    subscribe_headline: "Un'email ogni lunedì mattina.",
    subscribe_blurb:
      "Ogni lunedì ricevi il nuovo report via email. Nessuno spam, solo dati.",
    subscribe_placeholder: "indirizzo@esempio.it",
    subscribe_cta: "Iscrivimi",
    subscribe_success: "Ci siamo quasi — controlla la posta per confermare.",
    footer_rights: "Dati pubblici da ISTAT, Banca d'Italia, Eurostat.",
    severity: {
      moderate: "degna di nota",
      strong: "forte",
      extreme: "straordinaria",
    },
    direction: { up: "in rialzo", down: "in calo" },
  },
  en: {
    site_title: "Scarti",
    site_tagline: "Weekly anomalies in the Italian economy",
    latest_reports: "Latest reports",
    archive: "Archive",
    method: "Method",
    subscribe: "Subscribe",
    week_of: "Week of",
    read_time: "4 minute read",
    source: "Source",
    view_english: "Italiano",
    anomalies_found: (n: number) =>
      n === 1 ? "1 anomaly detected" : `${n} anomalies detected`,
    subscribe_headline: "One email every Monday morning.",
    subscribe_blurb:
      "Every Monday you get the new report by email. No spam, just data.",
    subscribe_placeholder: "you@example.com",
    subscribe_cta: "Subscribe",
    subscribe_success: "Almost there — check your inbox to confirm.",
    footer_rights: "Public data from ISTAT, Bank of Italy, Eurostat.",
    severity: {
      moderate: "notable",
      strong: "strong",
      extreme: "extreme",
    },
    direction: { up: "rising", down: "falling" },
  },
} as const;

export type Strings = typeof strings.it;

export function t(locale: Locale): Strings {
  return strings[locale];
}

export function localePath(locale: Locale, path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return locale === "it" ? p : `/en${p}`;
}

export function otherLocale(locale: Locale): Locale {
  return locale === "it" ? "en" : "it";
}
