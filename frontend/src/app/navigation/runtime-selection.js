/** P006.UI.2 — Selected NexiLabs runtime is distinct from deployment environment. */
export const SelectedRuntime = Object.freeze({
  SIMULATION: "simulation",
  PRODUCTION: "production",
});

export function createRuntimeSelection() {
  let selectedRuntime = null;
  return Object.freeze({
    get value() { return selectedRuntime; },
    select(runtime) {
      if (!Object.values(SelectedRuntime).includes(runtime)) {
        throw new Error(`Unsupported selected runtime: ${runtime}`);
      }
      selectedRuntime = runtime;
      return selectedRuntime;
    },
    clear() {
      selectedRuntime = null;
      return null;
    },
  });
}
