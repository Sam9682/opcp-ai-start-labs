# Implementation Plan

## Overview

This plan fixes the SCORM launch page bug where the locale redirect targets a bare
directory (`locale + '/'`, and the `<noscript>` links `en/` / `fr/`). On hosts that do
not auto-index (such as SCORM Cloud), the bare-directory target returns a 404 instead of
loading the locale landing page. The fix changes the launch page to redirect to an
explicit file (`locale + '/index.html'`, with `<noscript>` links `en/index.html` /
`fr/index.html`). It is a single-file change in `skillhub/index.html`; locale detection
and the SCORM build script are left unchanged. The work follows the exploratory bugfix
flow: write a failing bug-condition test, write passing preservation tests, apply the fix,
then confirm both.

## Tasks

- [x] 1. Write bug condition exploration test (BEFORE implementing the fix)
  - **Property 1: Bug Condition** - Explicit-File Redirect Loads the Locale Landing Page
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bare-directory redirect target defect
  - **Scoped PBT Approach**: The bug is deterministic (source emits `locale + '/'` for both locales `L ∈ {"en","fr"}`), so scope the property to the concrete failing cases: the JS redirect target and the two `<noscript>` links.
  - Create new vitest file `skillhub/tests/scorm-launch-redirect.test.js` that reads `skillhub/index.html` from disk via `fs.readFileSync` (do NOT import/execute the page; assert on the source text as the design's regression test prescribes).
  - Assert the JS redirect emits an explicit file: source contains `locale + '/index.html'` and does NOT contain the bare-directory form `locale + '/'` without a trailing filename (Bug Condition: `targetIsBareDirectory(X)` from design / isBugCondition).
  - Assert the `<noscript>` English link is `href="en/index.html"` and no bare `href="en/"` remains; assert the `<noscript>` French link is `href="fr/index.html"` and no bare `href="fr/"` remains (Expected Behavior clauses 2.1, 2.3).
  - Run test on UNFIXED code via `npm test` in WSL Ubuntu-24.04
  - **EXPECTED OUTCOME**: Test FAILS (correct - proves the bug: current source emits `locale + '/'`, `href="en/"`, `href="fr/"`)
  - Document counterexamples found (e.g., "redirect emits `locale + '/'` → `en/` 404s on SCORM Cloud; `<noscript>` links are `href="en/"` / `href="fr/"`")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.3, 2.1, 2.3, 2.4_

- [x] 2. Write preservation property tests (BEFORE implementing the fix)
  - **Property 2: Preservation** - Locale Detection and Build Contract Unchanged
  - **IMPORTANT**: Follow observation-first methodology - observe UNFIXED behavior, then encode it
  - Observe locale-selection behavior on the UNFIXED launch page for non-bug-condition inputs (locale detection is upstream of the redirect target, so it is identical before/after the fix):
    - Stored preference `skillhub-locale = 'fr'` → selects `fr` (overrides browser language); `= 'en'` → selects `en` (Req 3.1).
    - No stored preference + `navigator.language` starting with `fr` (e.g. `fr-CA`, mixed-case `FR-ca`) → selects `fr` (Req 3.2).
    - No stored preference + non-French language (e.g. `en-US`, `de`, empty) OR `localStorage` unavailable (use `disableLocalStorage()` from `skillhub/tests/setup.js`) → defaults to `en` (Req 3.3).
  - Write property-based tests that extract the detection logic (`detectLocaleAndRedirect` / stored-preference → browser-language → `en` default) and assert the selected locale matches the documented precedence across generated `(storedPreference ∈ {none,"en","fr"}, browserLanguage, localStorageAvailable)` tuples. Property-based testing generates many cases for stronger preservation guarantees (design: Property-Based Tests).
  - Add a build-contract preservation assertion (Req 3.5): confirm `scripts/build-scorm.mjs` is referenced unchanged and the manifest still declares `href="index.html"` (verify via build in task 3.4 / integration, or assert the manifest template string is unchanged).
  - Run tests on UNFIXED code via `npm test` in WSL Ubuntu-24.04
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline locale-detection and build behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix the bare-directory redirect target in the launch page

  - [x] 3.1 Apply the explicit-file redirect fix in `skillhub/index.html`
    - Change the JS redirect from `window.location.replace(locale + '/');` to `window.location.replace(locale + '/index.html');`
    - Change the `<noscript>` English link `<a href="en/">English</a>` to `<a href="en/index.html">English</a>`
    - Change the `<noscript>` French link `<a href="fr/">Français</a>` to `<a href="fr/index.html">Français</a>`
    - Leave locale detection untouched: `detectLocaleAndRedirect`, the `localStorage` lookup, the browser-language branch, and the `en` default remain exactly as written
    - Make NO change to `scripts/build-scorm.mjs`: it already copies `index.html` verbatim and declares `href="index.html"` in the manifest
    - _Bug_Condition: isBugCondition(X) = targetIsBareDirectory(X) AND NOT autoIndex(X.host); current code always emits `locale + '/'`_
    - _Expected_Behavior: result.target = X.locale + "/index.html" AND loadsLocaleLandingPage = true AND is404 = false (expectedBehavior from design)_
    - _Preservation: Locale detection (stored pref → browser lang → en default), auto-indexing-host behavior, and build verbatim-copy / href="index.html" contract unchanged_
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Explicit-File Redirect Loads the Locale Landing Page
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior; when it passes it confirms the explicit-file target is satisfied
    - Run `skillhub/tests/scorm-launch-redirect.test.js` from task 1 via `npm test`
    - **EXPECTED OUTCOME**: Test PASSES (confirms the redirect and `<noscript>` links are now explicit `index.html` files, bug fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Locale Detection and Build Contract Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run the preservation property tests from task 2 via `npm test`
    - **EXPECTED OUTCOME**: Tests PASS (locale selection and build contract unchanged - only the appended `/index.html` suffix differs in the final target)
    - Confirm all tests still pass after the fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.4 (Optional) Integration test - built SCORM package carries explicit targets
    - Import `buildScormPackage` from `scripts/build-scorm.mjs` and build into a temporary directory (e.g. via `os.tmpdir()`), passing a unique `outDir`
    - Read the built package-root `index.html` and assert it carries the explicit-file redirect (`locale + '/index.html'`) and `<noscript>` targets (`en/index.html`, `fr/index.html`), confirming the corrected page ships verbatim
    - Assert the generated `imsmanifest.xml` still declares `adlcp:scormtype="sco" href="index.html"` for the SCO (build contract preserved)
    - Clean up the temporary build directory after the assertions
    - _Bug_Condition: Built artifact ships the defect verbatim on unfixed code_
    - _Preservation: Build copies root index.html verbatim and declares href="index.html" (Req 3.5)_
    - _Requirements: 2.2, 2.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run `npm test` in WSL Ubuntu-24.04 and confirm the full suite passes (exploration test now green, preservation tests green, existing suites unaffected)
  - Run the SCORM build `npm run build:scorm` and confirm it completes successfully with the corrected launch page
  - If any question or unexpected failure arises, ask the user before proceeding
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_

## Task Dependency Graph

```
Task 1 (Bug Condition exploration test, must FAIL on unfixed code)
Task 2 (Preservation property tests, must PASS on unfixed code)
        │
        │  (both exploration and preservation tests exist and have been
        │   run against the UNFIXED code before any fix is applied)
        ▼
Task 3.1 (Apply the explicit-file redirect fix in skillhub/index.html)
        │
        ├──────────────┬───────────────┬──────────────────────────┐
        ▼              ▼               ▼                          ▼
Task 3.2          Task 3.3        Task 3.4                   (3.2, 3.3, 3.4
(re-run Task 1,   (re-run Task 2, (optional integration       all depend on
 now PASSES)       still PASSES)   test on built package)      the fix in 3.1)
        │              │               │
        └──────────────┴───────────────┘
                       │
                       ▼
Task 4 (Checkpoint - full suite + SCORM build; depends on all of the above)
```

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": ["1", "2"],
      "dependsOn": []
    },
    {
      "wave": 2,
      "tasks": ["3.1"],
      "dependsOn": ["1", "2"]
    },
    {
      "wave": 3,
      "tasks": ["3.2", "3.3", "3.4"],
      "dependsOn": ["3.1"]
    },
    {
      "wave": 4,
      "tasks": ["4"],
      "dependsOn": ["3.2", "3.3", "3.4"]
    }
  ]
}
```

Ordering summary:
- Task 1 and Task 2 come before Task 3.1 (tests are written and observed on unfixed code first).
- Task 3.2, Task 3.3, and Task 3.4 depend on Task 3.1 (they validate the applied fix).
- Task 4 depends on all preceding tasks (final verification gate).

## Notes

- Tests are run with `npm test` (vitest) in the WSL Ubuntu-24.04 environment.
- The fix is a single-file change in `skillhub/index.html` (JS redirect target plus the two `<noscript>` links). No other source files are modified.
- The SCORM build script `scripts/build-scorm.mjs` is intentionally left unchanged: it already copies `index.html` verbatim and declares `href="index.html"` in the manifest, so the corrected page ships as-is.
- The exploration test (Task 1) asserts on the `index.html` source text via `fs.readFileSync` rather than importing/executing the page; it is expected to FAIL on unfixed code, which confirms the bug.
- Preservation tests (Task 2) must PASS on the unfixed code before the fix is applied — locale detection is upstream of the redirect target and is unchanged by the fix.
- Task 3.4 is optional; skipping it does not block Task 4, but Task 4 still requires the full suite and the SCORM build to succeed.
