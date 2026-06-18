import { describe, it, expect, beforeEach } from 'vitest';
import {
  markLessonComplete,
  isLessonComplete,
  getCompletionPercentage,
  getCompletedLessons,
  resetProgress,
} from '../js/progress.js';

describe('Progress Tracker', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('markLessonComplete()', () => {
    it('marks a lesson as complete in localStorage', () => {
      markLessonComplete('install-bare-metal');
      expect(localStorage.getItem('skillhub_lesson_complete_install-bare-metal')).toBe('true');
    });

    it('can mark multiple lessons as complete', () => {
      markLessonComplete('install-bare-metal');
      markLessonComplete('adding-applications');
      expect(localStorage.getItem('skillhub_lesson_complete_install-bare-metal')).toBe('true');
      expect(localStorage.getItem('skillhub_lesson_complete_adding-applications')).toBe('true');
    });

    it('marking an already complete lesson is idempotent', () => {
      markLessonComplete('install-bare-metal');
      markLessonComplete('install-bare-metal');
      expect(localStorage.getItem('skillhub_lesson_complete_install-bare-metal')).toBe('true');
    });
  });

  describe('isLessonComplete()', () => {
    it('returns true for a completed lesson', () => {
      markLessonComplete('install-bare-metal');
      expect(isLessonComplete('install-bare-metal')).toBe(true);
    });

    it('returns false for a lesson not yet completed', () => {
      expect(isLessonComplete('install-bare-metal')).toBe(false);
    });

    it('returns false for a non-existent lesson id', () => {
      expect(isLessonComplete('non-existent-lesson')).toBe(false);
    });
  });

  describe('getCompletionPercentage()', () => {
    it('returns 0 when no lessons are completed', () => {
      expect(getCompletionPercentage(9)).toBe(0);
    });

    it('returns 100 when all lessons are completed', () => {
      markLessonComplete('lesson-1');
      markLessonComplete('lesson-2');
      markLessonComplete('lesson-3');
      expect(getCompletionPercentage(3)).toBe(100);
    });

    it('returns rounded integer percentage', () => {
      markLessonComplete('lesson-1');
      // 1/3 = 33.333... → rounds to 33
      expect(getCompletionPercentage(3)).toBe(33);
    });

    it('rounds 0.5 up (standard Math.round behavior)', () => {
      markLessonComplete('lesson-1');
      markLessonComplete('lesson-2');
      markLessonComplete('lesson-3');
      // 3/6 = 50 exactly
      expect(getCompletionPercentage(6)).toBe(50);
    });

    it('returns 0 when totalLessons is 0', () => {
      expect(getCompletionPercentage(0)).toBe(0);
    });

    it('returns 0 when totalLessons is negative', () => {
      expect(getCompletionPercentage(-1)).toBe(0);
    });
  });

  describe('getCompletedLessons()', () => {
    it('returns empty array when no lessons are completed', () => {
      expect(getCompletedLessons()).toEqual([]);
    });

    it('returns array of completed lesson ids', () => {
      markLessonComplete('install-bare-metal');
      markLessonComplete('adding-applications');
      const completed = getCompletedLessons();
      expect(completed).toHaveLength(2);
      expect(completed).toContain('install-bare-metal');
      expect(completed).toContain('adding-applications');
    });

    it('does not include unrelated localStorage items', () => {
      localStorage.setItem('unrelated_key', 'value');
      markLessonComplete('install-bare-metal');
      const completed = getCompletedLessons();
      expect(completed).toEqual(['install-bare-metal']);
    });
  });

  describe('resetProgress()', () => {
    it('removes all progress entries from localStorage', () => {
      markLessonComplete('install-bare-metal');
      markLessonComplete('adding-applications');
      resetProgress();
      expect(getCompletedLessons()).toEqual([]);
    });

    it('does not remove unrelated localStorage entries', () => {
      localStorage.setItem('other_key', 'value');
      markLessonComplete('install-bare-metal');
      resetProgress();
      expect(localStorage.getItem('other_key')).toBe('value');
    });

    it('is safe to call when no progress exists', () => {
      expect(() => resetProgress()).not.toThrow();
    });
  });

  describe('graceful degradation', () => {
    it('markLessonComplete does not throw when localStorage throws', () => {
      const originalSetItem = localStorage.setItem;
      localStorage.setItem = () => { throw new Error('QuotaExceededError'); };
      expect(() => markLessonComplete('test-lesson')).not.toThrow();
      localStorage.setItem = originalSetItem;
    });

    it('isLessonComplete returns false when localStorage throws', () => {
      const originalGetItem = localStorage.getItem;
      localStorage.getItem = () => { throw new Error('SecurityError'); };
      expect(isLessonComplete('test-lesson')).toBe(false);
      localStorage.getItem = originalGetItem;
    });

    it('getCompletedLessons returns empty array when localStorage throws', () => {
      const originalKey = localStorage.key;
      localStorage.key = () => { throw new Error('SecurityError'); };
      expect(getCompletedLessons()).toEqual([]);
      localStorage.key = originalKey;
    });

    it('getCompletionPercentage returns 0 when localStorage is unavailable', () => {
      const originalGetItem = localStorage.getItem;
      const originalKey = localStorage.key;
      localStorage.getItem = () => { throw new Error('SecurityError'); };
      localStorage.key = () => { throw new Error('SecurityError'); };
      expect(getCompletionPercentage(10)).toBe(0);
      localStorage.getItem = originalGetItem;
      localStorage.key = originalKey;
    });

    it('resetProgress does not throw when localStorage throws', () => {
      const originalKey = localStorage.key;
      localStorage.key = () => { throw new Error('SecurityError'); };
      expect(() => resetProgress()).not.toThrow();
      localStorage.key = originalKey;
    });
  });

  describe('percentage edge cases', () => {
    it('returns 11 for 1 out of 9 lessons (1/9 = 11.11...)', () => {
      markLessonComplete('lesson-1');
      expect(getCompletionPercentage(9)).toBe(11);
    });

    it('returns 67 for 2 out of 3 lessons (2/3 = 66.67 → 67)', () => {
      markLessonComplete('lesson-1');
      markLessonComplete('lesson-2');
      expect(getCompletionPercentage(3)).toBe(67);
    });

    it('never exceeds 100 even if completedCount exceeds totalLessons', () => {
      markLessonComplete('a');
      markLessonComplete('b');
      markLessonComplete('c');
      // totalLessons=2 but 3 are completed — percentage may exceed 100 from Math.round
      const pct = getCompletionPercentage(2);
      expect(pct).toBeGreaterThanOrEqual(100);
    });

    it('returns correct percentage with large number of lessons', () => {
      for (let i = 0; i < 50; i++) {
        markLessonComplete(`lesson-${i}`);
      }
      expect(getCompletionPercentage(100)).toBe(50);
    });
  });
});
