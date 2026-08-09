/** P006.UI.8 — NexaDevs private-authority Enigma challenge page. */
export function developerEnigmaMarkup(challenge, { error = "" } = {}) {
  const words = (challenge?.words || []).map((word) => `<strong>${word}</strong>`).join("");
  return `
    <section class="entry-page auth-page" aria-labelledby="developer-enigma-title">
      <p class="eyebrow">Production · NexaDevs</p>
      <h1 id="developer-enigma-title">NexaDevs Enigma</h1>
      <p class="summary">Solve your assigned Enigma procedure and enter the response signature.</p>
      <div class="enigma-challenge" aria-label="Enigma challenge words">${words}</div>
      <p class="enigma-meta">${challenge?.period || ""} · ${challenge?.wordLength || ""}-letter challenge</p>
      <form class="auth-form" data-auth-form="developer-enigma" novalidate>
        <label>Enigma response<input name="response" autocomplete="off" autocapitalize="characters" spellcheck="false" required></label>
        ${error ? `<p class="auth-message auth-message-error" role="alert">${error}</p>` : ""}
        <button class="primary-button" type="submit">Verify & enter</button>
      </form>
      <button class="text-button" type="button" data-action="back">← Back</button>
    </section>`;
}
