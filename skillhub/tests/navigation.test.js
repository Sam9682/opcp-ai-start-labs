import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  initNavigation,
  renderSidebar,
  initHamburgerMenu,
  navigateToLesson,
} from '../js/navigation.js';
import { lessons } from '../js/lessons.js';

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] ?? null,
    setItem: (key, value) => { store[key] = String(value); },
    removeItem: (key) => { delete store[key]; },
    clear: () => { store = {}; },
    get length() { return Object.keys(store).length; },
    key: (i) => Object.keys(store)[i] ?? null,
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('Navigation Module', () => {
  beforeEach(() => {
    localStorageMock.clear();
    document.body.innerHTML = '';
    // Reset location
    delete window.location;
    window.location = { href: '', pathname: '/en/index.html' };
  });

  describe('renderSidebar()', () => {
    it('renders lessons grouped by difficulty', () => {
      const container = document.createElement('div');
      container.className = 'sidebar';
      document.body.appendChild(container);

      renderSidebar(container, lessons, []);

      const sections = container.querySelectorAll('.sidebar-section');
      expect(sections.length).toBe(3); // beginner, intermediate, advanced

      const titles = container.querySelectorAll('.sidebar-section-title');
      expect(titles[0].textContent).toBe('Beginner');
      expect(titles[1].textContent).toBe('Intermediate');
      expect(titles[2].textContent).toBe('Advanced');
    });

    it('shows correct number of lessons per difficulty group', () => {
      const container = document.createElement('div');
      document.body.appendChild(container);

      renderSidebar(container, lessons, []);

      const navLists = container.querySelectorAll('.sidebar-nav');
      // beginner: 4 lessons
      expect(navLists[0].querySelectorAll('li').length).toBe(4);
      // intermediate: 4 lessons
      expect(navLists[1].querySelectorAll('li').length).toBe(4);
      // advanced: 1 lesson
      expect(navLists[2].querySelectorAll('li').length).toBe(1);
    });

    it('marks completed lessons with "completed" CSS class', () => {
      const container = document.createElement('div');
      document.body.appendChild(container);

      const completedIds = ['install-bare-metal', 'adding-applications'];
      renderSidebar(container, lessons, completedIds);

      const completedLinks = container.querySelectorAll('a.completed');
      expect(completedLinks.length).toBe(2);
    });

    it('adds checkmark aria-label to completed lessons', () => {
      const container = document.createElement('div');
      document.body.appendChild(container);

      renderSidebar(container, lessons, ['install-bare-metal']);

      const completedLink = container.querySelector('a.completed');
      expect(completedLink).not.toBeNull();
      expect(completedLink.getAttribute('aria-label')).toContain('completed');
    });

    it('does not mark uncompleted lessons with "completed" class', () => {
      const container = document.createElement('div');
      document.body.appendChild(container);

      renderSidebar(container, lessons, ['install-bare-metal']);

      const allLinks = container.querySelectorAll('a[data-lesson-id]');
      const nonCompleted = Array.from(allLinks).filter(
        (link) => !link.classList.contains('completed')
      );
      expect(nonCompleted.length).toBe(lessons.length - 1);
    });

    it('uses localStorage progress when progressData does not include a lesson', () => {
      // Mark a lesson complete in localStorage
      localStorageMock.setItem('skillhub_lesson_complete_mig-gpu', 'true');

      const container = document.createElement('div');
      document.body.appendChild(container);

      renderSidebar(container, lessons, []);

      const migLink = container.querySelector('a[data-lesson-id="mig-gpu"]');
      expect(migLink.classList.contains('completed')).toBe(true);
    });

    it('generates correct lesson URLs with locale', () => {
      const container = document.createElement('div');
      document.body.appendChild(container);

      renderSidebar(container, lessons, []);

      const firstLink = container.querySelector('a[data-slug="install-bare-metal"]');
      expect(firstLink.getAttribute('href')).toBe('/en/install-bare-metal.html');
    });

    it('renders French titles when locale is fr', () => {
      localStorageMock.setItem('skillhub-locale', 'fr');

      const container = document.createElement('div');
      document.body.appendChild(container);

      renderSidebar(container, lessons, []);

      const titles = container.querySelectorAll('.sidebar-section-title');
      expect(titles[0].textContent).toBe('Débutant');
      expect(titles[1].textContent).toBe('Intermédiaire');
      expect(titles[2].textContent).toBe('Avancé');
    });

    it('marks active lesson based on current URL', () => {
      window.location.pathname = '/en/install-bare-metal.html';

      const container = document.createElement('div');
      document.body.appendChild(container);

      renderSidebar(container, lessons, []);

      const activeLink = container.querySelector('a.active');
      expect(activeLink).not.toBeNull();
      expect(activeLink.getAttribute('data-slug')).toBe('install-bare-metal');
      expect(activeLink.getAttribute('aria-current')).toBe('page');
    });

    it('handles empty lessons array without error', () => {
      const container = document.createElement('div');
      document.body.appendChild(container);

      renderSidebar(container, [], []);

      const sections = container.querySelectorAll('.sidebar-section');
      expect(sections.length).toBe(0);
    });
  });

  describe('initHamburgerMenu()', () => {
    it('toggles sidebar open class on hamburger click', () => {
      document.body.innerHTML = `
        <button class="hamburger-btn"><span></span><span></span><span></span></button>
        <div class="sidebar"></div>
      `;

      initHamburgerMenu();

      const btn = document.querySelector('.hamburger-btn');
      const sidebar = document.querySelector('.sidebar');

      btn.click();
      expect(sidebar.classList.contains('open')).toBe(true);
      expect(btn.getAttribute('aria-expanded')).toBe('true');

      btn.click();
      expect(sidebar.classList.contains('open')).toBe(false);
      expect(btn.getAttribute('aria-expanded')).toBe('false');
    });

    it('closes sidebar when clicking outside', () => {
      document.body.innerHTML = `
        <button class="hamburger-btn"><span></span><span></span><span></span></button>
        <div class="sidebar"></div>
        <div class="main-content"></div>
      `;

      initHamburgerMenu();

      const sidebar = document.querySelector('.sidebar');
      const mainContent = document.querySelector('.main-content');

      // Open the sidebar first
      const btn = document.querySelector('.hamburger-btn');
      btn.click();
      expect(sidebar.classList.contains('open')).toBe(true);

      // Click outside - simulate a new click event on the document/main content
      const clickEvent = new MouseEvent('click', { bubbles: true });
      mainContent.dispatchEvent(clickEvent);
      expect(sidebar.classList.contains('open')).toBe(false);
    });

    it('closes sidebar on Escape key', () => {
      document.body.innerHTML = `
        <button class="hamburger-btn"><span></span><span></span><span></span></button>
        <div class="sidebar"></div>
      `;

      initHamburgerMenu();

      const btn = document.querySelector('.hamburger-btn');
      const sidebar = document.querySelector('.sidebar');

      // Open sidebar
      btn.click();
      expect(sidebar.classList.contains('open')).toBe(true);

      // Press Escape
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
      expect(sidebar.classList.contains('open')).toBe(false);
    });

    it('sets correct ARIA attributes on hamburger button', () => {
      document.body.innerHTML = `
        <button class="hamburger-btn"><span></span><span></span><span></span></button>
        <div class="sidebar"></div>
      `;

      initHamburgerMenu();

      const btn = document.querySelector('.hamburger-btn');
      expect(btn.getAttribute('aria-label')).toBe('Toggle navigation menu');
      expect(btn.getAttribute('aria-expanded')).toBe('false');
      expect(btn.getAttribute('aria-controls')).toBe('sidebar-nav');
    });

    it('does not throw when no hamburger button exists', () => {
      document.body.innerHTML = '<div class="sidebar"></div>';
      expect(() => initHamburgerMenu()).not.toThrow();
    });

    it('does not throw when no sidebar exists', () => {
      document.body.innerHTML = '<button class="hamburger-btn"></button>';
      expect(() => initHamburgerMenu()).not.toThrow();
    });
  });

  describe('navigateToLesson()', () => {
    it('navigates to correct URL with given locale', () => {
      navigateToLesson('install-bare-metal', 'en');
      expect(window.location.href).toBe('/en/install-bare-metal.html');
    });

    it('navigates to correct URL with fr locale', () => {
      navigateToLesson('adding-applications', 'fr');
      expect(window.location.href).toBe('/fr/adding-applications.html');
    });

    it('uses detected locale when invalid locale is provided', () => {
      // No stored locale preference, defaults to "en"
      navigateToLesson('mig-gpu', 'invalid');
      expect(window.location.href).toBe('/en/mig-gpu.html');
    });

    it('uses stored locale preference when locale is invalid', () => {
      localStorageMock.setItem('skillhub-locale', 'fr');
      navigateToLesson('making-backups', 'invalid');
      expect(window.location.href).toBe('/fr/making-backups.html');
    });
  });

  describe('initNavigation()', () => {
    it('renders sidebar and sets up hamburger menu', () => {
      document.body.innerHTML = `
        <button class="hamburger-btn"><span></span><span></span><span></span></button>
        <div class="sidebar"></div>
      `;

      initNavigation(lessons, ['install-bare-metal']);

      const sidebar = document.querySelector('.sidebar');
      const sections = sidebar.querySelectorAll('.sidebar-section');
      expect(sections.length).toBe(3);

      // Verify hamburger is set up
      const btn = document.querySelector('.hamburger-btn');
      expect(btn.getAttribute('aria-label')).toBe('Toggle navigation menu');
    });

    it('works when sidebar element is not present', () => {
      document.body.innerHTML = '<div class="main-content"></div>';
      expect(() => initNavigation(lessons, [])).not.toThrow();
    });
  });
});
