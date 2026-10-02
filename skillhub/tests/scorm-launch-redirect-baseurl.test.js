/**
 * Iteration 2 regression tests for the SCORM locale redirect 404 bug.
 *
 * Iteration 1 made the launch page redirect to the explicit file
 * `locale + '/index.html'`, but SCORM Cloud still 404s. Root cause: that target
 * is a RELATIVE URL. SCORM Cloud serves the SCO at a URL with NO trailing slash
 * (e.g. `.../courses/<id>/scorm<hash>`), so the browser resolves `en/index.html`
 * one directory ABOVE the SCO root, dropping the `scorm<hash>` segment -> 404.
 *
 * The fix anchors the redirect to the SCO root via `resolveLocaleTarget`, which
 * is extracted here from the live `skillhub/index.html` source and exercised
 * directly (so the test is coupled to the shipped launch page, not a copy).
 *
 * Property 3 (Bug Condition): location-anchored redirect resolves INSIDE the SCO root.
 * Property 4 (Preservation): trailing-slash / explicit-file launches unchanged.
 *
 * On Iteration 1 code these assertions FAIL (no resolveLocaleTarget, bare
 * relative target drops the SCO root). After the fix they PASS.
 *
 * Validates: Requirements 4.1, 4.2, 5.1, 5.2, 5.3
 */

import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const LAUNCH_PAGE = resolve(__dirname, '..', 'index.html');

function readLaunchPage() {
  return readFileSync(LAUNCH_PAGE, 'utf-8');
}

/**
 * Extract the live `resolveLocaleTarget` function from the launch page source
 * and return it as a callable. Fails loudly if the fix is absent (Iteration 1).
 */
function extractResolveLocaleTarget() {
  const src = readLaunchPage();
  const start = src.indexOf('function resolveLocaleTarget');
  if (start === -1) {
    throw new Error('resolveLocaleTarget not found in launch page source (unfixed Iteration 1 code)');
  }
  // Capture from the function keyword to the matching closing brace by brace counting.
  let i = src.indexOf('{', start);
  let depth = 0;
  let end = -1;
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') {
      depth--;
      if (depth === 0) { end = i + 1; break; }
    }
  }
  if (end === -1) throw new Error('Could not parse resolveLocaleTarget body');
  const fnSrc = src.slice(start, end);
  // eslint-disable-next-line no-new-func
  return new Function(`${fnSrc}; return resolveLocaleTarget;`)();
}

const SCORM_CLOUD_NOSLASH = '/sandbox/content/courses/34ARXMUXR9/scorm7ed41bcd-f4ce';
const SCO_ROOT_SEGMENT = 'scorm7ed41bcd-f4ce';

describe('Iteration 2: launch page defines resolveLocaleTarget (Req 5.1, 5.2)', () => {
  it('the launch page source anchors the redirect to window.location (not a bare relative string)', () => {
    const src = readLaunchPage();
    expect(src).toContain('resolveLocaleTarget');
    expect(src).toContain('window.location.pathname');
    // The old bare relative target must be gone from the redirect call.
    expect(src).not.toContain("window.location.replace(locale + '/index.html')");
  });
});

describe('Iteration 2 Property 3: Bug Condition - resolves inside the SCO root (Req 4.1, 4.2, 5.1, 5.2)', () => {
  it('no-trailing-slash SCORM Cloud launch URL PRESERVES the SCO root segment', () => {
    const resolveLocaleTarget = extractResolveLocaleTarget();
    const target = resolveLocaleTarget(SCORM_CLOUD_NOSLASH, 'en');
    expect(target).toBe(`${SCORM_CLOUD_NOSLASH}/en/index.html`);
    expect(target).toContain(`/${SCO_ROOT_SEGMENT}/en/index.html`);
  });

  it('browser URL resolver oracle: the fixed absolute target resolves inside the SCO root', () => {
    const resolveLocaleTarget = extractResolveLocaleTarget();
    const base = `https://cloud.scorm.com${SCORM_CLOUD_NOSLASH}`;
    const target = resolveLocaleTarget(SCORM_CLOUD_NOSLASH, 'fr');
    const resolved = new URL(target, base);
    expect(resolved.pathname).toBe(`${SCORM_CLOUD_NOSLASH}/fr/index.html`);
    expect(resolved.pathname).toContain(`/${SCO_ROOT_SEGMENT}/`);
  });

  it('demonstrates the Iteration 1 defect it fixes: a bare relative target drops the SCO root', () => {
    // This is the counterexample the fix eliminates (oracle on the OLD target).
    const base = `https://cloud.scorm.com${SCORM_CLOUD_NOSLASH}`;
    const oldResolved = new URL('en/index.html', base);
    expect(oldResolved.pathname).not.toContain(`/${SCO_ROOT_SEGMENT}/`);
    expect(oldResolved.pathname).toBe('/sandbox/content/courses/34ARXMUXR9/en/index.html');
  });
});

describe('Iteration 2 Property 4: Preservation - other launch forms unchanged (Req 5.3)', () => {
  it('trailing-slash launch URL resolves to the SCO-root landing page', () => {
    const resolveLocaleTarget = extractResolveLocaleTarget();
    expect(resolveLocaleTarget('/x/skillhub_scorm/', 'fr')).toBe('/x/skillhub_scorm/fr/index.html');
  });

  it('explicit index.html launch URL strips the file and resolves correctly', () => {
    const resolveLocaleTarget = extractResolveLocaleTarget();
    expect(resolveLocaleTarget('/x/skillhub_scorm/index.html', 'en')).toBe('/x/skillhub_scorm/en/index.html');
  });

  it('both locales resolve under the same SCO root for every launch form', () => {
    const resolveLocaleTarget = extractResolveLocaleTarget();
    const forms = [
      ['/a/b/scorm9', '/a/b/scorm9/'],
      ['/a/b/scorm9/', '/a/b/scorm9/'],
      ['/a/b/scorm9/index.html', '/a/b/scorm9/'],
    ];
    for (const [pathname, root] of forms) {
      expect(resolveLocaleTarget(pathname, 'en')).toBe(`${root}en/index.html`);
      expect(resolveLocaleTarget(pathname, 'fr')).toBe(`${root}fr/index.html`);
    }
  });

  it('keeps the Iteration 1 explicit-file <noscript> links (no bare directories)', () => {
    const src = readLaunchPage();
    expect(src).toContain('href="en/index.html"');
    expect(src).toContain('href="fr/index.html"');
    expect(src).not.toContain('href="en/"');
    expect(src).not.toContain('href="fr/"');
  });
});