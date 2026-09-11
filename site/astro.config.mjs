import { defineConfig } from "astro/config";

// French-only for now — see CLAUDE.md ("French-first") and docs/plan.md §2.1
// ("English mirror later under /en/, not at launch"). Add Astro's i18n router
// config here when that mirror actually starts; it isn't worth the config
// weight for a single locale.
export default defineConfig({
  site: "https://donnees-rca.example", // placeholder — replace once the real domain is chosen
  compressHTML: true,
});
