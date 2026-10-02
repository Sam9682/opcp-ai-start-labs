/**
 * ScormApiWrapper - Thin, defensive wrapper over the raw SCORM 1.2 `API`
 * method surface (LMSInitialize, LMSGetValue, LMSSetValue, LMSCommit,
 * LMSFinish). Every method is a safe no-op when no API was discovered, and
 * every raw call is wrapped in try/catch so an LMS error never propagates to
 * the course (graceful degradation).
 *
 * Validates: Requirements 6.3, 6.4, 7.1, 7.4
 */

export class ScormApiWrapper {
  /**
   * @param {object|null} api  Result of discoverApi(); null → inert wrapper.
   */
  constructor(api) {
    this.api = api;
    this.initialized = false;
  }

  /**
   * Whether a live LMS API object was discovered.
   * @returns {boolean}
   */
  get available() {
    return this.api != null;
  }

  /**
   * Initialize the SCORM session via LMSInitialize(""). Must run before any
   * get/set (Req 6.3). Safe no-op (returns false) when no API is available.
   * @returns {boolean} True if the LMS reported a successful initialization.
   */
  initialize() {
    if (!this.available) {
      return false;
    }
    try {
      const result = this.api.LMSInitialize("");
      // SCORM 1.2 returns the string "true"/"false" or a boolean.
      this.initialized = result === "true" || result === true;
      return this.initialized;
    } catch {
      return false;
    }
  }

  /**
   * Read a data model element via LMSGetValue.
   * @param {string} element  e.g. "cmi.suspend_data"
   * @returns {string} The value, or "" on error / when unavailable.
   */
  getValue(element) {
    if (!this.available) {
      return "";
    }
    try {
      const value = this.api.LMSGetValue(element);
      return value == null ? "" : String(value);
    } catch {
      return "";
    }
  }

  /**
   * Write a data model element via LMSSetValue.
   * @param {string} element  e.g. "cmi.core.lesson_status"
   * @param {string|number} value
   * @returns {boolean} True if the LMS reported a successful set.
   */
  setValue(element, value) {
    if (!this.available) {
      return false;
    }
    try {
      const result = this.api.LMSSetValue(element, String(value));
      return result === "true" || result === true;
    } catch {
      return false;
    }
  }

  /**
   * Persist pending values via LMSCommit("").
   * @returns {boolean} True if the LMS reported a successful commit.
   */
  commit() {
    if (!this.available) {
      return false;
    }
    try {
      const result = this.api.LMSCommit("");
      return result === "true" || result === true;
    } catch {
      return false;
    }
  }

  /**
   * End the SCORM session via LMSFinish("").
   * @returns {boolean} True if the LMS reported a successful finish.
   */
  terminate() {
    if (!this.available) {
      return false;
    }
    try {
      const result = this.api.LMSFinish("");
      if (result === "true" || result === true) {
        this.initialized = false;
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }
}
