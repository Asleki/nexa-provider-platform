/** P006.5 — deterministic ordered store for externally supplied map world-state updates. */
import { createWorldStateEnvelope, validateWorldStateEnvelope } from "./world-state-contracts.js";

function canonical(value) {
  return JSON.stringify(value);
}

export function createWorldStateStore({ runtimeMode } = {}) {
  let state = createWorldStateEnvelope({ revision: 0, runtimeMode, sourceReference: "source:nexilabs:baseline", stateReferences: [] });

  const receipt = (status, update, reason = null) => Object.freeze({
    status,
    revision: update?.revision ?? state.revision,
    currentRevision: state.revision,
    reason,
  });

  return Object.freeze({
    get state() { return state; },
    apply(update) {
      let next;
      try {
        next = validateWorldStateEnvelope(update, { runtimeMode });
      } catch (error) {
        return receipt("REJECTED", update, error instanceof Error ? error.message : String(error));
      }
      if (next.revision < state.revision) return receipt("REJECTED_STALE", next, "world-state revision is older than current state");
      if (next.revision === state.revision) {
        if (canonical(next) === canonical(state)) return receipt("DUPLICATE", next);
        return receipt("REJECTED_CONFLICT", next, "world-state revision conflicts with current state");
      }
      if (next.revision !== state.revision + 1) return receipt("REJECTED_GAP", next, "world-state revisions must be applied without gaps");
      state = next;
      return receipt("APPLIED", next);
    },
  });
}
