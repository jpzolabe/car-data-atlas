import { defineConfig } from "astro/config";

// French-only for now - see CLAUDE.md ("French-first") and docs/plan.md §2.1
// ("English mirror later under /en/, not at launch"). Add Astro's i18n router
// config here when that mirror actually starts; it isn't worth the config
// weight for a single locale.
export default defineConfig({
  site: "https://donnees-rca.example", // placeholder - replace once the real domain is chosen
  compressHTML: true,
  // Every page is meant to be one self-contained HTML file (no separate CSS/JS
  // requests) - check-page-weight.mjs's budget check relies on that. Without
  // this, Astro splits a page's CSS into an external /_astro/*.css file once
  // enough of it comes from shared components (ThemeToggle.astro, imported on
  // every page), which would silently make the weight check under-count real
  // page weight.
  build: { inlineStylesheets: "always" },
});
