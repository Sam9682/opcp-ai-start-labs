# SCORM Locale Redirect 404 Fix — Bugfix Design

## Overview

When the SkillHub course is launched in SCORM Cloud, the learner lands on a "Page not found" (404) screen instead of a lesson page. The package-root `index.html` (the SCO launch file) is a client-side locale redirect that sends the browser to a **bare directory** (`en/` or `fr/`). Local dev servers auto-serve that directory's `index.html` and hide the defect, but SCORM Cloud's static content host does not resolve a bare directory to `index.html`, so the request returns 404.

The fix is deliberately minimal and targeted at the redirect target only. In `skillhub/index.html` we change the JavaScript redirect from `window.location.replace(locale + '/')` to `window.location.replace(locale + '/index.html')`, and change the two `<noscript>` fallback links from `en/` / `fr/` to `en/index.html` / `fr/index.html`. Locale detection and everything upstream of the redirect target stay untouched. `scripts/build-scorm.mjs` already copies `index.html` verbatim and declares `href="index.html"` in the manifest, so no build logic changes — the corrected launch page simply ships as-is. A vitest regression test guards the explicit-file targets so the defect cannot silently return.

## Glossary

- **Bug_Condition (C)**: The redirect target emitted by the launch page is a bare directory (`locale + '/'`) and the serving host does not auto-resolve that directory to `index.html`. In the current code the bare-directory part is always true, so every non-auto-indexing host (SCORM Cloud) triggers the bug.
- **Property (P)**: The desired behavior — the launch page navigates to an explicit file `locale + '/index.html'` that resolves on any static host, loading the locale landing page instead of a 404.
- **Preservation**: Locale detection (stored preference → browser language → default `en`), the behavior on auto-indexing hosts, and the build script's copy/manifest contract must all remain unchanged.
- **detectLocaleAndRedirect**: The IIFE helper in `skillhub/index.html` that chooses a locale and calls `redirect(locale)`. Unchanged by the fix.
- **redirect(locale)**: The function in `skillhub/index.html` that performs `window.location.replace(...)`. This is the single line being changed.
- **autoIndex(H)**: Whether host `H` auto-serves a directory's `index.html`. `true` for typical local dev servers; `false` for SCORM Cloud's static host.
- **Build_Process**: `scripts/build-scorm.mjs`, which copies `skillhub/index.html` verbatim into the package root and declares it as the SCO launch file (`href="index.html"`).

## Bug Details

### Bug Condition

The bug manifests when the launch page redirects the browser to a bare locale directory (`en/` or `fr/`) and the serving host does not auto-resolve that directory to its `index.html`. The `redirect` function is navigating to `locale + '/'` instead of an explicit file, so the host receives a request for a directory it treats as a missing resource. Because the current code always emits a bare directory, the bug fires on every launch against a non-auto-indexing host (SCORM Cloud), while remaining invisible on auto-indexing dev servers.

**Formal Specification:**
```
FUNCTION isBugCondition(X)
  INPUT: X of type RedirectRequest { locale: L in {"en","fr"}, host: H }
  OUTPUT: boolean

  // Bug triggers when the redirect target is a bare directory AND the host
  // does not auto-resolve that directory to index.html.
  RETURN targetIsBareDirectory(X) AND NOT autoIndex(X.host)
END FUNCTION
```

In the current launch page `targetIsBareDirectory(X)` is always true because `redirect` emits `locale + '/'`.

### Examples

- **SCORM Cloud, English detected (bug):** host does not auto-index; redirect to `en/` → "Page not found" (404), course never loads a lesson. Expected: load `en/index.html`.
- **SCORM Cloud, French detected (bug):** stored preference `fr` → redirect to `fr/` → 404. Expected: load `fr/index.html`.
- **`<noscript>` fallback on SCORM Cloud (bug):** JavaScript disabled, user clicks "English" → link to `en/` → 404. Expected: link to `en/index.html` resolves.
- **Local dev server, English detected (not a bug — must stay correct):** host auto-indexes; redirect to `en/` resolves to `en/index.html`. After the fix, `en/index.html` still resolves correctly.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Locale selection honors a stored `skillhub-locale` preference (`fr` or `en`) over browser detection (Req 3.1).
- With no stored preference and a browser language starting with `fr`, the `fr` locale is selected (Req 3.2).
- With no stored preference and any non-French browser language, or when `localStorage` is unavailable, the `en` locale is the default (Req 3.3).
- On hosts that auto-serve a directory's `index.html`, the correct locale landing page still loads (Req 3.4).
- `scripts/build-scorm.mjs` continues to copy the root `index.html` verbatim as the single SCO launch file and declares it as `href="index.html"` in `imsmanifest.xml` (Req 3.5).

