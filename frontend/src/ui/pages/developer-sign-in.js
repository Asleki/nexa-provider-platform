/** P006.UI.7 — NexaDevs Developer primary credential page. */
export function developerSignInMarkup({ error = "" } = {}) {
  return `
    <section class="entry-page auth-page" aria-labelledby="developer-sign-in-title">
      <p class="eyebrow">Production · NexaDevs</p>
      <h1 id="developer-sign-in-title">Developer sign in</h1>
      <p class="summary">Primary credentials are verified before an Enigma challenge is issued.</p>
      <form class="auth-form" data-auth-form="developer" novalidate>
        <label>Username / Developer ID<input name="username" autocomplete="username" required></label>
        <label>Password<input name="password" type="password" autocomplete="current-password" required></label>
        ${error ? `<p class="auth-message auth-message-error" role="alert">${error}</p>` : ""}
        <button class="primary-button" type="submit">Continue</button>
      </form>
      <button class="text-button" type="button" data-action="back">← Back</button>
    </section>`;
}
