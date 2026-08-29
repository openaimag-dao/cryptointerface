import "@testing-library/jest-dom/vitest";

// This file runs for every test file regardless of its per-file
// `@vitest-environment` — a suite that opts into "node" (e.g.
// middleware.test.ts, which needs Node/Edge-realm Uint8Array semantics
// for jose, not a DOM) has no Element global, so every patch below must
// tolerate that instead of assuming jsdom.
if (typeof Element !== "undefined") {
  // jsdom doesn't implement these — Radix (Dialog, etc.) touches them.
  if (!Element.prototype.hasPointerCapture) {
    Element.prototype.hasPointerCapture = () => false;
  }
  if (!Element.prototype.releasePointerCapture) {
    Element.prototype.releasePointerCapture = () => {};
  }
  if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = () => {};
  }
}
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}
