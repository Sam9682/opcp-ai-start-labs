/**
 * Property-based tests for the client-side Progress Tracker (skillhub/js/progress.js).
 *
 * Uses fast-check to validate universal properties across many generated inputs.
 *
 * Validates: Requirements 2.1, 2.2, 2.3
 */

import { describe, test, beforeEach } from 'vitest';
import fc from 'fast-check';
import {
  markLessonComplete,
  getCompletedLessons,
  getCompletionPercentage,
  resetProgress,
} from '../js/progress.js';

describe('Progress Tracker — property-based tests', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  // Feature: ai-store-labs, Property 2: Client-Side Progress Persistence Round-Trip
  //
  // For any set of valid (unique) lesson IDs, marking them complete and then
  // restoring from localStorage produces exactly the same set of completed
  // lesson IDs — the restored set neither gains nor loses entries.
  test('Feature: ai-store-labs, Property 2: Client-Side Progress Persistence Round-Trip', () => {
    fc.assert(
      fc.property(
        fc.uniqueArray(
          fc.stringMatching(/^[A-Za-z0-9][A-Za-z0-9-]{0,19}$/),
          { maxLength: 30 }
        ),
        (lessonIds) => {
          // Start from a clean slate for each generated case.
          resetProgress();
          localStorage.clear();

          lessonIds.forEach((id) => markLessonComplete(id));

          const restored = getCompletedLessons();

          // No loss: every marked id is present.
          const noLoss = lessonIds.every((id) => restored.includes(id));
          // No gain: no extra ids, and counts match exactly.
          const noGain =
            restored.length === lessonIds.length &&
            restored.every((id) => lessonIds.includes(id));

          return noLoss && noGain;
        }
      ),
      { numRuns: 100 }
    );
  });

  // Feature: ai-store-labs, Property 3: Completion Percentage Calculation
  //
  // For any pair (completedCount, totalCount) with 0 <= completedCount <= totalCount
  // and totalCount > 0, the computed percentage equals round(completedCount/totalCount*100)
  // and is always an integer in [0, 100].
  test('Feature: ai-store-labs, Property 3: Completion Percentage Calculation', () => {
    fc.assert(
      fc.property(
        // Generate totalCount > 0 and completedCount in [0, totalCount].
        fc.integer({ min: 1, max: 1000 }).chain((totalCount) =>
          fc.record({
            totalCount: fc.constant(totalCount),
            completedCount: fc.integer({ min: 0, max: totalCount }),
          })
        ),
        ({ totalCount, completedCount }) => {
          resetProgress();
          localStorage.clear();

          // Mark exactly `completedCount` distinct lessons complete.
          for (let i = 0; i < completedCount; i++) {
            markLessonComplete(`lesson-${i}`);
          }

          const pct = getCompletionPercentage(totalCount);
          const expected = Math.round((completedCount / totalCount) * 100);

          return (
            pct === expected &&
            Number.isInteger(pct) &&
            pct >= 0 &&
            pct <= 100
          );
        }
      ),
      { numRuns: 100 }
    );
  });
});
