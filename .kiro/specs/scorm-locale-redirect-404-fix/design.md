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

---

# Iteration 2 Design — Location-Anchored Locale Redirect

## Overview (Iteration 2)

Iteration 1 fixed the bare-directory redirect (`locale + '/'` -> `locale + '/index.html'`), but the course still 404s in SCORM Cloud. The surviving root cause is that the redirect target is a **relative** URL. When the SCO launch page is served at a URL **without a trailing slash** (SCORM Cloud serves it at `.../scorm<hash>`), the browser resolves `en/index.html` against the parent of the launch document, dropping the SCO root segment, so the locale landing page is requested from the wrong directory and 404s.

The Iteration 2 fix anchors the redirect to the launch document's own directory. In `skillhub/index.html`, the `redirect(locale)` function computes the SCO root from `window.location.pathname` — stripping any trailing non-slash segment (a terminal file name such as `index.html` or SCORM Cloud's `scorm<hash>`), guaranteeing exactly one trailing slash — and then calls `window.location.replace(scoRoot + locale + '/index.html')`. Because the target now begins at the SCO root, it resolves identically whether or not the launch URL ends in a slash. Locale detection, the `<noscript>` fallback (already explicit files from Iteration 1), and the build/manifest contract are untouched.

## Glossary (Iteration 2)

- **Bug_Condition2 (C2)**: The redirect target is relative AND the launch URL has no trailing slash, so relative resolution drops the SCO root segment. In the Iteration 1 code the relative part is always true, so every no-trailing-slash launch triggers it.
- **Property2 (P2)**: The launch page navigates to a path anchored to the SCO root (`scoRoot(pathname) + locale + '/index.html'`) that resolves inside the SCO root on any host regardless of trailing slash.
- **scoRoot(pathname)**: The directory portion of the launch document's pathname with exactly one trailing slash. Derived by removing any trailing segment after the final `/` and ensuring the result ends with `/`.
- **redirect(locale)**: The function in `skillhub/index.html` performing the navigation. This is the single function being changed in Iteration 2.
- **endsWithSlash(P)**: Whether launch pathname `P` ends with `/`. SCORM Cloud launches without a trailing slash; many dev servers add one.

## Bug Details (Iteration 2)

### Bug Condition

The bug manifests when `redirect(locale)` navigates to a bare relative string (`locale + '/index.html'`) and the launch document URL has no trailing slash. The browser's relative-URL resolution strips the last path segment of the base (treating it as a file), so the target lands one directory above the SCO root.

```
FUNCTION isBugCondition2(X)
  INPUT: X of type RedirectRequest { locale: L in {"en","fr"}, pathname: P }
  OUTPUT: boolean
  RETURN targetIsRelative(X) AND NOT endsWithSlash(X.pathname)
END FUNCTION
```

In the current (Iteration 1) launch page `targetIsRelative(X)` is always true.

### Examples

- **SCORM Cloud, no trailing slash (bug):** launch at `.../courses/34ARXMUXR9/scorm7ed41bcd-f4ce`; `replace('en/index.html')` resolves to `.../courses/34ARXMUXR9/en/index.html` (SCO root `scorm7ed41bcd-f4ce` dropped) -> 404.
- **Dev server, trailing slash (not a bug — must stay correct):** launch at `.../skillhub_scorm/`; `replace('en/index.html')` resolves to `.../skillhub_scorm/en/index.html`. After the fix the anchored target resolves to the same path.
- **Launch at an explicit file (edge):** launch at `.../skillhub_scorm/index.html`; stripping the terminal `index.html` yields `.../skillhub_scorm/`, so `en/index.html` resolves correctly after the fix.

## Expected Behavior (Iteration 2)

### Preservation Requirements

