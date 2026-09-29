import '@testing-library/jest-dom/vitest';
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

// vitest.config.ts doesn't enable `test.globals`, so Testing Library can't
// auto-detect a global afterEach to hook its automatic unmount into - without
// this, each test's rendered tree leaks into the next one in the same file.
afterEach(() => {
  cleanup();
});

// jsdom doesn't implement these; Radix UI's Select/Dialog primitives call
// them during pointer interaction and layout, and throw without a stub.
if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false;
}
if (!Element.prototype.setPointerCapture) {
  Element.prototype.setPointerCapture = () => {};
}
if (!Element.prototype.releasePointerCapture) {
  Element.prototype.releasePointerCapture = () => {};
}
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}
if (typeof window.ResizeObserver === 'undefined') {
  window.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}