**Scope:**
All behavior that does NOT concern the redirect **target string** must be completely unaffected by this fix. This includes:
- The locale-detection branch logic (stored preference, browser language, default).
- The structure, styling, and loading UI of the launch page.
- The build script's copy, bootstrap-injection, schema, and manifest behavior.

**Note:** The expected correct behavior for the bug condition itself is defined in the Correctness Properties section (Property 1).

## Hypothesized Root Cause

Based on the bug analysis, the root cause is a single, well-isolated issue:

1. **Bare-directory redirect target**: `redirect(locale)` calls `window.location.replace(locale + '/')`, producing `en/` or `fr/`. Static hosts that do not auto-index a directory (SCORM Cloud) treat this as a missing resource and return 404.
   - The locale landing files `skillhub/en/index.html` and `skillhub/fr/index.html` already exist, so an explicit `locale + '/index.html'` target is valid.

2. **Matching `<noscript>` fallback links**: the fallback `<a href="en/">` / `<a href="fr/">` links share the same bare-directory defect for the JavaScript-disabled path.

3. **Build mechanism ships the defect verbatim**: `scripts/build-scorm.mjs` copies `index.html` unchanged, so the defective redirect reaches the SCORM package untouched. This is correct behavior for the build (no change needed) but is the vehicle by which the bug reaches SCORM Cloud.

4. **Host-dependent masking**: auto-indexing dev servers resolve `en/` to `en/index.html`, hiding the defect during local development and allowing it to pass unnoticed until SCORM Cloud launch.

The hypothesis is strong (not speculative): the current source literally emits `locale + '/'`, and SCORM Cloud's non-auto-indexing behavior is the documented trigger. The exploratory tests below confirm it against the unfixed source.

## Correctness Properties

Property 1: Bug Condition - Explicit-File Redirect Loads the Locale Landing Page

_For any_ redirect request where the bug condition holds (`isBugCondition` returns true — a bare-directory target against a non-auto-indexing host), the fixed launch page SHALL navigate to the explicit file `locale + '/index.html'` (e.g. `en/index.html`) and the `<noscript>` fallback links SHALL point to the same explicit files, so the locale landing page loads instead of a 404.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - Locale Detection and Build Contract Unchanged

_For any_ input where the bug condition does NOT hold (`isBugCondition` returns false — e.g. launches on auto-indexing hosts, and all locale-selection decisions), the fixed launch page SHALL produce the same result as the original, preserving stored-preference precedence, browser-language detection, the `en` default, correct loading on auto-indexing hosts, and the build script's verbatim-copy / `href="index.html"` manifest contract.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming the root-cause analysis is correct:

**File**: `skillhub/index.html`

**Function**: `redirect(locale)` and the `<noscript>` fallback block.

**Specific Changes**:
1. **JavaScript redirect target**: change
   `window.location.replace(locale + '/');`
   to
   `window.location.replace(locale + '/index.html');`

2. **`<noscript>` English link**: change `<a href="en/">English</a>` to `<a href="en/index.html">English</a>`.

3. **`<noscript>` French link**: change `<a href="fr/">Français</a>` to `<a href="fr/index.html">Français</a>`.

4. **Leave locale detection untouched**: `detectLocaleAndRedirect`, the `localStorage` lookup, the browser-language branch, and the `en` default remain exactly as written.

5. **No build-script change**: `scripts/build-scorm.mjs` already copies `index.html` verbatim and declares `href="index.html"`. The corrected launch page ships through the existing build unchanged; the manifest `href` still names the launch file (not a locale directory), which is correct.

### Regression Test (Req 2.4)

**File**: `skillhub/tests/scorm-launch-redirect.test.js` (new vitest file).

The test reads `skillhub/index.html` from disk and asserts:
- The JS redirect emits an explicit file: it contains `locale + '/index.html'` and does NOT contain the bare-directory form `locale + '/'` (with no trailing filename).
- Both `<noscript>` links point to `en/index.html` and `fr/index.html`, and no bare `href="en/"` / `href="fr/"` remains.

