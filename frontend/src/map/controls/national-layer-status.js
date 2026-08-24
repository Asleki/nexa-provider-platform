/** P006.7.11.15.0 / Bundle 22A — presentation-only reservation for future governed national map layers. */

export const NationalLayerAvailability = Object.freeze({
  PUBLICATION_PENDING: "PUBLICATION_PENDING",
  AVAILABLE: "AVAILABLE",
  UNAVAILABLE: "UNAVAILABLE",
});

export const NATIONAL_MAP_LAYER_CATALOG = Object.freeze([
  Object.freeze({ key: "places", label: "Places", futureMilestone: "P006.7.11.15.6" }),
  Object.freeze({ key: "roads", label: "Roads", futureMilestone: "P006.7.11.15.5" }),
  Object.freeze({ key: "administrativeBoundaries", label: "Administrative boundaries", futureMilestone: "P006.7.11.15.7" }),
  Object.freeze({ key: "hydrology", label: "Hydrology", futureMilestone: "P006.7.11.15.8" }),
  Object.freeze({ key: "landforms", label: "Landforms", futureMilestone: "P006.7.11.15.8" }),
]);

function normalizedAvailability(value) {
  return Object.values(NationalLayerAvailability).includes(value)
    ? value
    : NationalLayerAvailability.PUBLICATION_PENDING;
}

export function createNationalLayerStatus(overrides = {}) {
  return Object.freeze(NATIONAL_MAP_LAYER_CATALOG.map((layer) => {
    const override = overrides?.[layer.key] || {};
    const availability = normalizedAvailability(override.availability);
    return Object.freeze({
      ...layer,
      availability,
      enabled: availability === NationalLayerAvailability.AVAILABLE && override.enabled === true,
      authoritative: availability === NationalLayerAvailability.AVAILABLE && override.authoritative === true,
      statusLabel: availability === NationalLayerAvailability.AVAILABLE
        ? "Available"
        : availability === NationalLayerAvailability.UNAVAILABLE
          ? "Unavailable"
          : "Publication pending",
    });
  }));
}

export function nationalLayerStatusSummary(status = createNationalLayerStatus()) {
  const available = status.filter((item) => item.availability === NationalLayerAvailability.AVAILABLE).length;
  const pending = status.filter((item) => item.availability === NationalLayerAvailability.PUBLICATION_PENDING).length;
  return Object.freeze({ total: status.length, available, pending });
}
