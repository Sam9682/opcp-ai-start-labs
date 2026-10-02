// scripts/build-scorm.mjs
//
// Build_Process for the SkillHub SCORM 1.2 export.
//
// Assembles a single, self-contained SCORM 1.2 package from the existing
// SkillHub course (./skillhub) into ./scorm/skillhub_scorm. The package bundles
// both locales (en/, fr/), the js/ runtime (including js/scorm/*), and assets/,
// declares index.html as the single SCO launch file, copies the four SCORM 1.2
// schema templates to the package root, and emits a conformant imsmanifest.xml.
//
// Uses only the Node standard library (node:fs/promises, node:path) — no new
// runtime dependencies. The build is idempotent: the output directory is cleaned
// before every run.
//
// Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.5

import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs/promises";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/** Repository root — this script lives in <root>/scripts. */
const REPO_ROOT = path.resolve(__dirname, "..");

/** Directory holding the canonical SCORM 1.2 schema templates. */
const TEMPLATES_DIR = path.join(REPO_ROOT, "scripts", "scorm-templates");

/** The four SCORM 1.2 schema files copied verbatim to the package root (Req 2.4). */
const SCHEMA_FILES = [
  "adlcp_rootv1p2.xsd",
  "imscp_rootv1p1p2.xsd",
  "imsmd_rootv1p2p1.xsd",
  "ims_xml.xsd",
];

/** Top-level course content copied from srcDir into the package (Req 1.2, 1.3, 1.4). */
const CONTENT_ENTRIES = ["index.html", "en", "fr", "js", "assets"];

/** Directories whose files are enumerated as manifest dependencies. */
const DEPENDENCY_DIRS = ["en", "fr", "js", "assets"];

/**
 * Recursively copy a file or directory tree from src to dest.
 * Creates parent directories as needed.
 * @param {string} src
 * @param {string} dest
 */
async function copyRecursive(src, dest) {
  const stat = await fs.stat(src);
  if (stat.isDirectory()) {
    await fs.mkdir(dest, { recursive: true });
    const entries = await fs.readdir(src);
    for (const entry of entries) {
      await copyRecursive(path.join(src, entry), path.join(dest, entry));
    }
  } else {
    await fs.mkdir(path.dirname(dest), { recursive: true });
    await fs.copyFile(src, dest);
  }
}

/**
 * Recursively list files under dir, returning POSIX-style paths relative to baseDir.
 * Directories themselves are not emitted — only the files they contain.
 * @param {string} dir       Absolute directory to walk.
 * @param {string} baseDir   Absolute base the returned paths are relative to.
 * @returns {Promise<string[]>}
 */
async function listFilesRelative(dir, baseDir) {
  const out = [];
  let entries;
  try {
    entries = await fs.readdir(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const entry of entries) {
    const abs = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      out.push(...(await listFilesRelative(abs, baseDir)));
    } else {
      out.push(path.relative(baseDir, abs).split(path.sep).join("/"));
    }
  }
  return out;
}

/**
 * Clean/create outDir, then copy index.html, en/, fr/, js/, assets/ from srcDir.
 * Idempotent: the output directory is removed first so stale files never linger.
 * (Req 1.1, 1.2, 1.3, 1.4)
 * @param {string} srcDir  Absolute source course directory.
 * @param {string} outDir  Absolute output package directory.
 */
async function copyCourseContent(srcDir, outDir) {
  await fs.rm(outDir, { recursive: true, force: true });
  await fs.mkdir(outDir, { recursive: true });

  for (const entry of CONTENT_ENTRIES) {
    const src = path.join(srcDir, entry);
    try {
      await fs.access(src);
    } catch {
      throw new Error(`Missing required course content: ${entry} (looked in ${srcDir})`);
    }
    await copyRecursive(src, path.join(outDir, entry));
  }
}

/**
 * Ensure the SCORM runtime (js/scorm/*) is present in the copied js/.
 * copyCourseContent already copies js/ wholesale; this step verifies the runtime
 * actually made it into the package and fails loudly if it is missing. (Req 1.4)
 * @param {string} srcDir
 * @param {string} outDir
 */
