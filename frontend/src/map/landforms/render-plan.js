/** P005.2 semantic landform render-plan adapter. */
import { geographicToViewport } from "../presentation/viewport.js";
import { LANDFORM_COLORS, validateLandformPublication } from "./contracts.js";

export function createLandformRenderPlan(publication, viewport) {
  const value = validateLandformPublication(publication);
  const features = value.features.map((feature) => {
    const [longitude, latitude] = feature.geometry.coordinates;
    const center = geographicToViewport(longitude, latitude, viewport);
    const edge = geographicToViewport(longitude + feature.properties.influenceRadiusDegrees, latitude, viewport);
    return Object.freeze({
      landformId: feature.id,
      landformClass: feature.properties.landformClass,
      elevationMeters: feature.properties.elevationMeters,
      x: center.x,
      y: center.y,
      radius: Math.max(5, Math.abs(edge.x - center.x)),
      color: LANDFORM_COLORS[feature.properties.landformClass],
    });
  });
  return Object.freeze({
    renderPlanId: "render-plan:novegeo:landforms:v001",
    renderPlanVersion: 1,
    datasetId: value.properties.datasetId,
    datasetVersion: value.properties.datasetVersion,
    features: Object.freeze(features),
  });
}
