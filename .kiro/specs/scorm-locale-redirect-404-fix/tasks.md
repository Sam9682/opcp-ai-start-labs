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

---

## Iteration 2 Tasks — Location-Anchored Locale Redirect

### Overview (Iteration 2)

Iteration 1 shipped the explicit-file redirect but the course still 404s in SCORM Cloud because the redirect target is a **relative** URL. When the SCO is served at a URL with no trailing slash (`.../scorm<hash>`), the browser resolves `en/index.html` against the parent directory and drops the SCO root segment. Iteration 2 anchors the redirect to the launch document own directory via a pure `resolveLocaleTarget(pathname, locale)` helper, so the target resolves inside the SCO root regardless of trailing slash. Single-file change in `skillhub/index.html`; detection, `<noscript>` fallback, and the build are unchanged.

- [x] 5. Write bug condition exploration test for the relative-redirect base defect (BEFORE implementing the fix)
  - **Property 3: Bug Condition** - Location-Anchored Redirect Resolves Inside the SCO Root
  - **CRITICAL**: This test MUST FAIL on Iteration 1 code - failure confirms the no-trailing-slash defect
  - **DO NOT attempt to fix the test or the code when it fails**
  - **GOAL**: Surface the counterexample where a relative redirect against a no-trailing-slash launch URL resolves OUTSIDE the SCO root
  - Add tests to `skillhub/tests/scorm-launch-redirect.test.js` (or a new sibling file) that model the redirect resolution. Resolve the launch page target against a no-trailing-slash base using the standard URL API (`new URL(target, base)`), where `target` is the string the Iteration 1 page passes to `window.location.replace` (`locale + '/index.html'`) and `base` is a SCORM-Cloud-style URL ending in `.../scorm7ed41bcd-f4ce` (no slash).
  - Assert the resolved URL path contains the SCO root segment (e.g. `/scorm7ed41bcd-f4ce/en/index.html`). On Iteration 1 code this FAILS because the segment is dropped (`/courses/<id>/en/index.html`). Use `new URL(target, base)` as the oracle — this was confirmed empirically: `new URL('en/index.html', '.../scorm<hash>')` resolves to `.../courses/<id>/en/index.html`, dropping `scorm<hash>`.
  - Also assert the source of `skillhub/index.html` derives the target from `window.location` (e.g. references `window.location.pathname`) rather than passing a bare relative string - FAILS on Iteration 1 (bare `locale + '/index.html'`).
  - Run on Iteration 1 code via `npm test` in WSL Ubuntu-24.04
  - **EXPECTED OUTCOME**: Test FAILS (correct - proves the base-URL resolution defect)
  - Document the counterexample (resolved URL drops `scorm<hash>` and 404s)
  - _Requirements: 4.1, 4.2, 5.1, 5.2_

- [x] 6. Write preservation tests for Iteration 2 (BEFORE implementing the fix)
  - **Property 4: Preservation** - Trailing-Slash Launches and Detection Unchanged
  - **IMPORTANT**: Observation-first - these must PASS on Iteration 1 code
  - Assert that for a launch URL that already ends in a slash, resolving the Iteration 1 relative target yields the correct SCO-root-relative landing page (`.../skillhub_scorm/en/index.html`). This behavior is preserved by the fix.
  - Reuse / keep the Iteration 1 locale-detection preservation property tests (`scorm-launch-locale-preservation.property.test.js`) and the explicit-file `<noscript>` assertions - detection and fallback are unchanged by Iteration 2.
  - Add a build-contract preservation assertion (Req 6.4): manifest still declares `href="index.html"`.
  - Run on Iteration 1 code via `npm test` in WSL Ubuntu-24.04
  - **EXPECTED OUTCOME**: Tests PASS (confirms the trailing-slash + detection + build baseline to preserve)
  - _Requirements: 5.3, 6.1, 6.2, 6.3, 6.4_

