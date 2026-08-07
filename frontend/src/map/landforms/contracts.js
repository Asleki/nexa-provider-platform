/** P005.2 governed physical-land semantic contracts. */
export const LandformClass = Object.freeze({ MOUNTAIN: "mountain", VALLEY: "valley", PLAIN: "plain", PLATEAU: "plateau" });
const CLASSES = new Set(Object.values(LandformClass));
export const LANDFORM_COLORS = Object.freeze({ mountain: "rgba(247, 237, 218, 0.34)", valley: "rgba(75, 116, 78, 0.24)", plain: "rgba(166, 182, 102, 0.18)", plateau: "rgba(205, 160, 103, 0.22)" });
export function validateLandformPublication(value) {
  if (!value || value.type !== "FeatureCollection") throw new TypeError("landforms must be a FeatureCollection");
  const props=value.properties || {};
  if (props.datasetId !== "dataset:novegeo:landforms" || props.datasetVersion !== 1) throw new Error("unexpected landform dataset lineage");
  if (props.terrainDatasetId !== "dataset:novegeo:terrain:elevation" || props.terrainDatasetVersion !== 1) throw new Error("landforms must reference terrain v001");
  if (!Array.isArray(value.features) || value.features.length === 0) throw new Error("landform features are required");
  for (const feature of value.features) {
    if (!String(feature.id || "").startsWith("landform:novegeo:")) throw new Error("landform identity must be namespaced");
    if (!CLASSES.has(feature.properties?.landformClass)) throw new Error("unsupported landform class");
    if (feature.geometry?.type !== "Point") throw new Error("v001 landforms use Point authority anchors");
  }
  return value;
}
