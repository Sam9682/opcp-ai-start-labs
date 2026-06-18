/**
 * Navigation Module - Sidebar navigation, hamburger menu, and lesson routing.
 *
 * Groups lessons by difficulty in the sidebar.
 * Provides hamburger menu toggle for viewports ≤ 768px.
 * Marks completed lessons with checkmark icon and "completed" CSS class.
 *
 * Validates: Requirements 1.4, 2.2
 *
 * @module navigation
 */

import { isLessonComplete } from './progress.js';
import { detectLocale } from './i18n.js';

/** @type {string[]} Difficulty levels in display order */
const DIFFICULTY_ORDER = ['beginner', 'intermediate', 'advanced'];

/** @type {Record<string, {en: string, fr: string}>} Section titles per difficulty */
const SECTION_TITLES = {
  beginner: { en: 'Beginner', fr: 'Débutant' },
  intermediate: { en: 'Intermediate', fr: 'Intermédiaire' },
  advanced: { en: 'Advanced', fr: 'Avancé' }
};

/**
 * Initialize navigation: render sidebar and set up hamburger menu.
 *
 * @param {import('./lessons.js').Lesson[]} lessonsData - Array of all lessons
 * @param {string[]} progressData - Array of completed lesson IDs
 */
export function initNavigation(lessonsData, progressData) {
  const sidebarContainer = document.querySelector('.sidebar');
  if (sidebarContainer) {
    renderSidebar(sidebarContainer, lessonsData, progressData);
  }
  initHamburgerMenu();
}

/**
 * Render the sidebar content grouped by difficulty.
 * Shows checkmark icon and "completed" CSS class for completed lessons.
 *
 * @param {HTMLElement} container - The sidebar container element
 * @param {import('./lessons.js').Lesson[]} lessons - Array of all lessons
 * @param {string[]} progress - Array of completed lesson IDs
 */
export function renderSidebar(container, lessons, progress) {
  const locale = detectLocale();
  const completedSet = new Set(progress);

  // Clear existing sidebar content
  container.innerHTML = '';

  for (const difficulty of DIFFICULTY_ORDER) {
    const groupLessons = lessons.filter((l) => l.difficulty === difficulty);
    if (groupLessons.length === 0) {
      continue;
    }

    // Create section
    const section = document.createElement('div');
    section.className = 'sidebar-section';

    // Section title
    const title = document.createElement('h3');
    title.className = 'sidebar-section-title';
    title.textContent = SECTION_TITLES[difficulty][locale] || SECTION_TITLES[difficulty].en;
    section.appendChild(title);

    // Navigation list
    const nav = document.createElement('ul');
    nav.className = 'sidebar-nav';
    nav.setAttribute('role', 'list');

    for (const lesson of groupLessons) {
      const li = document.createElement('li');
      const link = document.createElement('a');

      link.href = buildLessonUrl(lesson.slug, locale);
      link.textContent = lesson.title[locale] || lesson.title.en;
      link.setAttribute('data-lesson-id', lesson.id);
      link.setAttribute('data-slug', lesson.slug);

      // Mark completed lessons
      const completed = completedSet.has(lesson.id) || isLessonComplete(lesson.id);
      if (completed) {
        link.classList.add('completed');
        link.setAttribute('aria-label',
          `${lesson.title[locale] || lesson.title.en} (${locale === 'fr' ? 'terminé' : 'completed'})`
        );
      }

      // Mark active lesson based on current URL
      if (isActiveLessonLink(lesson.slug)) {
        link.classList.add('active');
        link.setAttribute('aria-current', 'page');
      }

      link.addEventListener('click', (e) => {
        e.preventDefault();
        navigateToLesson(lesson.slug, locale);
      });

      li.appendChild(link);
      nav.appendChild(li);
    }

    section.appendChild(nav);
    container.appendChild(section);
  }
}

/**
 * Initialize the hamburger menu toggle for mobile viewports (≤ 768px).
 * Toggles the sidebar open/closed state.
 */
export function initHamburgerMenu() {
  const hamburgerBtn = document.querySelector('.hamburger-btn');
  const sidebar = document.querySelector('.sidebar');

  if (!hamburgerBtn || !sidebar) {
    return;
  }

  hamburgerBtn.setAttribute('aria-label', 'Toggle navigation menu');
  hamburgerBtn.setAttribute('aria-expanded', 'false');
  hamburgerBtn.setAttribute('aria-controls', 'sidebar-nav');
  sidebar.setAttribute('id', 'sidebar-nav');

  hamburgerBtn.addEventListener('click', () => {
    const isOpen = sidebar.classList.toggle('open');
    hamburgerBtn.setAttribute('aria-expanded', String(isOpen));
  });

  // Close sidebar when clicking outside on mobile
  document.addEventListener('click', (e) => {
    if (
      sidebar.classList.contains('open') &&
      !sidebar.contains(e.target) &&
      !hamburgerBtn.contains(e.target)
    ) {
      sidebar.classList.remove('open');
      hamburgerBtn.setAttribute('aria-expanded', 'false');
    }
  });

  // Close sidebar on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar.classList.contains('open')) {
      sidebar.classList.remove('open');
      hamburgerBtn.setAttribute('aria-expanded', 'false');
      hamburgerBtn.focus();
    }
  });
}

/**
 * Navigate to a lesson page by building the URL from slug and locale.
 *
 * @param {string} slug - The lesson slug (e.g., "install-bare-metal")
 * @param {string} locale - The locale ("en" or "fr")
 */
export function navigateToLesson(slug, locale) {
  const effectiveLocale = (locale === 'en' || locale === 'fr') ? locale : detectLocale();
  const url = buildLessonUrl(slug, effectiveLocale);
  window.location.href = url;
}

/**
 * Build the URL path for a lesson.
 *
 * @param {string} slug - The lesson slug
 * @param {string} locale - The locale ("en" or "fr")
 * @returns {string} The URL path (e.g., "/en/install-bare-metal.html")
 */
function buildLessonUrl(slug, locale) {
  return `/${locale}/${slug}.html`;
}

/**
 * Check if a lesson slug matches the current page URL.
 *
 * @param {string} slug - The lesson slug to check
 * @returns {boolean} True if the current page is for this lesson
 */
function isActiveLessonLink(slug) {
  if (typeof window === 'undefined') {
    return false;
  }
  const path = window.location.pathname;
  return path.includes(`/${slug}.html`) || path.endsWith(`/${slug}`);
}
