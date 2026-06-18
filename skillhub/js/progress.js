/**
 * Progress_Tracker - Persists lesson completion state in localStorage.
 * Degrades gracefully if localStorage is unavailable.
 *
 * Validates: Requirements 2.1, 2.2, 2.3, 2.4
 */

const STORAGE_PREFIX = "skillhub_lesson_complete_";

/**
 * Check if localStorage is available and functional.
 * @returns {boolean} True if localStorage can be used
 */
function isStorageAvailable() {
  try {
    const testKey = "__skillhub_storage_test__";
    localStorage.setItem(testKey, "1");
    localStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
}

/**
 * Mark a lesson as complete. Persists to localStorage if available.
 * @param {string} lessonId - The id of the lesson to mark as complete
 */
export function markLessonComplete(lessonId) {
  if (!isStorageAvailable()) {
    return;
  }
  try {
    localStorage.setItem(STORAGE_PREFIX + lessonId, "true");
  } catch {
    // Graceful degradation: quota exceeded or other write error
  }
}

/**
 * Check if a lesson has been completed.
 * @param {string} lessonId - The id of the lesson to check
 * @returns {boolean} True if the lesson is marked as complete
 */
export function isLessonComplete(lessonId) {
  if (!isStorageAvailable()) {
    return false;
  }
  try {
    return localStorage.getItem(STORAGE_PREFIX + lessonId) === "true";
  } catch {
    return false;
  }
}

/**
 * Calculate the overall completion percentage.
 * @param {number} totalLessons - The total number of lessons
 * @returns {number} Integer percentage in [0, 100]
 */
export function getCompletionPercentage(totalLessons) {
  if (!totalLessons || totalLessons <= 0) {
    return 0;
  }
  const completedCount = getCompletedLessons().length;
  return Math.round((completedCount / totalLessons) * 100);
}

/**
 * Get all completed lesson ids.
 * @returns {string[]} Array of completed lesson ids
 */
export function getCompletedLessons() {
  if (!isStorageAvailable()) {
    return [];
  }
  try {
    const completed = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(STORAGE_PREFIX)) {
        if (localStorage.getItem(key) === "true") {
          completed.push(key.slice(STORAGE_PREFIX.length));
        }
      }
    }
    return completed;
  } catch {
    return [];
  }
}

/**
 * Reset all lesson progress. Removes all progress entries from localStorage.
 */
export function resetProgress() {
  if (!isStorageAvailable()) {
    return;
  }
  try {
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(STORAGE_PREFIX)) {
        keysToRemove.push(key);
      }
    }
    for (const key of keysToRemove) {
      localStorage.removeItem(key);
    }
  } catch {
    // Graceful degradation: unable to clear storage
  }
}
