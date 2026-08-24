/** P006.7.11.15.4 — Canvas 2D cartographic label renderer. */
import { declutterCartographicLabels } from "./collision.js";

function font(style) {
  return `${style.fontWeight} ${style.resolvedFontSizePx}px ${style.fontFamily}`;
}

function measureSpacedText(context, text, letterSpacingPx) {
  const glyphs = [...text];
  const widths = glyphs.map((glyph) => context.measureText(glyph).width);
  const spacing = Math.max(0, glyphs.length - 1) * Number(letterSpacingPx || 0);
  return { glyphs, widths, width: widths.reduce((sum, value) => sum + value, 0) + spacing };
}

function drawSpacedText(context, text, centerX, baselineY, style, stroke = false) {
  const measured = measureSpacedText(context, text, style.letterSpacingPx);
  let x = centerX - measured.width / 2;
  measured.glyphs.forEach((glyph, index) => {
    const width = measured.widths[index];
    const gx = x + width / 2;
    if (stroke) context.strokeText(glyph, gx, baselineY);
    else context.fillText(glyph, gx, baselineY);
    x += width + Number(style.letterSpacingPx || 0);
  });
}

export function measureCartographicLabel(context, label) {
  context.save();
  context.font = font(label.style);
  const measured = measureSpacedText(context, label.renderedText, label.style.letterSpacingPx);
  context.restore();
  return Object.freeze({ width: measured.width, height: label.style.resolvedFontSizePx * 1.25 });
}

export function renderCartographicLabels({ context, plan } = {}) {
  if (!context || typeof context.measureText !== "function") throw new TypeError("Canvas 2D context is required");
  if (!plan || !Array.isArray(plan.labels)) throw new TypeError("cartographic label plan is required");
  const measured = plan.labels.map((label) => Object.freeze({ label, metrics: measureCartographicLabel(context, label) }));
  const collision = declutterCartographicLabels(measured);
  for (const item of collision.accepted) {
    const { label } = item;
    context.save();
    context.font = font(label.style);
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.lineJoin = "round";
    context.lineWidth = label.style.haloWidthPx * 2;
    context.strokeStyle = label.style.haloStyle;
    context.fillStyle = label.style.fillStyle;
    drawSpacedText(context, label.renderedText, label.x, label.y, label.style, true);
    drawSpacedText(context, label.renderedText, label.x, label.y, label.style, false);
    context.restore();
  }
  return Object.freeze({
    status: "RENDERED",
    planId: plan.planId,
    planVersion: plan.planVersion,
    candidateCount: plan.labels.length,
    renderedCount: collision.accepted.length,
    collisionRejectedCount: collision.rejected.length,
    renderedSubjectIds: Object.freeze(collision.accepted.map((item) => item.label.subjectId)),
  });
}
