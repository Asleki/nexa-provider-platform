/** P006.3 governed coordinate parsing and selection references. */
import { createGeographicCoordinate } from "../geography/contracts.js";

function insideExtent(coordinate, extent) {
  return coordinate.longitude >= extent.minLongitude && coordinate.longitude <= extent.maxLongitude && coordinate.latitude >= extent.minLatitude && coordinate.latitude <= extent.maxLatitude;
}

export function resolveCoordinateSearch({ longitude, latitude, extent, source = "coordinate_search" }) {
  const coordinate = createGeographicCoordinate(longitude, latitude);
  if (!insideExtent(coordinate, extent)) throw new RangeError("coordinate is outside the governed NoveGeo map extent");
  const key = `${coordinate.longitude.toFixed(6)},${coordinate.latitude.toFixed(6)}`;
  return Object.freeze({
    selectionReferenceId: `selection:novegeo:coordinate:${key}`,
    selectionReferenceVersion: 1,
    selectedCoordinate: coordinate,
    source,
    coordinateReferenceId: "crs:novegeo:geographic",
    runtimeMode: "shared_reference",
    registryAuthorityCreated: false,
  });
}

export function viewportPointToCoordinate({ x, y, viewportWidth, viewportHeight, padding = 0, extent, navigationState }) {
  const width = Number(viewportWidth);
  const height = Number(viewportHeight);
  const inset = Number(padding);
  const zoom = Number(navigationState.zoom);
  const centerX = width / 2;
  const centerY = height / 2;
  const baseX = (Number(x) - navigationState.offsetX - centerX) / zoom + centerX;
  const baseY = (Number(y) - navigationState.offsetY - centerY) / zoom + centerY;
  const drawableWidth = width - inset * 2;
  const drawableHeight = height - inset * 2;
  if (baseX < inset || baseX > width - inset || baseY < inset || baseY > height - inset) {
    throw new RangeError("selected point is outside the governed geographic drawing extent");
  }
  const longitude = extent.minLongitude + ((baseX - inset) / drawableWidth) * (extent.maxLongitude - extent.minLongitude);
  const latitude = extent.maxLatitude - ((baseY - inset) / drawableHeight) * (extent.maxLatitude - extent.minLatitude);
  return resolveCoordinateSearch({ longitude, latitude, extent, source: "map_selection" });
}
