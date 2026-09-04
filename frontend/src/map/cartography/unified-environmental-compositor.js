/**
 * P006.7.11.15.10.1.3 — unified-projection compatibility compositor for the
 * existing governed/reference NoveGeo environmental publications.
 *
 * This module owns no environmental authority. It reuses the locked P005
 * publications, validators, palettes and visual semantics while projecting
 * their geographic facts through the map-first unified projection supplied by
 * the caller.
 */
import { NOVEGEO_TERRAIN_STANDARD } from "../terrain/catalog.js";
import { terrainColorForElevation, validateTerrainPublication } from "../terrain/contracts.js";
import { NOVEGEO_LANDFORMS_STANDARD } from "../landforms/catalog.js";
import { LANDFORM_COLORS, validateLandformPublication } from "../landforms/contracts.js";
import { NOVEGEO_VEGETATION_STANDARD } from "../vegetation/catalog.js";
import { vegetationColorForClass, validateVegetationPublication } from "../vegetation/contracts.js";
import { NOVEGEO_HYDROLOGY_STANDARD } from "../hydrology/catalog.js";
import { validateHydrologyPublication } from "../hydrology/contracts.js";
import { NOVEGEO_CLIMATE_STANDARD } from "../climate/catalog.js";
import { climateColorForRainfall, validateClimatePublication } from "../climate/contracts.js";

export const UNIFIED_ENVIRONMENTAL_COMPOSITOR_ID = "presentation:novegeo:unified-environmental-compositor";
export const UNIFIED_ENVIRONMENTAL_COMPOSITOR_VERSION = 1;

export const UnifiedEnvironmentalLayerKey = Object.freeze({
  PHYSICAL_LAND: "physicalLand",
  BIOSPHERE: "biosphere",
  HYDROLOGY_ATMOSPHERE: "hydrologyAtmosphere",
  COORDINATES: "coordinates",
});

export const UNIFIED_ENVIRONMENTAL_LAYER_KEYS = Object.freeze(Object.values(UnifiedEnvironmentalLayerKey));

const TERRAIN_COMPOSITE_ALPHA = 0.72;
const SURROUNDING_WATER = "rgba(18,74,112,.78)";
const GRID_STROKE = "rgba(203, 213, 225, 0.24)";
const EQUATOR_STROKE = "#19d3e6";
const COORDINATE_INTERVAL_DEGREES = 5;

export function createUnifiedEnvironmentalLayerVisibility(overrides = {}) {
  return Object.freeze(Object.fromEntries(
    UNIFIED_ENVIRONMENTAL_LAYER_KEYS.map((key) => [key, overrides?.[key] !== false]),
  ));
}

function enabled(visibility, key) {
  return visibility?.[key] !== false;
}

function finitePoint(point) {
  const x = Number(point?.x);
  const y = Number(point?.y);
  if (!Number.isFinite(x) || !Number.isFinite(y)) throw new TypeError("unified environmental projection returned a non-finite point");
  return Object.freeze({ x, y });
}

function projected(project, longitude, latitude) {
  return finitePoint(project(Number(longitude), Number(latitude)));
}

function polygonsOf(geometry) {
  if (!geometry || typeof geometry !== "object") throw new TypeError("environment boundary geometry is required");
  if (geometry.type === "Polygon") return [geometry.coordinates];
  if (geometry.type === "MultiPolygon") return geometry.coordinates;
  throw new Error(`unsupported environmental boundary geometry type: ${geometry.type || "unknown"}`);
}

function traceBoundary(context, geometry, project) {
  context.beginPath();
  for (const polygon of polygonsOf(geometry)) {
    for (const ring of polygon) {
      if (!Array.isArray(ring) || ring.length < 4) throw new Error("environment boundary ring requires at least four coordinates");
      ring.forEach((coordinate, index) => {
        const point = projected(project, coordinate[0], coordinate[1]);
        if (index === 0) context.moveTo(point.x, point.y);
        else context.lineTo(point.x, point.y);
      });
      context.closePath();
    }
  }
}

function clipBoundary(context, boundaryPublication, project) {
  traceBoundary(context, boundaryPublication.geometry, project);
  context.clip("evenodd");
}

function projectedCellSize(project, longitude, latitude, spacing) {
  const p0 = projected(project, longitude, latitude);
  const px = projected(project, Number(longitude) + spacing, latitude);
  const py = projected(project, longitude, Number(latitude) + spacing);
  return Object.freeze({
    width: Math.max(2, Math.abs(px.x - p0.x) * 1.08),
    height: Math.max(2, Math.abs(py.y - p0.y) * 1.08),
  });
}

