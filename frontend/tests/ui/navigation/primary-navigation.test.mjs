import test from "node:test";
import assert from "node:assert/strict";
import { navigationMarkup, primaryNavigationItems } from "../../../src/ui/navigation/primary-navigation.js";
import { ApplicationRoute } from "../../../src/app/navigation/application-route.js";

test("P006.UI.15 primary navigation exposes only real routes and explicit planned placeholders", () => {
  const items = primaryNavigationItems();
  assert.equal(items.filter((item) => item.available).length, 3);
  assert.equal(items.filter((item) => !item.available).length, 2);
  const html = navigationMarkup(ApplicationRoute.RUNTIME_GATEWAY);
  assert.match(html, /aria-current="page"/);
  assert.match(html, /NoveGeo<small>Planned<\/small>/);
  assert.match(html, /Registries<small>Planned<\/small>/);
});