- Locale selection (stored preference -> browser French -> `en` default) is unchanged (Req 6.1, 6.2).
- The `<noscript>` fallback links remain the explicit files `en/index.html` / `fr/index.html` (Req 6.3).
- `scripts/build-scorm.mjs` still copies `index.html` verbatim and declares `href="index.html"` (Req 6.4).
- Launches on hosts that already serve a trailing slash resolve to the same locale landing page as before (Req 5.3).

**Scope:** Only the computation of the redirect **target path** inside `redirect(locale)` changes. Detection logic, markup, styling, the loading UI, and the build pipeline are unaffected.

## Hypothesized Root Cause (Iteration 2)

1. **Relative redirect target.** `redirect(locale)` passes a bare relative string to `window.location.replace`. Relative URLs resolve against the current document's base; with no trailing slash the final segment is dropped, moving the target outside the SCO root.
2. **Course assumes an SCO-root base.** `en/index.html` references `../assets/...` and sibling lesson pages, which only resolve when the launch URL behaves like a directory (trailing slash). The relative redirect is the only place that assumption is violated at launch time.
3. **Host-dependent masking.** Dev servers that normalize directory URLs with a trailing slash hide the defect; SCORM Cloud, serving at `.../scorm<hash>` with no slash, exposes it.

The hypothesis is confirmed by the Iteration 1 fix being present-and-correct in the package while the 404 persists, and by the screenshot URL lacking a trailing slash.

## Correctness Properties (Iteration 2)

Property 3: Bug Condition — Location-Anchored Redirect Resolves Inside the SCO Root

_For any_ launch where `isBugCondition2` holds (relative target against a no-trailing-slash URL), the fixed launch page SHALL navigate to `scoRoot(pathname) + locale + '/index.html'`, which resolves inside the SCO root and loads the locale landing page instead of a 404.

**Validates: Requirements 5.1, 5.2**

Property 4: Preservation — Trailing-Slash Launches and Detection Unchanged

_For any_ launch where `isBugCondition2` does NOT hold (URL already ends in a slash) and for all locale-selection decisions, the fixed launch page SHALL resolve to the same locale landing page as Iteration 1 and SHALL preserve stored-preference precedence, browser-language detection, the `en` default, the explicit `<noscript>` targets, and the build/manifest contract.

**Validates: Requirements 5.3, 6.1, 6.2, 6.3, 6.4**

## Fix Implementation (Iteration 2)

### Changes Required

**File:** `skillhub/index.html`
**Function:** `redirect(locale)`

Replace the bare relative navigation with a location-anchored absolute path. A pure helper computes the target so it can be unit/property tested in isolation:

```js
// Compute the SCO-root-anchored target from a pathname + locale.
// The launch document is always the SCO root index.html (manifest href).
// Decide what the final path segment is and normalize to the SCO root:
//   - empty (pathname ends with "/")   -> already the SCO root directory
//   - an explicit *.html/*.htm file    -> strip that file name
//   - anything else (e.g. "scorm<hash>" with no slash, as SCORM Cloud serves)
//                                       -> it IS the SCO root directory; append "/"
// then append `locale + '/index.html'`.
function resolveLocaleTarget(pathname, locale) {
    var lastSeg = pathname.substring(pathname.lastIndexOf('/') + 1);
    var root;
    if (lastSeg === '') {
        root = pathname;                       // already ends with "/"
    } else if (/\.html?$/i.test(lastSeg)) {
        root = pathname.replace(/[^/]*$/, ''); // strip the explicit launch file (index.html)
    } else {
        root = pathname + '/';                 // last segment is the SCO root dir -> keep it
    }
    return root + locale + '/index.html';
}

function redirect(locale) {
    window.location.replace(resolveLocaleTarget(window.location.pathname, locale));
}
```

