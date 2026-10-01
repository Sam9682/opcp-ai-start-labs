/**
 * Self_Assessment - Lightweight guardrail-coverage self-check for the
 * afternoon workshops (threat modeling and the design capstone).
 *
 * The learner ticks a checklist asserting their filled deliverable addresses
 * each of the five guardrail layers. The assessment passes only when ALL five
 * layers are checked (the "all-five-layers rule").
 *
 * @module self-assessment
 */

/** Canonical ids of the five guardrail layers (order is display order). */
export const GUARDRAIL_LAYERS = [
  'permissions',
  'operational-limits',
  'human-approval',
  'observability',
  'kill-switch',
];

/**
 * Evaluate a set of checked guardrail-layer ids against the all-five rule.
 *
 * @param {string[]} checkedLayers - Layer ids the learner has checked.
 * @returns {{passed: boolean, covered: string[], missing: string[]}}
 *   passed  - true only if every layer in GUARDRAIL_LAYERS is checked
 *   covered - the recognized layers that were checked (deduped, canonical order)
 *   missing - the layers still unchecked (canonical order)
 */
export function evaluateGuardrailChecklist(checkedLayers) {
  const checked = new Set(
    (checkedLayers || []).map((l) => String(l).trim().toLowerCase())
  );
  const covered = GUARDRAIL_LAYERS.filter((layer) => checked.has(layer));
  const missing = GUARDRAIL_LAYERS.filter((layer) => !checked.has(layer));
  return {
    passed: missing.length === 0,
    covered,
    missing,
  };
}

/**
 * Read the currently checked layers from a checklist container in the DOM.
 * Expects inputs of the form:
 *   <input type="checkbox" class="guardrail-check" data-layer="permissions">
 *
 * @param {HTMLElement} container - Element containing the checklist inputs.
 * @returns {string[]} The data-layer values of checked inputs.
 */
export function readCheckedLayers(container) {
  if (!container) {
    return [];
  }
  const inputs = container.querySelectorAll('input.guardrail-check[data-layer]');
  const checked = [];
  inputs.forEach((input) => {
    if (input.checked) {
      checked.push(input.getAttribute('data-layer'));
    }
  });
  return checked;
}

/**
 * Wire a self-assessment checklist: on any change, update a result element and
 * enable/disable the associated Mark-as-Complete button based on the all-five
 * rule.
 *
 * @param {Object} opts
 * @param {HTMLElement} opts.container - The checklist container.
 * @param {HTMLElement} [opts.resultEl] - Element to render pass/missing text.
 * @param {HTMLButtonElement} [opts.completeBtn] - Button to gate on completion.
 * @param {string} [opts.locale] - "en" | "fr" for result messages.
 * @returns {Function} An update function (also runs once immediately).
 */
export function initGuardrailChecklist(opts) {
  const { container, resultEl, completeBtn, locale = 'en' } = opts || {};
  if (!container) {
    return () => {};
  }

  const messages = {
    en: {
      pass: 'All five guardrail layers are covered. You may mark this complete.',
      missing: (m) => `Still to address: ${m.join(', ')}.`,
    },
    fr: {
      pass: 'Les cinq couches de garde-fous sont couvertes. Vous pouvez marquer comme terminé.',
      missing: (m) => `Reste à traiter : ${m.join(', ')}.`,
    },
  };
  const msg = messages[locale] || messages.en;

  function update() {
    const checked = readCheckedLayers(container);
    const { passed, missing } = evaluateGuardrailChecklist(checked);

    if (resultEl) {
      resultEl.textContent = passed ? msg.pass : msg.missing(missing);
      resultEl.classList.toggle('assessment-pass', passed);
      resultEl.classList.toggle('assessment-incomplete', !passed);
    }
    if (completeBtn) {
      completeBtn.disabled = !passed;
    }
    return passed;
  }

  container.addEventListener('change', update);
  update();
  return update;
}
