/**
 * Preservation property tests for the SCORM launch page.
 *
 * Spec: scorm-locale-redirect-404-fix (bugfix)
 * Property 2: Preservation - Locale Detection and Build Contract Unchanged
 *
 * These tests are written BEFORE the fix and MUST PASS on the UNFIXED code.
 * They encode the baseline behavior that the redirect-target fix must preserve:
 *
 *  - Locale selection honors a stored `skillhub-locale` preference over browser
 *    detection (Req 3.1).
 *  - With no stored preference and a browser language starting with `fr`, the
 *    `fr` locale is selected (Req 3.2).
 *  - With no stored preference and any non-French browser language, or when
 *    localStorage is unavailable, the `en` locale is the default (Req 3.3).
 *  - On auto-indexing hosts the correct locale landing page still loads (Req 3.4);
 *    locale selection is upstream of the redirect target, so the selected locale
 *    is identical regardless of host.
 *  - The build script copies the root `index.html` verbatim as the single SCO
 *    launch file and declares it as `href="index.html"` in the manifest (Req 3.5).
 *
 * The locale-detection logic is exercised directly against the live
 * `skillhub/index.html` source: the inline IIFE is extracted and executed in a
 * sandbox so the test is coupled to the shipped launch page rather than to a
 * re-implementation. The redirect target captured by the sandbox is only read for
 * its selected *locale* (the leading `en`/`fr` segment), which is what must be
 * preserved — the trailing path (`'/'` vs `'/index.html'`) is intentionally
 * ignored here and is covered by the bug-condition test.
 *
 * Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
 */

import { describe, it, expect, beforeEach } from 'vitest';
import fc from 'fast-check';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { disableLocalStorage } from './setup.js';
import { renderManifest } from '../../scripts/build-scorm.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const LAUNCH_PAGE = path.resolve(__dirname, '../index.html');

/**
 * Extract the body of the inline <script> IIFE from the launch page source.
 * @param {string} html - The full index.html source.
 * @returns {string} The JavaScript source inside the <script> element.
 */
function extractLaunchScript(html) {
  const match = html.match(/<script>([\s\S]*?)<\/script>/i);
  if (!match) {
    throw new Error('Could not find inline <script> in launch page');
  }
  return match[1];
}

/**
 * Run the live launch-page redirect logic in a sandbox and return the selected
 * locale (the `en`/`fr` segment of the redirect target).
 *
 * The real `index.html` script references `localStorage`, `navigator`, and
 * `window.location.replace`. We provide a `window` whose `location.replace`
 * captures the target string, delegate `localStorage` to the global mock (so
 * `disableLocalStorage()` continues to apply), and delegate `navigator` to the
 * global navigator configured per test.
 *
 * @returns {"en"|"fr"} The locale selected by the live launch-page logic.
 */
function runLaunchRedirect() {
  const scriptBody = extractLaunchScript(fs.readFileSync(LAUNCH_PAGE, 'utf8'));

  let captured = null;
  const windowSandbox = {
    location: {
      // Realistic SCO-root launch pathname so the live resolveLocaleTarget
      // (which reads window.location.pathname) resolves correctly. The test
      // asserts only the SELECTED LOCALE, not the full path.
      pathname: '/skillhub_scorm/index.html',
      replace(target) {
        captured = target;
      },
    },
  };

  // Execute the extracted IIFE with sandboxed window/localStorage/navigator.
  // localStorage and navigator are passed through to the live globals so the
  // mock + disableLocalStorage() and per-test navigator.language apply.
  // eslint-disable-next-line no-new-func
  const runner = new Function(
    'window',
    'localStorage',
    'navigator',
    `${scriptBody}`,
  );
  runner(windowSandbox, globalThis.localStorage, globalThis.navigator);

  if (captured === null) {
    throw new Error('Launch page did not call window.location.replace');
  }

  // The redirect target is now an absolute, SCO-root-anchored path such as
  // "/skillhub_scorm/en/index.html". The selected locale is the path segment
  // immediately before the trailing "index.html". This deliberately ignores the
  // anchoring details so the test stays insensitive to the redirect-target fix
  // and only asserts locale selection.
  const segs = captured.split('/').filter(Boolean);
  const locale = segs[segs.length - 2];
  return locale;
}

/**
 * Set navigator.language / navigator.languages for a test run.
 * @param {string} language - The browser language tag.
 */
function setBrowserLanguage(language) {
  Object.defineProperty(navigator, 'language', {
    value: language ?? '',
    configurable: true,
    writable: true,
  });
  Object.defineProperty(navigator, 'languages', {
    value: language ? [language] : [],
    configurable: true,
    writable: true,
  });
}

/**
 * Reference oracle for the documented locale-selection precedence:
 * stored preference ("en"/"fr") > browser language starting with "fr" > "en".
 * @param {null|"en"|"fr"} stored
 * @param {string} browserLang
 * @param {boolean} storageAvailable
 * @returns {"en"|"fr"}
 */
function expectedLocale(stored, browserLang, storageAvailable) {
  if (storageAvailable && (stored === 'en' || stored === 'fr')) {
    return stored;
  }
  if (
    typeof browserLang === 'string' &&
    browserLang.toLowerCase().startsWith('fr')
  ) {
    return 'fr';
  }
  return 'en';
}

