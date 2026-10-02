# Requirements Document

## Introduction

This feature packages the existing SkillHub static web course (located in `./skillhub`) as a SCORM 1.2 package written to `./scorm/skillhub_scorm`. The package is a single, self-contained unit that bundles both the English (`en/`) and French (`fr/`) locale content, preserves the current locale auto-detection and switching behavior, and launches from a single `index.html`. The course is tracked as a SINGLE SCORM content object (SCO): internal lesson navigation stays in-page, and the LMS receives one overall completion status and one score for the whole course.

A SCORM 1.2 runtime wrapper discovers the LMS API object by walking parent and opener frames, and maps the course's existing progress and self-assessment state onto the SCORM data model (`cmi.core.lesson_status`, `cmi.core.score.raw`, `cmi.suspend_data`, `cmi.core.exit`). The package includes an `imsmanifest.xml` and the SCORM 1.2 schema files required for conformant packaging. All runtime behavior degrades gracefully: the course remains fully usable when the SCORM API or `localStorage` is unavailable.

## Glossary

- **SCORM_Package**: The output artifact in `./scorm/skillhub_scorm` — a single SCORM 1.2 conformant package containing the course content, manifest, schema files, and runtime wrapper.
- **SCORM_Runtime**: The JavaScript SCORM 1.2 API wrapper included in the package that discovers the LMS API object and reads from / writes to the SCORM data model.
- **LMS_API**: The SCORM 1.2 API adapter object (named `API`) exposed by a hosting Learning Management System, located by walking `window.parent` and `window.opener` frame chains.
- **Course_Content**: The SkillHub lesson content for both locales — `index.html`, `en/` (index plus lesson pages), `fr/` (index plus lesson pages), `js/` modules, and `assets/` (css, img).
- **Locale_Detector**: The existing locale auto-detection and switching logic (`i18n.js` and the inline redirect in `index.html`) that resolves `en` or `fr` using the `localStorage` key `skillhub-locale`.
- **Progress_Tracker**: The existing module (`progress.js`) that persists lesson completion under the `localStorage` key prefix `skillhub_lesson_complete_` and computes completion percentage via `getCompletionPercentage()`.
- **Guardrail_Assessment**: The existing self-assessment logic (`self-assessment.js`) that evaluates the five guardrail layers via `evaluateGuardrailChecklist()` under the all-five-layers rule.
- **Build_Process**: The JavaScript build step that assembles the SCORM_Package from Course_Content and the SCORM_Runtime.
- **Launch_File**: `index.html` at the root of the SCORM_Package, declared as the SCO launch resource in `imsmanifest.xml`.
- **Completion_Percentage**: The integer value in the range 0 to 100 returned by the Progress_Tracker's `getCompletionPercentage()` function.

## Requirements

### Requirement 1: Single Dual-Locale SCORM 1.2 Package

**User Story:** As a course author, I want the SkillHub course packaged as a single SCORM 1.2 package containing both locales, so that I can upload one file set to any SCORM 1.2 LMS.

#### Acceptance Criteria

1. THE Build_Process SHALL write the SCORM_Package to the directory `./scorm/skillhub_scorm`.
2. THE Build_Process SHALL include both the `en/` and `fr/` locale content from Course_Content in a single SCORM_Package.
3. THE Build_Process SHALL include the Course_Content `js/` modules and `assets/` directories (css and img) in the SCORM_Package.
4. THE SCORM_Package SHALL declare `index.html` at the package root as the Launch_File.
5. THE SCORM_Package SHALL target the SCORM 1.2 standard.

### Requirement 2: Conformant Manifest and Schema Files

**User Story:** As an LMS administrator, I want a conformant manifest and schema files, so that the package imports and validates against SCORM 1.2.

#### Acceptance Criteria

1. THE SCORM_Package SHALL contain an `imsmanifest.xml` file at the package root.
2. THE imsmanifest.xml SHALL declare a single organization containing a single item that references a single resource.
3. THE imsmanifest.xml SHALL reference the Launch_File `index.html` as the launch location of the single resource.
4. THE SCORM_Package SHALL include the SCORM 1.2 schema files `adlcp_rootv1p2.xsd`, `imscp_rootv1p1p2.xsd`, `imsmd_rootv1p2p1.xsd`, and `ims_xml.xsd` at the package root.
5. THE imsmanifest.xml SHALL declare the SCORM 1.2 schema version as `1.2`.

