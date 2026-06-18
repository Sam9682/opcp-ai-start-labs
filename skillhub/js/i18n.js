/**
 * I18n Module - Locale detection, switching, and URL routing
 *
 * Supported locales: "en", "fr"
 * Priority: stored preference > browser language > default ("en")
 *
 * @module i18n
 */

const STORAGE_KEY = 'skillhub-locale';
const SUPPORTED_LOCALES = ['en', 'fr'];
const DEFAULT_LOCALE = 'en';

/**
 * Retrieve the stored locale preference from localStorage.
 * @returns {string|null} The stored locale ("en" or "fr"), or null if none is stored.
 */
export function getStoredLocalePreference() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'en' || stored === 'fr') {
      return stored;
    }
    return null;
  } catch (e) {
    // localStorage unavailable (e.g. private browsing, disabled)
    return null;
  }
}

/**
 * Persist the locale preference in localStorage.
 * @param {string} locale - The locale to store ("en" or "fr").
 */
export function setLocalePreference(locale) {
  const normalized = normalizeLocale(locale);
  try {
    localStorage.setItem(STORAGE_KEY, normalized);
  } catch (e) {
    // localStorage unavailable; preference will not persist
  }
}

/**
 * Detect the active locale.
 *
 * Resolution order:
 * 1. Stored preference in localStorage
 * 2. Browser language (navigator.language / navigator.languages)
 * 3. Default to "en"
 *
 * @returns {string} The resolved locale — always "en" or "fr".
 */
export function detectLocale() {
  // 1. Check stored preference
  const stored = getStoredLocalePreference();
  if (stored !== null) {
    return stored;
  }

  // 2. Detect from browser language
  const languages = getBrowserLanguages();
  for (const lang of languages) {
    if (lang.toLowerCase().startsWith('fr')) {
      return 'fr';
    }
  }

  // 3. Default
  return DEFAULT_LOCALE;
}

/**
 * Switch the active locale. Persists the choice in localStorage and
 * triggers navigation to the new locale folder.
 * @param {string} locale - The target locale ("en" or "fr").
 */
export function switchLocale(locale) {
  const normalized = normalizeLocale(locale);
  setLocalePreference(normalized);

  // Navigate to the new locale folder
  const currentPath = window.location.pathname;
  const newPath = replaceLocaleInPath(currentPath, normalized);
  window.location.href = newPath;
}

/**
 * Normalize a locale string to one of the supported values.
 * @param {string} locale - The input locale.
 * @returns {string} "fr" if the input starts with "fr", otherwise "en".
 */
function normalizeLocale(locale) {
  if (typeof locale === 'string' && locale.toLowerCase().startsWith('fr')) {
    return 'fr';
  }
  return DEFAULT_LOCALE;
}

/**
 * Get the list of browser languages.
 * @returns {string[]} Array of language tags from the browser.
 */
function getBrowserLanguages() {
  if (typeof navigator === 'undefined') {
    return [];
  }
  if (navigator.languages && navigator.languages.length > 0) {
    return Array.from(navigator.languages);
  }
  if (navigator.language) {
    return [navigator.language];
  }
  return [];
}

/**
 * Replace the locale segment in a URL path.
 * Handles paths like /en/lesson.html or /fr/lesson.html.
 * If no locale segment is found, prepends the locale folder.
 * @param {string} path - The current URL path.
 * @param {string} locale - The target locale.
 * @returns {string} The updated path with the new locale.
 */
function replaceLocaleInPath(path, locale) {
  // Match locale segment at the beginning of the path: /en/... or /fr/...
  const localePattern = /^\/(en|fr)(\/|$)/;
  if (localePattern.test(path)) {
    return path.replace(localePattern, '/' + locale + '$2');
  }
  // No locale segment found — redirect to locale root
  return '/' + locale + '/';
}
