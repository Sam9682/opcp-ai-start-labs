import { describe, it, expect, beforeEach } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import {
  GUARDRAIL_LAYERS,
  evaluateGuardrailChecklist,
  readCheckedLayers,
  initGuardrailChecklist,
} from '../js/self-assessment.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILLHUB_ROOT = resolve(__dirname, '..');

describe('Self-assessment: guardrail checklist', () => {
  describe('evaluateGuardrailChecklist (all-five-layers rule)', () => {
    it('passes only when all five layers are checked', () => {
      const { passed, missing } = evaluateGuardrailChecklist(GUARDRAIL_LAYERS);
      expect(passed).toBe(true);
      expect(missing).toEqual([]);
    });

    it('fails when any layer is missing', () => {
      const { passed, missing } = evaluateGuardrailChecklist([
        'permissions',
        'operational-limits',
        'human-approval',
        'observability',
        // kill-switch missing
      ]);
      expect(passed).toBe(false);
      expect(missing).toEqual(['kill-switch']);
    });

    it('fails on an empty checklist and reports all five missing', () => {
      const { passed, missing } = evaluateGuardrailChecklist([]);
      expect(passed).toBe(false);
      expect(missing).toEqual(GUARDRAIL_LAYERS);
    });

    it('ignores unknown layers and is case-insensitive', () => {
      const { passed, covered } = evaluateGuardrailChecklist([
        'Permissions', 'OPERATIONAL-LIMITS', 'human-approval',
        'observability', 'kill-switch', 'not-a-layer',
      ]);
      expect(passed).toBe(true);
      expect(covered).toEqual(GUARDRAIL_LAYERS);
    });

    it('deduplicates repeated layers', () => {
      const { passed } = evaluateGuardrailChecklist([
        'permissions', 'permissions', 'operational-limits',
        'human-approval', 'observability', 'kill-switch',
      ]);
      expect(passed).toBe(true);
    });
  });

  describe('DOM integration', () => {
    let container;

    beforeEach(() => {
      document.body.innerHTML = `
        <div id="guardrail-self-assessment">
          <ul class="guardrail-checklist">
            <li><label><input type="checkbox" class="guardrail-check" data-layer="permissions"></label></li>
            <li><label><input type="checkbox" class="guardrail-check" data-layer="operational-limits"></label></li>
            <li><label><input type="checkbox" class="guardrail-check" data-layer="human-approval"></label></li>
            <li><label><input type="checkbox" class="guardrail-check" data-layer="observability"></label></li>
            <li><label><input type="checkbox" class="guardrail-check" data-layer="kill-switch"></label></li>
          </ul>
          <p class="assessment-result"></p>
        </div>
        <button class="btn-mark-complete" disabled>Mark as Complete</button>
      `;
      container = document.getElementById('guardrail-self-assessment');
    });

    it('readCheckedLayers returns only checked layers', () => {
      const inputs = container.querySelectorAll('input.guardrail-check');
      inputs[0].checked = true;
      inputs[2].checked = true;
      expect(readCheckedLayers(container).sort()).toEqual(
        ['human-approval', 'permissions']
      );
    });

    it('enables the complete button only when all five are checked', () => {
      const resultEl = container.querySelector('.assessment-result');
      const completeBtn = document.querySelector('.btn-mark-complete');
      initGuardrailChecklist({ container, resultEl, completeBtn, locale: 'en' });

      // Initially nothing checked → disabled.
      expect(completeBtn.disabled).toBe(true);

      // Check four of five → still disabled.
      const inputs = container.querySelectorAll('input.guardrail-check');
      for (let i = 0; i < 4; i++) {
        inputs[i].checked = true;
        inputs[i].dispatchEvent(new Event('change', { bubbles: true }));
      }
      expect(completeBtn.disabled).toBe(true);

      // Check the fifth → enabled.
      inputs[4].checked = true;
      inputs[4].dispatchEvent(new Event('change', { bubbles: true }));
      expect(completeBtn.disabled).toBe(false);
    });
  });

  describe('workshop + capstone lesson wiring', () => {
    const SELF_ASSESSED_LESSONS = [
      'threat-modeling-workshop',
      'agent-design-capstone',
    ];
    for (const slug of SELF_ASSESSED_LESSONS) {
      for (const locale of ['en', 'fr']) {
        it(`${locale} ${slug} embeds all five data-layer checks`, () => {
          const html = readFileSync(
            resolve(SKILLHUB_ROOT, locale, `${slug}.html`),
            'utf-8'
          );
          for (const layer of GUARDRAIL_LAYERS) {
            expect(html, `${locale}/${slug}: data-layer="${layer}"`)
              .toContain(`data-layer="${layer}"`);
          }
          // Mark-as-Complete starts disabled, gated on the checklist.
          expect(html).toContain('btn-mark-complete');
          expect(html).toContain('self-assessment.js');
          expect(html).toContain('disabled');
        });
      }
    }
  });
});
