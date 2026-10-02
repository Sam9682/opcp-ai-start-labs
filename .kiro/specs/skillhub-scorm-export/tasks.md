# Implementation Plan: SkillHub SCORM Export

## Overview

Build a non-invasive SCORM 1.2 export for the existing SkillHub course. The runtime is layered bottom-up — pure, injectable modules first (`api-discovery`, `scorm-api`, `progress-bridge`), then the orchestrating `scorm-adapter`, then the side-effecting `scorm-bootstrap` entry point. The packaging script (`scripts/build-scorm.mjs`) and its static `.xsd` templates come next, followed by non-invasive wiring of the single bootstrap `<script type="module">` into the templates during the build. Tests are written alongside each module using the existing Vitest + jsdom + fast-check toolchain and shared `skillhub/tests/setup.js`, covering the 6 correctness properties plus example/smoke/edge-case tests mapped to acceptance criteria.

All code is JavaScript (ES modules), matching the existing codebase.

## Tasks

- [x] 1. Implement LMS API discovery module
  - [x] 1.1 Create `skillhub/js/scorm/api-discovery.js`
    - Export `findApiInChain(startWin)`: walk `win` then `win.parent` upward until a window exposing `API` is found or the top window / `MAX_DEPTH` (20) is reached; wrap every property access in `try/catch` to tolerate cross-origin errors (return `null` instead of throwing)
    - Export `discoverApi(win = window)`: parent-walk first, then if not found and `win.opener` exists repeat the parent-walk from `win.opener`; return the first `API` found else `null`
    - Keep functions pure over an injectable `startWin`/`win` so they can be driven by mock window graphs
    - _Requirements: 6.1, 6.2_

  - [ ]* 1.2 Write property test for API discovery across frame chains
    - **Property 5: LMS API discovery across frame chains**
    - **Validates: Requirements 6.1, 6.2**
    - Generate mock window graphs `{ API?, parent, opener }` placing `API` at an arbitrary finite depth along the parent chain or the opener chain; assert `discoverApi()` returns that `API`, and returns `null` when no reachable window exposes `API`; min. 100 iterations, tagged `Feature: skillhub-scorm-export, Property 5`
    - _Requirements: 6.1, 6.2_

  - [ ]* 1.3 Write edge-case unit tests for discovery degradation
    - Assert `discoverApi()` returns `null` (no throw) when no `API` exists and when property access throws (simulated cross-origin), and that depth is bounded against self-referential `parent`/`opener` cycles
    - _Requirements: 7.1, 6.1, 6.2_

- [x] 2. Implement defensive SCORM API wrapper
  - [x] 2.1 Create `skillhub/js/scorm/scorm-api.js`
    - Export class `ScormApiWrapper` taking the discovered `api` (or `null`) in its constructor; expose `get available()` (`this.api != null`) and `initialized` state
    - Implement `initialize()` (`LMSInitialize("")`), `getValue(element)`, `setValue(element, value)`, `commit()` (`LMSCommit("")`), `terminate()` (`LMSFinish("")`)
    - Every method is a safe no-op when `!available` (returns `false`/`""`); wrap every raw API call in `try/catch` so an LMS error never propagates
    - _Requirements: 6.3, 6.4, 7.1, 7.4_

  - [ ]* 2.2 Write property test for LMS error tolerance
    - **Property 6: LMS error tolerance**
    - **Validates: Requirements 7.4**
    - For any single SCORM method configured to throw (hand-rolled mock `API`), assert every `ScormApiWrapper` operation that invokes it completes without propagating, returns a safe default, and leaves the wrapper usable; min. 100 iterations, tagged `Feature: skillhub-scorm-export, Property 6`
    - _Requirements: 7.4_

  - [ ]* 2.3 Write unit tests for wrapper lifecycle and inert mode
    - Using a mock `API` recording `LMSSetValue`/`LMSCommit` calls, assert `initialize()` precedes get/set; assert a `null`-api wrapper is fully inert (`available === false`, all methods no-op without throwing)
    - _Requirements: 6.3, 7.1_

- [x] 3. Implement progress bridge (localStorage ⇄ suspend_data)
  - [x] 3.1 Create `skillhub/js/scorm/progress-bridge.js`
    - Define `STORAGE_PREFIX = "skillhub_lesson_complete_"`
    - Export `readCompletedIds()`: prefix-scoped `localStorage` scan returning sorted, deduped ids, `try/catch` → `[]` when storage unavailable
    - Export `serializeProgress(ids)` → compact JSON envelope `{"v":1,"done":[ids]}`
    - Export `deserializeProgress(suspendData)`: `JSON.parse` in `try/catch`, tolerate empty/garbage → `[]`
    - Export `restoreToLocalStorage(ids)`: `setItem(STORAGE_PREFIX + id, "true")`, guarded against storage errors
    - _Requirements: 5.1, 5.2, 5.4, 7.2_

  - [ ]* 3.2 Write property test for suspend-data round-trip
    - **Property 4: Suspend-data progress round-trip**
    - **Validates: Requirements 5.1, 5.2, 5.4**
    - For any set of completed lesson ids, assert `restoreToLocalStorage(deserializeProgress(serializeProgress(ids)))` reproduces exactly the same `skillhub_lesson_complete_*` entries (same ids, same prefix); min. 100 iterations, tagged `Feature: skillhub-scorm-export, Property 4`
    - _Requirements: 5.1, 5.2, 5.4_

  - [ ]* 3.3 Write edge-case tests for malformed suspend_data and storage loss
    - Assert `deserializeProgress("")` and malformed/garbage input return `[]`; using `disableLocalStorage()` from `tests/setup.js`, assert `readCompletedIds()` returns `[]` and `restoreToLocalStorage()` does not throw
    - _Requirements: 5.2, 7.2_

