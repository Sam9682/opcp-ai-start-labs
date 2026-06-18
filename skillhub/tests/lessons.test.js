import { describe, it, expect } from 'vitest';
import {
  lessons,
  getLessonBySlug,
  getLessonsByDifficulty,
  getPrerequisiteChain,
} from '../js/lessons.js';

describe('Lesson Catalog', () => {
  describe('lessons data structure', () => {
    it('contains exactly 9 lessons', () => {
      expect(lessons).toHaveLength(9);
    });

    it('each lesson has all required fields', () => {
      const validDifficulties = ['beginner', 'intermediate', 'advanced'];

      for (const lesson of lessons) {
        expect(lesson).toHaveProperty('id');
        expect(lesson).toHaveProperty('slug');
        expect(lesson).toHaveProperty('title');
        expect(lesson.title).toHaveProperty('en');
        expect(lesson.title).toHaveProperty('fr');
        expect(validDifficulties).toContain(lesson.difficulty);
        expect(lesson.estimatedMinutes).toBeGreaterThanOrEqual(1);
        expect(lesson.estimatedMinutes).toBeLessThanOrEqual(480);
        expect(Array.isArray(lesson.prerequisites)).toBe(true);
      }
    });

    it('all prerequisite ids reference existing lessons', () => {
      const ids = lessons.map((l) => l.id);
      for (const lesson of lessons) {
        for (const prereq of lesson.prerequisites) {
          expect(ids).toContain(prereq);
        }
      }
    });

    it('each lesson has a unique id', () => {
      const ids = lessons.map((l) => l.id);
      expect(new Set(ids).size).toBe(ids.length);
    });

    it('each lesson has a unique slug', () => {
      const slugs = lessons.map((l) => l.slug);
      expect(new Set(slugs).size).toBe(slugs.length);
    });
  });

  describe('getLessonBySlug()', () => {
    it('returns the correct lesson for a valid slug', () => {
      const lesson = getLessonBySlug('install-bare-metal');
      expect(lesson).toBeDefined();
      expect(lesson.id).toBe('install-bare-metal');
      expect(lesson.title.en).toBe('Installation on Bare-Metal Ubuntu');
    });

    it('returns undefined for a non-existent slug', () => {
      expect(getLessonBySlug('non-existent')).toBeUndefined();
    });

    it('returns correct lesson for mig-gpu slug', () => {
      const lesson = getLessonBySlug('mig-gpu');
      expect(lesson).toBeDefined();
      expect(lesson.difficulty).toBe('advanced');
    });
  });

  describe('getLessonsByDifficulty()', () => {
    it('returns beginner lessons', () => {
      const beginner = getLessonsByDifficulty('beginner');
      expect(beginner.length).toBe(4);
      beginner.forEach((l) => expect(l.difficulty).toBe('beginner'));
    });

    it('returns intermediate lessons', () => {
      const intermediate = getLessonsByDifficulty('intermediate');
      expect(intermediate.length).toBe(4);
      intermediate.forEach((l) => expect(l.difficulty).toBe('intermediate'));
    });

    it('returns advanced lessons', () => {
      const advanced = getLessonsByDifficulty('advanced');
      expect(advanced.length).toBe(1);
      expect(advanced[0].id).toBe('mig-gpu');
    });

    it('returns empty array for invalid difficulty', () => {
      expect(getLessonsByDifficulty('expert')).toEqual([]);
    });
  });

  describe('getPrerequisiteChain()', () => {
    it('returns empty array for lesson with no prerequisites', () => {
      const chain = getPrerequisiteChain('install-bare-metal');
      expect(chain).toEqual([]);
    });

    it('returns direct prerequisite for single-depth dependency', () => {
      const chain = getPrerequisiteChain('adding-applications');
      expect(chain).toEqual(['install-bare-metal']);
    });

    it('returns full chain in topological order for deep dependency', () => {
      const chain = getPrerequisiteChain('stopping-applications');
      expect(chain).toEqual([
        'install-bare-metal',
        'adding-applications',
        'starting-applications',
      ]);
    });

    it('returns full chain for mig-gpu (3 levels deep)', () => {
      const chain = getPrerequisiteChain('mig-gpu');
      expect(chain).toEqual([
        'install-bare-metal',
        'adding-applications',
        'starting-applications',
      ]);
    });

    it('returns empty array for non-existent lesson', () => {
      const chain = getPrerequisiteChain('non-existent');
      expect(chain).toEqual([]);
    });

    it('does not include the lesson itself in the chain', () => {
      const chain = getPrerequisiteChain('billing-cost-tracking');
      expect(chain).not.toContain('billing-cost-tracking');
      expect(chain).toEqual(['install-bare-metal']);
    });

    it('produces no duplicate entries in the chain', () => {
      // modifying-applications → adding-applications → install-bare-metal
      const chain = getPrerequisiteChain('modifying-applications');
      const uniqueChain = [...new Set(chain)];
      expect(chain).toEqual(uniqueChain);
    });

    it('returns prerequisites in correct topological order (earliest first)', () => {
      const chain = getPrerequisiteChain('stopping-applications');
      const installIdx = chain.indexOf('install-bare-metal');
      const addingIdx = chain.indexOf('adding-applications');
      const startingIdx = chain.indexOf('starting-applications');
      expect(installIdx).toBeLessThan(addingIdx);
      expect(addingIdx).toBeLessThan(startingIdx);
    });
  });

  describe('lesson catalog integrity', () => {
    it('all lessons have integer estimatedMinutes values', () => {
      for (const lesson of lessons) {
        expect(Number.isInteger(lesson.estimatedMinutes)).toBe(true);
      }
    });

    it('no lesson has itself as a prerequisite', () => {
      for (const lesson of lessons) {
        expect(lesson.prerequisites).not.toContain(lesson.id);
      }
    });

    it('the prerequisite graph is acyclic (no circular dependencies)', () => {
      // Simple cycle detection using DFS
      const visited = new Set();
      const stack = new Set();

      function hasCycle(id) {
        if (stack.has(id)) return true;
        if (visited.has(id)) return false;
        visited.add(id);
        stack.add(id);
        const lesson = lessons.find((l) => l.id === id);
        if (lesson) {
          for (const prereq of lesson.prerequisites) {
            if (hasCycle(prereq)) return true;
          }
        }
        stack.delete(id);
        return false;
      }

      for (const lesson of lessons) {
        expect(hasCycle(lesson.id)).toBe(false);
      }
    });

    it('all difficulty values are one of the valid enum values', () => {
      const valid = ['beginner', 'intermediate', 'advanced'];
      for (const lesson of lessons) {
        expect(valid).toContain(lesson.difficulty);
      }
    });

    it('all titles have non-empty en and fr values', () => {
      for (const lesson of lessons) {
        expect(lesson.title.en.length).toBeGreaterThan(0);
        expect(lesson.title.fr.length).toBeGreaterThan(0);
      }
    });
  });
});
