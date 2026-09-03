import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const mainUrl = new URL("../../src/main.js", import.meta.url);
const shellUrl = new URL("../../src/app/shell/nexilabs-shell.js", import.meta.url);

test("map-first coordinator is installed by the shell before geographic renderers while main stays on the locked CM1 seam", async () => {
  const [mainSource, shellSource] = await Promise.all([
    readFile(mainUrl, "utf8"),
    readFile(shellUrl, "utf8"),
  ]);

  // Historical CM1 main stays untouched; .15.10 does not take another main.js successor.
  assert.doesNotMatch(mainSource, /createNoveGeoPresentationCoordinator|presentationCoordinator/);
  assert.match(mainSource, /const application = await mountNexiLabsShell\(\{ documentRef, windowRef, fetchRef, config \}\)/);
  assert.match(mainSource, /novegeo-national-geography-experience\.js/);
  assert.match(mainSource, /novegeo-region-map-experience\.js/);
  assert.match(mainSource, /novegeo-city-map-experience\.js/);
  assert.doesNotMatch(mainSource, /order\s*[:=]\s*400/);

  const install = shellSource.indexOf("const presentationCoordinator = installNoveGeoPresentationCoordinator({ documentRef, windowRef })");
  const route = shellSource.indexOf("const renderRoute = (route) =>");
  const attach = shellSource.indexOf("presentationCoordinator?.attachViewport?.({ documentRef, windowRef })");
  const live = shellSource.indexOf("featureRuntime = mountNoveGeoLiveAuthorityRuntime({");

  assert.ok(install >= 0, "shell must create the presentation coordinator");
  assert.ok(install < route, "coordinator must exist before route rendering can install map surfaces");
  assert.ok(route < attach, "route must create the NoveGeo viewport before it is attached");
  assert.ok(attach < live, "coordinator must attach before the live feature runtime renders geography");
});
