/** P006.3 selection marker projection without creating registry authority. */
export function coordinateToViewportPoint({ coordinate, extent, viewportWidth, viewportHeight, padding = 0, navigationState }) {
  const width = Number(viewportWidth);
  const height = Number(viewportHeight);
  const inset = Number(padding);
  const drawableWidth = width - inset * 2;
  const drawableHeight = height - inset * 2;
  const baseX = inset + ((coordinate.longitude - extent.minLongitude) / (extent.maxLongitude - extent.minLongitude)) * drawableWidth;
  const baseY = inset + ((extent.maxLatitude - coordinate.latitude) / (extent.maxLatitude - extent.minLatitude)) * drawableHeight;
  const cx = width / 2;
  const cy = height / 2;
  return Object.freeze({
    x: (baseX - cx) * navigationState.zoom + cx + navigationState.offsetX,
    y: (baseY - cy) * navigationState.zoom + cy + navigationState.offsetY,
  });
}