### Requirement 3: In-Package Locale Selection

**User Story:** As a learner, I want to pick or keep my language inside the package, so that I can take the course in English or French from one launch point.

#### Acceptance Criteria

1. WHEN the Launch_File is opened, THE Locale_Detector SHALL resolve the active locale using the stored preference, then the browser language, then the default locale `en`.
2. THE Locale_Detector SHALL read and write the locale preference using the `localStorage` key `skillhub-locale`.
3. WHEN a learner selects a different locale through the language switcher, THE Locale_Detector SHALL navigate to the corresponding locale folder within the SCORM_Package.
4. IF `localStorage` is unavailable, THEN THE Locale_Detector SHALL resolve the active locale from the browser language and default to `en`.
5. WHERE JavaScript is disabled, THE Launch_File SHALL present selectable links to the `en/` and `fr/` locale folders.

### Requirement 4: Overall Completion and Score Reporting

**User Story:** As a learner, I want my overall course progress reported to the LMS, so that my completion and score are recorded across the whole course.

#### Acceptance Criteria

1. WHEN Completion_Percentage equals 100, THE SCORM_Runtime SHALL set `cmi.core.lesson_status` to `completed`.
2. WHILE Completion_Percentage is less than 100, THE SCORM_Runtime SHALL set `cmi.core.lesson_status` to `incomplete`.
3. THE SCORM_Runtime SHALL set `cmi.core.score.raw` to the Completion_Percentage value returned by the Progress_Tracker `getCompletionPercentage()` function.
4. WHEN the Guardrail_Assessment reports a passed result and Completion_Percentage equals 100, THE SCORM_Runtime SHALL set `cmi.core.lesson_status` to `passed`.
5. THE SCORM_Runtime SHALL report a single overall `cmi.core.lesson_status` and a single `cmi.core.score.raw` for the entire course.

### Requirement 5: Cross-Session Progress Persistence

**User Story:** As a learner, I want my progress to persist across sessions, so that I can resume the course where I left off.

#### Acceptance Criteria

1. WHEN lesson completion state changes, THE SCORM_Runtime SHALL write the Progress_Tracker entries (keys prefixed with `skillhub_lesson_complete_`) into `cmi.suspend_data`.
2. WHEN the Launch_File is opened and `cmi.suspend_data` contains stored progress, THE SCORM_Runtime SHALL restore the Progress_Tracker entries from `cmi.suspend_data` into `localStorage`.
3. WHEN the course page is unloaded, THE SCORM_Runtime SHALL set `cmi.core.exit` and commit the current data model values to the LMS_API.
4. THE SCORM_Runtime SHALL preserve the `localStorage` key prefix `skillhub_lesson_complete_` used by the Progress_Tracker when mirroring progress.

### Requirement 6: Reliable LMS API Discovery

**User Story:** As an integrator, I want the runtime to find the LMS API reliably, so that tracking works across different LMS frame layouts.

#### Acceptance Criteria

1. WHEN the course launches, THE SCORM_Runtime SHALL locate the LMS_API by walking the `window.parent` frame chain.
2. IF the LMS_API is not found in the parent frame chain, THEN THE SCORM_Runtime SHALL search the `window.opener` frame chain.
3. WHEN the LMS_API is located, THE SCORM_Runtime SHALL initialize the SCORM session with the LMS_API before reading or writing data model values.
4. THE SCORM_Runtime SHALL map course state to the data model elements `cmi.core.lesson_status`, `cmi.core.score.raw`, `cmi.suspend_data`, and `cmi.core.exit`.

### Requirement 7: Graceful Degradation Without an LMS

**User Story:** As a learner, I want the course to keep working without an LMS, so that I can run the content standalone or in a restricted browser.

#### Acceptance Criteria

1. IF the LMS_API cannot be located, THEN THE SCORM_Runtime SHALL allow the Course_Content to operate without reporting to an LMS.
2. IF `localStorage` is unavailable, THEN THE Progress_Tracker SHALL continue to function and report a Completion_Percentage of 0.
3. IF the LMS_API cannot be located, THEN THE SCORM_Runtime SHALL continue to persist progress using `localStorage` through the Progress_Tracker.
4. WHEN the SCORM_Runtime encounters an LMS_API error, THE SCORM_Runtime SHALL allow the Course_Content to continue operating.