Notes:
- The naive `pathname.replace(/[^/]*$/, '')` is WRONG for SCORM Cloud: it would strip the `scorm<hash>` segment (the SCO root) when the launch URL has no trailing slash, reproducing the 404. The segment must be KEPT, so the resolver branches on whether the last segment is a real `*.html` file (strip) or a directory name (keep + append slash). This was confirmed empirically: `new URL('en/index.html', '.../scorm<hash>')` drops `scorm<hash>`, while the resolver above preserves it.
- The result is a root-relative/absolute path (begins from the document directory), so the browser does not re-strip a segment — it resolves inside the SCO root for trailing-slash, no-slash, and explicit-index.html launch URLs alike.
- `detectLocaleAndRedirect`, the `localStorage` lookup, the browser-language branch, and the `en` default are unchanged.
- The `<noscript>` links keep the Iteration 1 explicit-file form; static HTML has no script to normalize the base, and these are a JS-disabled fallback.
- No change to `scripts/build-scorm.mjs`; the corrected page ships verbatim.

### Regression Test

**File:** `skillhub/tests/scorm-launch-redirect.test.js` (extend the existing Iteration 1 file) or a new sibling test file.

- Export/extract `resolveLocaleTarget` (or re-implement the same contract in the test by extracting it from source) and assert:
  - **No trailing slash (the SCORM Cloud failing case)**: `resolveLocaleTarget('/sandbox/content/courses/ABC/scorm7ed41bcd-f4ce', 'en')` === `/sandbox/content/courses/ABC/scorm7ed41bcd-f4ce/en/index.html` — the `scorm<hash>` SCO-root segment is PRESERVED (this is what the naive strip-last-segment version got wrong).
  - Trailing slash: `resolveLocaleTarget('/x/skillhub_scorm/', 'fr')` === `/x/skillhub_scorm/fr/index.html`.
  - Explicit launch file: `resolveLocaleTarget('/x/skillhub_scorm/index.html', 'en')` === `/x/skillhub_scorm/en/index.html`.
  - Also cross-check against the browser URL resolver as the oracle: `new URL(resolveLocaleTarget(p, 'en'), 'https://host' + p).pathname` must contain the SCO-root segment for the no-slash `p`.
- Keep the Iteration 1 assertions (explicit-file `<noscript>` links; no bare `href="en/"` / `href="fr/"`).

## Testing Strategy (Iteration 2)

### Exploratory Bug Condition Checking

Observe the Iteration 1 launch page: its `redirect` passes the bare relative `locale + '/index.html'` to `window.location.replace`. A test that resolves that relative target against a no-trailing-slash base (via the URL API or `resolveLocaleTarget` on the OLD logic) lands outside the SCO root — the concrete counterexample. On the unfixed (Iteration 1) code the SCO-root-preservation assertion fails.

### Fix Checking

```
FOR ALL (pathname, locale) WHERE NOT endsWithSlash(pathname) DO
  ASSERT resolveLocaleTarget(pathname, locale) startsWith scoRoot(pathname)
     AND resolveLocaleTarget(pathname, locale) endsWith locale + "/index.html"
END FOR
```

### Preservation Checking

```
FOR ALL (pathname, locale) WHERE endsWithSlash(pathname) DO
  ASSERT resolveLocaleTarget(pathname, locale) = pathname + locale + "/index.html"
END FOR
// plus: locale-detection precedence unchanged (reuse Iteration 1 preservation tests)
```

### Property-Based Tests

- Generate `(scoRoot, launchForm in {"/", "/index.html", "" (no slash)}, locale in {"en","fr"})` tuples where the launch pathname is `scoRoot + launchForm`; assert `resolveLocaleTarget` always yields `scoRoot + "/" + locale + "/index.html"` — i.e. the SCO root segment is preserved for ALL three launch forms (especially the no-slash form SCORM Cloud uses), with exactly one slash and the correct locale.
- Reuse the Iteration 1 detection preservation property to confirm locale selection is unchanged.

### Integration Tests

- Build the package and assert the shipped `index.html` contains the location-anchored redirect (references `window.location.pathname` and the `resolveLocaleTarget` contract) and no longer passes a bare relative string to `replace`.
- Manual/E2E note: launch the built package on a static host at a URL with no trailing slash and confirm the locale landing page loads (no 404).