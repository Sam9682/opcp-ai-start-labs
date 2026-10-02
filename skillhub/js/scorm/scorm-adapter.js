/**
 * ScormAdapter - The orchestrator that maps the course's existing progress and
 * guardrail self-assessment onto the SCORM 1.2 data model. The rest of the
 * course never has to know it exists.
 *
 * It owns the pure status/score computation and the three lifecycle hooks:
 *   - start(): initialize the session + restore progress from suspend_data
 *   - sync():  recompute status/score and push them (+ suspend_data) to the LMS
 *   - end():   mark the session as suspended, commit, and terminate
 *
 * The course functions are injected as `deps` so the status/score logic is
 * testable as pure functions and the DOM-reading guardrail path can be driven
 * by a mock. Every method degrades to a safe no-op when the SCORM API wrapper
 * reports it is unavailable, so the course keeps working standalone.
 *
 * Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 6.3, 6.4
 */

import {
  readCompletedIds,
  serializeProgress,
  deserializeProgress,
  restoreToLocalStorage,
} from "./progress-bridge.js";

export class ScormAdapter {
  /**
   * @param {import("./scorm-api.js").ScormApiWrapper} wrapper - defensive LMS
   *   API wrapper (its `available` getter gates every side effect).
   * @param {object} deps - injected pure course functions for testability:
   * @param {(totalLessons: number) => number} deps.getCompletionPercentage
   *   returns the integer completion percentage 0–100 for the given lesson count.
   * @param {number} deps.totalLessons - total number of lessons in the course.
   * @param {(checkedLayers: string[]) => {passed: boolean}} deps.evaluateGuardrailChecklist
   *   evaluates the all-five-layers guardrail rule.
   * @param {(container?: HTMLElement) => string[]} deps.readCheckedLayers
   *   reads the currently checked guardrail layers from the DOM.
   */
  constructor(wrapper, deps = {}) {
    this.wrapper = wrapper;
    this.getCompletionPercentage = deps.getCompletionPercentage;
    this.totalLessons = deps.totalLessons;
    this.evaluateGuardrailChecklist = deps.evaluateGuardrailChecklist;
    this.readCheckedLayers = deps.readCheckedLayers;
  }

  /**
   * Pure mapping from completion state to a SCORM `cmi.core.lesson_status`.
   *
   * - `passed`     when the course is complete (pct >= 100) AND the guardrail
   *                self-assessment passed (Req 4.4).
   * - `completed`  when the course is complete (pct >= 100) but the guardrail
   *                did not pass (Req 4.1).
   * - `incomplete` for any percentage below 100 (Req 4.2).
   *
   * @param {number} pct - completion percentage in [0, 100].
   * @param {boolean} guardrailPassed - whether the guardrail self-check passed.
   * @returns {"passed"|"completed"|"incomplete"}
   */
  computeStatus(pct, guardrailPassed) {
    if (pct >= 100) {
      return guardrailPassed ? "passed" : "completed";
    }
    return "incomplete";
  }

  /**
   * On launch: initialize the SCORM session, then restore any progress stored
   * in `cmi.suspend_data` back into localStorage before the page reads progress
   * (Req 5.2, 6.3). Safe no-op when the LMS API is unavailable.
   */
  start() {
    if (!this.wrapper || !this.wrapper.available) {
      return;
    }

    this.wrapper.initialize();

    // Restore progress from suspend_data into localStorage (Req 5.2).
    const suspendData = this.wrapper.getValue("cmi.suspend_data");
    const ids = deserializeProgress(suspendData);
    if (ids.length > 0) {
      restoreToLocalStorage(ids);
    }
  }

  /**
   * Recompute the overall status + score from current course state and push a
   * single `cmi.core.lesson_status`, `cmi.core.score.raw` (integer 0–100), and
   * `cmi.suspend_data` to the LMS, then commit (Req 4.*, 5.1). Safe no-op when
   * the LMS API is unavailable.
   */
  sync() {
    if (!this.wrapper || !this.wrapper.available) {
      return;
    }

    const pct = this._completionPercentage();
    const guardrailPassed = this._guardrailPassed();
    const status = this.computeStatus(pct, guardrailPassed);

    // Single overall status and score for the whole course (Req 4.5).
    this.wrapper.setValue("cmi.core.lesson_status", status);
    this.wrapper.setValue("cmi.core.score.raw", String(pct));

    // Mirror localStorage progress into suspend_data (Req 5.1).
    this.wrapper.setValue(
      "cmi.suspend_data",
      serializeProgress(readCompletedIds())
    );

    this.wrapper.commit();
  }

  /**
   * On unload: mark the session as suspended, commit the current data model
   * values, then terminate the session (Req 5.3). Safe no-op when the LMS API
   * is unavailable.
   */
  end() {
    if (!this.wrapper || !this.wrapper.available) {
      return;
    }

    this.wrapper.setValue("cmi.core.exit", "suspend");
    this.wrapper.commit();
    this.wrapper.terminate();
  }

  /**
   * Current completion percentage as a clamped integer in [0, 100].
   * @returns {number}
   * @private
   */
  _completionPercentage() {
    let pct = 0;
    if (typeof this.getCompletionPercentage === "function") {
      pct = this.getCompletionPercentage(this.totalLessons);
    }
    pct = Math.round(Number(pct) || 0);
    if (pct < 0) {
      return 0;
    }
    if (pct > 100) {
      return 100;
    }
    return pct;
  }

  /**
   * Whether the guardrail self-assessment currently passes. Reads the checked
   * layers from the DOM and evaluates the all-five-layers rule. Degrades to
   * `false` when the dependencies are not wired.
   * @returns {boolean}
   * @private
   */
  _guardrailPassed() {
    if (
      typeof this.evaluateGuardrailChecklist !== "function" ||
      typeof this.readCheckedLayers !== "function"
    ) {
      return false;
    }
    const checkedLayers = this.readCheckedLayers();
    const result = this.evaluateGuardrailChecklist(checkedLayers);
    return Boolean(result && result.passed);
  }
}