function drawTerrainAndLandforms(context, boundaryPublication, project, terrainPublication, landformPublication) {
  const terrain = validateTerrainPublication(terrainPublication);
  const landforms = validateLandformPublication(landformPublication);
  const spacing = terrain.publicationRepresentation === "overview" ? 0.84 : 0.42;
  const cell = projectedCellSize(project, terrain.extent.minLongitude, terrain.extent.minLatitude, spacing);

  context.save();
  clipBoundary(context, boundaryPublication, project);
  context.save();
  context.globalAlpha = TERRAIN_COMPOSITE_ALPHA;
  for (const sample of terrain.samples) {
    const point = projected(project, sample.longitude, sample.latitude);
    context.fillStyle = terrainColorForElevation(sample.elevationMeters);
    context.fillRect(point.x - cell.width / 2, point.y - cell.height / 2, cell.width, cell.height);
  }
  context.restore();

  for (const feature of landforms.features) {
    const [longitude, latitude] = feature.geometry.coordinates;
    const center = projected(project, longitude, latitude);
    const edge = projected(project, Number(longitude) + Number(feature.properties.influenceRadiusDegrees), latitude);
    context.fillStyle = LANDFORM_COLORS[feature.properties.landformClass];
    context.beginPath();
    context.arc(center.x, center.y, Math.max(5, Math.abs(edge.x - center.x)), 0, Math.PI * 2);
    context.fill();
  }
  context.restore();

  return Object.freeze({
    terrainDatasetId: terrain.datasetId,
    terrainSampleCount: terrain.samples.length,
    landformDatasetId: landforms.properties.datasetId,
    landformFeatureCount: landforms.features.length,
  });
}

function drawVegetation(context, boundaryPublication, project, vegetationPublication) {
  const vegetation = validateVegetationPublication(vegetationPublication);
  const cell = projectedCellSize(project, vegetation.extent.minLongitude, vegetation.extent.maxLatitude, 0.84);
  context.save();
  clipBoundary(context, boundaryPublication, project);
  for (const sample of vegetation.samples) {
    const point = projected(project, sample.longitude, sample.latitude);
    context.fillStyle = vegetationColorForClass(sample.vegetationClass);
    context.fillRect(point.x - cell.width / 2, point.y - cell.height / 2, cell.width, cell.height);
  }
  context.restore();
  return Object.freeze({
    vegetationDatasetId: vegetation.datasetId,
    vegetationSampleCount: vegetation.samples.length,
  });
}

function rainfallInfluence(system, point) {
  const dx = (point.x - system.x) / Math.max(1, system.radiusX);
  const dy = (point.y - system.y) / Math.max(1, system.radiusY);
  const angle = Math.atan2(dy, dx);
  const seed = Number(system.fieldModel?.shapeSeed || 1);
  const irregularity = Number(system.fieldModel?.irregularity || 0.2);
  const wobble = 1 + irregularity * (
    0.52 * Math.sin(angle * 3 + seed * 0.01)
    + 0.31 * Math.sin(angle * 5 - seed * 0.013)
    + 0.17 * Math.cos(angle * 7)
  );
  const distance = Math.sqrt(dx * dx + dy * dy) / Math.max(0.55, wobble);
  return Math.max(0, 1 - distance);
}

function rainfallColor(system, influence) {
  const powerful = system.intensityClass === "powerful";
  const alpha = (powerful ? 0.08 : 0.055) + influence * (powerful ? 0.28 : 0.20);
  return powerful ? `rgba(45,134,210,${alpha.toFixed(3)})` : `rgba(96,180,204,${alpha.toFixed(3)})`;
}

function riverWidth(river) {
  return river.streamOrder === 3 ? 3.2 : river.streamOrder === 2 ? 2.15 : 1.25;
}

function drawWindArrow(context, sample, point) {
  const length = 5 + Math.min(7, Number(sample.meanWindSpeedMps || 0) * 0.65);
  const angle = (Number(sample.prevailingWindDirectionDegrees || 0) - 90) * Math.PI / 180;
  const endX = point.x + Math.cos(angle) * length;
  const endY = point.y + Math.sin(angle) * length;
  context.beginPath();
  context.moveTo(point.x, point.y);
  context.lineTo(endX, endY);
  context.stroke();
}

