/** P006.UI.3 — Explicit authentication placeholders for Bundle 12D destinations. */
export function accessPlaceholderMarkup(kind) {
  const developer = kind === "developer";
  return `
    <section class="entry-page" aria-labelledby="access-placeholder-title">
      <p class="eyebrow">Production</p>
      <h1 id="access-placeholder-title">${developer ? "NexaDevs Developer" : "Guest"} access</h1>
      <p class="summary">${developer ? "Developer authentication and Enigma verification" : "Guest username and password authentication"} will be introduced in Bundle 12D.</p>
      <div class="planned-panel" role="note"><strong>Planned</strong><span>Authentication is intentionally not implemented in Bundle 12C.</span></div>
      <button class="text-button" type="button" data-action="back">← Back</button>
    </section>`;
}
