# Bugfix Requirements Document

## Introduction

When the SkillHub course is launched in SCORM Cloud, the learner lands on SCORM Cloud's "Oops! Page not found!" (404) screen instead of a lesson page. The URL stops at the package content root (`.../courses/.../scorm92c4d448-77c2`), so the course never progresses past its launch page.

The SCORM launch file is the package-root `index.html`, built by `scripts/build-scorm.mjs` from `skillhub/index.html` and declared in `imsmanifest.xml` as `href="index.html"`. That launch page is a client-side locale redirect that navigates to a **bare directory** (`en/` or `fr/`) rather than to an explicit file. A local dev server typically auto-serves the directory's `index.html`, which hides the defect, but SCORM Cloud's static content host does not resolve a bare directory to `index.html`, so the request for `en/` (or `fr/`) returns 404.

The fix is to make the redirect target an explicit file — `en/index.html` / `fr/index.html` — in both the JavaScript redirect (`window.location.replace(...)`) and the `<noscript>` fallback links, so the course loads on any host regardless of directory auto-indexing behavior. The locale landing pages `skillhub/en/index.html` and `skillhub/fr/index.html` already exist, so the explicit targets are valid.

**Reproduction:** Build the SCORM package and launch it in SCORM Cloud (or any static host that does not auto-serve a directory's `index.html`). The launch page redirects to `en/` or `fr/` and the host returns "Page not found" instead of loading the locale landing page.

**Affected files:**
- `skillhub/index.html` — the launch/redirect page where the actual fix lives (JS redirect + `<noscript>` links)
- `scripts/build-scorm.mjs` — copies `index.html` verbatim as the SCO launch file and declares it in the manifest; no logic change expected, but it is the mechanism that ships the defect
- `skillhub/tests/` (vitest, run via `npm test` in WSL) — no scorm/launch regression test currently exists; one must be added

## Bug Analysis

### Current Behavior (Defect)

The launch/redirect page sends the browser to a bare locale directory, which hosts that do not auto-index treat as a missing resource.

1.1 WHEN the launch page runs its JavaScript redirect with a detected locale THEN the system navigates to the bare directory `locale + '/'` (e.g. `en/`) via `window.location.replace`
1.2 WHEN the course is launched on a host that does not auto-serve a directory's `index.html` (e.g. SCORM Cloud) THEN the system lands on the host's "Page not found" (404) page and no lesson page loads
1.3 WHEN JavaScript is disabled and the user selects a language from the `<noscript>` fallback THEN the system follows a link to the bare directory (`en/` / `fr/`), which 404s on the same hosts

### Expected Behavior (Correct)

The launch/redirect page sends the browser to an explicit locale landing file that resolves on any static host.

2.1 WHEN the launch page runs its JavaScript redirect with a detected locale THEN the system SHALL navigate to the explicit file `locale + '/index.html'` (e.g. `en/index.html`) via `window.location.replace`
2.2 WHEN the course is launched on a host that does not auto-serve a directory's `index.html` (e.g. SCORM Cloud) THEN the system SHALL load the locale landing page (`en/index.html` or `fr/index.html`) instead of a 404
2.3 WHEN JavaScript is disabled and the user selects a language from the `<noscript>` fallback THEN the system SHALL follow a link to the explicit file (`en/index.html` / `fr/index.html`)
2.4 WHEN the SCORM package is built THEN the shipped launch `index.html` and its manifest `href` SHALL be guarded by a regression test asserting the redirect and fallback targets are explicit `index.html` files, not bare directories

### Unchanged Behavior (Regression Prevention)

Locale detection and all behavior unrelated to the redirect target must stay the same.

3.1 WHEN a stored preference `skillhub-locale` is `fr` or `en` THEN the system SHALL CONTINUE TO honor the stored preference over browser detection
3.2 WHEN there is no stored preference and the browser language starts with `fr` THEN the system SHALL CONTINUE TO select the `fr` locale
3.3 WHEN there is no stored preference and the browser language is anything other than French (or `localStorage` is unavailable) THEN the system SHALL CONTINUE TO default to the `en` locale
3.4 WHEN the course is launched on a host that DOES auto-serve a directory's `index.html` (e.g. local dev server) THEN the system SHALL CONTINUE TO load the correct locale landing page
3.5 WHEN the SCORM package is built THEN `scripts/build-scorm.mjs` SHALL CONTINUE TO copy the root `index.html` verbatim as the single SCO launch file and declare it as `href="index.html"` in `imsmanifest.xml`

## Bug Condition Derivation

**Input domain:** `X` = a redirect request produced by the launch page for a detected locale `L ∈ {"en", "fr"}`, resolved against a host `H` whose directory auto-indexing behavior is `autoIndex(H) ∈ {true, false}`.

### Bug Condition — `isBugCondition(X)`

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type RedirectRequest { locale: L, host: H }
  OUTPUT: boolean

  // Bug triggers when the redirect target is a bare directory AND the host
  // does not auto-resolve that directory to index.html.
  RETURN targetIsBareDirectory(X) AND NOT autoIndex(X.host)
END FUNCTION
```

In the current code `targetIsBareDirectory(X)` is always true because `redirect` emits `locale + '/'`, so every launch on a non-auto-indexing host (SCORM Cloud) triggers the bug.

### Property — Fix Checking

```pascal
// Property: Fix Checking — explicit-file redirect loads the locale landing page
FOR ALL X WHERE isBugCondition(X) DO
  result ← launchRedirect'(X)      // F' = fixed launch page
  ASSERT result.target = X.locale + "/index.html"
     AND result.loadsLocaleLandingPage = true
     AND result.is404 = false
END FOR
```

### Property — Preservation Checking

```pascal
// Property: Preservation Checking — non-buggy launches behave identically
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

- **F** — the original launch page in `skillhub/index.html`, redirecting to `locale + '/'` with `<noscript>` links to `en/` and `fr/`.
- **F'** — the fixed launch page redirecting to `locale + '/index.html'` with `<noscript>` links to `en/index.html` and `fr/index.html`.
- **Counterexample:** launching the built package in SCORM Cloud detects `en`, redirects to `en/`, and the host returns "Page not found" — the course never loads a lesson.

Locale selection (stored preference → browser language → default `en`) is upstream of the redirect target and is unchanged by the fix (clauses 3.1–3.3).

---

# Iteration 2 — Relative Redirect Breaks on No-Trailing-Slash Launch URL

## Introduction (Iteration 2)

The Iteration 1 fix (redirect to the explicit file `locale + '/index.html'` instead of the bare directory `locale + '/'`) shipped and is verified in the package, yet SCORM Cloud still shows "Oops! Page not found!" The screenshot URL ends at the content root with **no trailing slash** (`.../courses/34ARXMUXR9/scorm7ed41bcd-f4ce`).

The remaining defect is **base-URL resolution of the relative redirect**. `skillhub/index.html` calls `window.location.replace('en/index.html')` with a *relative* target. The browser resolves a relative URL against the current document's base URL. When SCORM Cloud serves the launch page at a URL **without a trailing slash**, the last path segment (`scorm7ed41bcd-f4ce`) is treated as a file name and dropped during resolution, so `en/index.html` resolves against the parent directory (`.../courses/34ARXMUXR9/en/index.html`) instead of the SCO root (`.../scorm7ed41bcd-f4ce/en/index.html`). The locale landing page is not found and the host returns 404.

The whole course is built on root-relative assumptions that only hold when the launch URL ends in a slash: `en/index.html` loads `../assets/css/style.css` (one level up from `en/`) and links to sibling lesson pages. So the fix must make the launch page redirect resolve to the SCO root regardless of whether the host presents the launch URL with or without a trailing slash.

**The fix** is to compute the redirect target from `window.location` so it is anchored to the SCO launch document's own directory rather than to an ambiguous relative base: strip any trailing file-name segment from `window.location.pathname`, ensure a single trailing slash, then append `locale + '/index.html'`. Navigate to that resolved path. The `<noscript>` links (static HTML, no script base to normalize) keep the explicit-file form from Iteration 1.

**Reproduction:** Build the package and launch in SCORM Cloud. Observe the address bar lands on a path where `en/`/`fr/` sits one directory *above* the SCO root (missing the `scorm<hash>` segment), producing 404. Equivalent local reproduction: serve the package with a static host and request the SCO at a URL with no trailing slash (e.g. `.../skillhub_scorm` rather than `.../skillhub_scorm/`).

**Affected files:**
- `skillhub/index.html` — the launch/redirect page; the `redirect(locale)` function changes from a bare relative string to a location-anchored absolute path
- `skillhub/tests/` (vitest) — add regression coverage for the base-URL resolution behavior

## Bug Analysis (Iteration 2)

### Current Behavior (Defect)

4.1 WHEN the launch page runs `window.location.replace('en/index.html')` AND the current document URL has no trailing slash THEN the browser resolves the relative target against the parent directory, dropping the SCO root segment, and the request 404s
4.2 WHEN SCORM Cloud (or any static host) serves the SCO launch page at a URL without a trailing slash THEN the relative redirect points outside the SCO root and no locale landing page loads

### Expected Behavior (Correct)

5.1 WHEN the launch page performs the locale redirect THEN the system SHALL navigate to a path anchored to the launch document own directory (the SCO root), independent of whether the launch URL ends with a trailing slash, so `locale/index.html` always resolves inside the SCO root
5.2 WHEN the SCO root path is derived from `window.location.pathname` THEN the system SHALL treat the final segment correctly: strip it only when it is an explicit `*.html` launch file; otherwise (a directory name such as SCORM Cloud's `scorm<hash>` served with no trailing slash, or an already-slash-terminated path) KEEP it as the SCO root, normalize to a single trailing slash, and append `locale + '/index.html'`. The SCO-root segment MUST NOT be dropped.
5.3 WHEN the course is launched on a host that serves the SCO at a URL WITH a trailing slash THEN the system SHALL CONTINUE TO resolve to the same correct locale landing page (behavior preserved)

### Unchanged Behavior (Regression Prevention)

6.1 WHEN a stored preference `skillhub-locale` is `fr` or `en` THEN the system SHALL CONTINUE TO honor the stored preference over browser detection
6.2 WHEN there is no stored preference THEN the system SHALL CONTINUE TO select `fr` for a French browser language and otherwise default to `en`
6.3 WHEN JavaScript is disabled THEN the `<noscript>` fallback links SHALL CONTINUE TO point to the explicit files `en/index.html` / `fr/index.html` from Iteration 1
6.4 WHEN the SCORM package is built THEN `scripts/build-scorm.mjs` SHALL CONTINUE TO copy the root `index.html` verbatim and declare it as `href="index.html"` in `imsmanifest.xml`

## Bug Condition Derivation (Iteration 2)

**Input domain:** `X` = a redirect produced by the launch page for a detected locale `L in {"en","fr"}`, where the launch document is served at pathname `P`. Let `endsWithSlash(P)` be whether `P` ends with `/`.

### Bug Condition — `isBugCondition2(X)`

```pascal
FUNCTION isBugCondition2(X)
  INPUT: X of type RedirectRequest { locale: L, pathname: P }
  OUTPUT: boolean

  // Bug triggers when the redirect target is RELATIVE (not anchored to the SCO
  // root) AND the launch URL has no trailing slash, so relative resolution drops
  // the SCO root segment.
  RETURN targetIsRelative(X) AND NOT endsWithSlash(X.pathname)
END FUNCTION
```

In the Iteration 1 code `targetIsRelative(X)` is always true (the target is the bare relative string `locale + '/index.html'`), so every launch at a no-trailing-slash URL triggers the bug.

### Property — Fix Checking

```pascal
FOR ALL X WHERE isBugCondition2(X) DO
  result <- launchRedirect2(X)        // F2 = Iteration 2 fixed launch page
  ASSERT result.target = scoRoot(X.pathname) + X.locale + "/index.html"
     AND result.resolvesInsideScoRoot = true
     AND result.is404 = false
END FOR
```

### Property — Preservation Checking

```pascal
FOR ALL X WHERE NOT isBugCondition2(X) DO
  ASSERT F1(X) = F2(X)   // trailing-slash launches resolve to the same target
END FOR
```

- **F1** — the Iteration 1 launch page (explicit-file relative target).
- **F2** — the Iteration 2 launch page (location-anchored absolute target).
- **Counterexample:** SCORM Cloud serves the SCO at `.../scorm7ed41bcd-f4ce` (no slash); `window.location.replace('en/index.html')` resolves to `.../courses/34ARXMUXR9/en/index.html` (SCO root segment dropped) and returns "Page not found".

Locale selection (stored preference -> browser language -> default `en`) remains upstream of the redirect target and is unchanged (clauses 6.1, 6.2).