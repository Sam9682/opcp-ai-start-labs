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
 * Render the imsmanifest.xml content from a model describing the resource files.
 * Single organization → single item → single resource referencing index.html,
 * schemaversion 1.2, scormtype "sco", masteryscore 100, with dependency files
 * enumerated for en/, fr/, js/, assets/. (Req 2.1, 2.2, 2.3, 2.5, 1.4, 1.5)
 * @param {{ files: string[] }} model
 * @returns {string}
 */
function renderManifest(model) {
  const fileEls = model.files
    .map((href) => `      <file href="${href}"/>`)
    .join("\n");

  return `<?xml version="1.0" encoding="UTF-8"?>
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
 * @param {{ files?: string[] }} [model]
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
  const xml = renderManifest({ files });
  const manifestPath = path.join(outDir, "imsmanifest.xml");
  await fs.writeFile(manifestPath, xml, "utf8");
  return manifestPath;
}

/**
 * Assemble the SCORM 1.2 package.
 * @param {object} [opts]
 * @param {string} [opts.srcDir="skillhub"]              Source course dir (resolved against repo root if relative).
 * @param {string} [opts.outDir="scorm/skillhub_scorm"]  Output package dir (resolved against repo root if relative).
 * @returns {Promise<{outDir: string, files: string[]}>}
 */
export async function buildScormPackage({
  srcDir = "skillhub",
  outDir = "scorm/skillhub_scorm",
} = {}) {
  const absSrc = path.isAbsolute(srcDir) ? srcDir : path.resolve(REPO_ROOT, srcDir);
  const absOut = path.isAbsolute(outDir) ? outDir : path.resolve(REPO_ROOT, outDir);

  // 1. Clean/create output + copy course content (index.html, en/, fr/, js/, assets/).
  await copyCourseContent(absSrc, absOut);

  // 2. Ensure the SCORM runtime (js/scorm/*) is present in the copied js/.
  await injectRuntime(absSrc, absOut);

  // 2b. Wire the single bootstrap <script> tag into the copied HTML pages
  //     (outDir only — source skillhub/ files are never modified). Idempotent.
  await injectBootstrapScript(absOut);

  // 3. Copy the four SCORM 1.2 schema templates to the package root.
  await writeSchemaFiles(absOut);

  // 4. Generate imsmanifest.xml at the package root.
  await writeManifest(absOut);

  // Final listing of everything in the package, relative + POSIX-style.
  const files = (await listFilesRelative(absOut, absOut)).sort();

  return { outDir: absOut, files };
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
  listFilesRelative,
  SCHEMA_FILES,
  CONTENT_ENTRIES,
  BOOTSTRAP_SRC_MARKER,
};

// Run as a CLI when invoked directly: `node scripts/build-scorm.mjs`.
if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  buildScormPackage()
    .then(({ outDir, files }) => {
      console.log(`SCORM 1.2 package built at: ${outDir}`);
      console.log(`${files.length} files written.`);
    })
    .catch((err) => {
      console.error("SCORM build failed:", err);
      process.exitCode = 1;
    });
}
