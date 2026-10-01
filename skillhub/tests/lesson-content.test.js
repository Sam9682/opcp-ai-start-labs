import { describe, it, expect } from 'vitest';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { getLessonBySlug } from '../js/lessons.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILLHUB_ROOT = resolve(__dirname, '..');

/**
 * Slugs of the authored agentic lessons that must exist as bilingual HTML.
 * Extended as each authoring task lands:
 *   - Task 2: morning fundamentals (below)
 *   - Task 5/7/8: afternoon lessons
 */
export const AUTHORED_SLUGS = [
  // Morning — fundamentals
  'assistant-vs-agent',
  'agent-anatomy-7-components',
  'agentic-loop-and-variants',
  'stopping-criteria',
  // Afternoon — design & governance
  'multi-agent-patterns',
  'when-not-multi-agent',
  'guardrails-5-layers',
  'human-in-the-loop-ovhcloud-policy',
  'threat-modeling-workshop',
  'agent-design-capstone',
];

function lessonPath(locale, slug) {
  return resolve(SKILLHUB_ROOT, locale, `${slug}.html`);
}

function readLesson(locale, slug) {
  return readFileSync(lessonPath(locale, slug), 'utf-8');
}

/** Count heading tags (h1..h3) in an HTML string. */
function countHeadings(html) {
  const matches = html.match(/<h[1-3][\s>]/gi);
  return matches ? matches.length : 0;
}

describe('Authored lesson content (bilingual)', () => {
  it('every authored slug exists in the lesson catalog', () => {
    for (const slug of AUTHORED_SLUGS) {
      expect(getLessonBySlug(slug), `catalog entry for ${slug}`).toBeDefined();
    }
  });

  for (const slug of AUTHORED_SLUGS) {
    describe(slug, () => {
      it('has both EN and FR files', () => {
        expect(existsSync(lessonPath('en', slug)), `en/${slug}.html`).toBe(true);
        expect(existsSync(lessonPath('fr', slug)), `fr/${slug}.html`).toBe(true);
      });

      it('declares the correct lang attribute per locale', () => {
        expect(readLesson('en', slug)).toContain('<html lang="en">');
        expect(readLesson('fr', slug)).toContain('<html lang="fr">');
      });

      it('EN and FR have the same number of headings (structural parity)', () => {
        const enHeadings = countHeadings(readLesson('en', slug));
        const frHeadings = countHeadings(readLesson('fr', slug));
        expect(enHeadings).toBeGreaterThan(0);
        expect(frHeadings).toBe(enHeadings);
      });

      it('wires the Mark-as-Complete button to the lesson id', () => {
        const expected = `data-lesson-id="${slug}"`;
        expect(readLesson('en', slug)).toContain(expected);
        expect(readLesson('fr', slug)).toContain(expected);
      });

      it('references the opcp-explorer sandbox', () => {
        expect(readLesson('en', slug).toLowerCase()).toContain('opcp-explorer');
        expect(readLesson('fr', slug).toLowerCase()).toContain('opcp-explorer');
      });
    });
  }
});
