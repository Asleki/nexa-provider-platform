/** P004.3-P004.4 map presentation orchestration and responsive redraw boundary. */

import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "./publication.js";
import { MapFitMode } from "./contracts.js";
import { createViewport } from "./viewport.js";
import { createBoundaryRenderPlan } from "./boundary-render-plan.js";
import { createCoordinateGrid } from "./coordinate-grid.js";
import { renderMapCanvas } from "./canvas-renderer.js";
import { qualifyMapCore } from "../validation/qualification.js";

const DEFAULT_VIEWPORT_WIDTH = 640;
const MINIMUM_VIEWPORT_WIDTH = 280;
const MINIMUM_VIEWPORT_HEIGHT = 260;
const VIEWPORT_ASPECT_RATIO = 0.68;

function setStatus(container, status, message) {
  if (container?.dataset) {
    container.dataset.mapStatus = status;
  }

  const statusNode = container?.querySelector?.(
    "[data-role='map-render-status']",
  );

  if (statusNode) {
    statusNode.textContent = message;
  }
}

function createCanvas(documentRef) {
  const canvas = documentRef.createElement("canvas");

  canvas.setAttribute("data-role", "novegeo-map-canvas");
  canvas.setAttribute(
    "aria-label",
    "Rendered NoveGeo sovereign boundary with longitude, latitude and equator reference lines",
  );

  return canvas;
}

function resolveViewportWidth(container) {
  const rect =
    typeof container.getBoundingClientRect === "function"
      ? container.getBoundingClientRect()
      : null;

  const measuredWidth = Number(
    rect?.width ||
      container.clientWidth ||
      DEFAULT_VIEWPORT_WIDTH,
  );

  if (!Number.isFinite(measuredWidth) || measuredWidth <= 0) {
    return DEFAULT_VIEWPORT_WIDTH;
  }

  return Math.max(MINIMUM_VIEWPORT_WIDTH, measuredWidth);
}

function resolveViewportHeight(cssWidth) {
  const proportionalHeight = Math.round(
    cssWidth * VIEWPORT_ASPECT_RATIO,
  );

  return Math.max(
    MINIMUM_VIEWPORT_HEIGHT,
    proportionalHeight,
  );
}

export function mountMapPresentation(
  documentRef,
  {
    publication = BUNDLED_WORLD_BOUNDARY_PUBLICATION,
    devicePixelRatio = Number(globalThis.devicePixelRatio || 1),
    longitudeInterval = 5,
    latitudeInterval = 5,
    observeResize = true,
  } = {},
) {
  const container = documentRef?.querySelector?.(
    "[data-role='future-map-viewport']",
  );

  if (!container) {
    return Object.freeze({
      status: "UNAVAILABLE",
      reason: "viewport_missing",
    });
  }

  if (typeof documentRef.createElement !== "function") {
    setStatus(container, "UNAVAILABLE", "Map unavailable");

    return Object.freeze({
      status: "UNAVAILABLE",
      reason: "document_creation_unavailable",
    });
  }

  const canvas = createCanvas(documentRef);

  if (typeof container.replaceChildren === "function") {
    container.replaceChildren(canvas);
  } else if (typeof container.appendChild === "function") {
    container.appendChild(canvas);
  }

  let lastReceipt = null;
  let lastRenderedWidth = null;
  let renderScheduled = false;

  const render = () => {
    try {
      const cssWidth = resolveViewportWidth(container);
      const cssHeight = resolveViewportHeight(cssWidth);

      const viewport = createViewport({
        cssWidth,
        cssHeight,
        devicePixelRatio,
        padding: Math.min(
          36,
          Math.max(20, cssWidth * 0.055),
        ),
        fitMode: MapFitMode.BOUNDARY,
        extent: publication.extent,
      });

      const qualification = qualifyMapCore({ publication, viewport });

      if (qualification.status !== "PASSED") {
        const failedCodes = qualification.findings
          .filter((finding) => !finding.passed)
          .map((finding) => finding.code)
          .join(", ");
        throw new Error(`map-core qualification failed: ${failedCodes}`);
      }

      const boundaryPlan = qualification.renderPlan || createBoundaryRenderPlan(
        publication,
        viewport,
      );

      const grid = qualification.grid || createCoordinateGrid(viewport, {
        longitudeInterval,
        latitudeInterval,
      });

      const renderReceipt = renderMapCanvas({
        canvas,
        viewport,
        boundaryPlan,
        grid,
      });

      lastReceipt = Object.freeze({
        ...renderReceipt,
        qualificationId: qualification.qualificationId,
        qualificationVersion: qualification.qualificationVersion,
        qualificationStatus: qualification.status,
        qualificationFindingCount: qualification.findingCount,
      });

      lastRenderedWidth = cssWidth;

      setStatus(container, "READY", "Map rendered");

      return lastReceipt;
    } catch (error) {
      lastReceipt = Object.freeze({
        status: "DEGRADED",
        reason:
          error instanceof Error
            ? error.message
            : String(error),
      });

      setStatus(
        container,
        "DEGRADED",
        "Map rendering unavailable",
      );

      return lastReceipt;
    }
  };

  const scheduleRender = () => {
    if (renderScheduled) {
      return;
    }

    renderScheduled = true;

    const run = () => {
      renderScheduled = false;

      const nextWidth = resolveViewportWidth(container);

      if (
        lastRenderedWidth !== null &&
        Math.abs(nextWidth - lastRenderedWidth) < 1
      ) {
        return;
      }

      render();
    };

    if (typeof globalThis.requestAnimationFrame === "function") {
      globalThis.requestAnimationFrame(run);
    } else {
      run();
    }
  };

  const firstReceipt = render();

  let observer = null;

  if (
    observeResize &&
    typeof globalThis.ResizeObserver === "function"
  ) {
    observer = new globalThis.ResizeObserver(() => {
      scheduleRender();
    });

    observer.observe(container);
  }

  return Object.freeze({
    ...firstReceipt,

    get latestReceipt() {
      return lastReceipt;
    },

    redraw() {
      lastRenderedWidth = null;
      return render();
    },

    disconnect() {
      observer?.disconnect();
    },
  });
}