- [x] 4. Checkpoint - Ensure all leaf-module tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement the ScormAdapter orchestrator
  - [x] 5.1 Create `skillhub/js/scorm/scorm-adapter.js`
    - Export class `ScormAdapter(wrapper, deps)` where `deps` injects pure course functions `{ getCompletionPercentage, totalLessons, evaluateGuardrailChecklist, readCheckedLayers }` for testability
    - Implement pure `computeStatus(pct, guardrailPassed)`: `passed` when `pct >= 100` and guardrail passed, `completed` when `pct >= 100` and not passed, `incomplete` when `pct < 100`
    - Implement `start()`: `wrapper.initialize()` then restore progress from `cmi.suspend_data` via the progress bridge before the page reads progress
    - Implement `sync()`: recompute status + score, write `cmi.core.lesson_status`, `cmi.core.score.raw` (integer 0–100), `cmi.suspend_data`, then `commit()`
    - Implement `end()`: set `cmi.core.exit = "suspend"`, `commit()`, `terminate()`
    - Every method degrades to a no-op when the wrapper is unavailable
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 6.3, 6.4_

  - [ ]* 5.2 Write property test for completion status mapping
    - **Property 2: Completion status mapping**
    - **Validates: Requirements 4.1, 4.2, 4.4**
    - For any percentage in 0–100 and any guardrail-passed boolean, assert `computeStatus` returns `passed`/`completed`/`incomplete` per the mapping; min. 100 iterations, tagged `Feature: skillhub-scorm-export, Property 2`
    - _Requirements: 4.1, 4.2, 4.4_

  - [ ]* 5.3 Write property test for score equals completion percentage
    - **Property 3: Score equals completion percentage**
    - **Validates: Requirements 4.3**
    - For any set of completed lessons, assert the value written to `cmi.core.score.raw` equals the integer `getCompletionPercentage()` returns for that same state (verify via mock `API` recording); min. 100 iterations, tagged `Feature: skillhub-scorm-export, Property 3`
    - _Requirements: 4.3_

  - [ ]* 5.4 Write unit tests for adapter lifecycle and single-report guarantee
    - With a mock `API`: assert `start()` initializes then restores from non-empty `suspend_data`; assert `end()` sets `cmi.core.exit="suspend"`, commits, and terminates in order; assert exactly one `lesson_status` and one `score.raw` are reported for the whole course
    - _Requirements: 4.5, 5.2, 5.3, 6.3, 6.4_

- [x] 6. Implement the bootstrap entry point
  - [x] 6.1 Create `skillhub/js/scorm/scorm-bootstrap.js`
    - Side-effecting module: `import { discoverApi }`, `ScormApiWrapper`, `ScormAdapter`, and course functions (`getCompletionPercentage`, `getCompletedLessons` from `../progress.js`; `evaluateGuardrailChecklist`, `readCheckedLayers` from `../self-assessment.js`)
    - Construct `new ScormAdapter(new ScormApiWrapper(discoverApi(window)), { ...deps, totalLessons })`
    - Wire listeners: `DOMContentLoaded` → `adapter.start()`, `storage` → `adapter.sync()`, `pagehide` → `adapter.end()`
    - No existing module source changes
    - _Requirements: 5.3, 6.1, 6.2, 6.3, 7.1, 7.3_

  - [ ]* 6.2 Write integration test for bootstrap wiring and standalone operation
    - In jsdom with no `API` reachable, assert importing the bootstrap and dispatching `DOMContentLoaded`/`storage`/`pagehide` never throws and leaves the course operational (graceful standalone); with a mock `API` on `window.parent`, assert the adapter initializes and syncs
    - _Requirements: 7.1, 7.3, 6.1_

- [x] 7. Checkpoint - Ensure runtime tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Add SCORM 1.2 schema template assets
  - [x] 8.1 Add the four SCORM 1.2 `.xsd` templates under `scripts/scorm-templates/`
    - Store `adlcp_rootv1p2.xsd`, `imscp_rootv1p1p2.xsd`, `imsmd_rootv1p2p1.xsd`, and `ims_xml.xsd` as canonical static ADL/IMS SCORM 1.2 schema files (copied verbatim at build time, not generated)
    - _Requirements: 2.4_

