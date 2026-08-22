/** P006.7.11.9 — Live PostgreSQL NNGLA status panel; never claims static fallback authority. */
import { createLiveNnglaReadClient } from "./live-read-client.js";

function familyByCode(status, code) {
  return status.families.find((item) => item.family === code) || { sourceCount: 0, canonicalCount: 0, publishedCount: 0, mapRenderableCount: 0 };
}

function statusMarkup(status) {
  const places = familyByCode(status, "PLACE");
  const roads = familyByCode(status, "ROAD");
  const features = familyByCode(status, "GEOGRAPHIC_FEATURE");
  const admin = familyByCode(status, "ADMINISTRATIVE_AREA");
  const canonicalTotal = status.families.reduce((sum, item) => sum + item.canonicalCount, 0);
  const publishedTotal = status.families.reduce((sum, item) => sum + item.publishedCount, 0);
  const mapTotal = status.families.reduce((sum, item) => sum + item.mapRenderableCount, 0);
  return `<div class="nngla-status-heading"><div><span class="section-kicker">NNGLA sovereign registry</span><strong>Live Database Authority</strong></div><span class="nngla-status-badge">API · READ ONLY</span></div>
    <p>PostgreSQL/PostGIS is the server-side authority. Canonical records are not public until an explicit governed publication projection exists.</p>
    <dl class="workspace-facts nngla-status-facts">
      <div><dt>Read runtime</dt><dd>${status.readRuntime}</dd></div>
      <div><dt>Places</dt><dd>${places.canonicalCount} canonical / ${places.sourceCount} source</dd></div>
      <div><dt>Roads</dt><dd>${roads.canonicalCount} canonical / ${roads.sourceCount} source</dd></div>
      <div><dt>Features / admin</dt><dd>${features.canonicalCount} features · ${admin.canonicalCount} admin</dd></div>
      <div><dt>Canonical total</dt><dd>${canonicalTotal}</dd></div>
      <div><dt>Published</dt><dd>${publishedTotal}</dd></div>
      <div><dt>Map-renderable</dt><dd>${mapTotal}</dd></div>
      <div><dt>Migration</dt><dd>${status.liveDatabaseMigrationStatus}</dd></div>
    </dl>`;
}

export function mountLiveNnglaPublicationStatus({ documentRef = globalThis.document, fetchRef = globalThis.fetch, apiBaseUrl = "" } = {}) {
  const page = documentRef?.querySelector?.(".novegeo-feature-page");
  if (!page) return Object.freeze({ status: "UNAVAILABLE", reason: "novegeo_page_missing", disconnect() {} });
  const panel = documentRef.createElement?.("aside");
  if (!panel) return Object.freeze({ status: "UNAVAILABLE", reason: "dom_creation_unavailable", disconnect() {} });
  panel.className = "privacy-note nngla-publication-status";
  panel.dataset.role = "nngla-live-publication-status";
  panel.setAttribute?.("role", "status");
  panel.setAttribute?.("aria-live", "polite");
  page.append?.(panel);

  if (!String(apiBaseUrl).trim()) {
    panel.dataset.status = "DEGRADED";
    panel.innerHTML = `<strong>NNGLA live database authority unavailable</strong><p>No API endpoint is configured. Bundled geography is not being promoted as current national authority.</p>`;
    return Object.freeze({ status: "DEGRADED", reason: "api_base_url_unconfigured", disconnect() { panel.remove?.(); } });
  }

  panel.dataset.status = "LOADING";
  panel.innerHTML = `<strong>NNGLA sovereign registry</strong><p>Checking PostgreSQL-backed read authority…</p>`;
  const client = createLiveNnglaReadClient({ apiBaseUrl, fetchRef });
  const ready = client.status().then((status) => {
    panel.dataset.status = "READY";
    panel.innerHTML = statusMarkup(status);
    return status;
  }).catch((error) => {
    panel.dataset.status = "DEGRADED";
    panel.innerHTML = `<strong>NNGLA live database authority unavailable</strong><p>The authoritative API read failed. No bundled registry or map data has been substituted as live authority.</p>`;
    return Object.freeze({ error: error?.message || String(error) });
  });
  return Object.freeze({ status: "LOADING", ready, disconnect() { panel.remove?.(); } });
}
