/**
 * ProgressBridge - Translates between the course's localStorage progress keys
 * and the single SCORM `cmi.suspend_data` string.
 *
 * This is the non-invasive seam between the course and the LMS: it only ever
 * reads/writes the `skillhub_lesson_complete_*` keys the Progress_Tracker
 * already owns, so the existing progress module is never modified. Every
 * storage access is guarded so the bridge degrades gracefully when
 * localStorage is unavailable.
 *
 * Validates: Requirements 5.1, 5.2, 5.4, 7.2
 */

/**
 * The exact localStorage key prefix used by the Progress_Tracker (progress.js).
 * Preserved verbatim when mirroring progress so restored keys match the course
 * format (Req 5.4).
 * @type {string}
 */
const STORAGE_PREFIX = "skillhub_lesson_complete_";

/**
 * Collect completed lesson ids straight from localStorage (prefix-scoped).
 * Returns a sorted, deduped list of ids with the prefix stripped. Returns an
 * empty array when localStorage is unavailable or any access throws (Req 7.2).
 * @returns {string[]} sorted, deduped completed lesson ids ([] on failure)
 */
export function readCompletedIds() {
  try {
    const seen = new Set();
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(STORAGE_PREFIX)) {
        if (localStorage.getItem(key) === "true") {
          seen.add(key.slice(STORAGE_PREFIX.length));
        }
      }
    }
    return Array.from(seen).sort();
  } catch {
    return [];
  }
}

/**
 * Encode completed ids into a compact `cmi.suspend_data` envelope.
 * The ids are sorted and deduped so the output is stable regardless of input
 * ordering. The envelope carries a schema version to allow future evolution.
 * @param {string[]} ids - completed lesson ids
 * @returns {string} e.g. '{"v":1,"done":["adding-applications",...]}'
 */
export function serializeProgress(ids) {
  const list = Array.isArray(ids) ? ids : [];
  const done = Array.from(new Set(list.filter((id) => typeof id === "string"))).sort();
  return JSON.stringify({ v: 1, done });
}

/**
 * Decode `cmi.suspend_data` back into completed lesson ids. Tolerates empty,
 * malformed, or garbage input by returning an empty array (Req 5.2).
 * @param {string} suspendData - the raw suspend_data string from the LMS
 * @returns {string[]} completed lesson ids ([] on empty/invalid input)
 */
export function deserializeProgress(suspendData) {
  if (typeof suspendData !== "string" || suspendData.length === 0) {
    return [];
  }
  try {
    const parsed = JSON.parse(suspendData);
    if (!parsed || !Array.isArray(parsed.done)) {
      return [];
    }
    return parsed.done.filter((id) => typeof id === "string");
  } catch {
    return [];
  }
}

/**
 * Write completed ids back into localStorage using the exact course prefix,
 * reproducing the `skillhub_lesson_complete_*` keys the Progress_Tracker owns
 * (Req 5.2, 5.4). Guarded against storage errors so a restore never throws
 * (Req 7.2).
 * @param {string[]} ids - completed lesson ids to restore
 */
export function restoreToLocalStorage(ids) {
  const list = Array.isArray(ids) ? ids : [];
  for (const id of list) {
    if (typeof id !== "string") {
      continue;
    }
    try {
      localStorage.setItem(STORAGE_PREFIX + id, "true");
    } catch {
      // Graceful degradation: storage unavailable or quota exceeded (Req 7.2)
    }
  }
}
