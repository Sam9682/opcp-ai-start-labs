/**
 * Main - Application bootstrap and module initialization.
 * Imports and coordinates all SkillHub modules on DOMContentLoaded.
 *
 * Validates: Requirements 1.8
 */

import { detectLocale } from './i18n.js';
import { lessons } from './lessons.js';
import { getCompletedLessons, getCompletionPercentage } from './progress.js';
import { highlightAll } from './code-highlight.js';

/**
 * Initialize the SkillHub application.
 * Sets up locale, navigation, progress display, and code highlighting.
 */
export function initApp() {
  // Detect active locale
  const locale = detectLocale();

  // Gather progress state
  const completedLessons = getCompletedLessons();
  const completionPercentage = getCompletionPercentage(lessons.length);

  // Initialize navigation if the module is available
  initNavigation(locale, completedLessons);

  // Update progress display
  updateProgressDisplay(completionPercentage);

  // Apply code highlighting to all code blocks
  highlightAll();
}

/**
 * Initialize navigation with lesson data and progress state.
 * Dynamically imports navigation module if available.
 * @param {string} locale - The active locale ("en" or "fr")
 * @param {string[]} completedLessons - Array of completed lesson ids
 */
function initNavigation(locale, completedLessons) {
  // Try to initialize navigation module if it exists in the DOM context
  try {
    import('./navigation.js').then((navModule) => {
      if (navModule && typeof navModule.initNavigation === 'function') {
        const progressData = {
          completedLessons,
          locale
        };
        navModule.initNavigation(lessons, progressData);
      }
    }).catch(() => {
      // Navigation module not available yet — graceful degradation
    });
  } catch {
    // Static import not supported or module missing — graceful degradation
  }
}

/**
 * Update the progress bar display in the header if present.
 * @param {number} percentage - Completion percentage (0-100)
 */
function updateProgressDisplay(percentage) {
  const progressBar = document.querySelector('.progress-bar');
  if (progressBar) {
    progressBar.style.width = percentage + '%';
    progressBar.setAttribute('aria-valuenow', String(percentage));
  }

  const progressText = document.querySelector('.progress-text');
  if (progressText) {
    progressText.textContent = percentage + '%';
  }
}

// Bootstrap on DOMContentLoaded
document.addEventListener('DOMContentLoaded', initApp);
