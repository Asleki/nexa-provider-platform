import test from "node:test";
import assert from "node:assert/strict";
import { resolveProductionWorkspace, WorkspaceKind } from "../../../src/app/workspaces/workspace-resolution.js";
import { DEVELOPER_CAPABILITIES, GUEST_CAPABILITIES, SIMULATION_CAPABILITIES } from "../../../src/app/workspaces/workspace-capabilities.js";

test("P006.UI.10/P006.UI.11 production workspace resolution keeps runtime and role semantically distinct", () => {
  assert.equal(resolveProductionWorkspace({ sessionId: "s1", runtime: "production", identityType: "nexadevs_developer" }), WorkspaceKind.PRODUCTION_DEVELOPER);
  assert.equal(resolveProductionWorkspace({ sessionId: "s2", runtime: "production", identityType: "guest" }), WorkspaceKind.PRODUCTION_GUEST);
  assert.equal(resolveProductionWorkspace({ sessionId: "s3", runtime: "simulation", identityType: "guest" }), null);
  assert.equal(resolveProductionWorkspace({ runtime: "production", identityType: "guest" }), null);
});

test("P006.UI.10-P006.UI.12 capability contracts expose only currently real NoveGeo navigation", () => {
  assert.equal(DEVELOPER_CAPABILITIES.find((item) => item.id === "novegeo")?.availability, "available");
  assert.equal(GUEST_CAPABILITIES.find((item) => item.id === "novegeo")?.availability, "available");
  assert.equal(SIMULATION_CAPABILITIES.find((item) => item.id === "novegeo")?.availability, "available");
  assert.equal(DEVELOPER_CAPABILITIES.find((item) => item.id === "citizen-registry")?.availability, "planned");
  assert.equal(GUEST_CAPABILITIES.find((item) => item.id === "business-relationships")?.availability, "planned");
});