describe('SCORM launch page - Property 2: Preservation (locale detection)', () => {
  beforeEach(() => {
    localStorage.clear();
    setBrowserLanguage('en-US');
  });

  it('selects the locale per stored-preference > browser-fr > en-default across generated inputs (Req 3.1, 3.2, 3.3)', () => {
    const storedArb = fc.constantFrom(null, 'en', 'fr');
    const browserLangArb = fc.constantFrom(
      'fr',
      'fr-FR',
      'fr-CA',
      'FR-ca',
      'FR-FR',
      'en',
      'en-US',
      'en-GB',
      'de',
      'de-DE',
      'es-ES',
      'ja-JP',
      '',
    );
    const storageAvailableArb = fc.boolean();

    fc.assert(
      fc.property(
        storedArb,
        browserLangArb,
        storageAvailableArb,
        (stored, browserLang, storageAvailable) => {
          localStorage.clear();
          if (stored !== null) {
            localStorage.setItem('skillhub-locale', stored);
          }
          setBrowserLanguage(browserLang);

          let restore = null;
          if (!storageAvailable) {
            restore = disableLocalStorage();
          }
          try {
            const selected = runLaunchRedirect();

            // Output is always exactly "en" or "fr".
            expect(selected === 'en' || selected === 'fr').toBe(true);

            // Output matches the documented precedence (preservation oracle).
            expect(selected).toBe(
              expectedLocale(stored, browserLang, storageAvailable),
            );
          } finally {
            if (restore) {
              restore();
            }
          }
        },
      ),
      { numRuns: 300 },
    );
  });
});

describe('SCORM launch page - Property 2: Preservation (locale detection, explicit cases)', () => {
  beforeEach(() => {
    localStorage.clear();
    setBrowserLanguage('en-US');
  });

  it('stored preference "fr" overrides a non-French browser language (Req 3.1)', () => {
    localStorage.setItem('skillhub-locale', 'fr');
    setBrowserLanguage('en-US');
    expect(runLaunchRedirect()).toBe('fr');
  });

  it('stored preference "en" overrides a French browser language (Req 3.1)', () => {
    localStorage.setItem('skillhub-locale', 'en');
    setBrowserLanguage('fr-FR');
    expect(runLaunchRedirect()).toBe('en');
  });

  it('no stored preference + browser language starting with "fr" selects fr (Req 3.2)', () => {
    setBrowserLanguage('fr-CA');
    expect(runLaunchRedirect()).toBe('fr');
  });

  it('no stored preference + mixed-case "FR-ca" browser language selects fr (Req 3.2)', () => {
    setBrowserLanguage('FR-ca');
    expect(runLaunchRedirect()).toBe('fr');
  });

  it('no stored preference + non-French browser language defaults to en (Req 3.3)', () => {
    setBrowserLanguage('de-DE');
    expect(runLaunchRedirect()).toBe('en');
  });

  it('no stored preference + empty browser language defaults to en (Req 3.3)', () => {
    setBrowserLanguage('');
    expect(runLaunchRedirect()).toBe('en');
  });

  it('localStorage unavailable falls back to browser detection / en default (Req 3.3)', () => {
    setBrowserLanguage('en-US');
    const restore = disableLocalStorage();
    try {
      expect(runLaunchRedirect()).toBe('en');
    } finally {
      restore();
    }
  });

  it('localStorage unavailable + French browser language still selects fr (Req 3.2, 3.3)', () => {
    setBrowserLanguage('fr-FR');
    const restore = disableLocalStorage();
    try {
      expect(runLaunchRedirect()).toBe('fr');
    } finally {
      restore();
    }
  });
});

describe('SCORM launch page - Property 2: Preservation (host behavior)', () => {
  beforeEach(() => {
    localStorage.clear();
    setBrowserLanguage('en-US');
  });

  it('selected locale is independent of host auto-indexing behavior (Req 3.4)', () => {
    // Locale detection is upstream of the redirect target, so the selected
    // locale does not depend on the serving host. We assert the selection is
    // stable across repeated runs (host behavior affects only resolution of the
    // target path, which is covered by the bug-condition test).
    setBrowserLanguage('fr-FR');
    expect(runLaunchRedirect()).toBe('fr');
    setBrowserLanguage('en-US');
    expect(runLaunchRedirect()).toBe('en');
  });
});

describe('SCORM launch page - Property 2: Preservation (build contract)', () => {
  it('build manifest declares the SCO launch file as href="index.html" (Req 3.5)', () => {
    const xml = renderManifest({ files: ['en/index.html', 'fr/index.html'] });

    // The SCO resource references index.html as the single launch file.
    expect(xml).toContain('adlcp:scormtype="sco" href="index.html"');
    expect(xml).toContain('<file href="index.html"/>');

    // The manifest declares SCORM 1.2.
    expect(xml).toContain('<schemaversion>1.2</schemaversion>');
  });

  it('launch page is a self-contained redirect copied verbatim by the build (Req 3.5)', () => {
    // The build (scripts/build-scorm.mjs) copies skillhub/index.html verbatim.
    // Guard that the source launch page remains the inline-script redirect the
    // build ships unchanged, so the manifest href="index.html" keeps pointing at
    // a valid SCO launch file.
    const html = fs.readFileSync(LAUNCH_PAGE, 'utf8');
    expect(html).toMatch(/<script>[\s\S]*detectLocaleAndRedirect\(\)[\s\S]*<\/script>/);
    expect(html).toContain('window.location.replace');
  });
});
