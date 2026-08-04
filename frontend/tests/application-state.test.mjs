import test from "node:test";
import assert from "node:assert/strict";
import { ApplicationState, ApplicationStatus } from "../src/core/application-state.js";

test("application state starts CREATED and exposes an immutable snapshot", () => {
  const state = new ApplicationState({ clock: () => "2026-08-04T00:00:00.000Z" });
  assert.equal(state.snapshot.status, ApplicationStatus.CREATED);
  assert.equal(state.snapshot.sequence, 0);
  assert.equal(Object.isFrozen(state.snapshot), true);
  assert.equal(Object.isFrozen(state.snapshot.details), true);
});

test("legal bootstrap transitions are accepted", () => {
  const stamps = ["created", "booting", "ready"];
  const state = new ApplicationState({ clock: () => stamps.shift() });
  assert.equal(state.transition(ApplicationStatus.BOOTING).status, "BOOTING");
  assert.equal(state.transition(ApplicationStatus.READY).status, "READY");
  assert.equal(state.snapshot.sequence, 2);
});

test("invalid transitions are rejected", () => {
  const state = new ApplicationState();
  assert.throws(() => state.transition(ApplicationStatus.READY), /Invalid application transition/);
  assert.throws(() => state.transition("UNKNOWN"), /Unknown application status/);
});

test("failure details are copied and frozen", () => {
  const state = new ApplicationState();
  state.transition(ApplicationStatus.BOOTING);
  const details = { message: "missing mount" };
  const snapshot = state.transition(ApplicationStatus.FAILED, details);
  details.message = "changed";
  assert.equal(snapshot.details.message, "missing mount");
  assert.equal(Object.isFrozen(snapshot.details), true);
});