async function injectRuntime(srcDir, outDir) {
  const srcScormDir = path.join(srcDir, "js", "scorm");
  const outScormDir = path.join(outDir, "js", "scorm");

  // If the runtime was not copied (e.g. js/ lacked scorm/), copy it explicitly.
  let present = false;
  try {
    const stat = await fs.stat(outScormDir);
    present = stat.isDirectory();
  } catch {
    present = false;
  }

  if (!present) {
    try {
      await fs.access(srcScormDir);
    } catch {
      throw new Error(`SCORM runtime not found at ${srcScormDir}`);
    }
    await copyRecursive(srcScormDir, outScormDir);
  }

  const files = await listFilesRelative(outScormDir, outDir);
  if (files.length === 0) {
    throw new Error("SCORM runtime (js/scorm/*) is empty in the output package");
  }
}

/** Marker identifying an already-injected bootstrap script tag (idempotency check). */
const BOOTSTRAP_SRC_MARKER = "js/scorm/scorm-bootstrap.js";

/** HTML pages that receive the bootstrap tag, relative to outDir, with their folder depth. */
const BOOTSTRAP_PAGES = [
  { file: "index.html", depth: 0 },
  // en/ and fr/ lesson pages are discovered dynamically (depth 1).
];

/**
 * Build the bootstrap <script> tag for a page at the given folder depth.
 * Root (depth 0) → "js/scorm/scorm-bootstrap.js"; a page one folder deep
 * (en/, fr/) → "../js/scorm/scorm-bootstrap.js". (Req 1.4, 6.3)
 * @param {number} depth  Number of folders between the page and outDir root.
 * @returns {string}
 */
function bootstrapTagForDepth(depth) {
  const prefix = depth > 0 ? "../".repeat(depth) : "";
  return `<script type="module" src="${prefix}${BOOTSTRAP_SRC_MARKER}"></script>`;
}

/**
 * Insert the bootstrap tag into a single HTML string, before </body> (or </head>
 * as a fallback). Idempotent: if a scorm-bootstrap.js script tag is already present
 * the HTML is returned unchanged. Returns null when no suitable insertion point
 * exists so the caller can skip the file.
 * @param {string} html
 * @param {number} depth
 * @returns {string|null}
 */
function injectBootstrapIntoHtml(html, depth) {
  if (html.includes(BOOTSTRAP_SRC_MARKER)) {
    return html; // already injected — leave untouched (idempotent)
  }

  const tag = bootstrapTagForDepth(depth);
  const bodyIdx = html.lastIndexOf("</body>");
  if (bodyIdx !== -1) {
    return `${html.slice(0, bodyIdx)}    ${tag}\n${html.slice(bodyIdx)}`;
  }

  const headIdx = html.lastIndexOf("</head>");
  if (headIdx !== -1) {
    return `${html.slice(0, headIdx)}    ${tag}\n${html.slice(headIdx)}`;
  }

  return null; // no </body> or </head> — nothing to anchor to
}

/**
 * Inject the single SCORM bootstrap <script type="module"> tag into the copied
 * lesson/index templates in outDir ONLY (source skillhub/ files are never touched).
 * Operates on the root index.html (depth 0) and every .html page under en/ and fr/
 * (depth 1), computing the correct root-relative path per page depth. Injection is
 * idempotent — a page that already references scorm-bootstrap.js is left unchanged,
 * so re-running the build never duplicates the tag. (Req 1.4, 6.3)
 * @param {string} outDir
 * @returns {Promise<string[]>} POSIX-relative paths of pages that received the tag.
 */
async function injectBootstrapScript(outDir) {
  const pages = [...BOOTSTRAP_PAGES];

  // Discover lesson/index HTML pages inside en/ and fr/ (depth 1).
  for (const locale of ["en", "fr"]) {
    const localeDir = path.join(outDir, locale);
    let entries;
    try {
      entries = await fs.readdir(localeDir, { withFileTypes: true });
    } catch {
      continue; // locale folder absent — nothing to inject there
    }
    for (const entry of entries) {
      if (entry.isFile() && entry.name.toLowerCase().endsWith(".html")) {
        pages.push({ file: `${locale}/${entry.name}`, depth: 1 });
      }
    }
  }

  const injected = [];
  for (const { file, depth } of pages) {
    const abs = path.join(outDir, file);
    let html;
    try {
      html = await fs.readFile(abs, "utf8");
    } catch {
      continue; // page not present in the package — skip
    }

    const alreadyPresent = html.includes(BOOTSTRAP_SRC_MARKER);
    const next = injectBootstrapIntoHtml(html, depth);
    if (next !== null && next !== html) {
      await fs.writeFile(abs, next, "utf8");
    }
    if (!alreadyPresent && next !== null && next !== html) {
      injected.push(file);
    }
  }

  return injected;
}

