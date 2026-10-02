/**
 * Integration tests for the generalized multi-lab SCORM build
 * (scripts/build-scorm.mjs): discoverLabSites, per-lab buildScormPackage with
 * derived metadata, and the buildAllScormPackages driver.
 *
 * Each test builds synthetic lab sites in a unique temp directory, so the real
 * skillhub source and scorm/skillhub_scorm artifact are never touched.
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { mkdtemp, rm, mkdir, writeFile, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import {
  discoverLabSites,
  buildScormPackage,
  buildAllScormPackages,
} from '../../scripts/build-scorm.mjs';

/**
 * Create a minimal skillhub-shaped lab site under <root>/<name>.
 * Includes index.html, en/index.html, fr/index.html, js/scorm/scorm-bootstrap.js,
 * and an assets/ file so the structure matches a real site.
 * @param {string} root
 * @param {string} name
 */
async function makeSyntheticSite(root, name) {
  const site = path.join(root, name);
  await mkdir(path.join(site, 'en'), { recursive: true });
  await mkdir(path.join(site, 'fr'), { recursive: true });
  await mkdir(path.join(site, 'js', 'scorm'), { recursive: true });
  await mkdir(path.join(site, 'assets', 'css'), { recursive: true });

  await writeFile(
    path.join(site, 'index.html'),
    '<!DOCTYPE html><html><head><title>t</title></head><body></body></html>',
    'utf8',
  );
  await writeFile(path.join(site, 'en', 'index.html'), '<!DOCTYPE html><html><body>en</body></html>', 'utf8');
  await writeFile(path.join(site, 'fr', 'index.html'), '<!DOCTYPE html><html><body>fr</body></html>', 'utf8');
  await writeFile(path.join(site, 'js', 'main.js'), '// main', 'utf8');
  await writeFile(path.join(site, 'js', 'scorm', 'scorm-bootstrap.js'), '// bootstrap', 'utf8');
  await writeFile(path.join(site, 'assets', 'css', 'style.css'), 'body{}', 'utf8');
  return site;
}

describe('discoverLabSites', () => {
  let root;

  beforeAll(async () => {
    root = await mkdtemp(path.join(tmpdir(), 'scorm-discover-'));
    // valid site
    await makeSyntheticSite(root, 'trace-reading');
    // near-miss: missing fr/
    const nearMiss = path.join(root, 'broken-site');
    await mkdir(path.join(nearMiss, 'en'), { recursive: true });
    await mkdir(path.join(nearMiss, 'js'), { recursive: true });
    await mkdir(path.join(nearMiss, 'assets'), { recursive: true });
    await writeFile(path.join(nearMiss, 'index.html'), '<html></html>', 'utf8');
    // excluded by name even though well-shaped
    await makeSyntheticSite(root, 'scorm');
    // a dotfolder is ignored
    await makeSyntheticSite(root, '.hidden');
  });

  afterAll(async () => {
    if (root) await rm(root, { recursive: true, force: true });
  });

  it('returns only structurally valid, non-excluded, non-dot sites', async () => {
    const sites = await discoverLabSites(root);
    expect(sites).toEqual(['trace-reading']);
  });
});

describe('buildScormPackage with a synthetic lab (derived metadata)', () => {
  let root;
  let manifestXml;

  beforeAll(async () => {
    root = await mkdtemp(path.join(tmpdir(), 'scorm-lab-build-'));
    await makeSyntheticSite(root, 'trace-reading');
    const outDir = path.join(root, 'out', 'trace-reading_scorm');
    const result = await buildScormPackage({
      srcDir: path.join(root, 'trace-reading'),
      outDir,
      labName: 'trace-reading',
    });
    expect(result.outDir).toBe(outDir);
    manifestXml = await readFile(path.join(outDir, 'imsmanifest.xml'), 'utf8');
  });

  afterAll(async () => {
    if (root) await rm(root, { recursive: true, force: true });
  });

  it('writes a manifest with the derived identifiers and title', () => {
    expect(manifestXml).toContain('identifier="TRACE_READING_SCORM12"');
    expect(manifestXml).toContain('<organization identifier="ORG-TRACE-READING">');
    expect(manifestXml).toContain('<title>Trace Reading</title>');
  });

  it('preserves the SCO contract', () => {
    expect(manifestXml).toMatch(/adlcp:scormtype="sco"\s+href="index\.html"/);
  });

  it('derives labName from srcDir basename when not passed explicitly', async () => {
    const outDir = path.join(root, 'out2', 'trace-reading_scorm');
    const { meta, labName } = await buildScormPackage({
      srcDir: path.join(root, 'trace-reading'),
      outDir,
    });
    expect(labName).toBe('trace-reading');
    expect(meta.identifier).toBe('TRACE_READING_SCORM12');
  });
});

describe('buildAllScormPackages driver', () => {
  let root;
  let results;

  beforeAll(async () => {
    root = await mkdtemp(path.join(tmpdir(), 'scorm-all-'));
    await makeSyntheticSite(root, 'trace-reading');
    await makeSyntheticSite(root, 'making-backups');
    results = await buildAllScormPackages({ repoRoot: root });
  });

  afterAll(async () => {
    if (root) await rm(root, { recursive: true, force: true });
  });

  it('builds one package per discovered lab into scorm/<lab>_scorm/', async () => {
    expect(results).toHaveLength(2);
    const byLab = Object.fromEntries(results.map((r) => [r.lab, r]));
    expect(byLab['making-backups']).toBeDefined();
    expect(byLab['trace-reading']).toBeDefined();

    for (const lab of ['trace-reading', 'making-backups']) {
      const r = byLab[lab];
      expect(r.error).toBeUndefined();
      expect(r.outDir).toBe(path.join(root, 'scorm', `${lab}_scorm`));
      expect(r.fileCount).toBeGreaterThan(0);
      const xml = await readFile(path.join(r.outDir, 'imsmanifest.xml'), 'utf8');
      expect(xml).toContain('adlcp:scormtype="sco"');
    }
  });

  it('produces lab-specific manifests (no cross-contamination)', async () => {
    const traceXml = await readFile(
      path.join(root, 'scorm', 'trace-reading_scorm', 'imsmanifest.xml'),
      'utf8',
    );
    const backupsXml = await readFile(
      path.join(root, 'scorm', 'making-backups_scorm', 'imsmanifest.xml'),
      'utf8',
    );
    expect(traceXml).toContain('TRACE_READING_SCORM12');
    expect(traceXml).not.toContain('MAKING_BACKUPS_SCORM12');
    expect(backupsXml).toContain('MAKING_BACKUPS_SCORM12');
    expect(backupsXml).not.toContain('TRACE_READING_SCORM12');
  });
});
