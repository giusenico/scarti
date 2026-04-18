import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import react from "@astrojs/react";
import vercel from "@astrojs/vercel";

export default defineConfig({
  site: process.env.SCARTI_SITE_URL || "https://scarti.example",
  output: "server",
  adapter: vercel(),
  integrations: [react(), mdx()],
  i18n: {
    defaultLocale: "it",
    locales: ["it", "en"],
    routing: {
      prefixDefaultLocale: false,
    },
  },
  vite: {
    ssr: {
      noExternal: ["@observablehq/plot"],
    },
  },
});
