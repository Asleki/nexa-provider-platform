/** P006.UI.10/P006.UI.11 — Production feature guard while authentication context is resolved. */
export function productionFeatureGuardMarkup() {
  return `
    <section class="entry-page" aria-labelledby="production-feature-guard-title">
      <p class="eyebrow">Production</p>
      <h1 id="production-feature-guard-title">Checking governed access</h1>
      <p class="summary">Production NoveGeo opens only after the active Production session has been resolved.</p>
    </section>`;
}
