/** Canvas 2D adapter for deterministic map render plans. */

function drawLine(context, line) {
  context.beginPath();
  context.moveTo(line.start.x, line.start.y);
  context.lineTo(line.end.x, line.end.y);
  context.stroke();
}

export function renderMapCanvas({ canvas, viewport, boundaryPlan, grid }) {
  if (!canvas || typeof canvas.getContext !== "function") throw new TypeError("canvas must provide getContext");
  const context = canvas.getContext("2d");
  if (!context) throw new Error("Canvas 2D rendering is unavailable");
  canvas.width = viewport.renderWidth;
  canvas.height = viewport.renderHeight;
  if (canvas.style) {
    canvas.style.width = `${viewport.cssWidth}px`;
    canvas.style.height = `${viewport.cssHeight}px`;
  }
  context.setTransform(viewport.devicePixelRatio, 0, 0, viewport.devicePixelRatio, 0, 0);
  context.clearRect(0, 0, viewport.cssWidth, viewport.cssHeight);
  context.fillStyle = "#07111f";
  context.fillRect(0, 0, viewport.cssWidth, viewport.cssHeight);

  context.save();
  context.strokeStyle = "rgba(203, 213, 225, 0.24)";
  context.lineWidth = 1;
  for (const line of [...grid.longitudeLines, ...grid.latitudeLines]) drawLine(context, line);
  context.restore();

  if (grid.equator) {
    context.save();
    context.strokeStyle = "#19d3e6";
    context.lineWidth = 2;
    context.setLineDash([7, 5]);
    drawLine(context, grid.equator);
    context.restore();
  }

  context.save();
  context.beginPath();
  for (const polygon of boundaryPlan.polygons) {
    for (const ring of polygon.rings) {
      ring.points.forEach((point, index) => index === 0 ? context.moveTo(point.x, point.y) : context.lineTo(point.x, point.y));
      context.closePath();
    }
  }
  context.fillStyle = "rgba(37, 99, 235, 0.34)";
  context.strokeStyle = "#e8f0ff";
  context.lineWidth = 2;
  context.fill("evenodd");
  context.stroke();
  context.restore();

  context.save();
  context.fillStyle = "#cbd5e1";
  context.font = "12px system-ui, sans-serif";
  context.textBaseline = "top";
  for (const line of grid.longitudeLines) context.fillText(line.label, line.start.x + 4, Math.max(3, line.start.y + 3));
  context.textBaseline = "middle";
  for (const line of grid.latitudeLines) context.fillText(line.label, Math.max(3, line.start.x + 4), line.start.y);
  if (grid.equator) {
    context.fillStyle = "#67e8f9";
    context.fillText(grid.equator.label, Math.max(3, grid.equator.start.x + 4), grid.equator.start.y - 10);
  }
  context.restore();

  return Object.freeze({
    status: "RENDERED",
    boundaryId: boundaryPlan.boundaryId,
    boundaryVersion: boundaryPlan.boundaryVersion,
    polygonCount: boundaryPlan.polygons.length,
    longitudeLineCount: grid.longitudeLines.length,
    latitudeLineCount: grid.latitudeLines.length,
    equatorRendered: Boolean(grid.equator),
    viewportId: viewport.viewportId,
    viewportVersion: viewport.viewportVersion,
  });
}
