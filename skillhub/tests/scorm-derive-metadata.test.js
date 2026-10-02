/**
 * Unit tests for deriveLabMetadata (scripts/build-scorm.mjs).
 *
 * Verifies the pure folder-name → SCORM metadata derivation:
 *   - "skillhub" is a documented special case returning the original
 *     product-name identifiers/title verbatim (byte-for-byte compatibility).
 *   - Hyphenated and underscore lab names map to UPPER_SNAKE identifiers,
 *     ORG-/ITEM-/RES- dashed ids, and a Title-Cased title.
 *   - Casing is stable/idempotent regardless of input casing or separators.
 */

import { describe, it, expect } from 'vitest';
import { deriveLabMetadata } from '../../scripts/build-scorm.mjs';

describe('deriveLabMetadata', () => {
  it('returns the exact skillhub metadata (special case)', () => {
    expect(deriveLabMetadata('skillhub')).toEqual({
      identifier: 'SKILLHUB_SCORM12',
      orgId: 'ORG-SKILLHUB',
      itemId: 'ITEM-SKILLHUB',
      resId: 'RES-SKILLHUB',
      title: 'Agentic AI OPCP Labs - SkillHub',
    });
  });

  it('derives from a hyphenated lab name', () => {
    expect(deriveLabMetadata('trace-reading')).toEqual({
      identifier: 'TRACE_READING_SCORM12',
      orgId: 'ORG-TRACE-READING',
      itemId: 'ITEM-TRACE-READING',
      resId: 'RES-TRACE-READING',
      title: 'Trace Reading',
    });
  });

  it('derives from an underscore lab name', () => {
    expect(deriveLabMetadata('making_backups')).toEqual({
      identifier: 'MAKING_BACKUPS_SCORM12',
      orgId: 'ORG-MAKING-BACKUPS',
      itemId: 'ITEM-MAKING-BACKUPS',
      resId: 'RES-MAKING-BACKUPS',
      title: 'Making Backups',
    });
  });

  it('handles a single-word lab name', () => {
    expect(deriveLabMetadata('migration')).toEqual({
      identifier: 'MIGRATION_SCORM12',
      orgId: 'ORG-MIGRATION',
      itemId: 'ITEM-MIGRATION',
      resId: 'RES-MIGRATION',
      title: 'Migration',
    });
  });

  it('is stable regardless of input casing or mixed separators', () => {
    const canonical = deriveLabMetadata('trace-reading');
    expect(deriveLabMetadata('Trace-Reading')).toEqual(canonical);
    expect(deriveLabMetadata('TRACE_reading')).toEqual(canonical);
    expect(deriveLabMetadata('  trace  reading  ')).toEqual(canonical);
    // Idempotent: deriving from the derived title's slug yields the same result.
    expect(deriveLabMetadata('trace reading')).toEqual(canonical);
  });

  it('throws on an empty / separator-only name', () => {
    expect(() => deriveLabMetadata('')).toThrow();
    expect(() => deriveLabMetadata('   ')).toThrow();
    expect(() => deriveLabMetadata('-_-')).toThrow();
  });
});
