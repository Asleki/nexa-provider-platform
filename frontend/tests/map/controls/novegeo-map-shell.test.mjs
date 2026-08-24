import test from "node:test";
import assert from "node:assert/strict";
import {
  BUNDLE22A_MAP_NOTE,
  BUNDLE22A_MAP_SHELL_VERSION,
  BUNDLE22A_STYLE_HREF,
  summarizeAuthorityState,
} from "../../../src/map/controls/novegeo-map-shell.js";

test("Bundle 22A exposes current truthful map wording and a versioned additive style surface", () => {
  assert.equal(BUNDLE22A_MAP_SHELL_VERSION, "bundle22a-v1");
  assert.equal(BUNDLE22A_STYLE_HREF, "./styles/novegeo-map-shell-v1.css");
  assert.match(BUNDLE22A_MAP_NOTE, /Published NNGLA geography only/);
  assert.match(BUNDLE22A_MAP_NOTE, /Unpublished canonical records remain hidden/);
  assert.doesNotMatch(BUNDLE22A_MAP_NOTE, /Bundle 12E/);
});

test("Bundle 22A authority summary stays concise while retaining fail-closed meaning", () => {
  assert.equal(summarizeAuthorityState({ status: "LOADING" }), "Connecting to live NNGLA authority…");
  assert.equal(summarizeAuthorityState({ status: "READY", boundaryVersion: 2 }), "✓ Live NNGLA authority · Boundary v2");
  assert.match(summarizeAuthorityState({ status: "DEGRADED" }), /no static authority substituted/);
});
