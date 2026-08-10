/** P006.UI.10-P006.UI.12 — Stable workspace capability descriptors for Bundle 12E. */

export const CapabilityAvailability = Object.freeze({
  AVAILABLE: "available",
  FOUNDATION: "foundation",
  PLANNED: "planned",
  DEFERRED: "deferred",
});

function capability({ id, title, description, availability, route = null, requiredPermission = null }) {
  return Object.freeze({ id, title, description, availability, route, requiredPermission });
}

export const DEVELOPER_CAPABILITIES = Object.freeze([
  capability({
    id: "novegeo",
    title: "NoveGeo",
    description: "Open the governed NoveGeo geography and current map interaction surface.",
    availability: CapabilityAvailability.AVAILABLE,
    route: "production-novegeo",
  }),
  capability({
    id: "name-catalogue",
    title: "Name Catalogue",
    description: "Governed canonical-name authority foundation. Browser read/search remains a later API-first consumer milestone.",
    availability: CapabilityAvailability.FOUNDATION,
  }),
  capability({
    id: "citizen-registry",
    title: "Citizen Registry",
    description: "Reserved for a later governed registry milestone.",
    availability: CapabilityAvailability.PLANNED,
  }),
  capability({
    id: "business-registry",
    title: "Business Registry",
    description: "Reserved for a later governed registry milestone.",
    availability: CapabilityAvailability.PLANNED,
  }),
]);

export const GUEST_CAPABILITIES = Object.freeze([
  capability({
    id: "novegeo",
    title: "NoveGeo",
    description: "Explore the governed NoveGeo geography through your authenticated Production Guest context.",
    availability: CapabilityAvailability.AVAILABLE,
    route: "production-novegeo",
  }),
  capability({
    id: "citizen-relationships",
    title: "Citizen relationships",
    description: "Reserved. A Guest account and a future NoveGeo citizen identity remain separate objects.",
    availability: CapabilityAvailability.PLANNED,
  }),
  capability({
    id: "business-relationships",
    title: "Business relationships",
    description: "Reserved. A Guest account may later hold governed relationships to business identities.",
    availability: CapabilityAvailability.PLANNED,
  }),
]);

export const SIMULATION_CAPABILITIES = Object.freeze([
  capability({
    id: "novegeo",
    title: "Explore NoveGeo",
    description: "Enter the public simulation-facing NoveGeo world map.",
    availability: CapabilityAvailability.AVAILABLE,
    route: "simulation-novegeo",
  }),
  capability({
    id: "public-experience",
    title: "Public NexiLabs experience",
    description: "About, news, reviews, contact, weather, traffic, projects and NexVox access are reserved for later services.",
    availability: CapabilityAvailability.PLANNED,
  }),
  capability({
    id: "public-registries",
    title: "Public registry views",
    description: "Future privacy-safe published views may expose places and public facts without unrestricted citizen identity search.",
    availability: CapabilityAvailability.DEFERRED,
  }),
]);
