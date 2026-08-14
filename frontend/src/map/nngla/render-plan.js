/** P006.7.9 — Map plan for already-public NNGLA read items. Never invents position. */
export function createNnglaRenderPlan(items = []) {
  if (!Array.isArray(items)) throw new TypeError("NNGLA render-plan items must be an array");
  const renderable = [];
  const deferred = [];
  for (const item of items) {
    if (!item?.publicEligible) throw new Error("NNGLA render plan accepts public-eligible items only");
    if (item.mapRenderable === true) {
      if (!item.geometryReference) throw new Error("NNGLA map-renderable item requires authoritative geometryReference");
      renderable.push(Object.freeze({ subjectId: item.subjectId, family: item.family, geometryReference: item.geometryReference, displayName: item.displayName }));
    } else {
      deferred.push(Object.freeze({ subjectId: item.subjectId, family: item.family, reason: "NOT_MAP_RENDERABLE" }));
    }
  }
  return Object.freeze({ renderable: Object.freeze(renderable), deferred: Object.freeze(deferred), inventedCoordinates: false });
}
