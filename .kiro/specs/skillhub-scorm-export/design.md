# Design Document

## Overview

This design packages the existing SkillHub static web course (`./skillhub`) as a single, self-contained **SCORM 1.2** package written to `./scorm/skillhub_scorm`. The whole course is tracked as **one SCO**: internal lesson navigation and locale switching stay in-page, and the LMS receives a single overall completion status and a single score.

Two things are added on top of the existing course:

1. A **Build_Process** (a plain Node/ESM script run via `npm`) that copies the course content into the package directory, injects a small SCORM runtime, and emits a conformant `imsmanifest.xml` plus the four SCORM 1.2 schema files.
2. A **SCORM_Runtime** — a new JavaScript module (`js/scorm/`) that discovers the LMS `API` object across parent/opener frame chains, initializes a session, and maps the course's existing `localStorage` progress and guardrail self-assessment onto the SCORM data model.

A hard design constraint is **non-invasiveness**: `progress.js`, `self-assessment.js`, `i18n.js`, and the lesson HTML are not rewritten. The runtime reads from the public functions those modules already export (`getCompletionPercentage`, `getCompletedLessons`, `evaluateGuardrailChecklist`) and observes `localStorage` through a thin adapter. The course remains fully usable when the SCORM `API` or `localStorage` is absent (graceful degradation).

Primary language: **JavaScript (ES modules)**, matching the existing codebase and its Vitest + jsdom + fast-check test toolchain.

### Goals

- Produce a reproducible SCORM 1.2 package containing both `en/` and `fr/` locales under one launch point.
- Mirror course progress into the LMS without changing how the course stores progress locally.
- Fail soft everywhere: no LMS, no storage, or an LMS that throws must never break the course.

### Non-Goals

- Multi-SCO sequencing, SCORM 2004, or cmi.interactions-level reporting.
- Changing lesson content, styling, or the existing locale/progress behavior.
- Zipping/uploading the package to a specific LMS (the output is a directory ready to be zipped).

## Architecture

```
Build time (Node):
  ./skillhub (source)                     ./scorm/skillhub_scorm (output)
  ├─ index.html ───────── copy ─────────▶ ├─ index.html          (Launch_File)
  ├─ en/ fr/ ──────────── copy ─────────▶ ├─ en/ fr/
  ├─ js/ ──────────────── copy ─────────▶ ├─ js/
  │                       inject ────────▶ │  └─ scorm/           (SCORM_Runtime)
  ├─ assets/ ──────────── copy ─────────▶ ├─ assets/
                          generate ──────▶ ├─ imsmanifest.xml
                          copy templates ▶ ├─ adlcp_rootv1p2.xsd
                                           ├─ imscp_rootv1p1p2.xsd
                                           ├─ imsmd_rootv1p2p1.xsd
                                           └─ ims_xml.xsd

Run time (browser inside an LMS frame):
  Launch_File index.html
    └─ locale redirect ─▶ en/ or fr/ lesson pages
          each page loads:
            js/progress.js         (unchanged)
            js/self-assessment.js  (unchanged)
            js/scorm/scorm-bootstrap.js  ─▶ ScormAdapter
                                              ├─ ApiDiscovery (parent → opener)
                                              ├─ ScormApiWrapper (init/get/set/commit/terminate)
                                              └─ ProgressBridge (localStorage ⇄ suspend_data)
```

The runtime is driven entirely from a single bootstrap entry point loaded by each lesson page. The bootstrap wires three collaborators and then stays out of the way; the existing modules keep calling `localStorage` exactly as before.

### Request / lifecycle flow

1. **Launch** — `scorm-bootstrap.js` runs on `DOMContentLoaded`. It asks `ApiDiscovery` for the LMS `API`. If found, `ScormApiWrapper.initialize()` calls `LMSInitialize("")`.
2. **Restore** — If `cmi.suspend_data` is non-empty, `ProgressBridge.restore()` decodes it and writes `skillhub_lesson_complete_*` keys back into `localStorage` before the page reads progress.
3. **Sync** — Whenever progress changes (storage event / explicit hook / before unload), `ScormAdapter.sync()` recomputes status + score and writes `cmi.*` values, then `LMSCommit("")`.
4. **Unload** — `beforeunload`/`pagehide` sets `cmi.core.exit` to `suspend`, commits, and calls `LMSFinish("")`.

