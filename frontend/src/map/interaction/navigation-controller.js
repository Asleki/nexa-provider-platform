/** P006.1 unified controller for pointer, touch, wheel and keyboard navigation. */
import { createNavigationState, constrainOffsets, clampZoom } from "./navigation-state.js";

const TRANSFORMED_ROLES = Object.freeze([
  "novegeo-map-canvas",
  "novegeo-physical-land-canvas",
  "novegeo-biosphere-canvas",
  "novegeo-hydrology-atmosphere-canvas",
  "novegeo-full-viewport-coordinate-canvas",
]);

function dimensionsOf(viewportElement) {
  const rect = viewportElement?.getBoundingClientRect?.();
  const width = Number(rect?.width || viewportElement?.clientWidth || 640);
  const height = Number(rect?.height || viewportElement?.clientHeight || Math.round(width * 0.68));
  return { width: Math.max(1, width), height: Math.max(1, height) };
}

function layerNodes(viewportElement) {
  return TRANSFORMED_ROLES.map((role) => viewportElement?.querySelector?.(`[data-role='${role}']`)).filter(Boolean);
}

export function createMapNavigationController({ viewportElement, onChange = () => {} } = {}) {
  if (!viewportElement) throw new TypeError("viewportElement is required");
  let state = createNavigationState();

  const apply = () => {
    const transform = `translate(${state.offsetX}px, ${state.offsetY}px) scale(${state.zoom})`;
    for (const node of layerNodes(viewportElement)) {
      Object.assign(node.style || {}, {
        transform,
        transformOrigin: "50% 50%",
        willChange: "transform",
      });
    }
    if (viewportElement.dataset) {
      viewportElement.dataset.mapZoom = state.zoom.toFixed(3);
      viewportElement.dataset.mapNavigationRevision = String(state.revision);
    }
    onChange(state);
    return state;
  };

  const commit = ({ zoom = state.zoom, offsetX = state.offsetX, offsetY = state.offsetY, source }) => {
    const dims = dimensionsOf(viewportElement);
    const constrained = constrainOffsets({ zoom, offsetX, offsetY }, dims);
    state = createNavigationState({ zoom, ...constrained, revision: state.revision + 1, source });
    return apply();
  };

  return Object.freeze({
    get state() { return state; },
    apply,
    panBy(dx, dy, source = "pan") {
      return commit({ offsetX: state.offsetX + Number(dx), offsetY: state.offsetY + Number(dy), source });
    },
    zoomBy(factor, source = "zoom") {
      const nextZoom = clampZoom(state.zoom * Number(factor));
      const ratio = nextZoom / state.zoom;
      return commit({ zoom: nextZoom, offsetX: state.offsetX * ratio, offsetY: state.offsetY * ratio, source });
    },
    zoomTo(zoom, source = "zoom") {
      const nextZoom = clampZoom(zoom);
      const ratio = nextZoom / state.zoom;
      return commit({ zoom: nextZoom, offsetX: state.offsetX * ratio, offsetY: state.offsetY * ratio, source });
    },
    reset(source = "reset") {
      return commit({ zoom: 1, offsetX: 0, offsetY: 0, source });
    },
  });
}
