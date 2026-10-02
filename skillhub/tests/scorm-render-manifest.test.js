/**
 * Unit tests for renderManifest (scripts/build-scorm.mjs).
 *
 * Verifies that:
 *   - With no meta (or skillhub meta), the manifest reproduces the original
 *     skillhub identifiers and titles exactly — guarding byte-for-byte
 *     backward compatibility of the shipped scorm/skillhub_scorm artifact.
 *   - With a derived lab meta, the four identifiers and both <title> tags
 *     reflect the lab while the SCO contract and schema block are unchanged.
 */

import { describe, it, expect } from 'vitest';
import { renderManifest, deriveLabMetadata } from '../../scripts/build-scorm.mjs';

const SAMPLE_FILES = ['js/main.js', 'en/index.html', 'fr/index.html'];

describe('renderManifest', () => {
  it('defaults to the exact skillhub identifiers and titles when meta omitted', () => {
    const xml = renderManifest({ files: SAMPLE_FILES });
    expect(xml).toContain('identifier="SKILLHUB_SCORM12"');
    expect(xml).toContain('default="ORG-SKILLHUB"');
    expect(xml).toContain('<organization identifier="ORG-SKILLHUB">');
    expect(xml).toContain('identifier="ITEM-SKILLHUB" identifierref="RES-SKILLHUB"');
    expect(xml).toContain('identifier="RES-SKILLHUB"');
    expect(xml).toContain('<title>Agentic AI OPCP Labs - SkillHub</title>');
  });

  it('explicit skillhub meta matches the no-meta default', () => {
    const withMeta = renderManifest({ files: SAMPLE_FILES, meta: deriveLabMetadata('skillhub') });
    const defaulted = renderManifest({ files: SAMPLE_FILES });
    expect(withMeta).toBe(defaulted);
  });

  it('preserves the SCO contract and schema version', () => {
    const xml = renderManifest({ files: SAMPLE_FILES });
    expect(xml).toContain('<schemaversion>1.2</schemaversion>');
    expect(xml).toContain('<adlcp:masteryscore>100</adlcp:masteryscore>');
    expect(xml).toMatch(/adlcp:scormtype="sco"\s+href="index\.html"/);
    expect(xml).toContain('<file href="index.html"/>');
  });

  it('enumerates every supplied dependency file', () => {
    const xml = renderManifest({ files: SAMPLE_FILES });
    for (const f of SAMPLE_FILES) {
      expect(xml).toContain(`<file href="${f}"/>`);
    }
  });

  it('renders derived identifiers and title for a non-skillhub lab', () => {
    const meta = deriveLabMetadata('trace-reading');
    const xml = renderManifest({ files: SAMPLE_FILES, meta });
    expect(xml).toContain('identifier="TRACE_READING_SCORM12"');
    expect(xml).toContain('default="ORG-TRACE-READING"');
    expect(xml).toContain('<organization identifier="ORG-TRACE-READING">');
    expect(xml).toContain('identifier="ITEM-TRACE-READING" identifierref="RES-TRACE-READING"');
    expect(xml).toContain('identifier="RES-TRACE-READING"');
    expect(xml).toContain('<title>Trace Reading</title>');
    // skillhub identifiers must not leak into a lab manifest.
    expect(xml).not.toContain('SKILLHUB');
    // SCO contract remains intact.
    expect(xml).toMatch(/adlcp:scormtype="sco"\s+href="index\.html"/);
  });
});
