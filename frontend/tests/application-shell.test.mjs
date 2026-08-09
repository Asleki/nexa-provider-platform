import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const FRONTEND = resolve(HERE, "..");
const html = readFileSync(resolve(FRONTEND, "index.html"), "utf8");
const header = readFileSync(resolve(FRONTEND, "src/ui/partials/header.html"), "utf8");
const footer = readFileSync(resolve(FRONTEND, "src/ui/partials/footer.html"), "utf8");
const css = readFileSync(resolve(FRONTEND, "styles/app.css"), "utf8");
const shellMarkup = `${html}\n${header}\n${footer}`;

test("application shell consumes canonical tokens and logo", () => {
  assert.match(html, /public\/brand\/nexilabs\/metadata\/brand-tokens\.css/);
  assert.match(header, /public\/brand\/nexilabs\/vectors\/nexilabs_logo_horizontal\.svg/);
  assert.match(header, /data-role="brand-logo"/);
  assert.doesNotMatch(shellMarkup, /https?:\/\//);
});

test("application shell exposes semantic and accessible regions", () => {
  for (const marker of [
    'class="skip-link"',
    '<header class="application-header"',
    '<main id="main-content"',
    '<footer class="application-footer"',
    'aria-live="polite"',
  ]) assert.ok(shellMarkup.includes(marker), marker);
});

test("responsive styles use canonical tokens and preserve health states", () => {
  for (const marker of [
    "var(--nexilabs-navy)",
    "var(--nexilabs-cyan)",
    "var(--nexilabs-teal)",
    "@media (max-width: 56rem)",
    "@media (max-width: 44rem)",
    "@media (prefers-reduced-motion: reduce)",
    '[data-health-status="READY"]',
    '[data-health-status="FAILED"]',
    ":focus-visible",
  ]) assert.ok(css.includes(marker), marker);
});
