/**
 * Lesson_Catalog - Defines all available lessons with metadata.
 * Each lesson has: id, slug, bilingual title, difficulty, estimatedMinutes, prerequisites.
 *
 * Validates: Requirements 1.3
 */

/**
 * @typedef {Object} LessonTitle
 * @property {string} en - English title
 * @property {string} fr - French title
 */

/**
 * @typedef {Object} Lesson
 * @property {string} id - Unique lesson identifier
 * @property {string} slug - URL-friendly slug
 * @property {LessonTitle} title - Bilingual title object
 * @property {"beginner"|"intermediate"|"advanced"} difficulty - Lesson difficulty level
 * @property {number} estimatedMinutes - Estimated completion time (1-480)
 * @property {string[]} prerequisites - Array of prerequisite lesson ids
 */

/** @type {Lesson[]} */
export const lessons = [
  {
    id: "install-bare-metal",
    slug: "install-bare-metal",
    title: {
      en: "Installation on Bare-Metal Ubuntu",
      fr: "Installation sur Ubuntu Bare-Metal"
    },
    difficulty: "beginner",
    estimatedMinutes: 120,
    prerequisites: []
  },
  {
    id: "adding-applications",
    slug: "adding-applications",
    title: {
      en: "Adding New Applications",
      fr: "Ajout de nouvelles applications"
    },
    difficulty: "beginner",
    estimatedMinutes: 60,
    prerequisites: ["install-bare-metal"]
  },
  {
    id: "starting-applications",
    slug: "starting-applications",
    title: {
      en: "Starting Applications",
      fr: "Démarrage des applications"
    },
    difficulty: "beginner",
    estimatedMinutes: 60,
    prerequisites: ["adding-applications"]
  },
  {
    id: "stopping-applications",
    slug: "stopping-applications",
    title: {
      en: "Stopping Applications",
      fr: "Arrêt des applications"
    },
    difficulty: "beginner",
    estimatedMinutes: 45,
    prerequisites: ["starting-applications"]
  },
  {
    id: "making-backups",
    slug: "making-backups",
    title: {
      en: "Making Backups",
      fr: "Création de sauvegardes"
    },
    difficulty: "intermediate",
    estimatedMinutes: 90,
    prerequisites: ["install-bare-metal"]
  },
  {
    id: "modifying-applications",
    slug: "modifying-applications",
    title: {
      en: "Modifying Existing Applications",
      fr: "Modification des applications existantes"
    },
    difficulty: "intermediate",
    estimatedMinutes: 90,
    prerequisites: ["adding-applications"]
  },
  {
    id: "mig-gpu",
    slug: "mig-gpu",
    title: {
      en: "Docker Applications with MIG GPU",
      fr: "Applications Docker avec GPU MIG"
    },
    difficulty: "advanced",
    estimatedMinutes: 120,
    prerequisites: ["starting-applications"]
  },
  {
    id: "serverless-execution",
    slug: "serverless-execution",
    title: {
      en: "Serverless Docker Execution",
      fr: "Exécution Docker sans serveur"
    },
    difficulty: "intermediate",
    estimatedMinutes: 60,
    prerequisites: ["starting-applications"]
  },
  {
    id: "billing-cost-tracking",
    slug: "billing-cost-tracking",
    title: {
      en: "Billing and Cost Tracking",
      fr: "Facturation et suivi des coûts"
    },
    difficulty: "intermediate",
    estimatedMinutes: 60,
    prerequisites: ["install-bare-metal"]
  }
];

/**
 * Find a lesson by its slug.
 * @param {string} slug - The lesson slug to search for
 * @returns {Lesson|undefined} The matching lesson or undefined if not found
 */
export function getLessonBySlug(slug) {
  return lessons.find((lesson) => lesson.slug === slug);
}

/**
 * Get all lessons matching a given difficulty level.
 * @param {"beginner"|"intermediate"|"advanced"} difficulty - The difficulty to filter by
 * @returns {Lesson[]} Array of lessons with the specified difficulty
 */
export function getLessonsByDifficulty(difficulty) {
  return lessons.filter((lesson) => lesson.difficulty === difficulty);
}

/**
 * Get the full prerequisite chain for a given lesson (recursive, depth-first).
 * Returns all lessons that must be completed before the specified lesson,
 * ordered from earliest prerequisite to the immediate prerequisite.
 * Each lesson appears at most once in the result (no duplicates).
 *
 * @param {string} lessonId - The lesson id to get prerequisites for
 * @returns {string[]} Ordered array of prerequisite lesson ids (earliest first)
 */
export function getPrerequisiteChain(lessonId) {
  const visited = new Set();
  const chain = [];

  function collect(id) {
    if (visited.has(id)) {
      return;
    }
    visited.add(id);

    const lesson = lessons.find((l) => l.id === id);
    if (!lesson) {
      return;
    }

    for (const prereqId of lesson.prerequisites) {
      collect(prereqId);
    }

    // Add the lesson after its prerequisites (topological order)
    // but don't include the originally requested lesson itself
    if (id !== lessonId) {
      chain.push(id);
    }
  }

  collect(lessonId);
  return chain;
}
