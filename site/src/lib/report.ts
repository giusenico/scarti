import type { CollectionEntry } from "astro:content";

export interface ChartPayload {
  series_id: string;
  title_it: string;
  title_en: string;
  unit: string;
  anomaly_period: string;
  anomaly_value: number;
  history: { period: string; value: number | null }[];
}

export type ChartsBySeries = Record<string, ChartPayload>;

export async function loadChartsForReport(slug: string): Promise<ChartsBySeries> {
  const modules = import.meta.glob("/src/data/series/*.json");
  const key = `/src/data/series/${slug}.json`;
  const loader = modules[key];
  if (!loader) return {};
  const mod = (await loader()) as { default: ChartsBySeries };
  return mod.default;
}

export function reportBody(
  entry: CollectionEntry<"reports">,
  locale: "it" | "en",
) {
  return locale === "it" ? entry.data.it : entry.data.en;
}
