import { describe, it, expect, beforeEach, vi } from 'vitest';
import { initApp } from '../js/main.js';

describe('Main Module', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
    localStorage.clear();
  });

  it('initializes without errors when DOM is ready', () => {
    expect(() => initApp()).not.toThrow();
  });

  it('applies code highlighting to code blocks on init', () => {
    document.body.innerHTML = '<pre><code class="language-javascript">const x = 1;</code></pre>';
    initApp();
    const codeEl = document.querySelector('code');
    expect(codeEl.dataset.highlighted).toBe('true');
    expect(codeEl.innerHTML).toContain('<span class="hljs-keyword">const</span>');
  });

  it('updates progress bar if present in DOM', () => {
    document.body.innerHTML = `
      <div class="progress-bar" style="width: 0%" aria-valuenow="0"></div>
      <span class="progress-text">0%</span>
    `;
    initApp();
    // With no completed lessons, percentage should be 0
    const bar = document.querySelector('.progress-bar');
    expect(bar.style.width).toBe('0%');
    expect(bar.getAttribute('aria-valuenow')).toBe('0');
  });

  it('displays correct percentage when lessons are completed', () => {
    // Mark some lessons as complete in localStorage
    localStorage.setItem('skillhub_lesson_complete_install-bare-metal', 'true');
    localStorage.setItem('skillhub_lesson_complete_adding-applications', 'true');

    document.body.innerHTML = `
      <div class="progress-bar" style="width: 0%" aria-valuenow="0"></div>
      <span class="progress-text">0%</span>
    `;
    initApp();
    const bar = document.querySelector('.progress-bar');
    const text = document.querySelector('.progress-text');
    // 2 out of 9 lessons = 22%
    expect(bar.style.width).toBe('22%');
    expect(text.textContent).toBe('22%');
  });

  it('degrades gracefully when progress elements are not in DOM', () => {
    document.body.innerHTML = '<div>No progress bar here</div>';
    expect(() => initApp()).not.toThrow();
  });
});
