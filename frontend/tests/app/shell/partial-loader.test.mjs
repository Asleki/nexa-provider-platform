import test from "node:test";
import assert from "node:assert/strict";
import { loadPartial, ShellPartial } from "../../../src/app/shell/partial-loader.js";

test("P006.UI.1 shared header/footer partials load into shell slots", async () => {
  const slot = { innerHTML: "", dataset: {} };
  const documentRef = { querySelector: () => slot };
  const fetchRef = async () => ({ ok: true, async text() { return "<header>Shared</header>"; } });
  const receipt = await loadPartial({ documentRef, fetchRef, descriptor: ShellPartial.HEADER });
  assert.equal(receipt.ready, true);
  assert.equal(slot.dataset.partialReady, "true");
  assert.match(slot.innerHTML, /Shared/);
});