function drawHydrologyAtmosphere(context, cssWidth, cssHeight, boundaryPublication, project, hydrologyPublication, climatePublication) {
  const hydrology = validateHydrologyPublication(hydrologyPublication);
  const climate = validateClimatePublication(climatePublication);

  context.save();
  context.fillStyle = SURROUNDING_WATER;
  context.beginPath();
  context.moveTo(0, 0);
  context.lineTo(cssWidth, 0);
  context.lineTo(cssWidth, cssHeight);
  context.lineTo(0, cssHeight);
  context.closePath();
  for (const polygon of polygonsOf(boundaryPublication.geometry)) {
    for (const ring of polygon) {
      ring.forEach((coordinate, index) => {
        const point = projected(project, coordinate[0], coordinate[1]);
        if (index === 0) context.moveTo(point.x, point.y);
        else context.lineTo(point.x, point.y);
      });
      context.closePath();
    }
  }
  context.fill("evenodd");
  context.restore();

  const climateCell = projectedCellSize(project, climate.extent.minLongitude, climate.extent.maxLatitude, 0.84);
  const climateCells = climate.samples.map((sample) => Object.freeze({ sample, point: projected(project, sample.longitude, sample.latitude) }));
  const rainfallSystems = climate.rainfallSystems.map((system) => {
    const center = projected(project, system.center.longitude, system.center.latitude);
    const xEdge = projected(project, Number(system.center.longitude) + Number(system.radiusLongitudeDegrees), system.center.latitude);
    const yEdge = projected(project, system.center.longitude, Number(system.center.latitude) + Number(system.radiusLatitudeDegrees));
    return Object.freeze({
      ...system,
      x: center.x,
      y: center.y,
      radiusX: Math.abs(xEdge.x - center.x),
      radiusY: Math.abs(yEdge.y - center.y),
    });
  });

  context.save();
  clipBoundary(context, boundaryPublication, project);

  for (const { sample, point } of climateCells) {
    context.fillStyle = climateColorForRainfall(sample.annualRainfallMm);
    context.fillRect(point.x - climateCell.width / 2, point.y - climateCell.height / 2, climateCell.width, climateCell.height);
  }

  for (const system of rainfallSystems) {
    for (const { point } of climateCells) {
      const influence = rainfallInfluence(system, point);
      if (influence <= 0.08) continue;
      context.fillStyle = rainfallColor(system, influence);
      context.beginPath();
      context.arc(point.x, point.y, Math.max(climateCell.width, climateCell.height) * (0.55 + 0.7 * influence), 0, Math.PI * 2);
      context.fill();
    }
  }

  context.save();
  context.strokeStyle = "rgba(225,239,246,.36)";
  context.lineWidth = 0.9;
  for (let index = 0; index < climateCells.length; index += 9) {
    const { sample, point } = climateCells[index];
    drawWindArrow(context, sample, point);
  }
  context.restore();

  context.fillStyle = "rgba(32,132,197,.90)";
  for (const lake of hydrology.lakes) {
    for (const ring of lake.geometry.coordinates) {
      context.beginPath();
      ring.forEach((coordinate, index) => {
        const point = projected(project, coordinate[0], coordinate[1]);
        if (index === 0) context.moveTo(point.x, point.y);
        else context.lineTo(point.x, point.y);
      });
      context.closePath();
      context.fill();
    }
  }

  context.strokeStyle = "rgba(58,168,226,.94)";
  context.lineCap = "round";
  context.lineJoin = "round";
  for (const river of [...hydrology.rivers].sort((a, b) => a.streamOrder - b.streamOrder)) {
    context.lineWidth = riverWidth(river);
    context.beginPath();
    river.geometry.coordinates.forEach((coordinate, index) => {
      const point = projected(project, coordinate[0], coordinate[1]);
      if (index === 0) context.moveTo(point.x, point.y);
      else context.lineTo(point.x, point.y);
    });
    context.stroke();
  }
  context.restore();

  return Object.freeze({
    hydrologyDatasetId: hydrology.datasetId,
    riverCount: hydrology.rivers.length,
    lakeCount: hydrology.lakes.length,
    climateDatasetId: climate.datasetId,
    climateSampleCount: climate.samples.length,
    rainfallSystemCount: climate.rainfallSystems.length,
    windMarkCount: Math.ceil(climate.samples.length / 9),
    surroundingWaterContext: true,
  });
}

function firstIntervalValue(minimum, interval) {
  return Math.ceil(Number(minimum) / interval) * interval;
}

