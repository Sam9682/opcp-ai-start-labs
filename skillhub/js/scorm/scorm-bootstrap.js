/**
 * SCORM bootstrap - the single side-effecting entry point loaded by each lesson
 * page. It is the only SCORM file the course templates reference.
 *
 * On import it:
 *   1. Discovers the LMS `API` object across the parent/opener frame chains.
 *   2. Builds a defensive `ScormApiWrapper` around it (inert when no API found).
 *   3. Wires a `ScormAdapter` with the course's existing (unchanged) progress
 *      and guardrail self-assessment functions injected as dependencies.
 *   4. Attaches lifecycle listeners that drive the adapter:
 *        - DOMContentLoaded → start() (initialize + restore from suspend_data)
 *        - storage          → sync()  (progress changed → push status/score)
 *        - pagehide         → end()   (suspend, commit, terminate)
 *
 * Non-invasive by design: it only reads from the public functions the existing
 * modules already export and never mutates their source. Every path degrades to
 * the course's standalone behavior when the LMS API or `localStorage` is absent,
 * and simply importing this module in a non-DOM/standalone context must never
 * throw.
 *
 * Validates: Requirements 5.3, 6.1, 6.2, 6.3, 7.1, 7.3
 */

import { discoverApi } from "./api-discovery.js";
import { ScormApiWrapper } from "./scorm-api.js";
import { ScormAdapter } from "./scorm-adapter.js";
import { getCompletionPercentage, getCompletedLessons } from "../progress.js";
import {
  evaluateGuardrailChecklist,
  readCheckedLayers,
} from "../self-assessment.js";

/**
 * Total number of lessons in the SkillHub course. Used to turn the completion
 * count into an overall percentage/score. (design.md: 19 lessons)
 */
const TOTAL_LESSONS = 19;

// Resolve the host window defensively: importing in a non-browser/standalone
// context (e.g. a plain module runner) must never throw. We pass `null` (not
// `undefined`) downstream so `discoverApi`'s `win = window` default parameter is
// never triggered when there is no global `window`.
const hostWindow = typeof window !== "undefined" ? window : null;

const adapter = new ScormAdapter(
  new ScormApiWrapper(discoverApi(hostWindow)),
  {
    getCompletionPercentage,
    totalLessons: TOTAL_LESSONS,
    evaluateGuardrailChecklist,
    readCheckedLayers,
  }
);

// Wire lifecycle listeners only when a DOM/window with addEventListener exists.
// Each handler is itself a no-op when the LMS API is unavailable, so standalone
// operation is preserved end to end (Req 7.1, 7.3).
if (hostWindow && typeof hostWindow.addEventListener === "function") {
  hostWindow.addEventListener("DOMContentLoaded", () => adapter.start());
  hostWindow.addEventListener("storage", () => adapter.sync());
  hostWindow.addEventListener("pagehide", () => adapter.end());
}

export { adapter };