- [x] 9. Implement the build/packaging script
  - [x] 9.1 Create `scripts/build-scorm.mjs` with individually testable steps
    - Export `buildScormPackage({ srcDir = "skillhub", outDir = "scorm/skillhub_scorm" } = {})` using only `node:fs/promises` and `node:path` (no new deps)
    - Implement `copyCourseContent(srcDir, outDir)`: clean/create outDir, copy `index.html`, `en/`, `fr/`, `js/`, `assets/`
    - Implement `injectRuntime(outDir)`: ensure `js/scorm/*` is present in the copied `js/`
    - Implement `writeSchemaFiles(outDir)`: copy the four `.xsd` templates from `scripts/scorm-templates/` to the package root
    - Implement `writeManifest(outDir, model)`: emit `imsmanifest.xml` at root — single organization → single item → single resource referencing `index.html`, `schemaversion` `1.2`, enumerating dependency files for `en/`, `fr/`, `js/`, `assets/`
    - Return `{ outDir, files }`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.5_

  - [x] 9.2 Add the `build:scorm` npm script
    - Add `"build:scorm": "node scripts/build-scorm.mjs"` to `package.json` scripts
    - _Requirements: 1.1_

  - [ ]* 9.3 Write build smoke tests
    - Run `buildScormPackage()` into a temp dir; assert the output dir equals `scorm/skillhub_scorm` resolution, that `index.html`, `en/`, `fr/`, `js/`, `js/scorm/`, `assets/`, `imsmanifest.xml`, and the four `.xsd` files exist, and that `imsmanifest.xml` parses as XML
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.4_

  - [ ]* 9.4 Write unit tests for manifest structure and suspend_data size guard
    - Assert the generated manifest declares exactly one organization → one item → one resource referencing `index.html`, `scormtype="sco"`, and `schemaversion` `1.2`; assert the worst-case (19 lessons) `serializeProgress` envelope stays under the 4096-char `suspend_data` budget
    - _Requirements: 2.2, 2.3, 2.5, 1.4, 1.5_

- [x] 10. Wire the bootstrap script into templates during build (non-invasive)
  - [x] 10.1 Inject the single bootstrap tag during the build
    - In `scripts/build-scorm.mjs`, add a step that inserts a single `<script type="module" src="../js/scorm/scorm-bootstrap.js"></script>` (root-relative as appropriate) into the copied lesson/index templates in `outDir` only, without modifying source `skillhub/` files; make injection idempotent (skip if already present)
    - _Requirements: 1.4, 6.3_

  - [ ]* 10.2 Write test asserting non-invasive injection
    - Assert the bootstrap tag appears exactly once per output page after build, that re-running the build does not duplicate it, and that source `skillhub/` templates are left unchanged
    - _Requirements: 1.4_

- [ ] 11. Locale resolution verification (behavior unchanged)
  - [ ]* 11.1 Write property test for locale resolution precedence
    - **Property 1: Locale resolution precedence**
    - **Validates: Requirements 3.1, 3.4**
    - For any stored locale and browser language, assert the resolver returns the stored value when `en`/`fr`, else `fr` when the browser language starts with `fr` (case-insensitive), else `en`; use `disableLocalStorage()` for the 3.4 branch; min. 100 iterations, tagged `Feature: skillhub-scorm-export, Property 1`
    - _Requirements: 3.1, 3.4_

  - [ ]* 11.2 Write example tests for in-package locale selection and noscript fallback
    - Assert the resolver reads/writes the `skillhub-locale` key, that selecting a locale navigates to the corresponding in-package folder, and that the launch `index.html` provides `<noscript>` links to `en/` and `fr/`
    - _Requirements: 3.2, 3.3, 3.5_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; they are all test sub-tasks (property, unit, integration, smoke, and edge-case tests).
- The implementation language is JavaScript (ES modules), already determined from the existing codebase during the Clarify phase.
- Each task references specific requirement acceptance criteria for traceability.
- Runtime modules are built bottom-up (pure/injectable first) so each layer is unit-testable before the orchestrator and bootstrap wire them together.
- Graceful degradation is preserved throughout: every runtime path degrades to the course's existing standalone behavior when the LMS `API` or `localStorage` is absent, and no existing module source is modified.
- Tests reuse the existing Vitest + jsdom + fast-check toolchain and the shared `skillhub/tests/setup.js` (localStorage mock, `disableLocalStorage()` helper, navigator language defaults).

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "3.1", "8.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "2.2", "2.3", "3.2", "3.3", "5.1"] },
    { "id": 2, "tasks": ["5.2", "5.3", "5.4", "6.1", "9.1"] },
    { "id": 3, "tasks": ["6.2", "9.2", "9.3", "9.4", "11.1", "11.2"] },
    { "id": 4, "tasks": ["10.1"] },
    { "id": 5, "tasks": ["10.2"] }
  ]
}
```
