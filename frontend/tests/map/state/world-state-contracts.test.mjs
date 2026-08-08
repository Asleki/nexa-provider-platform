import test from "node:test";
import assert from "node:assert/strict";
import { createWorldStateEnvelope, validateWorldStateEnvelope } from "../../../src/map/state/world-state-contracts.js";

test("P006.5 world-state envelope is runtime-scoped, reference-oriented and cannot mutate governed geography", () => {
  const state = createWorldStateEnvelope({
    revision: 1,
    runtimeMode: "simulation",
    effectiveAt: "2026-08-08T12:00:00Z",
    sourceReference: "source:nexilabs:test-fixture",
    stateReferences: [{ stateReferenceId: "state-ref:1", subjectReference: "feature:future:1", stateType: "availability", value: true }],
  });
  assert.equal(state.revision, 1);
  assert.equal(state.mutatesGovernedGeography, false);
  assert.equal(state.stateReferences[0].subjectReference, "feature:future:1");
  assert.throws(() => validateWorldStateEnvelope({ ...state, mutatesGovernedGeography: true }, { runtimeMode: "simulation" }), /may not mutate governed geography/);
  assert.throws(() => validateWorldStateEnvelope({ ...state, runtimeMode: "production" }, { runtimeMode: "simulation" }), /different runtime mode/);
});
