/** P006.2 presentation-only map layer visibility state. */
export const MAP_LAYER_CATALOG = Object.freeze([
  Object.freeze({ key: "physicalLand", label: "Terrain & landforms", roles: Object.freeze(["novegeo-physical-land-canvas"]), legend: "Elevation and physical landform context" }),
  Object.freeze({ key: "biosphere", label: "Vegetation & aridity", roles: Object.freeze(["novegeo-biosphere-canvas"]), legend: "Vegetation and arid-zone classes" }),
  Object.freeze({ key: "hydrologyAtmosphere", label: "Water & atmosphere", roles: Object.freeze(["novegeo-hydrology-atmosphere-canvas"]), legend: "Rivers, lakes, rainfall and wind" }),
  Object.freeze({ key: "coordinates", label: "Coordinates", roles: Object.freeze(["novegeo-full-viewport-coordinate-canvas"]), legend: "Latitude, longitude and Equator · 0°" }),
]);

export function createLayerVisibility(overrides = {}) {
  return Object.freeze(Object.fromEntries(MAP_LAYER_CATALOG.map((layer) => [layer.key, overrides[layer.key] !== false])));
}

export function applyLayerVisibility(viewportElement, visibility) {
  for (const layer of MAP_LAYER_CATALOG) {
    for (const role of layer.roles) {
      const node = viewportElement?.querySelector?.(`[data-role='${role}']`);
      if (node?.style) node.style.visibility = visibility[layer.key] === false ? "hidden" : "visible";
    }
  }
  return visibility;
}
