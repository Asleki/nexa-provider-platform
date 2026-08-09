import test from "node:test";
import assert from "node:assert/strict";
import { runtimeGatewayMarkup } from "../../../src/ui/pages/runtime-gateway.js";
import { productionAccessMarkup } from "../../../src/ui/pages/production-access.js";
import { simulationEntryMarkup } from "../../../src/ui/pages/simulation-entry.js";
import { accessPlaceholderMarkup } from "../../../src/ui/pages/access-placeholder.js";

test("P006.UI.2 runtime gateway offers only Simulation and Production", () => {
  const html = runtimeGatewayMarkup();
  assert.match(html, /Welcome to NexiLabs/);
  assert.match(html, /data-select-runtime="simulation"/);
  assert.match(html, /data-select-runtime="production"/);
  assert.doesNotMatch(html, /NoveGeo world geometry/);
});

test("P006.UI.3 production access branches to Developer and Guest without implementing authentication", () => {
  const html = productionAccessMarkup();
  assert.match(html, /NexaDevs Developer/);
  assert.match(html, />Guest</);
  assert.match(accessPlaceholderMarkup("developer"), /Bundle 12D/);
  assert.match(accessPlaceholderMarkup("guest"), /Bundle 12D/);
});

test("P006.UI.2 simulation entry does not invent simulation activity", () => {
  const html = simulationEntryMarkup();
  assert.match(html, /No simulation activity is generated/);
});
