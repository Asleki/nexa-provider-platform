import test from "node:test";
import assert from "node:assert/strict";
import { createWorldStateEnvelope } from "../../../src/map/state/world-state-contracts.js";
import { createWorldStateStore } from "../../../src/map/state/world-state-store.js";

function update(revision, value = revision) {
  return createWorldStateEnvelope({
    revision,
    runtimeMode: "simulation",
    sourceReference: "source:nexilabs:test-fixture",
    stateReferences: [{ stateReferenceId: `state-ref:${revision}`, subjectReference: "feature:future:1", stateType: "test", value }],
  });
}

test("P006.5 store applies contiguous revisions and rejects stale, gaps and conflicting duplicates", () => {
  const store = createWorldStateStore({ runtimeMode: "simulation" });
  assert.equal(store.apply(update(1)).status, "APPLIED");
  assert.equal(store.state.revision, 1);
  assert.equal(store.apply(update(3)).status, "REJECTED_GAP");
  assert.equal(store.apply(update(0)).status, "REJECTED_STALE");
  assert.equal(store.apply(update(1, "different")).status, "REJECTED_CONFLICT");
  assert.equal(store.apply(store.state).status, "DUPLICATE");
  assert.equal(store.apply(update(2)).status, "APPLIED");
  assert.equal(store.state.revision, 2);
});
