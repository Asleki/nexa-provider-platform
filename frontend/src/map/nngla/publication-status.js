/** P006.7.9 / Bundle 15.0D — NNGLA source/canonical/publication status below the NoveGeo map. */
import { createNnglaReadClient } from "./read-client.js";

function apiBaseUrlFromDocument(documentRef) {
  return String(documentRef?.documentElement?.dataset?.apiBaseUrl ?? "").trim();
}

function familyByCode(status, code) {
  return status.families.find((item) => item.family === code) || { sourceCount: 0, canonicalCount: 0, publishedCount: 0, mapRenderableCount: 0, populationState: "UNKNOWN" };
}

function statusMarkup(status) {
  const places = familyByCode(status, "PLACE");
  const roads = familyByCode(status, "ROAD");
  const features = familyByCode(status, "GEOGRAPHIC_FEATURE");
  const admin = familyByCode(status, "ADMINISTRATIVE_AREA");
  const addresses = familyByCode(status, "ADDRESS");
  const parcels = familyByCode(status, "PARCEL");
  const titles = familyByCode(status, "TITLE");
  const stateLand = familyByCode(status, "STATE_LAND");
  const sourceTotal = places.sourceCount + roads.sourceCount + features.sourceCount + admin.sourceCount + addresses.sourceCount + parcels.sourceCount + titles.sourceCount + stateLand.sourceCount;
  const canonicalTotal = status.families.reduce((sum, item) => sum + item.canonicalCount, 0);
  const publishedTotal = status.families.reduce((sum, item) => sum + item.publishedCount, 0);
  const mapTotal = status.families.reduce((sum, item) => sum + item.mapRenderableCount, 0);
  return `<div class="nngla-status-heading"><div><span class="section-kicker">NNGLA sovereign registry</span><strong>Publication Status</strong></div><span class="nngla-status-badge">READ ONLY</span></div>
    <p>Governed CSV sources are distinct from PostgreSQL canonical, published and map-renderable records.</p>
    <dl class="workspace-facts nngla-status-facts">
      <div><dt>Governed source records</dt><dd>${sourceTotal.toLocaleString()} selected NNGLA records</dd></div>
      <div><dt>Places / roads source</dt><dd>${places.sourceCount} places · ${roads.sourceCount} roads</dd></div>
      <div><dt>Features / admin source</dt><dd>${features.sourceCount} features · ${admin.sourceCount} admin</dd></div>
      <div><dt>PostgreSQL canonical</dt><dd>${canonicalTotal}</dd></div>
      <div><dt>Published</dt><dd>${publishedTotal}</dd></div>
      <div><dt>Map-renderable</dt><dd>${mapTotal}</dd></div>
      <div><dt>Migration</dt><dd>${status.liveDatabaseMigrationStatus}</dd></div>
    </dl>`;
}

export function mountNnglaPublicationStatus({ documentRef = globalThis.document, fetchRef = globalThis.fetch, apiBaseUrl = apiBaseUrlFromDocument(documentRef) } = {}) {
  const page = documentRef?.querySelector?.(".novegeo-feature-page");
  if (!page) return Object.freeze({ status: "UNAVAILABLE", reason: "novegeo_page_missing" });
  const panel = documentRef.createElement?.("aside");
  if (!panel) return Object.freeze({ status: "UNAVAILABLE", reason: "dom_creation_unavailable" });
  panel.className = "privacy-note nngla-publication-status";
  panel.dataset.role = "nngla-publication-status";
  panel.setAttribute?.("role", "status");
  panel.setAttribute?.("aria-live", "polite");
  panel.innerHTML = `<strong>NNGLA sovereign registry</strong><p>Checking read-only publication status…</p>`;
  page.append?.(panel);

  if (!apiBaseUrl) {
    panel.dataset.status = "DEGRADED";
    panel.innerHTML = `<div class="nngla-status-heading"><div><span class="section-kicker">NNGLA sovereign registry</span><strong>Publication Status</strong></div><span class="nngla-status-badge">LOCAL</span></div><p>Registry API is not connected in this browser environment. Governed CSV sources remain in the repository, PostgreSQL migration is not executed, and the governed offline base map remains available.</p>`;
    return Object.freeze({ status: "DEGRADED", reason: "api_base_url_unconfigured", disconnect() { panel.remove?.(); } });
  }

  const client = createNnglaReadClient({ apiBaseUrl, fetchRef });
  const ready = client.status().then((status) => {
    panel.dataset.status = "READY";
    panel.innerHTML = statusMarkup(status);
    return status;
  }).catch((error) => {
    panel.dataset.status = "DEGRADED";
    panel.innerHTML = `<strong>NNGLA sovereign registry</strong><p>Live registry reads are temporarily unavailable. The governed offline base map remains available.</p>`;
    return Object.freeze({ error: error?.message || String(error) });
  });

  return Object.freeze({ status: "LOADING", ready, disconnect() { panel.remove?.(); } });
}
