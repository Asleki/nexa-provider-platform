import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const main = readFileSync(resolve(ROOT, "src/main.js"), "utf8");
const shell = readFileSync(resolve(ROOT, "src/app/shell/nexilabs-shell.js"), "utf8");

test("P006.UI.1 browser bootstrap owns NexiLabs shell and no longer mounts NoveGeo at startup", () => {
  assert.match(main, /mountNexiLabsShell/);
  assert.doesNotMatch(main, /mountPhysicalLandPresentation/);
  assert.doesNotMatch(main, /mountMapNavigationDiscovery/);
  assert.match(shell, /applicationName: "NexiLabs PWA"/);
});
