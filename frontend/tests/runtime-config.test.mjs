import test from "node:test";
import assert from "node:assert/strict";
import { createRuntimeConfig, RuntimeMode } from "../src/config/runtime-config.js";

test("safe public runtime configuration is normalized and frozen", () => {
  const config = createRuntimeConfig({
    runtimeMode: RuntimeMode.SIMULATION,
    applicationVersion: "0.1.0",
    apiBaseUrl: "https://api.example.test/",
    buildReference: "build-42",
  });
  assert.equal(config.runtimeMode, "simulation");
  assert.equal(config.apiBaseUrl, "https://api.example.test");
  assert.equal(Object.isFrozen(config), true);
  assert.deepEqual(config.capabilities, [
    "application_shell",
    "runtime_configuration",
    "health_state",
    "governed_world_boundary",
    "coordinate_reference",
    "coordinate_projection",
    "map_canvas_renderer",
    "coordinate_grid_overlay",
    "world_extent_validation",
    "map_core_qualification",
  ]);
});

test("unsupported runtime modes are rejected", () => {
  assert.throws(() => createRuntimeConfig({ runtimeMode: "mixed" }), /Unsupported runtime mode/);
});

test("database connection material is rejected", () => {
  for (const value of [
    "postgresql://admin:secret@db.example:5432/app",
    "npp-dev.rds.amazonaws.com",
    "db.internal:5432",
    "AWS_SECRET_KEY=secret",
    "database_password=secret",
  ]) {
    assert.throws(() => createRuntimeConfig({ apiBaseUrl: value }), /Unsafe public runtime configuration/);
  }
});

test("non-HTTPS public APIs are rejected outside localhost", () => {
  assert.throws(() => createRuntimeConfig({ apiBaseUrl: "http://api.example.test" }), /must use HTTPS/);
  assert.equal(createRuntimeConfig({ apiBaseUrl: "http://localhost:8080" }).apiBaseUrl, "http://localhost:8080");
});