/**
 * Copy the four SCORM 1.2 schema templates to the package root. (Req 2.4)
 * @param {string} outDir
 */
async function writeSchemaFiles(outDir) {
  for (const file of SCHEMA_FILES) {
    const src = path.join(TEMPLATES_DIR, file);
    try {
      await fs.access(src);
    } catch {
      throw new Error(`Missing schema template: ${file} (looked in ${TEMPLATES_DIR})`);
    }
    await fs.copyFile(src, path.join(outDir, file));
  }
}

/**
 * Exact SCORM metadata for the original skillhub package. Preserved verbatim so
 * the shipped scorm/skillhub_scorm artifact and its tests stay byte-identical.
 * skillhub's title is a product name, not a title-cased slug, hence this special
 * case rather than the generic derivation below.
 */
const SKILLHUB_METADATA = {
  identifier: "SKILLHUB_SCORM12",
  orgId: "ORG-SKILLHUB",
  itemId: "ITEM-SKILLHUB",
  resId: "RES-SKILLHUB",
  title: "Agentic AI OPCP Labs - SkillHub",
};

/**
 * Split a lab folder name into lowercase word tokens, treating hyphens,
 * underscores, and whitespace as separators and dropping empty tokens.
 * @param {string} labName
 * @returns {string[]}
 */
function tokenizeLabName(labName) {
  return String(labName)
    .trim()
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map((t) => t.toLowerCase());
}

/**
 * Derive the SCORM manifest metadata for a lab from its folder name. (Req: auto
 * metadata derivation.) The "skillhub" lab is a documented special case that
 * returns the original product-name metadata verbatim; every other lab uses the
 * generic slug convention:
 *   identifier → UPPER_SNAKE(name) + "_SCORM12"   ("trace-reading" → "TRACE_READING_SCORM12")
 *   orgId/itemId/resId → "ORG-/ITEM-/RES-" + UPPER-DASH(name)  ("ORG-TRACE-READING")
 *   title → Title-Cased words                      ("Trace Reading")
 * Pure: no filesystem access.
 * @param {string} labName  The lab folder's basename.
 * @returns {{identifier: string, orgId: string, itemId: string, resId: string, title: string}}
 */
function deriveLabMetadata(labName) {
  const tokens = tokenizeLabName(labName);
  if (tokens.join("-") === "skillhub") {
    return { ...SKILLHUB_METADATA };
  }
  if (tokens.length === 0) {
    throw new Error(`Cannot derive SCORM metadata from empty lab name: ${JSON.stringify(labName)}`);
  }
  const upperSnake = tokens.map((t) => t.toUpperCase()).join("_");
  const upperDash = tokens.map((t) => t.toUpperCase()).join("-");
  const title = tokens.map((t) => t.charAt(0).toUpperCase() + t.slice(1)).join(" ");
  return {
    identifier: `${upperSnake}_SCORM12`,
    orgId: `ORG-${upperDash}`,
    itemId: `ITEM-${upperDash}`,
    resId: `RES-${upperDash}`,
    title,
  };
}

/**
 * Render the imsmanifest.xml content from a model describing the resource files.
 * Single organization → single item → single resource referencing index.html,
 * schemaversion 1.2, scormtype "sco", masteryscore 100, with dependency files
 * enumerated for en/, fr/, js/, assets/. (Req 2.1, 2.2, 2.3, 2.5, 1.4, 1.5)
 *
 * The four manifest identifiers and both <title> tags come from model.meta; when
 * omitted they default to the skillhub metadata so legacy callers are unaffected.
 * @param {{ files: string[], meta?: {identifier: string, orgId: string, itemId: string, resId: string, title: string} }} model
 * @returns {string}
 */
function renderManifest(model) {
  const meta = model.meta || SKILLHUB_METADATA;
  const fileEls = model.files
    .map((href) => `      <file href="${href}"/>`)
    .join("\n");

  return `<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="${meta.identifier}" version="1.0"
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
  <organizations default="${meta.orgId}">
    <organization identifier="${meta.orgId}">
      <title>${meta.title}</title>
      <item identifier="${meta.itemId}" identifierref="${meta.resId}" isvisible="true">
        <title>${meta.title}</title>
        <adlcp:masteryscore>100</adlcp:masteryscore>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="${meta.resId}" type="webcontent"
              adlcp:scormtype="sco" href="index.html">
      <file href="index.html"/>
${fileEls}
    </resource>
  </resources>
</manifest>
`;
}