Every step is a no-op (not an error) when the API is missing or when `localStorage` is unavailable.

## Components and Interfaces

### 1. Build_Process — `scripts/build-scorm.mjs`

Pure Node ESM script, invoked through a new `package.json` script (e.g. `npm run build:scorm`). No new runtime dependencies; uses `node:fs/promises` and `node:path`.

```javascript
/**
 * Assemble the SCORM 1.2 package.
 * @param {object} [opts]
 * @param {string} [opts.srcDir="skillhub"]
 * @param {string} [opts.outDir="scorm/skillhub_scorm"]
 * @returns {Promise<{outDir: string, files: string[]}>}
 */
export async function buildScormPackage(opts) { /* ... */ }

// Internal, individually unit-testable steps:
function copyCourseContent(srcDir, outDir)   // index.html, en/, fr/, js/, assets/
function injectRuntime(outDir)               // ensure js/scorm/* present in output
function writeSchemaFiles(outDir)            // 4 .xsd files at root (from scripts/scorm-templates/)
function writeManifest(outDir, model)        // imsmanifest.xml at root
```

Build steps (idempotent — output dir is cleaned first):

1. Clean/create `./scorm/skillhub_scorm`.
2. Copy `index.html`, `en/`, `fr/`, `js/`, `assets/` from `./skillhub` (Req 1.2, 1.3).
3. Ensure the SCORM runtime (`js/scorm/*`) is present in the copied `js/` (Req 1.4 wiring).
4. Copy the four schema `.xsd` templates to the package root (Req 2.4).
5. Generate `imsmanifest.xml` at root (Req 2.1–2.3, 2.5).

The schema `.xsd` files are stored as static template assets under `scripts/scorm-templates/` and copied verbatim; they are the canonical ADL/IMS SCORM 1.2 schemas and are not generated.

### 2. ApiDiscovery — `js/scorm/api-discovery.js`

Locates the LMS adapter object named `API` by walking frame chains. Depth-bounded to avoid infinite loops in self-referential window graphs.

```javascript
const MAX_DEPTH = 20; // guards against cycles / detached frames

/**
 * Walk a window's .parent chain looking for a window exposing `API`.
 * @param {Window} startWin
 * @returns {object|null} the LMS API object or null
 */
export function findApiInChain(startWin) { /* parent-walk, depth-bounded */ }

/**
 * Discover the LMS API: parent chain first (Req 6.1), then opener chain (Req 6.2).
 * @param {Window} [win=window]
 * @returns {object|null}
 */
export function discoverApi(win = window) { /* ... */ }
```

Discovery order (Req 6.1, 6.2):
1. Walk `win` then `win.parent` upward until `win.API` is found or the top window / `MAX_DEPTH` is reached.
2. If not found and `win.opener` exists, repeat the parent-walk starting from `win.opener`.
3. Return the first `API` found, else `null`.

All property access is wrapped in `try/catch` to tolerate cross-origin frame access errors (returns `null` rather than throwing).

### 3. ScormApiWrapper — `js/scorm/scorm-api.js`

Thin, defensive wrapper over the raw SCORM 1.2 `API` method surface (`LMSInitialize`, `LMSGetValue`, `LMSSetValue`, `LMSCommit`, `LMSFinish`, `LMSGetLastError`). Every method is a safe no-op when no API was discovered, and every raw call is wrapped so an LMS error never propagates (Req 7.4).

```javascript
export class ScormApiWrapper {
  /** @param {object|null} api  Result of discoverApi(); null → inert wrapper. */
  constructor(api) { this.api = api; this.initialized = false; }

  get available() { return this.api != null; }

  /** LMSInitialize(""). Must run before get/set (Req 6.3). @returns {boolean} */
  initialize() { /* no-op → false when !available; try/catch */ }

  /** @param {string} element @returns {string} ("" on error/unavailable) */
  getValue(element) { /* ... */ }

  /** @param {string} element @param {string|number} value @returns {boolean} */
  setValue(element, value) { /* ... */ }

  /** @returns {boolean} */
  commit() { /* LMSCommit("") */ }

  /** @returns {boolean} */
  terminate() { /* LMSFinish("") */ }
}
```

