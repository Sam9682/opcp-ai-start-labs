/**
 * Property-based tests for the SkillHub I18n module.
 *
 * Feature: ai-store-labs
 * Property 1: Locale Resolution Priority
 *
 * For any combination of stored locale preference and browser language, the
 * I18n_Module returns the stored preference when one exists, otherwise returns
 * "fr" for French browser languages, and "en" for all other cases. The output
 * is always exactly "en" or "fr".
 *
 * Validates: Requirements 1.1, 1.5
 */

import { describe, it, expect, beforeEach } from 'vitest';
import fc from 'fast-check';
import { detectLocale } from '../js/i18n.js';

/**
 * Set navigator.language and navigator.languages for a test run.
 * @param {string|null} language - The primary browser language tag, or null to clear.
 */
function setBrowserLanguages(language) {
  const languages = language ? [language] : [];
  Object.defineProperty(navigator, 'language', {
    value: language ?? '',
    configurable: true,
    writable: true,
  });
  Object.defineProperty(navigator, 'languages', {
    value: languages,
    configurable: true,
    writable: true,
  });
}

/**
 * Reference implementation of the expected locale resolution logic.
 * Mirrors the specification priority: stored preference > French browser language > "en".
 * @param {string|null} stored - Stored preference ("en", "fr", or an invalid/absent value).
 * @param {string} browserLang - The browser language tag.
 * @returns {"en"|"fr"} The expected resolved locale.
 */
function expectedLocale(stored, browserLang) {
  if (stored === 'en' || stored === 'fr') {
    return stored;
  }
  if (typeof browserLang === 'string' && browserLang.toLowerCase().startsWith('fr')) {
    return 'fr';
  }
  return 'en';
}

describe('I18n Module - Property-Based Tests', () => {
  beforeEach(() => {
    localStorage.clear();
    setBrowserLanguages('en-US');
  });

  it('Feature: ai-store-labs, Property 1: Locale Resolution Priority', () => {
    // Generators spanning the full input space:
    // - stored preference: valid ("en"/"fr"), invalid, or absent (null)
    // - browser language: French variants, non-French tags, and arbitrary strings
    const storedArb = fc.oneof(
      fc.constant(null),
      fc.constantFrom('en', 'fr'),
      fc.constantFrom('de', 'es', 'EN', 'FR', '', 'fr-CA'),
      fc.string(),
    );

    const browserLangArb = fc.oneof(
      fc.constantFrom(
        'fr',
        'fr-FR',
        'fr-CA',
        'fr-BE',
        'FR-FR',
        'en',
        'en-US',
        'en-GB',
        'de-DE',
        'es-ES',
        'ja-JP',
        'frisian',
      ),
      fc.string(),
    );

    fc.assert(
      fc.property(storedArb, browserLangArb, (stored, browserLang) => {
        localStorage.clear();
        if (stored !== null) {
          localStorage.setItem('skillhub-locale', stored);
        }
        setBrowserLanguages(browserLang);

        const result = detectLocale();

        // Output is always exactly "en" or "fr".
        expect(result === 'en' || result === 'fr').toBe(true);

        // Output matches the specified resolution priority.
        expect(result).toBe(expectedLocale(stored, browserLang));
      }),
      { numRuns: 200 },
    );
  });
});
