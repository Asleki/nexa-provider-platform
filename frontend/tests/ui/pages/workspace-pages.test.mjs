import test from "node:test";
import assert from "node:assert/strict";
import { productionDeveloperWorkspaceMarkup } from "../../../src/ui/pages/production-developer-workspace.js";
import { productionGuestWorkspaceMarkup } from "../../../src/ui/pages/production-guest-workspace.js";
import { simulationWorkspaceMarkup } from "../../../src/ui/pages/simulation-workspace.js";
import { noveGeoFeatureMarkup } from "../../../src/ui/pages/novegeo-feature.js";

const developer = Object.freeze({ principalId: "developer:nexadevs:development:0001", runtime: "production", authenticationStrength: "developer_password_enigma" });
const guest = Object.freeze({ principalId: "guest:development:0001", runtime: "production", authenticationStrength: "guest_password" });

test("P006.UI.10 developer workspace is supervision-oriented and does not expose raw database administration", () => {
  const html = productionDeveloperWorkspaceMarkup(developer);
  assert.match(html, /Production Developer Workspace/);
  assert.match(html, /Name Catalogue/);
  assert.match(html, /Open NoveGeo/);
  assert.match(html, /Server-side authority only/);
  assert.doesNotMatch(html, /PGPASSWORD|SELECT \*|raw SQL console/i);
});

test("P006.UI.11 Guest owns future citizen/business relationships without fake registration workflows", () => {
  const html = productionGuestWorkspaceMarkup(guest);
  assert.match(html, /Citizen relationships/);
  assert.match(html, /Business relationships/);
  assert.match(html, /planned/);
  assert.doesNotMatch(html, /Add a Citizen|Add a Business|registration request/i);
});

test("P006.UI.12 Simulation is public-facing but keeps privacy and deferred-service boundaries explicit", () => {
  const html = simulationWorkspaceMarkup();
  assert.match(html, /Simulation · Public world/);
  assert.match(html, /Explore NoveGeo/);
  assert.match(html, /Unrestricted citizen-name search is outside/);
  assert.match(html, /weather, traffic, projects and NexVox access are reserved/i);
});

test("P006.UI.13 NoveGeo page gives the map its own dominant feature surface", () => {
  const html = noveGeoFeatureMarkup({ runtime: "simulation", backRoute: "simulation-entry" });
  assert.match(html, /data-role="novegeo-map-stage"/);
  assert.match(html, /data-role="future-map-viewport"/);
  assert.match(html, /data-role="novegeo-tool-rail"/);
  assert.match(html, /No citizen, business, institution or population overlays/);
});
