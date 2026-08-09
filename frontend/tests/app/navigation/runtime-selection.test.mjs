import test from "node:test";
import assert from "node:assert/strict";
import { createRuntimeSelection, SelectedRuntime } from "../../../src/app/navigation/runtime-selection.js";

test("P006.UI.2 selected runtime is simulation or production, never development environment", () => {
  const state = createRuntimeSelection();
  assert.equal(state.value, null);
  assert.equal(state.select(SelectedRuntime.SIMULATION), "simulation");
  assert.equal(state.select(SelectedRuntime.PRODUCTION), "production");
  assert.throws(() => state.select("development"), /Unsupported selected runtime/);
});
