import { describe, it, expect } from 'vitest';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DELIVERABLES = resolve(__dirname, '..', '..', 'deliverables');

/** The five guardrail layers that every mapping must cover. */
export const GUARDRAIL_LAYERS = [
  'permissions',
  'operational limits',
  'human approval',
  'observability',
  'kill switch',
];

/** The five guardrail layers in French. */
export const GUARDRAIL_LAYERS_FR = [
  'permissions',
  'limites opérationnelles',
  'approbation humaine',
  'observabilité',
  'kill switch',
];

function read(name) {
  return readFileSync(resolve(DELIVERABLES, name), 'utf-8');
}

function containsAll(haystack, needles) {
  const lower = haystack.toLowerCase();
  return needles.filter((n) => !lower.includes(n.toLowerCase()));
}

describe('Deliverable templates', () => {
  const files = [
    'agent-design-template.md',
    'agent-design-template.fr.md',
    'threat-model-template.md',
    'threat-model-template.fr.md',
    'trace-annotation-worksheet.md',
    'trace-annotation-worksheet.fr.md',
    'README.md',
  ];

  it('all template files exist', () => {
    for (const f of files) {
      expect(existsSync(resolve(DELIVERABLES, f)), f).toBe(true);
    }
  });

  describe('agent-design-template (EN)', () => {
    const doc = () => read('agent-design-template.md');

    it('has the required design sections', () => {
      const required = [
        'Autonomy Level',
        'Seven Core Components',
        'Loop Variant',
        'Stopping Criteria',
        'Guardrails (Five Layers)',
        'Multi-Agent Decision',
        'Responsible-AI Alignment',
      ];
      expect(containsAll(doc(), required)).toEqual([]);
    });

    it('covers all five guardrail layers', () => {
      expect(containsAll(doc(), GUARDRAIL_LAYERS)).toEqual([]);
    });

    it('names each of the seven components', () => {
      const components = [
        'Brain', 'Short-Term Memory', 'Long-Term Memory',
        'Tools', 'Planner', 'Execution Loop', 'Guardrails',
      ];
      expect(containsAll(doc(), components)).toEqual([]);
    });
  });

  describe('agent-design-template (FR)', () => {
    const doc = () => read('agent-design-template.fr.md');

    it('has the required design sections', () => {
      const required = [
        "Niveau d'autonomie",
        'sept composants',
        'Variante de boucle',
        "Critères d'arrêt",
        'Garde-fous (cinq couches)',
        'Décision multi-agents',
        'IA responsable',
      ];
      expect(containsAll(doc(), required)).toEqual([]);
    });

    it('covers all five guardrail layers (FR)', () => {
      expect(containsAll(doc(), GUARDRAIL_LAYERS_FR)).toEqual([]);
    });
  });

  describe('threat-model-template (EN)', () => {
    const doc = () => read('threat-model-template.md');

    it('covers the agent-specific threats', () => {
      const threats = ['Tool Misuse', 'Prompt Injection', 'Runaway Loops'];
      expect(containsAll(doc(), threats)).toEqual([]);
    });

    it('maps mitigations to all five guardrail layers', () => {
      expect(containsAll(doc(), GUARDRAIL_LAYERS)).toEqual([]);
    });

    it('has a guardrail-layer coverage checklist', () => {
      expect(doc()).toContain('Coverage Checklist');
    });
  });

  describe('threat-model-template (FR)', () => {
    const doc = () => read('threat-model-template.fr.md');

    it('covers the agent-specific threats (FR)', () => {
      const threats = ["Détournement d'outil", "Injection d'invite", 'Boucles emballées'];
      expect(containsAll(doc(), threats)).toEqual([]);
    });

    it('maps mitigations to all five guardrail layers (FR)', () => {
      expect(containsAll(doc(), GUARDRAIL_LAYERS_FR)).toEqual([]);
    });
  });

  describe('trace-annotation-worksheet', () => {
    it('EN has the four annotation sections', () => {
      const doc = read('trace-annotation-worksheet.md');
      const required = [
        'Label the Loop Phases',
        'Identify the Tools',
        'Name the Stopping Criterion',
        'Spot the Guardrail Trigger',
      ];
      expect(containsAll(doc, required)).toEqual([]);
    });

    it('FR has the four annotation sections', () => {
      const doc = read('trace-annotation-worksheet.fr.md');
      const required = [
        'Étiqueter les phases',
        'Identifier les outils',
        "Nommer le critère d'arrêt",
        'Repérer le déclenchement',
      ];
      expect(containsAll(doc, required)).toEqual([]);
    });
  });
});
