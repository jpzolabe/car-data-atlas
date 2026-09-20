// Page-weight budget from AGENTS.md: 150 KB/page, uncompressed, HTML+CSS+fonts+
// SVG+images combined. Since every page here is a single self-contained HTML
// file (no separate CSS/JS/image requests), checking the HTML file size is
// checking the whole page weight. Fails the build if any page is over budget,
// per AGENTS.md: "Fail the build if a page exceeds budget rather than shipping it."

import { readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const BUDGET_BYTES = 150 * 1024;
const DIST = "dist";

function findHtmlFiles(dir) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...findHtmlFiles(path));
    else if (entry.name.endsWith(".html")) out.push(path);
  }
  return out;
}

const files = findHtmlFiles(DIST);
let failed = false;

for (const file of files) {
  const size = statSync(file).size;
  const kb = (size / 1024).toFixed(1);
  const status = size > BUDGET_BYTES ? "FAIL" : "ok";
  if (size > BUDGET_BYTES) failed = true;
  console.log(`${status.padEnd(4)} ${kb.padStart(7)} KB  ${file}`);
}

if (failed) {
  console.error(`\nOne or more pages exceed the ${BUDGET_BYTES / 1024} KB budget.`);
  process.exit(1);
}
console.log(`\nAll ${files.length} page(s) under the ${BUDGET_BYTES / 1024} KB budget.`);