/**
 * Emit imsmanifest.xml at the package root. If no model is supplied, enumerate the
 * dependency files from the copied en/, fr/, js/, assets/ trees. (Req 2.1–2.3, 2.5)
 * @param {string} outDir
 * @param {{ files?: string[], meta?: {identifier: string, orgId: string, itemId: string, resId: string, title: string} }} [model]
 * @returns {Promise<string>} the manifest's absolute path.
 */
async function writeManifest(outDir, model) {
  let files = model && model.files;
  if (!files) {
    files = [];
    for (const dir of DEPENDENCY_DIRS) {
      files.push(...(await listFilesRelative(path.join(outDir, dir), outDir)));
    }
    files.sort();
  }
  const xml = renderManifest({ files, meta: model && model.meta });
  const manifestPath = path.join(outDir, "imsmanifest.xml");
  await fs.writeFile(manifestPath, xml, "utf8");
  return manifestPath;
}

/**
 * Assemble the SCORM 1.2 package.
 * @param {object} [opts]
 * @param {string} [opts.srcDir="skillhub"]              Source course dir (resolved against repo root if relative).
 * @param {string} [opts.outDir="scorm/skillhub_scorm"]  Output package dir (resolved against repo root if relative).
 * @param {string} [opts.labName]                        Lab name for metadata; defaults to srcDir basename.
 * @returns {Promise<{outDir: string, files: string[], labName: string, meta: object}>}
 */
export async function buildScormPackage({
  srcDir = "skillhub",
  outDir = "scorm/skillhub_scorm",
  labName,
} = {}) {
  const absSrc = path.isAbsolute(srcDir) ? srcDir : path.resolve(REPO_ROOT, srcDir);
  const absOut = path.isAbsolute(outDir) ? outDir : path.resolve(REPO_ROOT, outDir);

  // Derive per-lab SCORM metadata from the lab name (defaulting to the source
  // folder's basename, e.g. "skillhub"), so the manifest identifiers and titles
  // are specific to each lab. (Req: auto metadata derivation.)
  const resolvedLabName = labName || path.basename(absSrc);
  const meta = deriveLabMetadata(resolvedLabName);

  // 1. Clean/create output + copy course content (index.html, en/, fr/, js/, assets/).
  await copyCourseContent(absSrc, absOut);

  // 2. Ensure the SCORM runtime (js/scorm/*) is present in the copied js/.
  await injectRuntime(absSrc, absOut);

  // 2b. Wire the single bootstrap <script> tag into the copied HTML pages
  //     (outDir only — source skillhub/ files are never modified). Idempotent.
  await injectBootstrapScript(absOut);

  // 3. Copy the four SCORM 1.2 schema templates to the package root.
  await writeSchemaFiles(absOut);

  // 4. Generate imsmanifest.xml at the package root with the derived metadata.
  await writeManifest(absOut, { meta });

  // Final listing of everything in the package, relative + POSIX-style.
  const files = (await listFilesRelative(absOut, absOut)).sort();

  return { outDir: absOut, files, labName: resolvedLabName, meta };
}

/** Top-level sibling directories that are never lab sites. */
const NON_SITE_DIRS = new Set([
  "node_modules", ".git", "scorm", "labs", "scripts", "templates",
  "shared", "src", "conf", "nginx", "deliverables", "docs", ".venv",
]);

/** Structural markers every lab site must contain to be recognized. */
const SITE_MARKERS = ["index.html", "en", "fr", "js", "assets"];

/**
 * Return true if dir contains all of SITE_MARKERS with the expected kinds
 * (index.html a file; en/fr/js/assets directories).
 * @param {string} dir
 * @returns {Promise<boolean>}
 */
async function looksLikeLabSite(dir) {
  for (const marker of SITE_MARKERS) {
    const abs = path.join(dir, marker);
    let stat;
    try {
      stat = await fs.stat(abs);
    } catch {
      return false;
    }
    const wantDir = marker !== "index.html";
    if (wantDir ? !stat.isDirectory() : !stat.isFile()) {
      return false;
    }
  }
  return true;
}