### 4. ProgressBridge — `js/scorm/progress-bridge.js`

Translates between the course's `localStorage` progress keys and the single `cmi.suspend_data` string. This is the non-invasive seam: it only ever reads/writes the `skillhub_lesson_complete_*` keys the Progress_Tracker already owns (Req 5.4). Serialization is a round-trippable, size-conscious JSON envelope.

```javascript
const STORAGE_PREFIX = "skillhub_lesson_complete_";

/**
 * Collect completed lesson ids straight from localStorage (prefix-scoped).
 * @returns {string[]}  sorted, deduped completed ids ([] if storage unavailable)
 */
export function readCompletedIds() { /* prefix scan, try/catch → [] */ }

/**
 * Encode completed ids into a compact suspend_data string.
 * @param {string[]} ids
 * @returns {string}   e.g. '{"v":1,"done":["adding-applications",...]}'
 */
export function serializeProgress(ids) { /* ... */ }

/**
 * Decode suspend_data back into completed ids. Tolerates empty/garbage input.
 * @param {string} suspendData
 * @returns {string[]}
 */
export function deserializeProgress(suspendData) { /* try/catch → [] */ }

/**
 * Write completed ids back into localStorage using the exact course prefix.
 * @param {string[]} ids
 */
export function restoreToLocalStorage(ids) { /* setItem(PREFIX+id,"true") */ }
```

Guarantee: `deserializeProgress(serializeProgress(ids))` yields the same set, and `restoreToLocalStorage` reproduces exactly the `skillhub_lesson_complete_*` keys (round-trip, Req 5.1, 5.2, 5.4).

### 5. ScormAdapter + bootstrap — `js/scorm/scorm-adapter.js`, `js/scorm/scorm-bootstrap.js`

The adapter is the orchestrator that the rest of the course never has to know about. It owns the status/score computation and the lifecycle hooks.

```javascript
export class ScormAdapter {
  /**
   * @param {ScormApiWrapper} wrapper
   * @param {object} deps  injected pure functions for testability:
   *   { getCompletionPercentage, totalLessons, evaluateGuardrailChecklist, readCheckedLayers }
   */
  constructor(wrapper, deps) { /* ... */ }

  /** On launch: initialize session + restore progress from suspend_data (Req 5.2, 6.3). */
  start() { /* ... */ }

  /** Pure mapping used by sync() and unit tests (Req 4.1, 4.2, 4.4). */
  computeStatus(pct, guardrailPassed) {
    if (pct >= 100) return guardrailPassed ? "passed" : "completed";
    return "incomplete";
  }

  /** Recompute + push status, score, suspend_data to the LMS, then commit (Req 4.*, 5.1). */
  sync() { /* setValue lesson_status, score.raw, suspend_data; commit() */ }

  /** On unload: set cmi.core.exit="suspend", commit, terminate (Req 5.3). */
  end() { /* ... */ }
}
```

`scorm-bootstrap.js` is the only file lesson pages reference. It is a side-effecting entry module:

```javascript
import { discoverApi } from "./api-discovery.js";
import { ScormApiWrapper } from "./scorm-api.js";
import { ScormAdapter } from "./scorm-adapter.js";
import { getCompletionPercentage, getCompletedLessons } from "../progress.js";
import { evaluateGuardrailChecklist, readCheckedLayers } from "../self-assessment.js";

const adapter = new ScormAdapter(new ScormApiWrapper(discoverApi(window)), {
  getCompletionPercentage, totalLessons: /* lessons.length */ 19,
  evaluateGuardrailChecklist, readCheckedLayers,
});

window.addEventListener("DOMContentLoaded", () => adapter.start());
window.addEventListener("storage", () => adapter.sync());        // cross-tab + same-tab progress change
window.addEventListener("pagehide", () => adapter.end());        // commit on unload (Req 5.3)
```

