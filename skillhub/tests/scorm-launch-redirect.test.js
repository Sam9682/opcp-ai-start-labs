/**
 * Bug condition exploration test for the SCORM locale redirect 404 bug.
 *
 * The package-root SCORM launch page (`skillhub/index.html`) is a client-side
 * locale redirect. On the unfixed code it navigates to a BARE DIRECTORY
 * (`locale + '/'`, and the `<noscript>` links `en/` / `fr/`). Hosts that do not
 * auto-index a directory (SCORM Cloud) return 404 for a bare-directory request,
 * so the learner lands on "Page not found" instead of the locale landing page.
 *
 * This test reads the launch page SOURCE from disk (it does NOT import/execute
 * the page) and asserts the redirect targets are EXPLICIT files
 * (`locale + '/index.html'`, `href="en/index.html"`, `href="fr/index.html"`).
 *
 * Property 1 (Bug Condition / Expected Behavior): Explicit-File Redirect Loads
 * the Locale Landing Page.
 *
 * On UNFIXED code these assertions are EXPECTED TO FAIL — the failure surfaces
 * the bare-directory counterexample and confirms the bug exists. After the fix
 * (task 3.1) the same assertions pass and guard against regression.
 *
 * Validates: Requirements 1.1, 1.3, 2.1, 2.3, 2.4
 */

import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const LAUNCH_PAGE = resolve(__dirname, '..', 'index.html');

/** Read the launch page source text (assert on source, do not execute). */
function readLaunchPage() {
  return readFileSync(LAUNCH_PAGE, 'utf-8');
}

describe('SCORM launch page locale redirect (bug condition exploration)', () => {
  describe('JavaScript redirect target (Req 1.1, 2.1)', () => {
    it('redirects to an explicit file `locale + \'/index.html\'`', () => {
      const src = readLaunchPage();
      expect(src).toContain("locale + '/index.html'");
    });

    it('does NOT emit the bare-directory redirect `locale + \'/\'`', () => {
      const src = readLaunchPage();
      // Bare-directory form: `locale + '/'` with no trailing filename.
      // (Matches the string literal exactly, not the explicit-file form.)
      expect(src).not.toContain("locale + '/'");
    });
  });

  describe('<noscript> fallback links (Req 1.3, 2.3)', () => {
    it('English link points to the explicit file `en/index.html`', () => {
      const src = readLaunchPage();
      expect(src).toContain('href="en/index.html"');
    });

    it('French link points to the explicit file `fr/index.html`', () => {
      const src = readLaunchPage();
      expect(src).toContain('href="fr/index.html"');
    });

    it('no bare `href="en/"` directory link remains', () => {
      const src = readLaunchPage();
      expect(src).not.toContain('href="en/"');
    });

    it('no bare `href="fr/"` directory link remains', () => {
      const src = readLaunchPage();
      expect(src).not.toContain('href="fr/"');
    });
  });
});