function drawCoordinates(context, cssWidth, cssHeight, boundaryPublication, project, interval = COORDINATE_INTERVAL_DEGREES) {
  const extent = boundaryPublication.extent;
  const referenceLongitude = (Number(extent.minLongitude) + Number(extent.maxLongitude)) / 2;
  const referenceLatitude = (Number(extent.minLatitude) + Number(extent.maxLatitude)) / 2;
  let longitudeLineCount = 0;
  let latitudeLineCount = 0;

  context.save();
  context.strokeStyle = GRID_STROKE;
  context.lineWidth = 1;
  context.setLineDash([]);

  for (let longitude = firstIntervalValue(extent.minLongitude, interval); longitude <= Number(extent.maxLongitude) + 1e-9; longitude += interval) {
    const point = projected(project, longitude, referenceLatitude);
    context.beginPath();
    context.moveTo(point.x, 0);
    context.lineTo(point.x, cssHeight);
    context.stroke();
    longitudeLineCount += 1;
  }

  for (let latitude = firstIntervalValue(extent.minLatitude, interval); latitude <= Number(extent.maxLatitude) + 1e-9; latitude += interval) {
    if (Math.abs(latitude) < 1e-9) continue;
    const point = projected(project, referenceLongitude, latitude);
    context.beginPath();
    context.moveTo(0, point.y);
    context.lineTo(cssWidth, point.y);
    context.stroke();
    latitudeLineCount += 1;
  }
  context.restore();

  let equatorRendered = false;
  if (Number(extent.minLatitude) <= 0 && Number(extent.maxLatitude) >= 0) {
    const point = projected(project, referenceLongitude, 0);
    context.save();
    context.beginPath();
    context.moveTo(0, point.y);
    context.lineTo(cssWidth, point.y);
    context.setLineDash([7, 5]);
    context.strokeStyle = EQUATOR_STROKE;
    context.lineWidth = 2;
    context.stroke();
    context.restore();
    equatorRendered = true;
  }

  return Object.freeze({ longitudeLineCount, latitudeLineCount, equatorRendered, frameCoverage: "full_viewport" });
}

export function renderUnifiedEnvironmentalComposition({
  context,
  cssWidth,
  cssHeight,
  boundaryPublication,
  project,
  layerVisibility = {},
  terrainPublication = NOVEGEO_TERRAIN_STANDARD,
  landformPublication = NOVEGEO_LANDFORMS_STANDARD,
  vegetationPublication = NOVEGEO_VEGETATION_STANDARD,
  hydrologyPublication = NOVEGEO_HYDROLOGY_STANDARD,
  climatePublication = NOVEGEO_CLIMATE_STANDARD,
} = {}) {
  if (!context || typeof context.save !== "function") throw new TypeError("unified environmental compositor requires a Canvas 2D context");
  if (!boundaryPublication?.extent || !boundaryPublication?.geometry) throw new TypeError("unified environmental compositor requires the sovereign boundary");
  if (typeof project !== "function") throw new TypeError("unified environmental compositor requires a geographic project function");
  const width = Number(cssWidth);
  const height = Number(cssHeight);
  if (!Number.isFinite(width) || width <= 0 || !Number.isFinite(height) || height <= 0) throw new RangeError("unified environmental compositor requires positive frame dimensions");

  const visibility = createUnifiedEnvironmentalLayerVisibility(layerVisibility);
  let physicalLand = null;
  let biosphere = null;
  let hydrologyAtmosphere = null;
  let coordinates = null;

  if (enabled(visibility, UnifiedEnvironmentalLayerKey.PHYSICAL_LAND)) {
    physicalLand = drawTerrainAndLandforms(context, boundaryPublication, project, terrainPublication, landformPublication);
  }
  if (enabled(visibility, UnifiedEnvironmentalLayerKey.BIOSPHERE)) {
    biosphere = drawVegetation(context, boundaryPublication, project, vegetationPublication);
  }
  if (enabled(visibility, UnifiedEnvironmentalLayerKey.HYDROLOGY_ATMOSPHERE)) {
    hydrologyAtmosphere = drawHydrologyAtmosphere(
      context,
      width,
      height,
      boundaryPublication,
      project,
      hydrologyPublication,
      climatePublication,
    );
  }
  if (enabled(visibility, UnifiedEnvironmentalLayerKey.COORDINATES)) {
    coordinates = drawCoordinates(context, width, height, boundaryPublication, project);
  }

  return Object.freeze({
    status: "RENDERED",
    compositorId: UNIFIED_ENVIRONMENTAL_COMPOSITOR_ID,
    compositorVersion: UNIFIED_ENVIRONMENTAL_COMPOSITOR_VERSION,
    projectionMode: "UNIFIED",
    visibility,
    physicalLand,
    biosphere,
    hydrologyAtmosphere,
    coordinates,
    equatorRendered: Boolean(coordinates?.equatorRendered),
  });
}
