import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  detectLocale,
  switchLocale,
  getStoredLocalePreference,
  setLocalePreference,
} from '../js/i18n.js';

describe('I18n Module', () => {
  beforeEach(() => {
    localStorage.clear();
    // Reset navigator.language to default
    Object.defineProperty(navigator, 'language', {
      value: 'en-US',
      configurable: true,
    });
    Object.defineProperty(navigator, 'languages', {
      value: ['en-US'],
      configurable: true,
    });
  });

  describe('getStoredLocalePreference()', () => {
    it('returns null when no preference is stored', () => {
      expect(getStoredLocalePreference()).toBe(null);
    });

    it('returns "en" when "en" is stored', () => {
      localStorage.setItem('skillhub-locale', 'en');
      expect(getStoredLocalePreference()).toBe('en');
    });

    it('returns "fr" when "fr" is stored', () => {
      localStorage.setItem('skillhub-locale', 'fr');
      expect(getStoredLocalePreference()).toBe('fr');
    });

    it('returns null for invalid stored values', () => {
      localStorage.setItem('skillhub-locale', 'de');
      expect(getStoredLocalePreference()).toBe(null);
    });
  });

  describe('setLocalePreference()', () => {
    it('stores "en" in localStorage', () => {
      setLocalePreference('en');
      expect(localStorage.getItem('skillhub-locale')).toBe('en');
    });

    it('stores "fr" in localStorage', () => {
      setLocalePreference('fr');
      expect(localStorage.getItem('skillhub-locale')).toBe('fr');
    });

    it('normalizes "fr-CA" to "fr"', () => {
      setLocalePreference('fr-CA');
      expect(localStorage.getItem('skillhub-locale')).toBe('fr');
    });

    it('normalizes unknown locales to "en"', () => {
      setLocalePreference('de');
      expect(localStorage.getItem('skillhub-locale')).toBe('en');
    });
  });

  describe('detectLocale()', () => {
    it('returns stored preference when available', () => {
      localStorage.setItem('skillhub-locale', 'fr');
      Object.defineProperty(navigator, 'language', {
        value: 'en-US',
        configurable: true,
      });
      expect(detectLocale()).toBe('fr');
    });

    it('returns "fr" when browser language is French', () => {
      Object.defineProperty(navigator, 'language', {
        value: 'fr-FR',
        configurable: true,
      });
      Object.defineProperty(navigator, 'languages', {
        value: ['fr-FR', 'fr'],
        configurable: true,
      });
      expect(detectLocale()).toBe('fr');
    });

    it('returns "en" when browser language is German (not French)', () => {
      Object.defineProperty(navigator, 'language', {
        value: 'de-DE',
        configurable: true,
      });
      Object.defineProperty(navigator, 'languages', {
        value: ['de-DE', 'de'],
        configurable: true,
      });
      expect(detectLocale()).toBe('en');
    });

    it('returns "en" when browser language is English', () => {
      Object.defineProperty(navigator, 'language', {
        value: 'en-GB',
        configurable: true,
      });
      Object.defineProperty(navigator, 'languages', {
        value: ['en-GB'],
        configurable: true,
      });
      expect(detectLocale()).toBe('en');
    });

    it('stored preference takes priority over browser language', () => {
      localStorage.setItem('skillhub-locale', 'en');
      Object.defineProperty(navigator, 'language', {
        value: 'fr-FR',
        configurable: true,
      });
      Object.defineProperty(navigator, 'languages', {
        value: ['fr-FR'],
        configurable: true,
      });
      expect(detectLocale()).toBe('en');
    });

    it('returns "en" as default when no preference and browser is not French', () => {
      Object.defineProperty(navigator, 'language', {
        value: 'ja-JP',
        configurable: true,
      });
      Object.defineProperty(navigator, 'languages', {
        value: ['ja-JP'],
        configurable: true,
      });
      expect(detectLocale()).toBe('en');
    });
  });

  describe('switchLocale()', () => {
    beforeEach(() => {
      // Mock window.location.href setter and pathname
      delete window.location;
      window.location = {
        pathname: '/en/lesson.html',
        href: '',
      };
    });

    it('persists "fr" and navigates to French locale path', () => {
      switchLocale('fr');
      expect(localStorage.getItem('skillhub-locale')).toBe('fr');
      expect(window.location.href).toBe('/fr/lesson.html');
    });

    it('persists "en" and navigates to English locale path', () => {
      window.location.pathname = '/fr/lesson.html';
      switchLocale('en');
      expect(localStorage.getItem('skillhub-locale')).toBe('en');
      expect(window.location.href).toBe('/en/lesson.html');
    });

    it('handles paths without locale segment', () => {
      window.location.pathname = '/some/other/path';
      switchLocale('fr');
      expect(window.location.href).toBe('/fr/');
    });

    it('normalizes fr-BE to fr and navigates correctly', () => {
      switchLocale('fr-BE');
      expect(localStorage.getItem('skillhub-locale')).toBe('fr');
      expect(window.location.href).toBe('/fr/lesson.html');
    });
  });

  describe('graceful degradation', () => {
    it('detectLocale returns "en" when localStorage throws', () => {
      const originalGetItem = localStorage.getItem;
      localStorage.getItem = () => { throw new Error('SecurityError'); };
      // With no stored preference and English browser, should default to "en"
      expect(detectLocale()).toBe('en');
      localStorage.getItem = originalGetItem;
    });

    it('setLocalePreference does not throw when localStorage is unavailable', () => {
      const originalSetItem = localStorage.setItem;
      localStorage.setItem = () => { throw new Error('QuotaExceededError'); };
      expect(() => setLocalePreference('fr')).not.toThrow();
      localStorage.setItem = originalSetItem;
    });

    it('detectLocale falls back to browser language when localStorage throws', () => {
      const originalGetItem = localStorage.getItem;
      localStorage.getItem = () => { throw new Error('SecurityError'); };
      Object.defineProperty(navigator, 'language', {
        value: 'fr-FR',
        configurable: true,
      });
      Object.defineProperty(navigator, 'languages', {
        value: ['fr-FR'],
        configurable: true,
      });
      expect(detectLocale()).toBe('fr');
      localStorage.getItem = originalGetItem;
    });
  });
});