Optionally (host-independence of the shipped artifact), the test imports `buildScormPackage` from `scripts/build-scorm.mjs`, builds into a temporary directory, reads the built package-root `index.html`, and asserts the same explicit-file targets — confirming the corrected page ships verbatim and the manifest `href="index.html"` contract is intact.

## Testing Strategy

### Validation Approach

Two phases: first surface counterexamples that demonstrate the bug on the unfixed launch page, then verify the fix produces explicit-file targets and preserves locale detection and the build contract.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix, and confirm the root-cause hypothesis (bare-directory redirect target). If the counterexamples do not appear, re-hypothesize.

**Test Plan**: Read the UNFIXED `skillhub/index.html` and assert that the redirect target is an explicit `index.html` file. On unfixed code this assertion fails, surfacing the bare-directory target as the concrete counterexample. Pair this with the SCORM Cloud reproduction described in the requirements.

**Test Cases**:
1. **JS redirect target**: assert the redirect string resolves to `locale + '/index.html'` (will fail on unfixed code — it emits `locale + '/'`).
2. **`<noscript>` English link**: assert `href="en/index.html"` (will fail on unfixed code — `href="en/"`).
3. **`<noscript>` French link**: assert `href="fr/index.html"` (will fail on unfixed code — `href="fr/"`).
4. **Built package launch page (edge/integration)**: build the package and assert the package-root `index.html` carries the explicit targets (will fail on unfixed code — defect ships verbatim).

**Expected Counterexamples**:
- The launch page redirects to `en/` / `fr/`, which 404s on SCORM Cloud.
- Cause: `redirect` emits `locale + '/'` and the `<noscript>` links use bare directories.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed launch page produces the explicit-file target.

**Pseudocode:**
```
FOR ALL X WHERE isBugCondition(X) DO
  result := launchRedirect_fixed(X)
  ASSERT result.target = X.locale + "/index.html"
     AND result.loadsLocaleLandingPage = true
     AND result.is404 = false
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed launch page behaves identically to the original — same locale selection, same behavior on auto-indexing hosts, same build/manifest contract.

**Pseudocode:**
```
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT launchRedirect_original(X) = launchRedirect_fixed(X)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many `(stored preference, browser language, localStorage availability)` combinations across the input domain.
- It catches edge cases manual unit tests might miss (e.g. mixed-case `FR-ca`, empty language).
- It gives strong confidence that locale selection is byte-for-byte unchanged by the redirect-target fix.

**Test Plan**: Observe locale-selection behavior on the UNFIXED code first, then write tests capturing that behavior and assert it is unchanged after the fix. Confirm the chosen locale (`en`/`fr`) is identical; only the appended `/index.html` suffix differs in the final target.

**Test Cases**:
1. **Stored preference precedence**: `skillhub-locale = fr` (and `en`) still wins over browser language after the fix (Req 3.1).
2. **Browser French detection**: no stored preference + `navigator.language` starting with `fr` still selects `fr` (Req 3.2).
3. **Default to en**: no stored preference + non-French language, or `localStorage` unavailable, still defaults to `en` (Req 3.3).
4. **Auto-indexing host**: `en/index.html` / `fr/index.html` still resolve on dev servers (Req 3.4).
5. **Build contract**: build still copies `index.html` verbatim and emits `href="index.html"` in the manifest (Req 3.5).

### Unit Tests

- Assert the JS redirect target in `skillhub/index.html` is `locale + '/index.html'` and contains no bare-directory redirect.
- Assert the `<noscript>` links are `en/index.html` and `fr/index.html` and contain no bare `href="en/"` / `href="fr/"`.
- Assert locale-detection branches (stored preference, browser `fr`, default `en`, `localStorage` unavailable) are unchanged.

### Property-Based Tests

- Generate random `(storedPreference ∈ {none,"en","fr"}, browserLanguage, localStorageAvailable)` tuples and assert the selected locale matches the documented precedence after the fix (preservation of detection).
- Generate the two locales and assert the final redirect target is always `locale + '/index.html'` and never a bare directory (fix invariant).

### Integration Tests

- Build the SCORM package via `buildScormPackage` into a temp dir and assert the package-root `index.html` carries the explicit-file redirect and `<noscript>` targets.
- Assert the generated `imsmanifest.xml` still declares `href="index.html"` for the SCO (build contract preserved).
- End-to-end reproduction note: launching the built package on a non-auto-indexing host now loads `en/index.html` / `fr/index.html` instead of 404.
