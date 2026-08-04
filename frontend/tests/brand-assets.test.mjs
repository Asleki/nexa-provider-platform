import test from "node:test";
import assert from "node:assert/strict";
import { BrandAsset, isCanonicalBrandAssetPath } from "../src/branding/brand-assets.js";
import { NexiLabsBrand, applyBrand } from "../src/branding/brand-config.js";

test("brand assets resolve only inside the canonical NexiLabs package", () => {
  for (const [key, value] of Object.entries(BrandAsset)) {
    if (key === "root") continue;
    assert.equal(isCanonicalBrandAssetPath(value), true, `${key}: ${value}`);
  }
  assert.equal(BrandAsset.root, "./public/brand/nexilabs");
  assert.equal(NexiLabsBrand.name, "NexiLabs");
  assert.equal(Object.isFrozen(NexiLabsBrand), true);
});

test("applyBrand mounts the canonical logo without requiring a network dependency", () => {
  const logo = { src: "", alt: "", dataset: {} };
  const name = { textContent: "" };
  const nodes = new Map([
    ["[data-role='brand-logo']", logo],
    ["[data-role='brand-name']", name],
  ]);
  const receipt = applyBrand({ querySelector: (selector) => nodes.get(selector) ?? null });
  assert.equal(logo.src, BrandAsset.horizontalLogo);
  assert.equal(logo.alt, "NexiLabs");
  assert.equal(name.textContent, "NexiLabs");
  assert.equal(receipt.canonical, true);
  assert.equal(receipt.logoApplied, true);
});

test("applyBrand remains safe when optional brand nodes are absent", () => {
  const receipt = applyBrand({ querySelector: () => null });
  assert.equal(receipt.logoApplied, false);
  assert.equal(receipt.canonical, true);
});
