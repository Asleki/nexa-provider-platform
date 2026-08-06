/** P004.5 deterministic map-core qualification orchestration. */
import { validateWorldBoundaryPublication } from "../geography/contracts.js";
import { createBoundaryRenderPlan } from "../presentation/boundary-render-plan.js";
import { createCoordinateGrid } from "../presentation/coordinate-grid.js";
import { MAP_QUALIFICATION_ID, MAP_QUALIFICATION_VERSION, QualificationStatus, createValidationFinding } from "./contracts.js";
import { validateBoundaryGeometry } from "./geometry-validator.js";
import { deriveBoundaryExtent } from "./extent-calculator.js";
import { assertPositionsWithinExtent, validateExtentParity } from "./extent-validator.js";
import { validateProjectionPositions } from "./projection-validator.js";
import { validateRenderPlanWithinViewport } from "./viewport-validator.js";

export function qualifyMapCore({ publication, viewport }) {
  const findings = [];
  const run = (code, message, operation) => {
    try {
      const details = operation();
      findings.push(createValidationFinding({ code, passed: true, message, details }));
      return details;
    } catch (error) {
      findings.push(createValidationFinding({ code, passed: false, message, details: { reason: error instanceof Error ? error.message : String(error) } }));
      return null;
    }
  };

  const validatedPublication = run("PUBLICATION_CONTRACT", "World-boundary publication satisfies the browser authority contract.", () => validateWorldBoundaryPublication(publication));
  const geometry = validatedPublication ? run("GEOMETRY_STRUCTURE", "MultiPolygon geometry, rings and coordinates are valid.", () => validateBoundaryGeometry(validatedPublication.geometry)) : null;
  const derived = geometry ? run("EXTENT_DERIVATION", "Boundary extent is derived deterministically from governed positions.", () => deriveBoundaryExtent(validatedPublication.geometry)) : null;
  if (derived) run("EXTENT_PARITY", "Declared and derived world extents match.", () => validateExtentParity(validatedPublication.extent, derived.extent));
  if (geometry) run("EXTENT_CONTAINMENT", "Every governed boundary position lies within the declared extent.", () => ({ extent: assertPositionsWithinExtent(geometry.positions, validatedPublication.extent) }));
  if (geometry) run("PROJECTION_ROUND_TRIP", "Every governed boundary position projects and restores within tolerance.", () => validateProjectionPositions(geometry.positions));

  let renderPlan = null;
  let grid = null;
  if (validatedPublication && viewport) {
    renderPlan = run("RENDER_PLAN", "A deterministic boundary render plan is produced.", () => createBoundaryRenderPlan(validatedPublication, viewport));
    if (renderPlan) run("VIEWPORT_BOUNDS", "Every rendered boundary point lies within the drawable viewport.", () => validateRenderPlanWithinViewport(renderPlan, viewport));
    grid = run("GRID_CONTRACT", "Latitude, longitude and equator overlays agree with the active extent.", () => createCoordinateGrid(viewport));
  }

  const status = findings.every((finding) => finding.passed) ? QualificationStatus.PASSED : QualificationStatus.FAILED;
  return Object.freeze({
    qualificationId: MAP_QUALIFICATION_ID,
    qualificationVersion: MAP_QUALIFICATION_VERSION,
    status,
    boundaryId: publication?.boundaryId ?? null,
    boundaryVersion: publication?.boundaryVersion ?? null,
    findingCount: findings.length,
    findings: Object.freeze(findings),
    geometrySummary: geometry,
    derivedExtent: derived?.extent ?? null,
    renderPlan,
    grid,
    databaseWritesPerformed: 0,
  });
}
