/** P006.UI.9 — Safe authenticated transition; workspaces remain Bundle 12E. */
export function authenticatedTransitionMarkup(session) {
  const developer = session?.identityType === "nexadevs_developer";
  return `
    <section class="entry-page auth-page" aria-labelledby="authenticated-title">
      <p class="eyebrow">${session?.runtime || "Production"} · Authenticated</p>
      <h1 id="authenticated-title">${developer ? "NexaDevs Developer" : "Guest"} authenticated</h1>
      <p class="summary">Your NexiLabs session is active. Role-based workspace integration follows in Bundle 12E.</p>
      <dl class="auth-session-summary">
        <div><dt>Principal</dt><dd>${session?.principalId || ""}</dd></div>
        <div><dt>Authentication</dt><dd>${session?.authenticationStrength || ""}</dd></div>
      </dl>
      <button class="primary-button" type="button" data-auth-action="logout">Sign out</button>
    </section>`;
}
