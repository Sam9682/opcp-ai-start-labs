/**
 * Integration test for the SCORM locale redirect 404 fix (Task 3.4).
 *
 * Builds the SCORM package via `buildScormPackage` from `scripts/build-scorm.mjs`
 * into a unique temporary directory, then asserts the SHIPPED artifact carries the
 * corrected explicit-file redirect targets and preserves the build contract:
 *
 *   - The built package-root `index.html` redirects to `locale + '/index.html'`
 *     (never a bare `locale + '/'`) and the `<noscript>` links point to
 *     `en/index.html` / `fr/index.html` (never bare `href="en/"` / `href="fr/"`).
 *   - The generated `imsmanifest.xml` still declares the SCO as
 *     `adlcp:scormtype="sco"` with `href="index.html"` (build contract preserved).
 *
 * This confirms the corrected launch page ships verbatim through the build and
 * that fixing the redirect target did not disturb the manifest's SCO contract.
 *
 * Validates: Requirements 2.2, 2.4, 3.5
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { readFile, mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { buildScormPackage } from '../../scripts/build-scorm.mjs';

describe('SCORM build ships the explicit-file redirect (integration)', () => {
  /** @type {string} unique temp dir the package is built into */
  let tmpRoot;
  /** @type {string} absolute path to the built package root */
  let outDir;
  /** @type {string} built package-root index.html source */
  let builtIndexHtml;
  /** @type {string} generated imsmanifest.xml source */
  let manifestXml;

  beforeAll(async () => {
    // Build into a unique temporary directory so we never touch scorm/skillhub_scorm.
    tmpRoot = await mkdtemp(path.join(tmpdir(), 'scorm-build-it-'));
    outDir = path.join(tmpRoot, 'skillhub_scorm');

    const result = await buildScormPackage({ outDir });
    // Sanity: buildScormPackage returns the absolute outDir it wrote to.
    expect(result.outDir).toBe(outDir);

    builtIndexHtml = await readFile(path.join(outDir, 'index.html'), 'utf8');
    manifestXml = await readFile(path.join(outDir, 'imsmanifest.xml'), 'utf8');
  });

  afterAll(async () => {
    // Clean up the temporary build directory.
    if (tmpRoot) {
      await rm(tmpRoot, { recursive: true, force: true });
    }
  });

  describe('built package-root index.html (Req 2.2)', () => {
    it('redirects to the explicit file `locale + \'/index.html\'`', () => {
      expect(builtIndexHtml).toContain("locale + '/index.html'");
    });

    it('does NOT ship the bare-directory redirect `locale + \'/\'`', () => {
      expect(builtIndexHtml).not.toContain("locale + '/'");
    });

    it('ships the explicit `<noscript>` English link `en/index.html`', () => {
      expect(builtIndexHtml).toContain('href="en/index.html"');
      expect(builtIndexHtml).not.toContain('href="en/"');
    });

    it('ships the explicit `<noscript>` French link `fr/index.html`', () => {
      expect(builtIndexHtml).toContain('href="fr/index.html"');
      expect(builtIndexHtml).not.toContain('href="fr/"');
    });
  });

  describe('generated imsmanifest.xml build contract (Req 2.4, 3.5)', () => {
    it('declares the SCO as adlcp:scormtype="sco" with href="index.html"', () => {
      expect(manifestXml).toContain('adlcp:scormtype="sco"');
      expect(manifestXml).toContain('href="index.html"');
      // The SCO resource ties scormtype="sco" to href="index.html" on the resource element.
      expect(manifestXml).toMatch(
        /adlcp:scormtype="sco"\s+href="index\.html"/,
      );
    });
  });
});
