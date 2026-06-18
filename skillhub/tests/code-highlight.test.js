import { describe, it, expect, beforeEach } from 'vitest';
import { highlightCode, highlightAll } from '../js/code-highlight.js';

describe('Code Highlight Module', () => {
  describe('highlightCode()', () => {
    describe('JavaScript highlighting', () => {
      it('highlights keywords', () => {
        const result = highlightCode('const x = 5;', 'javascript');
        expect(result).toContain('<span class="hljs-keyword">const</span>');
      });

      it('highlights strings', () => {
        const result = highlightCode('const s = "hello";', 'javascript');
        expect(result).toContain('<span class="hljs-string">"hello"</span>');
      });

      it('highlights single-line comments', () => {
        const result = highlightCode('// a comment', 'javascript');
        expect(result).toContain('<span class="hljs-comment">// a comment</span>');
      });

      it('highlights numbers', () => {
        const result = highlightCode('let x = 42;', 'javascript');
        expect(result).toContain('<span class="hljs-number">42</span>');
      });

      it('highlights multi-line comments', () => {
        const result = highlightCode('/* multi\nline */', 'javascript');
        expect(result).toContain('<span class="hljs-comment">/* multi\nline */</span>');
      });
    });

    describe('Python highlighting', () => {
      it('highlights keywords', () => {
        const result = highlightCode('def hello():', 'python');
        expect(result).toContain('<span class="hljs-keyword">def</span>');
      });

      it('highlights hash comments', () => {
        const result = highlightCode('# comment', 'python');
        expect(result).toContain('<span class="hljs-comment"># comment</span>');
      });

      it('highlights strings', () => {
        const result = highlightCode('x = "world"', 'python');
        expect(result).toContain('<span class="hljs-string">"world"</span>');
      });

      it('highlights numbers', () => {
        const result = highlightCode('x = 3.14', 'python');
        expect(result).toContain('<span class="hljs-number">3.14</span>');
      });
    });

    describe('Bash highlighting', () => {
      it('highlights keywords', () => {
        const result = highlightCode('export PATH=/usr/bin', 'bash');
        expect(result).toContain('<span class="hljs-keyword">export</span>');
      });

      it('highlights comments', () => {
        const result = highlightCode('# setup', 'bash');
        expect(result).toContain('<span class="hljs-comment"># setup</span>');
      });

      it('highlights strings', () => {
        const result = highlightCode('echo "hello"', 'bash');
        expect(result).toContain('<span class="hljs-string">"hello"</span>');
      });
    });

    describe('JSON highlighting', () => {
      it('highlights property keys', () => {
        const result = highlightCode('"name": "value"', 'json');
        expect(result).toContain('hljs-attr');
        expect(result).toContain('"name"');
      });

      it('highlights string values', () => {
        const result = highlightCode('"key": "value"', 'json');
        expect(result).toContain('hljs-string');
        expect(result).toContain('"value"');
      });

      it('highlights numbers', () => {
        const result = highlightCode('"count": 42', 'json');
        expect(result).toContain('<span class="hljs-number">42</span>');
      });

      it('highlights boolean keywords', () => {
        const result = highlightCode('"flag": true', 'json');
        expect(result).toContain('<span class="hljs-keyword">true</span>');
      });
    });

    describe('Edge cases', () => {
      it('returns escaped HTML for unknown languages', () => {
        const result = highlightCode('<script>alert("xss")</script>', 'unknown');
        expect(result).toBe('&lt;script&gt;alert("xss")&lt;/script&gt;');
      });

      it('escapes HTML in code before highlighting', () => {
        const result = highlightCode('if (x < 5) {}', 'javascript');
        expect(result).toContain('&lt;');
        expect(result).not.toContain('<5');
      });

      it('handles empty string', () => {
        const result = highlightCode('', 'javascript');
        expect(result).toBe('');
      });
    });
  });

  describe('highlightAll()', () => {
    beforeEach(() => {
      document.body.innerHTML = '';
    });

    it('highlights code elements with language class', () => {
      document.body.innerHTML = '<pre><code class="language-javascript">const x = 1;</code></pre>';
      highlightAll();
      const codeEl = document.querySelector('code');
      expect(codeEl.innerHTML).toContain('<span class="hljs-keyword">const</span>');
      expect(codeEl.dataset.highlighted).toBe('true');
    });

    it('highlights code elements with lang- prefix', () => {
      document.body.innerHTML = '<pre><code class="lang-python">def foo():</code></pre>';
      highlightAll();
      const codeEl = document.querySelector('code');
      expect(codeEl.innerHTML).toContain('<span class="hljs-keyword">def</span>');
    });

    it('does not re-highlight already highlighted elements', () => {
      document.body.innerHTML = '<pre><code class="language-bash" data-highlighted="true">echo "hi"</code></pre>';
      const originalHtml = document.querySelector('code').innerHTML;
      highlightAll();
      expect(document.querySelector('code').innerHTML).toBe(originalHtml);
    });

    it('skips code elements without a recognized language class', () => {
      document.body.innerHTML = '<pre><code>plain text</code></pre>';
      highlightAll();
      const codeEl = document.querySelector('code');
      expect(codeEl.dataset.highlighted).toBeUndefined();
    });

    it('adds hljs class to highlighted elements', () => {
      document.body.innerHTML = '<pre><code class="language-json">{"a": 1}</code></pre>';
      highlightAll();
      const codeEl = document.querySelector('code');
      expect(codeEl.classList.contains('hljs')).toBe(true);
    });
  });
});
