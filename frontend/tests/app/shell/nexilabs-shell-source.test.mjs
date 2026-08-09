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

test("Bundle 12.0C shell degrades past partial failure and installs foreground recovery", () => {
  assert.match(shell, /shellChromeStatus = "DEGRADED"/);
  assert.match(shell, /installShellPartialRecovery/);
  assert.match(shell, /nexilabs_shell_mounted_degraded/);
});

test("Bundle 12.0C starts service-worker recovery before awaiting the NexiLabs shell", () => {
  const registration = main.indexOf("registerServiceWorker");
  const mount = main.indexOf("await mountNexiLabsShell");
  assert.ok(registration >= 0 && mount >= 0 && registration < mount);
});
