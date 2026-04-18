import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const severity = z.enum(["moderate", "strong", "extreme"]);
const direction = z.enum(["up", "down"]);
const method = z.enum(["mod_zscore_stl", "mod_zscore", "yoy_percentile"]);

const anomaly = z.object({
  series_id: z.string(),
  period: z.string(),
  value: z.number(),
  method,
  zscore: z.number().nullable(),
  baseline_center: z.number().nullable(),
  baseline_scale: z.number().nullable(),
  severity,
  direction,
  mom_change_pct: z.number().nullable(),
  yoy_change_pct: z.number().nullable(),
  yoy_percentile: z.number().nullable(),
});

const localeBody = z.object({
  headline: z.string(),
  lede: z.string(),
  sections: z.array(
    z.object({
      anomaly_index: z.number().int(),
      body: z.string(),
    }),
  ),
});

const reports = defineCollection({
  loader: glob({ pattern: "**/*.json", base: "./src/content/reports" }),
  schema: z.object({
    slug: z.string(),
    week_of: z.string(),
    generated_at: z.string(),
    anomalies: z.array(anomaly),
    it: localeBody,
    en: localeBody,
  }),
});

export const collections = { reports };
