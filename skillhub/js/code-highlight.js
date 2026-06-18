/**
 * Code_Highlight - Lightweight syntax highlighting for code blocks.
 * Supports: bash, python, javascript, json.
 * No external library dependency.
 *
 * Validates: Requirements 1.8
 */

/**
 * Language-specific keyword and pattern definitions.
 * Each language provides arrays of { pattern, className } entries
 * applied in order (earlier rules take precedence via placeholder protection).
 */
const LANGUAGES = {
  javascript: {
    keywords: [
      'const', 'let', 'var', 'function', 'return', 'if', 'else', 'for',
      'while', 'do', 'switch', 'case', 'break', 'continue', 'new', 'this',
      'class', 'extends', 'import', 'export', 'from', 'default', 'try',
      'catch', 'finally', 'throw', 'async', 'await', 'yield', 'typeof',
      'instanceof', 'in', 'of', 'null', 'undefined', 'true', 'false'
    ],
    patterns: [
      { source: '\\/\\/[^\\n]*', className: 'hljs-comment' },
      { source: '\\/\\*[\\s\\S]*?\\*\\/', className: 'hljs-comment' },
      { source: '"(?:[^"\\\\]|\\\\.)*"|\'(?:[^\'\\\\]|\\\\.)*\'|`(?:[^`\\\\]|\\\\.)*`', className: 'hljs-string' },
      { source: '\\b\\d+(?:\\.\\d+)?\\b', className: 'hljs-number' }
    ]
  },
  python: {
    keywords: [
      'def', 'class', 'return', 'if', 'elif', 'else', 'for', 'while',
      'import', 'from', 'as', 'try', 'except', 'finally', 'raise', 'with',
      'pass', 'break', 'continue', 'and', 'or', 'not', 'in', 'is', 'lambda',
      'yield', 'async', 'await', 'None', 'True', 'False', 'self'
    ],
    patterns: [
      { source: '#[^\\n]*', className: 'hljs-comment' },
      { source: '"""[\\s\\S]*?"""|\'\'\'[\\s\\S]*?\'\'\'', className: 'hljs-string' },
      { source: '"(?:[^"\\\\]|\\\\.)*"|\'(?:[^\'\\\\]|\\\\.)*\'', className: 'hljs-string' },
      { source: '\\b\\d+(?:\\.\\d+)?\\b', className: 'hljs-number' }
    ]
  },
  bash: {
    keywords: [
      'if', 'then', 'else', 'elif', 'fi', 'for', 'while', 'do', 'done',
      'case', 'esac', 'function', 'return', 'exit', 'export', 'source',
      'echo', 'read', 'local', 'declare', 'set', 'unset', 'shift', 'true', 'false'
    ],
    patterns: [
      { source: '#[^\\n]*', className: 'hljs-comment' },
      { source: '"(?:[^"\\\\]|\\\\.)*"|\'[^\']*\'', className: 'hljs-string' },
      { source: '\\b\\d+(?:\\.\\d+)?\\b', className: 'hljs-number' }
    ]
  },
  json: {
    keywords: ['true', 'false', 'null'],
    patterns: [
      { source: '"(?:[^"\\\\]|\\\\.)*"(?=\\s*:)', className: 'hljs-attr' },
      { source: '"(?:[^"\\\\]|\\\\.)*"', className: 'hljs-string' },
      { source: '\\b\\d+(?:\\.\\d+)?\\b', className: 'hljs-number' }
    ]
  }
};

/**
 * Detect language from a <code> element's class list.
 * Looks for patterns like "language-javascript", "lang-python", or bare "bash".
 * @param {Element} codeEl - The code element
 * @returns {string|null} Detected language name or null
 */
function detectLanguage(codeEl) {
  const classes = codeEl.className || '';
  const match = classes.match(/(?:language-|lang-)(\w+)/);
  if (match && LANGUAGES[match[1]]) {
    return match[1];
  }
  // Check bare class names
  for (const lang of Object.keys(LANGUAGES)) {
    if (classes.split(/\s+/).includes(lang)) {
      return lang;
    }
  }
  return null;
}

/**
 * Escape HTML special characters in text.
 * @param {string} text - Raw text
 * @returns {string} HTML-safe text
 */
function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/**
 * Apply syntax highlighting to a code string for a given language.
 * Uses a single-pass tokenizer to avoid conflicts between rules.
 * @param {string} code - The raw code text
 * @param {string} language - The language key
 * @returns {string} HTML string with highlighting spans
 */
export function highlightCode(code, language) {
  const langDef = LANGUAGES[language];
  if (!langDef) {
    return escapeHtml(code);
  }

  // Build a combined regex with each rule in its own capture group
  const classNames = [];
  const parts = [];

  for (const rule of langDef.patterns) {
    parts.push(`(${rule.source})`);
    classNames.push(rule.className);
  }

  if (langDef.keywords.length > 0) {
    parts.push(`(\\b(?:${langDef.keywords.join('|')})\\b)`);
    classNames.push('hljs-keyword');
  }

  if (parts.length === 0) {
    return escapeHtml(code);
  }

  const combined = new RegExp(parts.join('|'), 'g');

  let result = '';
  let lastIndex = 0;

  let match;
  while ((match = combined.exec(code)) !== null) {
    // Append text before this match
    if (match.index > lastIndex) {
      result += escapeHtml(code.slice(lastIndex, match.index));
    }

    const fullMatch = match[0];

    // Determine which rule matched by checking capture groups
    let className = null;
    for (let i = 0; i < classNames.length; i++) {
      if (match[i + 1] !== undefined) {
        className = classNames[i];
        break;
      }
    }

    if (className) {
      result += `<span class="${className}">${escapeHtml(fullMatch)}</span>`;
    } else {
      result += escapeHtml(fullMatch);
    }

    lastIndex = match.index + fullMatch.length;
  }

  // Append remaining text
  if (lastIndex < code.length) {
    result += escapeHtml(code.slice(lastIndex));
  }

  return result;
}

/**
 * Apply syntax highlighting to all <code> elements on the page.
 * Targets <pre><code> blocks and standalone <code> elements with a language class.
 */
export function highlightAll() {
  const codeElements = document.querySelectorAll('pre code, code[class*="language-"], code[class*="lang-"]');

  for (const codeEl of codeElements) {
    // Skip already-highlighted elements
    if (codeEl.dataset.highlighted === 'true') {
      continue;
    }

    const language = detectLanguage(codeEl);
    if (!language) {
      continue;
    }

    const rawCode = codeEl.textContent || '';
    codeEl.innerHTML = highlightCode(rawCode, language);
    codeEl.dataset.highlighted = 'true';
    codeEl.classList.add('hljs');
  }
}
