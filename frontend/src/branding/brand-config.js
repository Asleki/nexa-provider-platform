/** NexiLabs brand-consumption contract for the NoveGeo PWA shell. */

import { BrandAsset, isCanonicalBrandAssetPath } from "./brand-assets.js";

export const NexiLabsBrand = Object.freeze({
  id: "nexilabs",
  name: "NexiLabs",
  productName: "NoveGeo PWA",
  assets: BrandAsset,
});

export function applyBrand(documentRef) {
  if (!documentRef || typeof documentRef.querySelector !== "function") {
    throw new TypeError("documentRef must provide querySelector");
  }

  const logo = documentRef.querySelector("[data-role='brand-logo']");
  if (logo) {
    logo.src = BrandAsset.horizontalLogo;
    logo.alt = "NexiLabs";
    logo.dataset.brandAsset = "horizontal-logo";
  }

  const brandName = documentRef.querySelector("[data-role='brand-name']");
  if (brandName) brandName.textContent = NexiLabsBrand.name;

  return Object.freeze({
    brandId: NexiLabsBrand.id,
    logoApplied: Boolean(logo),
    canonical: isCanonicalBrandAssetPath(BrandAsset.horizontalLogo),
  });
}
