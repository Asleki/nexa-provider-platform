/**
 * P004.M1.5 runtime publication bridge.
 *
 * The map renderer consumes a publication object without owning how that
 * publication was authored or selected. The active bundled national view now
 * resolves through the governed v002 multi-resolution catalogue.
 */
import { selectWorldBoundaryPublication } from "../publication/catalog.js";

export const BUNDLED_WORLD_BOUNDARY_PUBLICATION =
  selectWorldBoundaryPublication("standard");
