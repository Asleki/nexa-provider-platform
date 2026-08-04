/** Canonical NexiLabs public brand asset locations. */

const BRAND_ROOT = "./public/brand/nexilabs";

export const BrandAsset = Object.freeze({
  root: BRAND_ROOT,
  horizontalLogo: `${BRAND_ROOT}/vectors/nexilabs_logo_horizontal.svg`,
  mark: `${BRAND_ROOT}/vectors/nexilabs_mark.svg`,
  monochromeWhiteMark: `${BRAND_ROOT}/vectors/nexilabs_mark_monochrome_white.svg`,
  monochromeBlackMark: `${BRAND_ROOT}/vectors/nexilabs_mark_monochrome_black.svg`,
  tokenStylesheet: `${BRAND_ROOT}/metadata/brand-tokens.css`,
});

export function isCanonicalBrandAssetPath(value) {
  return typeof value === "string" && value.startsWith(`${BRAND_ROOT}/`);
}
