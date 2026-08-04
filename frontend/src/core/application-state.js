/**
 * NexiLabs NoveGeo PWA
 * P002.1/P002.2 — Application lifecycle state contract.
 */

export const ApplicationStatus = Object.freeze({
  CREATED: "CREATED",
  BOOTING: "BOOTING",
  READY: "READY",
  DEGRADED: "DEGRADED",
  FAILED: "FAILED",
  STOPPED: "STOPPED",
});

const ALLOWED_TRANSITIONS = Object.freeze({
  CREATED: Object.freeze([ApplicationStatus.BOOTING]),
  BOOTING: Object.freeze([
    ApplicationStatus.READY,
    ApplicationStatus.DEGRADED,
    ApplicationStatus.FAILED,
  ]),
  READY: Object.freeze([ApplicationStatus.DEGRADED, ApplicationStatus.STOPPED]),
  DEGRADED: Object.freeze([
    ApplicationStatus.READY,
    ApplicationStatus.FAILED,
    ApplicationStatus.STOPPED,
  ]),
  FAILED: Object.freeze([ApplicationStatus.STOPPED]),
  STOPPED: Object.freeze([]),
});

function assertKnownStatus(status) {
  if (!Object.values(ApplicationStatus).includes(status)) {
    throw new TypeError(`Unknown application status: ${String(status)}`);
  }
}

function freezeSnapshot(snapshot) {
  return Object.freeze({
    ...snapshot,
    details: Object.freeze({ ...(snapshot.details ?? {}) }),
  });
}

export class ApplicationState {
  #snapshot;
  #clock;

  constructor({ clock = () => new Date().toISOString() } = {}) {
    if (typeof clock !== "function") {
      throw new TypeError("clock must be a function");
    }
    this.#clock = clock;
    this.#snapshot = freezeSnapshot({
      status: ApplicationStatus.CREATED,
      sequence: 0,
      changedAt: this.#clock(),
      details: {},
    });
  }

  get snapshot() {
    return this.#snapshot;
  }

  canTransitionTo(nextStatus) {
    assertKnownStatus(nextStatus);
    return ALLOWED_TRANSITIONS[this.#snapshot.status].includes(nextStatus);
  }

  transition(nextStatus, details = {}) {
    assertKnownStatus(nextStatus);
    if (details === null || typeof details !== "object" || Array.isArray(details)) {
      throw new TypeError("transition details must be an object");
    }
    if (!this.canTransitionTo(nextStatus)) {
      throw new Error(
        `Invalid application transition: ${this.#snapshot.status} -> ${nextStatus}`,
      );
    }
    this.#snapshot = freezeSnapshot({
      status: nextStatus,
      sequence: this.#snapshot.sequence + 1,
      changedAt: this.#clock(),
      details,
    });
    return this.#snapshot;
  }
}