/**
 * Discover top-level sibling lab sites under repoRoot. A directory qualifies when
 * it is not a known non-site dir, is not a dotfile/dir, and structurally matches
 * skillhub's shape (index.html + en/ + fr/ + js/ + assets/). Matching is
 * structural (not an allowlist) so new sibling sites are picked up automatically.
 * @param {string} [repoRoot=REPO_ROOT]
 * @returns {Promise<string[]>} sorted lab-site directory names.
 */
async function discoverLabSites(repoRoot = REPO_ROOT) {
  let entries;
  try {
    entries = await fs.readdir(repoRoot, { withFileTypes: true });
  } catch {
    return [];
  }
  const sites = [];
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const name = entry.name;
    if (name.startsWith(".")) continue;
    if (NON_SITE_DIRS.has(name)) continue;
    if (await looksLikeLabSite(path.join(repoRoot, name))) {
      sites.push(name);
    }
  }
  sites.sort();
  return sites;
}

/**
 * Build SCORM packages for every discovered sibling lab site into
 * scorm/<lab>_scorm/. Each lab is built independently; a failure is captured and
 * reported but does not abort the remaining labs. (Req: multi-lab driver.)
 * @param {object} [opts]
 * @param {string} [opts.repoRoot=REPO_ROOT]
 * @returns {Promise<Array<{lab: string, outDir?: string, fileCount?: number, error?: string}>>}
 */
async function buildAllScormPackages({ repoRoot = REPO_ROOT } = {}) {
  const sites = await discoverLabSites(repoRoot);
  const results = [];
  for (const lab of sites) {
    try {
      const { outDir, files } = await buildScormPackage({
        srcDir: path.join(repoRoot, lab),
        outDir: path.join(repoRoot, "scorm", `${lab}_scorm`),
        labName: lab,
      });
      results.push({ lab, outDir, fileCount: files.length });
    } catch (err) {
      results.push({ lab, error: err && err.message ? err.message : String(err) });
    }
  }
  return results;
}

// Expose internal steps for individual unit testing (Req: individually testable steps).
export {
  copyCourseContent,
  injectRuntime,
  injectBootstrapScript,
  injectBootstrapIntoHtml,
  bootstrapTagForDepth,
  writeSchemaFiles,
  writeManifest,
  renderManifest,
  deriveLabMetadata,
  discoverLabSites,
  buildAllScormPackages,
  listFilesRelative,
  SCHEMA_FILES,
  CONTENT_ENTRIES,
  BOOTSTRAP_SRC_MARKER,
};

/**
 * CLI entry point. Supported invocations:
 *   node build-scorm.mjs            → build skillhub into scorm/skillhub_scorm (default, unchanged)
 *   node build-scorm.mjs <labName>  → build that sibling lab into scorm/<labName>_scorm
 *   node build-scorm.mjs --all      → build every discovered sibling lab site
 */
async function runCli(argv) {
  const args = argv.filter((a) => a !== "");
  if (args.includes("--all")) {
    const results = await buildAllScormPackages();
    let failed = 0;
    for (const r of results) {
      if (r.error) {
        failed++;
        console.error(`  ✗ ${r.lab}: ${r.error}`);
      } else {
        console.log(`  ✓ ${r.lab} → ${r.outDir} (${r.fileCount} files)`);
      }
    }
    console.log(`Built ${results.length - failed}/${results.length} SCORM package(s).`);
    if (failed > 0) {
      process.exitCode = 1;
    }
    return;
  }

  const positional = args.find((a) => !a.startsWith("-"));
  if (positional) {
    const { outDir, files } = await buildScormPackage({
      srcDir: path.join(REPO_ROOT, positional),
      outDir: path.join(REPO_ROOT, "scorm", `${positional}_scorm`),
      labName: positional,
    });
    console.log(`SCORM 1.2 package built at: ${outDir}`);
    console.log(`${files.length} files written.`);
    return;
  }

  // No args → preserve the original default behavior exactly.
  const { outDir, files } = await buildScormPackage();
  console.log(`SCORM 1.2 package built at: ${outDir}`);
  console.log(`${files.length} files written.`);
}

// Run as a CLI when invoked directly: `node scripts/build-scorm.mjs`.
if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  runCli(process.argv.slice(2)).catch((err) => {
    console.error("SCORM build failed:", err);
    process.exitCode = 1;
  });
}
