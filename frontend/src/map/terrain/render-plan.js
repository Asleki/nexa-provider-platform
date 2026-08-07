/** P005.1 terrain sample to viewport render-plan adapter. */
import { geographicToViewport } from "../presentation/viewport.js";
import { terrainColorForElevation, validateTerrainPublication } from "./contracts.js";

export function createTerrainRenderPlan(publication, viewport) {
  const value = validateTerrainPublication(publication);
  const spacing = Number(value.publicationRepresentation === "overview" ? 0.84 : 0.42);
  const x0 = geographicToViewport(value.extent.minLongitude, value.extent.minLatitude, viewport);
  const x1 = geographicToViewport(value.extent.minLongitude + spacing, value.extent.minLatitude, viewport);
  const y1 = geographicToViewport(value.extent.minLongitude, value.extent.minLatitude + spacing, viewport);
  const cellWidth = Math.max(2, Math.abs(x1.x - x0.x) * 1.08);
  const cellHeight = Math.max(2, Math.abs(y1.y - x0.y) * 1.08);
  const samples = value.samples.map((sample) => {
    const point = geographicToViewport(sample.longitude, sample.latitude, viewport);
    return Object.freeze({
      ...sample,
      x: point.x,
      y: point.y,
      color: terrainColorForElevation(sample.elevationMeters),
    });
  });
  return Object.freeze({
    renderPlanId: "render-plan:novegeo:terrain:v001",
    renderPlanVersion: 1,
    terrainId: value.terrainId,
    terrainVersion: value.terrainVersion,
    datasetId: value.datasetId,
    datasetVersion: value.datasetVersion,
    cellWidth,
    cellHeight,
    samples: Object.freeze(samples),
  });
}
