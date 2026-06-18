/**
 * Test environment setup for SkillHub frontend tests.
 *
 * Provides:
 * - localStorage mock with full Storage API (get, set, remove, clear, key, length)
 * - Automatic localStorage.clear() before each test via beforeEach hook
 * - Utility to simulate localStorage unavailability for graceful degradation tests
 *
 * Validates: Requirements 17.5
 */

import { beforeEach, afterEach } from 'vitest';

// --- localStorage Mock ---
// jsdom provides a basic localStorage, but we augment setup to ensure
// a clean slate between tests and provide helpers for degradation testing.

/**
 * In-memory localStorage implementation.
 * Used as a reliable mock that can be inspected and controlled in tests.
 */
class LocalStorageMock {
  constructor() {
    this._store = {};
  }

  get length() {
    return Object.keys(this._store).length;
  }

  key(index) {
    const keys = Object.keys(this._store);
    return keys[index] ?? null;
  }

  getItem(key) {
    return Object.prototype.hasOwnProperty.call(this._store, key)
      ? this._store[key]
      : null;
  }

  setItem(key, value) {
    this._store[key] = String(value);
  }

  removeItem(key) {
    delete this._store[key];
  }

  clear() {
    this._store = {};
  }
}

// Install the localStorage mock on the global window object
const localStorageMock = new LocalStorageMock();

Object.defineProperty(globalThis, 'localStorage', {
  value: localStorageMock,
  writable: true,
  configurable: true,
});

// --- Automatic cleanup between tests ---
beforeEach(() => {
  localStorage.clear();
});

// --- Test environment defaults ---
// Ensure navigator.language defaults are set for i18n tests
Object.defineProperty(globalThis.navigator, 'language', {
  value: 'en-US',
  configurable: true,
  writable: true,
});

Object.defineProperty(globalThis.navigator, 'languages', {
  value: ['en-US'],
  configurable: true,
  writable: true,
});

// --- Utility: simulate localStorage unavailability ---

/**
 * Temporarily disable localStorage to test graceful degradation.
 * Returns a restore function that re-enables localStorage.
 *
 * Usage:
 *   const restore = disableLocalStorage();
 *   // ... run code that should degrade gracefully ...
 *   restore();
 *
 * @returns {Function} Restore function to re-enable localStorage
 */
export function disableLocalStorage() {
  const originalSetItem = localStorage.setItem;
  const originalGetItem = localStorage.getItem;
  const originalRemoveItem = localStorage.removeItem;
  const originalKey = localStorage.key;

  localStorage.setItem = () => { throw new DOMException('Storage disabled', 'SecurityError'); };
  localStorage.getItem = () => { throw new DOMException('Storage disabled', 'SecurityError'); };
  localStorage.removeItem = () => { throw new DOMException('Storage disabled', 'SecurityError'); };
  localStorage.key = () => { throw new DOMException('Storage disabled', 'SecurityError'); };

  return () => {
    localStorage.setItem = originalSetItem;
    localStorage.getItem = originalGetItem;
    localStorage.removeItem = originalRemoveItem;
    localStorage.key = originalKey;
  };
}
