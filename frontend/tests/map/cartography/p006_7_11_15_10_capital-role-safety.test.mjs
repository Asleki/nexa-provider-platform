import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const sourceUrl = new URL("../../../src/map/cartography/presentation-coordinator.js", import.meta.url);

test("national-capital presentation is reserved and never inferred from Orivane or CITY", async () => {
  const source = await readFile(sourceUrl, "utf8");
  assert.match(source, /presentationRoles\s*=\s*Object\.freeze\(\{\}\)/);
  assert.doesNotMatch(source, /displayName\s*===\s*["']Orivane["']/);
  assert.doesNotMatch(source, /CITY\s*===\s*NATIONAL_CAPITAL/);
});
