import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  installAccountEnrollmentExperience,
  ACCOUNT_ENROLLMENT_FOUNDATION_MESSAGE,
} from "../../src/app/account/account-enrollment-experience.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const source = readFileSync(resolve(ROOT, "src/app/account/account-enrollment-experience.js"), "utf8");
const mainSource = readFileSync(resolve(ROOT, "src/main.js"), "utf8");

function fixture({ hash = "#/runtime" } = {}) {
  const listeners = new Map();
  const headChildren = [];
  const root = { dataset: {} };
  const outlet = { innerHTML: "" };
  const main = { focusCalls: 0, focus() { this.focusCalls += 1; } };
  const gateway = {
    inserted: [],
    querySelector() { return null; },
    insertAdjacentHTML(_position, html) { this.inserted.push(html); },
  };
  let styleLink = null;

  const documentRef = {
    head: { appendChild(node) { headChildren.push(node); styleLink = node; } },
    createElement(tag) { return { tagName: tag.toUpperCase(), dataset: {} }; },
    querySelector(selector) {
      if (selector === "link[data-account-enrollment-styles='true']") return styleLink;
      if (selector === "#nexilabs-app") return root;
      if (selector === "[data-role='application-page']") return outlet;
      if (selector === "#main-content") return main;
      if (selector === ".runtime-gateway") return gateway;
      return null;
    },
    addEventListener(type, listener) { listeners.set(type, listener); },
    removeEventListener(type) { listeners.delete(type); },
  };
  const windowListeners = new Map();
  const windowRef = {
    location: { hash },
    addEventListener(type, listener) { windowListeners.set(type, listener); },
    removeEventListener(type) { windowListeners.delete(type); },
  };

  return { documentRef, windowRef, listeners, windowListeners, root, outlet, main, gateway, headChildren };
}

test("P006.UI.10.1 experience installs one stylesheet and decorates only the Home runtime gateway", () => {
  const fx = fixture();
  const experience = installAccountEnrollmentExperience({ documentRef: fx.documentRef, windowRef: fx.windowRef });
  assert.equal(fx.headChildren.length, 1);
  assert.equal(fx.headChildren[0].href, "./styles/account-enrollment-v1.css");
  assert.equal(fx.gateway.inserted.length, 1);
  assert.match(fx.gateway.inserted[0], /Create Account/);
  assert.equal("accountEnrollmentRoute" in fx.root.dataset, false);
  experience.dispose();
});

test("P006.UI.10.1 account hashes render through the additive account experience without changing runtime routes", () => {
  const fx = fixture({ hash: "#/account" });
  const experience = installAccountEnrollmentExperience({ documentRef: fx.documentRef, windowRef: fx.windowRef });
  assert.match(fx.outlet.innerHTML, /Your NexiLabs Account/);
  assert.equal(fx.root.dataset.accountEnrollmentRoute, "account-enrollment");
  assert.equal(fx.gateway.inserted.length, 0);

  fx.windowRef.location.hash = "#/account/developer/verify-setup";
  experience.render();
  assert.match(fx.outlet.innerHTML, /Verify Developer Setup/);
  assert.equal(fx.root.dataset.accountEnrollmentRoute, "account-developer-verify-setup");
  experience.dispose();
});

test("P006.UI.10.1 foundation forms never submit data and report the deferred authority boundary", () => {
  const fx = fixture({ hash: "#/account/guest/create" });
  const experience = installAccountEnrollmentExperience({ documentRef: fx.documentRef, windowRef: fx.windowRef });
  const message = { textContent: "" };
  const form = { querySelector: () => message };
  let prevented = false;
  fx.listeners.get("submit")({
    target: { closest: (selector) => selector === "[data-account-foundation-form]" ? form : null },
    preventDefault() { prevented = true; },
  });
  assert.equal(prevented, true);
  assert.equal(message.textContent, ACCOUNT_ENROLLMENT_FOUNDATION_MESSAGE);
  experience.dispose();
});


test("P006.UI.10.1 same-hash Home navigation restores the secondary Create Account entry after shell rerender", async () => {
  const fx = fixture();
  const experience = installAccountEnrollmentExperience({ documentRef: fx.documentRef, windowRef: fx.windowRef });
  fx.gateway.inserted.length = 0;
  fx.listeners.get("click")({
    target: {
      closest(selector) {
        if (selector === "[data-account-route]") return null;
        if (selector === "[data-route='runtime-gateway']") return { dataset: { route: "runtime-gateway" } };
        return null;
      },
    },
  });
  await Promise.resolve();
  assert.equal(fx.gateway.inserted.length, 1);
  assert.match(fx.gateway.inserted[0], /Create Account/);
  experience.dispose();
});

test("P006.UI.10.1 account frontend contains no API, browser credential persistence or clipboard authority", () => {
  assert.doesNotMatch(source, /\bfetch\s*\(/);
  assert.doesNotMatch(source, /localStorage|sessionStorage/);
  assert.doesNotMatch(source, /development-auth-client|\/auth\//);
  assert.doesNotMatch(source, /navigator\.clipboard/);
});

test("P006.UI.10.1 main composition adds enrollment without replacing the proven authentication installer", () => {
  assert.match(mainSource, /import\("\.\/app\/account\/account-enrollment-experience\.js"\)/);
  assert.match(mainSource, /installAccountEnrollmentExperience/);
  assert.match(mainSource, /import\("\.\/app\/auth\/authentication-experience\.js"\)/);
  assert.match(mainSource, /installAuthenticationExperience/);
});