Integration is additive: a single `<script type="module" src="../js/scorm/scorm-bootstrap.js"></script>` tag is added to the lesson/index templates during the build (or is already present and simply travels with the copy). No existing module's source changes.

### imsmanifest.xml structure (Req 2.1–2.3, 2.5)

Single organization → single item → single resource referencing `index.html`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="SKILLHUB_SCORM12" version="1.0"
          xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd
                              http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd
                              http://www.imsglobal.org/xsd/imsmd_rootv1p2p1 imsmd_rootv1p2p1.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="ORG-SKILLHUB">
    <organization identifier="ORG-SKILLHUB">
      <title>Agentic AI OPCP Labs - SkillHub</title>
      <item identifier="ITEM-SKILLHUB" identifierref="RES-SKILLHUB" isvisible="true">
        <title>Agentic AI OPCP Labs - SkillHub</title>
        <adlcp:masteryscore>100</adlcp:masteryscore>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="RES-SKILLHUB" type="webcontent"
              adlcp:scormtype="sco" href="index.html">
      <file href="index.html"/>
      <!-- dependency file list enumerated by the build for en/, fr/, js/, assets/ -->
    </resource>
  </resources>
</manifest>
```

## Data Models

### SCORM 1.2 data model mapping (Req 4.*, 5.*, 6.4)

| Course concept | Source (existing code) | SCORM element | Written value | Direction | Validates |
|---|---|---|---|---|---|
| Overall completion status | `getCompletionPercentage()` + guardrail result | `cmi.core.lesson_status` | `incomplete` (pct<100), `completed` (pct==100), `passed` (pct==100 AND guardrail passed) | course → LMS | 4.1, 4.2, 4.4, 4.5 |
| Overall score | `getCompletionPercentage(totalLessons)` | `cmi.core.score.raw` | integer 0–100 | course → LMS | 4.3, 4.5 |
| Lesson progress snapshot | `localStorage` keys `skillhub_lesson_complete_*` | `cmi.suspend_data` | JSON envelope `{"v":1,"done":[ids]}` | course ⇄ LMS (write on change, read on launch) | 5.1, 5.2, 5.4 |
| Session exit intent | lifecycle (`pagehide`/`beforeunload`) | `cmi.core.exit` | `suspend` | course → LMS | 5.3 |

### ProgressSnapshot (suspend_data envelope)

```javascript
/** @typedef {{ v: 1, done: string[] }} ProgressSnapshot */
```

- `v` — schema version, lets future builds evolve the format while staying backward-tolerant.
- `done` — sorted, deduped completed lesson ids (the `skillhub_lesson_complete_` prefix is stripped on write and re-added on restore, preserving the exact key format).

SCORM 1.2 limits `cmi.suspend_data` to 4096 characters; with 19 lessons the envelope stays well within budget. The build asserts the worst-case size as a guard.

### Locale resolution (unchanged behavior, Req 3.*)

Resolution precedence remains **stored (`skillhub-locale`) → browser language → `en`**, exactly as the existing `index.html` redirect and `i18n.js` implement it. The SCORM package introduces no change here; the build simply copies both locale trees so the in-package redirect targets `en/` or `fr/` that now exist as siblings of the launch file.

## Error Handling

| Condition | Detection | Behavior | Validates |
|---|---|---|---|
| LMS `API` not found in any chain | `discoverApi()` returns `null` | Wrapper is inert; `start/sync/end` become safe no-ops; course runs standalone | 7.1 |
| `localStorage` unavailable | existing `isStorageAvailable()` guard + `try/catch` in bridge | Progress functions return `0`/`[]`; wrapper skips suspend_data mirroring; no throw | 7.2, 7.3 |
| LMS method throws (`LMSSetValue`, etc.) | `try/catch` around every raw API call in `ScormApiWrapper` | Error swallowed, method returns `false`/`""`, course continues | 7.4 |
| Cross-origin frame access during discovery | `try/catch` on `win.API`/`win.parent` access | Treated as "not here", walk continues or returns `null` | 6.1, 6.2 |
| Malformed/empty `suspend_data` on restore | `JSON.parse` in `try/catch` | `deserializeProgress` returns `[]`; nothing restored; course starts fresh | 5.2 |
| JavaScript disabled | n/a (static) | `index.html` `<noscript>` offers `en/` and `fr/` links | 3.5 |

Guiding rule: the SCORM layer may only *add* behavior. Any failure in discovery, the API, or storage degrades to the course's existing standalone behavior without surfacing an error to the learner.

## Testing Strategy

Reuses the existing toolchain — **Vitest** (`npm test` → `vitest --run`), **jsdom** environment, **fast-check** for property tests, and the shared `skillhub/tests/setup.js` (localStorage mock, `disableLocalStorage()` helper, navigator language defaults). New tests live alongside the current suite in `skillhub/tests/`.

Design-for-test choices that keep tests fast and deterministic:
- `ScormAdapter` takes its course functions as injected dependencies, so status/score logic is testable as pure functions.
- The raw LMS `API` is a hand-rolled mock object recording `LMSSetValue`/`LMSCommit` calls; no real LMS needed.
- `ApiDiscovery` is tested against mock window graphs (`{ API?, parent, opener }`) rather than real frames.

### Dual approach

- **Property tests** (`*.property.test.js`, min. 100 iterations each, tagged `Feature: skillhub-scorm-export, Property N: ...`) cover the universal mappings and round-trips.
- **Unit/example tests** cover lifecycle ordering, the manifest structure, graceful-degradation edge cases, and build output presence.
- **Build smoke tests** run `buildScormPackage()` into a temp dir and assert required files exist and the manifest parses.

Mapping of tests to properties and criteria:

- Property 1 (locale resolution) → 3.1; edge 3.4 via `disableLocalStorage()`.
- Property 2 (status mapping) → 4.1, 4.2, 4.4.
- Property 3 (score equals percentage) → 4.3.
- Property 4 (suspend_data round-trip) → 5.1, 5.2, 5.4.
- Property 5 (API discovery across chains) → 6.1, 6.2.
- Property 6 (LMS error tolerance) → 7.4.
- Example tests → 1.4, 1.5, 2.2, 2.3, 2.5, 3.2, 3.3, 3.5, 4.5, 5.3, 6.3, 6.4.
- Smoke tests → 1.1, 1.2, 1.3, 2.1, 2.4.
- Edge-case tests → 3.4, 7.1, 7.2, 7.3.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Locale resolution precedence

For any stored locale value and any browser language string, the locale resolver returns the stored value when it is `en` or `fr`; otherwise it returns `fr` if the browser language starts with `fr` (case-insensitive); otherwise it returns `en`.

**Validates: Requirements 3.1, 3.4**

### Property 2: Completion status mapping

For any completion percentage in 0–100 and any guardrail-passed boolean, the computed `cmi.core.lesson_status` is `passed` when the percentage equals 100 and the guardrail passed, `completed` when the percentage equals 100 and the guardrail did not pass, and `incomplete` for any percentage below 100.

**Validates: Requirements 4.1, 4.2, 4.4**

### Property 3: Score equals completion percentage

For any set of completed lessons, the value written to `cmi.core.score.raw` equals the integer returned by `getCompletionPercentage()` for that same state.

**Validates: Requirements 4.3**

### Property 4: Suspend-data progress round-trip

For any set of completed lesson ids, serializing them to `cmi.suspend_data` and then deserializing and restoring to `localStorage` reproduces exactly the same `skillhub_lesson_complete_` entries (same ids, same key prefix).

**Validates: Requirements 5.1, 5.2, 5.4**

### Property 5: LMS API discovery across frame chains

For any mock window graph in which the `API` object is reachable at an arbitrary finite depth along either the parent chain or the opener chain, `discoverApi()` returns that `API` object; when no reachable window exposes `API`, it returns `null`.

**Validates: Requirements 6.1, 6.2**

### Property 6: LMS error tolerance

For any single SCORM API method configured to throw, every `ScormApiWrapper` operation that invokes it completes without propagating the error (returning a safe default) and leaves the course operational.

**Validates: Requirements 7.4**
