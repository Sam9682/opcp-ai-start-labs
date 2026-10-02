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