- [x] 7. Apply the location-anchored redirect fix

  - [x] 7.1 Add `resolveLocaleTarget` and rewire `redirect(locale)` in `skillhub/index.html`
    - Add a pure helper `resolveLocaleTarget(pathname, locale)` that derives the SCO root from the final path segment: if the segment is empty (trailing slash) keep the path; if it is an explicit `*.html` launch file strip it; otherwise (a directory name such as SCORM Cloud's `scorm<hash>` served with NO trailing slash) KEEP it and append `/`. Then return `root + locale + '/index.html'`. CRITICAL: do NOT use a naive `pathname.replace(/[^/]*$/, '')` — it drops the `scorm<hash>` SCO-root segment on the no-slash launch URL and reproduces the 404.
    - Change `redirect(locale)` to call `window.location.replace(resolveLocaleTarget(window.location.pathname, locale))`
    - Leave locale detection untouched: `detectLocaleAndRedirect`, the `localStorage` lookup, the browser-language branch, and the `en` default remain exactly as written
    - Keep the Iteration 1 `<noscript>` explicit-file links (`en/index.html`, `fr/index.html`) unchanged
    - Make NO change to `scripts/build-scorm.mjs`
    - _Bug_Condition: isBugCondition2(X) = targetIsRelative(X) AND NOT endsWithSlash(X.pathname)_
    - _Expected_Behavior: target = scoRoot(pathname) + locale + "/index.html" AND resolvesInsideScoRoot = true AND is404 = false_
    - _Preservation: detection, <noscript> fallback, trailing-slash resolution, and build/manifest contract unchanged_
    - _Requirements: 5.1, 5.2_

  - [x] 7.2 Verify the Iteration 2 bug condition exploration test now passes
    - **IMPORTANT**: Re-run the SAME test from task 5 - do NOT write a new test
    - Run via `npm test`
    - **EXPECTED OUTCOME**: Test PASSES (resolved target now preserves the SCO root segment for no-trailing-slash launch URLs)
    - _Requirements: 5.1, 5.2_

  - [x] 7.3 Verify Iteration 2 preservation tests still pass
    - **IMPORTANT**: Re-run the SAME tests from task 6 (and the Iteration 1 preservation suite) - do NOT write new tests
    - Run via `npm test`
    - **EXPECTED OUTCOME**: Tests PASS (trailing-slash resolution, locale detection, `<noscript>` fallback, and build contract unchanged)
    - _Requirements: 5.3, 6.1, 6.2, 6.3, 6.4_

- [x] 8. Checkpoint - Ensure all tests pass and rebuild the package
  - Run `npm test` in WSL Ubuntu-24.04 and confirm the full suite passes (Iteration 2 exploration test now green, all preservation tests green, Iteration 1 tests still green, existing suites unaffected except the known pre-existing `navigation.test.js` failure)
  - Run `npm run build:scorm` and confirm the rebuilt `scorm/skillhub_scorm/index.html` carries the location-anchored redirect
  - Note for manual verification: re-upload to SCORM Cloud and confirm the locale landing page loads (no 404)
  - _Requirements: 4.1, 4.2, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.4_

## Iteration 2 Task Dependency Graph

```
Task 5 (Bug Condition exploration test, must FAIL on Iteration 1 code)
Task 6 (Preservation tests, must PASS on Iteration 1 code)
        |
        v
Task 7.1 (Add resolveLocaleTarget + rewire redirect in skillhub/index.html)
        |
        +---------------+
        v               v
Task 7.2           Task 7.3
(re-run Task 5,    (re-run Task 6,
 now PASSES)        still PASSES)
        |               |
        +-------+-------+
                v
Task 8 (Checkpoint - full suite + SCORM rebuild)
```

```json
{
  "waves": [
    { "wave": 1, "tasks": ["5", "6"], "dependsOn": [] },
    { "wave": 2, "tasks": ["7.1"], "dependsOn": ["5", "6"] },
    { "wave": 3, "tasks": ["7.2", "7.3"], "dependsOn": ["7.1"] },
    { "wave": 4, "tasks": ["8"], "dependsOn": ["7.2", "7.3"] }
  ]
}
```