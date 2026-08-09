/** P006.UI.6 — Guest username/password development sign-in page. */
export function guestSignInMarkup({ error = "" } = {}) {
  return `
    <section class="entry-page auth-page" aria-labelledby="guest-sign-in-title">
      <p class="eyebrow">Production · Guest</p>
      <h1 id="guest-sign-in-title">Guest sign in</h1>
      <p class="summary">Sign in for client and observational access.</p>
      <form class="auth-form" data-auth-form="guest" novalidate>
        <label>Username<input name="username" autocomplete="username" required></label>
        <label>Password<input name="password" type="password" autocomplete="current-password" required></label>
        ${error ? `<p class="auth-message auth-message-error" role="alert">${error}</p>` : ""}
        <button class="primary-button" type="submit">Sign in</button>
      </form>
      <button class="text-button" type="button" data-action="back">← Back</button>
    </section>`;
}
